from datetime import datetime

from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class TrendQualityStrategy(IStrategy):
    """
    Composite trend quality scoring strategy.

    What this strategy does:
    - Scores the quality of the current trend using three independent lenses:
        1. ADX strength: the higher the ADX, the more directional the market.
        2. EMA alignment: counts how many of [EMA21, EMA50, EMA100] are stacked in
           the right order (fast > mid > slow for uptrend, reverse for downtrend).
        3. Linear regression slope: the slope of a linear regression line fitted
           to recent closing prices, normalized by current price. A steep positive
           slope = strong upward price trajectory.
    - Only enters when all three components agree (composite score at maximum).
    - This triple-confirmation approach avoids entering weak or false trends.
    - Exits when the composite score falls below a minimum threshold.

    Why it may work:
    Each indicator captures a different aspect of trend quality:
    - ADX measures trend strength without direction bias.
    - EMA alignment captures multi-timeframe trend confirmation.
    - Regression slope captures the statistical direction of recent price action.
    Requiring all three to agree simultaneously filters out most choppy, weak,
    and sideways environments. The strategy trades infrequently but with higher
    expected quality per trade. This approach is consistent with systematic
    trend-following research that shows triple-confirmation filters improve
    risk-adjusted returns at the cost of reduced trade frequency.

    Expected failure modes:
    - Very few trades in range-bound markets (all quality scores collapse).
    - Trend reversals: by the time all three metrics reverse, some drawdown
      has already occurred.
    - Strong, sudden trend initiations may be missed because the score needs time
      to build.

    Retail-friendly because:
    - Each component is individually explainable and well-documented.
    - The score combines them transparently.
    - 4h timeframe is practical for a retail trader.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 150
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.18}
    stoploss = -0.065
    trailing_stop = False

    adx_threshold = IntParameter(20, 40, default=25, space="buy", optimize=True, load=True)
    linreg_period = IntParameter(15, 40, default=20, space="buy", optimize=True, load=True)
    linreg_slope_min = DecimalParameter(
        0.001, 0.010, default=0.003, decimals=4, space="buy", optimize=True, load=True
    )
    exit_score_threshold = IntParameter(1, 2, default=1, space="sell", optimize=True, load=True)

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {
            "ema21": {"color": "green"},
            "ema50": {"color": "orange"},
            "ema100": {"color": "red"},
        },
        "subplots": {
            "Quality Score": {
                "trend_score": {"color": "blue"},
            },
            "Components": {
                "adx": {"color": "gray"},
                "linreg_slope_norm": {"color": "purple"},
            },
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        lr_period = int(self.linreg_period.value)

        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema100"] = ta.EMA(dataframe, timeperiod=100)

        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)

        # Linear regression slope normalized by price
        linreg = ta.LINEARREG_SLOPE(dataframe["close"], timeperiod=lr_period)
        dataframe["linreg_slope"] = linreg
        dataframe["linreg_slope_norm"] = linreg / dataframe["close"]

        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        return dataframe

    def _compute_scores(self, dataframe: DataFrame) -> tuple:
        """Return (uptrend_score, downtrend_score) as integer 0-3."""
        adx_ok = dataframe["adx"] >= self.adx_threshold.value  # 0 or 1
        slope_min = float(self.linreg_slope_min.value)

        # EMA alignment: each step gives +1
        ema_bull = (dataframe["ema21"] > dataframe["ema50"]).astype(int) + (
            dataframe["ema50"] > dataframe["ema100"]
        ).astype(int)
        ema_bear = (dataframe["ema21"] < dataframe["ema50"]).astype(int) + (
            dataframe["ema50"] < dataframe["ema100"]
        ).astype(int)

        slope_bull = (dataframe["linreg_slope_norm"] > slope_min).astype(int)
        slope_bear = (dataframe["linreg_slope_norm"] < -slope_min).astype(int)

        uptrend_score = adx_ok.astype(int) + ema_bull + slope_bull
        downtrend_score = adx_ok.astype(int) + ema_bear + slope_bear

        return uptrend_score, downtrend_score

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        lr_period = int(self.linreg_period.value)

        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema100"] = ta.EMA(dataframe, timeperiod=100)

        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)

        linreg = ta.LINEARREG_SLOPE(dataframe["close"], timeperiod=lr_period)
        dataframe["linreg_slope"] = linreg
        dataframe["linreg_slope_norm"] = linreg / dataframe["close"]

        up_score, dn_score = self._compute_scores(dataframe)
        dataframe["trend_score"] = up_score.where(up_score >= dn_score, -dn_score)

        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        up_score, dn_score = self._compute_scores(dataframe)

        # Require maximum quality score (all 3 components agree)
        long_setup = (up_score == 3) & (dataframe["volume"] > 0)
        short_setup = (dn_score == 3) & (dataframe["volume"] > 0)

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "trend_quality_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "trend_quality_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        up_score, dn_score = self._compute_scores(dataframe)
        exit_thresh = int(self.exit_score_threshold.value)

        # Exit when quality score drops below threshold
        exit_long = (up_score <= exit_thresh) | (dn_score > up_score)
        exit_short = (dn_score <= exit_thresh) | (up_score > dn_score)

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "trend_quality_exit_long",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "trend_quality_exit_short",
        )
        return dataframe

    def leverage(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        return min(2.0, max_leverage)
