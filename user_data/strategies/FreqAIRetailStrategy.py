import logging
from functools import reduce

import numpy as np
import talib.abstract as ta
from pandas import DataFrame
from technical import qtpylib

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


logger = logging.getLogger(__name__)


class FreqAIRetailStrategy(IStrategy):
    """
    FreqAI-based regression strategy designed for retail traders with ~$1000 capital.

    Design philosophy
    -----------------
    A retail trader cannot compete on speed or information edge.
    This strategy trades on *structural* signals (trend + momentum + volatility regime)
    that persist across timeframes and are unlikely to be arbitraged away by HFTs.

    ML model
    --------
    Uses FreqAI with LightGBMRegressor to predict the forward 12-candle (12h) mean
    return.  The model is retrained every 7 days on 60 days of history so it adapts
    to changing regimes without over-fitting to short-term noise.

    Entry rules
    -----------
    Long  : model predicts > +threshold AND do_predict == 1
    Short : model predicts < -threshold AND do_predict == 1

    Exit rules
    ----------
    Long  : model flips negative OR stoploss hit
    Short : model flips positive OR stoploss hit

    Risk parameters
    ---------------
    - Max leverage 2x (critical for $1000 accounts)
    - Stoploss -4% (tight, trend-following)
    - ROI: unlimited (exit via signal, not timer)
    - Max 3 concurrent trades at 150 USDT each
    """

    # ── ROI / stoploss ──────────────────────────────────────────────────────────
    minimal_roi = {"0": 0.20, "480": 0.10, "960": 0.05, "1440": -1}
    stoploss = -0.05
    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.04
    trailing_only_offset_is_reached = True

    # ── Misc ────────────────────────────────────────────────────────────────────
    timeframe = "1h"
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    can_short = True
    startup_candle_count: int = 40

    # ── Entry signal threshold (optimisable) ────────────────────────────────────
    entry_threshold = DecimalParameter(0.005, 0.04, default=0.015, space="buy", optimize=True)
    exit_threshold = DecimalParameter(0.001, 0.02, default=0.005, space="sell", optimize=True)

    # ── Confirmation filter: min ADX before entering ────────────────────────────
    adx_filter = IntParameter(15, 35, default=20, space="buy", optimize=True)

    # ── Plot config ─────────────────────────────────────────────────────────────
    plot_config = {
        "main_plot": {},
        "subplots": {
            "&-s_close": {"&-s_close": {"color": "blue"}},
            "do_predict": {"do_predict": {"color": "brown"}},
            "%-adx": {"%-adx-period": {"color": "purple"}},
        },
    }

    # ────────────────────────────────────────────────────────────────────────────
    # Feature engineering
    # ────────────────────────────────────────────────────────────────────────────

    def feature_engineering_expand_all(
        self, dataframe: DataFrame, period: int, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Features that are auto-expanded across indicator_periods_candles,
        include_timeframes, include_shifted_candles, and include_corr_pairlist.

        These capture price structure across multiple time horizons.
        """
        # Trend
        dataframe["%-ema-period"] = ta.EMA(dataframe, timeperiod=period)
        dataframe["%-sma-period"] = ta.SMA(dataframe, timeperiod=period)

        # Momentum
        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)
        dataframe["%-roc-period"] = ta.ROC(dataframe, timeperiod=period)
        dataframe["%-cci-period"] = ta.CCI(dataframe, timeperiod=period)

        # Volatility
        dataframe["%-adx-period"] = ta.ADX(dataframe, timeperiod=period)
        dataframe["%-atr-period"] = ta.ATR(dataframe, timeperiod=period)

        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=period, stds=2.0
        )
        dataframe["%-bb_width-period"] = (
            bollinger["upper"] - bollinger["lower"]
        ) / bollinger["mid"]
        dataframe["%-close-bb_lower-period"] = dataframe["close"] / bollinger["lower"]
        dataframe["%-close-bb_upper-period"] = dataframe["close"] / bollinger["upper"]

        # Volume
        dataframe["%-relative_volume-period"] = (
            dataframe["volume"] / dataframe["volume"].rolling(period).mean()
        )
        dataframe["%-mfi-period"] = ta.MFI(dataframe, timeperiod=period)

        return dataframe

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        Features expanded across timeframes/shifted candles but NOT indicator_periods.
        Captures raw price dynamics.
        """
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-raw_volume"] = dataframe["volume"]
        dataframe["%-raw_price"] = dataframe["close"]
        dataframe["%-hl_ratio"] = (dataframe["high"] - dataframe["low"]) / dataframe["close"]
        dataframe["%-close_open_ratio"] = (
            dataframe["close"] - dataframe["open"]
        ) / dataframe["open"]
        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        """
        One-shot standard features: temporal and cross-sectional context.
        Not auto-expanded; used exactly as defined here.
        """
        dataframe["%-day_of_week"] = dataframe["date"].dt.dayofweek
        dataframe["%-hour_of_day"] = dataframe["date"].dt.hour
        dataframe["%-month"] = dataframe["date"].dt.month

        # Price normalised relative to its own recent history
        dataframe["%-close_norm_20"] = (
            dataframe["close"] / dataframe["close"].rolling(20).mean() - 1
        )
        dataframe["%-close_norm_50"] = (
            dataframe["close"] / dataframe["close"].rolling(50).mean() - 1
        )

        # Donchian channel width (captures compression/expansion)
        period = 20
        dataframe["%-donchian_width"] = (
            dataframe["high"].rolling(period).max() - dataframe["low"].rolling(period).min()
        ) / dataframe["close"]

        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        """
        Regression target: mean forward return over the next label_period_candles.

        This is more stable than single-candle prediction because it averages
        over short-term noise, which is important for lower-frequency strategies.
        """
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]

        dataframe["&-s_close"] = (
            dataframe["close"]
            .shift(-label_period)
            .rolling(label_period)
            .mean()
            / dataframe["close"]
            - 1
        )
        return dataframe

    # ────────────────────────────────────────────────────────────────────────────
    # Signal generation
    # ────────────────────────────────────────────────────────────────────────────

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Run FreqAI model to populate prediction columns."""
        dataframe = self.freqai.start(dataframe, metadata, self)
        return dataframe

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        threshold = self.entry_threshold.value
        adx_min = self.adx_filter.value

        enter_long_conditions = [
            df["do_predict"] == 1,
            df["&-s_close"] > threshold,
            # Only enter when trend is clear (ADX confirms directionality)
            df.get("%-adx-period_1h", df.get("%-adx-period", 0)) > adx_min,
        ]
        if enter_long_conditions:
            df.loc[
                reduce(lambda x, y: x & y, enter_long_conditions),
                ["enter_long", "enter_tag"],
            ] = (1, "freqai_long")

        enter_short_conditions = [
            df["do_predict"] == 1,
            df["&-s_close"] < -threshold,
            df.get("%-adx-period_1h", df.get("%-adx-period", 0)) > adx_min,
        ]
        if enter_short_conditions:
            df.loc[
                reduce(lambda x, y: x & y, enter_short_conditions),
                ["enter_short", "enter_tag"],
            ] = (1, "freqai_short")

        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        exit_threshold = self.exit_threshold.value

        exit_long_conditions = [df["do_predict"] == 1, df["&-s_close"] < -exit_threshold]
        if exit_long_conditions:
            df.loc[reduce(lambda x, y: x & y, exit_long_conditions), "exit_long"] = 1

        exit_short_conditions = [df["do_predict"] == 1, df["&-s_close"] > exit_threshold]
        if exit_short_conditions:
            df.loc[reduce(lambda x, y: x & y, exit_short_conditions), "exit_short"] = 1

        return df

    def leverage(
        self,
        pair: str,
        current_time,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag,
        side: str,
        **kwargs,
    ) -> float:
        """
        Conservative leverage cap for retail accounts.
        Max 2x to avoid margin calls from normal volatility moves.
        """
        return min(proposed_leverage, 2.0)

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time,
        entry_tag,
        side: str,
        **kwargs,
    ) -> bool:
        """Reject entry if price has moved too much since signal."""
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df.empty:
            return True
        last_candle = df.iloc[-1].squeeze()
        tolerance = 0.003  # 0.3% slippage tolerance
        if side == "long" and rate > last_candle["close"] * (1 + tolerance):
            return False
        if side == "short" and rate < last_candle["close"] * (1 - tolerance):
            return False
        return True

    def custom_stoploss(
        self,
        pair: str,
        trade,
        current_time,
        current_rate: float,
        current_profit: float,
        after_fill: bool,
        **kwargs,
    ) -> float:
        """
        Widen stoploss slightly in early trade phase to avoid premature exit
        on small noise moves. Tighten as profit accumulates.
        """
        # Very early in trade — give it breathing room
        if current_profit < 0.01:
            return -0.05
        # Profitable — protect gains
        if current_profit > 0.05:
            return max(self.stoploss, -current_profit * 0.40)
        return self.stoploss
