from datetime import datetime

from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class MarketStructureSwingStrategy(IStrategy):
    """
    Market structure strategy based on Higher Highs / Higher Lows detection.

    What this strategy does:
    - Detects the structural state of the market by comparing rolling window highs
      and lows against their values N bars ago.
    - Uptrend structure: the current N-bar highest high is above the same measure
      from M bars ago (Higher Highs) AND the current N-bar lowest low is also above
      the same measure from M bars ago (Higher Lows).
    - Downtrend structure: Lower Highs AND Lower Lows.
    - Requires ADX confirmation to ensure the structural trend has momentum.
    - Uses an EMA as a secondary trend context filter.

    Why it may work:
    Classic Dow Theory and Wyckoff analysis define a trend as a series of Higher
    Highs and Higher Lows (uptrend) or Lower Highs and Lower Lows (downtrend).
    This structural view is more robust than EMAs because it is based on actual
    price extremes, not smoothed averages. When market structure shifts (e.g., the
    first HL after a series of LLs), it often marks the beginning of a new trend.
    Systematic detection of this shift is a robust, explainable entry condition.

    Expected failure modes:
    - Volatile, spiky markets create frequent false structural signals because
      one large wick can temporarily break the rolling high/low.
    - Transitions take several bars to confirm; entries are never at the exact turn.
    - Range-bound markets never develop sustained HH/HL or LH/LL structures.

    Retail-friendly because:
    - The concept of market structure is widely taught and understood by traders.
    - Rolling high/low comparisons are entirely transparent computations.
    - 1d timeframe reduces noise and keeps the signal count manageable.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "1d"
    startup_candle_count: int = 100
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.20}
    stoploss = -0.08
    trailing_stop = False

    swing_window = IntParameter(3, 10, default=5, space="buy", optimize=True, load=True)
    lookback_bars = IntParameter(10, 30, default=15, space="buy", optimize=True, load=True)
    adx_min = IntParameter(15, 30, default=20, space="buy", optimize=True, load=True)
    trend_ema = IntParameter(30, 80, default=50, space="buy", optimize=True, load=True)
    structure_score_min = DecimalParameter(
        0.001, 0.03, default=0.005, decimals=4, space="buy", optimize=True, load=True
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
            "swing_high_now": {"color": "green"},
            "swing_low_now": {"color": "red"},
            "ema_trend": {"color": "orange"},
        },
        "subplots": {
            "Structure": {
                "hh": {"color": "green"},
                "hl": {"color": "blue"},
                "lh": {"color": "red"},
                "ll": {"color": "purple"},
            },
            "ADX": {
                "adx": {"color": "gray"},
            },
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        sw = int(self.swing_window.value)
        lb = int(self.lookback_bars.value)
        ema_p = int(self.trend_ema.value)

        # Rolling swing high and low (current window)
        dataframe["swing_high_now"] = dataframe["high"].rolling(sw).max()
        dataframe["swing_low_now"] = dataframe["low"].rolling(sw).min()

        # Rolling swing high and low from lb bars ago (past reference)
        dataframe["swing_high_past"] = dataframe["swing_high_now"].shift(lb)
        dataframe["swing_low_past"] = dataframe["swing_low_now"].shift(lb)

        # Structure signals
        dataframe["hh"] = dataframe["swing_high_now"] > dataframe["swing_high_past"]
        dataframe["hl"] = dataframe["swing_low_now"] > dataframe["swing_low_past"]
        dataframe["lh"] = dataframe["swing_high_now"] < dataframe["swing_high_past"]
        dataframe["ll"] = dataframe["swing_low_now"] < dataframe["swing_low_past"]

        # Structure margin: how much higher are the new highs vs old highs?
        dataframe["hh_margin"] = (
            dataframe["swing_high_now"] / dataframe["swing_high_past"].replace(0, float("nan")) - 1
        )
        dataframe["ll_margin"] = (
            dataframe["swing_low_past"] / dataframe["swing_low_now"].replace(0, float("nan")) - 1
        )

        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["ema_trend"] = ta.EMA(dataframe, timeperiod=ema_p)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        adx_ok = dataframe["adx"] >= self.adx_min.value
        margin_min = float(self.structure_score_min.value)

        # Long: uptrend structure (Higher Highs AND Higher Lows) with trend and ADX
        long_setup = (
            dataframe["hh"]
            & dataframe["hl"]
            & (dataframe["hh_margin"] > margin_min)
            & (dataframe["close"] > dataframe["ema_trend"])
            & adx_ok
            & (dataframe["volume"] > 0)
        )
        # Short: downtrend structure (Lower Highs AND Lower Lows)
        short_setup = (
            dataframe["lh"]
            & dataframe["ll"]
            & (dataframe["ll_margin"] > margin_min)
            & (dataframe["close"] < dataframe["ema_trend"])
            & adx_ok
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "market_structure_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "market_structure_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exit when structure breaks (opposite structure forms or EMA flips)
        exit_long = dataframe["lh"] | (dataframe["close"] < dataframe["ema_trend"])
        exit_short = dataframe["hh"] | (dataframe["close"] > dataframe["ema_trend"])

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "market_structure_exit_long",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "market_structure_exit_short",
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
