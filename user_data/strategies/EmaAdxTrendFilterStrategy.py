from datetime import datetime

import numpy as np
from pandas import DataFrame

import talib.abstract as ta
from technical import qtpylib

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class EmaAdxTrendFilterStrategy(IStrategy):
    """
    EMA/ADX trend-following strategy with volatility-aware stake sizing.

    What this strategy does:
    - Trades only long in established upward trends.
    - Uses a fast/slow EMA structure to define the primary regime.
        - Waits for price to reclaim the fast EMA with MACD confirmation instead of
            buying strength blindly.
        - Scales stake size inversely with realized volatility so exposure is
            reduced when the market becomes unstable.

    Indicators / metrics used:
    - Fast EMA and slow EMA for regime definition
    - ADX for directional strength
    - MACD for trend continuation confirmation
    - 20-day realized volatility for volatility-aware stake sizing

    Why this may work:
    Retail traders usually lose edge when chasing noisy intraday moves. This strategy instead
    waits for a slower trend to be in place, then enters on orderly continuation. The volatility
    scaling is designed to keep dollar risk more stable across calm and volatile conditions.

    Expected failure mode:
    The strategy can underperform during sharp V-shaped reversals because the slow trend filter
    is intentionally late. It can also miss fast breakouts that never retest the fast EMA.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "1d"
    startup_candle_count: int = 220
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.50}
    stoploss = -0.09
    trailing_stop = False

    fast_ema_period = IntParameter(30, 80, default=50, space="buy", optimize=True, load=True)
    slow_ema_period = IntParameter(120, 250, default=200, space="buy", optimize=True, load=True)
    adx_threshold = IntParameter(18, 35, default=22, space="buy", optimize=True, load=True)
    volatility_target = DecimalParameter(
        0.008, 0.020, default=0.012, decimals=3, space="buy", optimize=False, load=True
    )

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {
            "ema_fast": {"color": "green"},
            "ema_slow": {"color": "red"},
        },
        "subplots": {
            "Trend": {
                "adx": {"color": "blue"},
                "macd": {"color": "purple"},
                "macdsignal": {"color": "orange"},
            },
            "Volatility": {
                "realized_vol_20": {"color": "brown"},
            },
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Build trend, momentum, and volatility indicators for the daily continuation setup.
        """
        fast_period = int(self.fast_ema_period.value)
        slow_period = int(self.slow_ema_period.value)

        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=fast_period)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=slow_period)
        dataframe["adx"] = ta.ADX(dataframe)

        macd = ta.MACD(dataframe)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]

        dataframe["realized_vol_20"] = dataframe["close"].pct_change().rolling(20).std()
        dataframe["ema_gap"] = (
            (dataframe["ema_fast"] - dataframe["ema_slow"]) / dataframe["ema_slow"]
        )

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Enter on a bullish continuation signal after price reclaims the fast EMA inside an uptrend.
        """
        trend_regime = (
            (dataframe["close"] > dataframe["ema_slow"])
            & (dataframe["ema_fast"] > dataframe["ema_slow"])
            & (dataframe["adx"] > self.adx_threshold.value)
        )

        continuation_trigger = qtpylib.crossed_above(dataframe["close"], dataframe["ema_fast"])
        momentum_confirmation = dataframe["macd"] > dataframe["macdsignal"]

        dataframe.loc[
            trend_regime
            & continuation_trigger
            & momentum_confirmation
            & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "ema_reclaim_macd_confirm")

        short_trend_regime = (
            (dataframe["close"] < dataframe["ema_slow"])
            & (dataframe["ema_fast"] < dataframe["ema_slow"])
            & (dataframe["adx"] > self.adx_threshold.value)
        )
        short_trigger = qtpylib.crossed_below(dataframe["close"], dataframe["ema_fast"])
        short_momentum_confirmation = dataframe["macd"] < dataframe["macdsignal"]

        dataframe.loc[
            short_trend_regime
            & short_trigger
            & short_momentum_confirmation
            & (dataframe["volume"] > 0),
            ["enter_short", "enter_tag"],
        ] = (1, "ema_reject_macd_confirm")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit when the continuation thesis breaks via fast EMA failure or MACD momentum loss.
        """
        exit_condition = (
            qtpylib.crossed_below(dataframe["close"], dataframe["ema_fast"])
            | qtpylib.crossed_below(dataframe["macd"], dataframe["macdsignal"])
        )

        dataframe.loc[
            exit_condition & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "ema_failure_or_macd_rollover")

        short_exit_condition = (
            qtpylib.crossed_above(dataframe["close"], dataframe["ema_fast"])
            | qtpylib.crossed_above(dataframe["macd"], dataframe["macdsignal"])
        )

        dataframe.loc[
            short_exit_condition & (dataframe["volume"] > 0),
            ["exit_short", "exit_tag"],
        ] = (1, "short_ema_failure_or_macd_reversal")

        return dataframe

    def custom_stake_amount(
        self,
        pair: str,
        current_time: datetime,
        current_rate: float,
        proposed_stake: float,
        min_stake: float | None,
        max_stake: float,
        leverage: float,
        entry_tag: str | None,
        side: str,
        **kwargs,
    ) -> float:
        """
        Scale stake inversely with 20-day realized volatility.

        This is a pragmatic Freqtrade-friendly approximation of constant-volatility sizing:
        when realized volatility rises, the stake is reduced; when volatility falls, the stake
        can increase, but never beyond available wallet limits.
        """
        if not self.dp:
            return proposed_stake

        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        if dataframe.empty:
            return proposed_stake

        current_candle = dataframe.iloc[-1]
        realized_vol = current_candle.get("realized_vol_20", np.nan)
        if not np.isfinite(realized_vol) or realized_vol <= 0:
            return proposed_stake

        raw_stake = proposed_stake * float(self.volatility_target.value) / float(realized_vol)
        capped_stake = min(max_stake, raw_stake, proposed_stake * 2.0)

        if min_stake is not None:
            capped_stake = max(min_stake, capped_stake)

        return float(capped_stake)

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
        """
        Keep leverage capped at 2x to match the guide's initial risk constraints.
        """
        return min(2.0, max_leverage)
