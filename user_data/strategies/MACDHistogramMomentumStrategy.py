from datetime import datetime

from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class MACDHistogramMomentumStrategy(IStrategy):
    """
    MACD histogram momentum strategy with RSI filter.

    What this strategy does:
    - Uses the MACD histogram (the difference between the MACD line and the signal line)
      as the primary momentum indicator.
    - Enters long when the histogram crosses from negative to positive AND is accelerating
      upward (current bar > previous bar > 0).
    - Enters short when the histogram crosses from positive to negative AND is accelerating
      downward.
    - Adds an RSI filter to prevent entering into already overbought/oversold conditions.
    - Exits when the MACD histogram reverses direction.

    Why it may work:
    The MACD histogram captures momentum acceleration. A shift from negative to positive
    histogram readings reflects increasing buying pressure — the fast EMA is closing
    the gap with the slow EMA and accelerating. Academic research confirms that
    momentum indicators based on EMA convergence/divergence have explanatory power
    for short-to-medium-term returns in equity and crypto markets.

    The RSI filter prevents entering when price is already at an extreme (overbought
    for longs, oversold for shorts), which historically reduces the frequency of
    unfavorable entries at local exhaustion points.

    Expected failure modes:
    - Whipsaw in range-bound markets: MACD histograms oscillate rapidly.
    - Divergences (MACD positive but price falling) can produce false entries.
    - RSI is itself a lagging indicator and can stay extreme for extended periods.

    Retail-friendly because:
    - MACD is one of the most widely used indicators; logic is universally understood.
    - The RSI filter adds a secondary independent check on market extremes.
    - 4h timeframe gives several entries per week without over-trading.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 80
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.12}
    stoploss = -0.055
    trailing_stop = False

    macd_fast = IntParameter(8, 20, default=12, space="buy", optimize=True, load=True)
    macd_slow = IntParameter(20, 35, default=26, space="buy", optimize=True, load=True)
    macd_signal = IntParameter(5, 15, default=9, space="buy", optimize=True, load=True)
    rsi_period = IntParameter(10, 21, default=14, space="buy", optimize=True, load=True)
    rsi_overbought = IntParameter(65, 85, default=70, space="buy", optimize=True, load=True)
    rsi_oversold = IntParameter(15, 35, default=30, space="buy", optimize=True, load=True)

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {},
        "subplots": {
            "MACD": {
                "macd": {"color": "blue"},
                "macdsignal": {"color": "orange"},
                "macdhist": {"color": "green"},
            },
            "RSI": {
                "rsi": {"color": "purple"},
            },
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast = int(self.macd_fast.value)
        slow = int(self.macd_slow.value)
        signal = int(self.macd_signal.value)
        rsi_p = int(self.rsi_period.value)

        macd = ta.MACD(dataframe, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        # Histogram momentum: current hist greater than previous bar
        dataframe["hist_rising"] = dataframe["macdhist"] > dataframe["macdhist"].shift(1)
        dataframe["hist_falling"] = dataframe["macdhist"] < dataframe["macdhist"].shift(1)

        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=rsi_p)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi_ob = int(self.rsi_overbought.value)
        rsi_os = int(self.rsi_oversold.value)

        # Long: histogram crossed positive AND accelerating AND RSI not overbought
        hist_cross_up = (dataframe["macdhist"] > 0) & (dataframe["macdhist"].shift(1) <= 0)
        long_setup = (
            hist_cross_up
            & dataframe["hist_rising"]
            & (dataframe["rsi"] < rsi_ob)
            & (dataframe["volume"] > 0)
        )

        # Short: histogram crossed negative AND accelerating AND RSI not oversold
        hist_cross_down = (dataframe["macdhist"] < 0) & (dataframe["macdhist"].shift(1) >= 0)
        short_setup = (
            hist_cross_down
            & dataframe["hist_falling"]
            & (dataframe["rsi"] > rsi_os)
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "macd_hist_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "macd_hist_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exit long when histogram starts falling (momentum fading)
        exit_long = (dataframe["macdhist"] < 0) | dataframe["hist_falling"]
        # Exit short when histogram starts rising
        exit_short = (dataframe["macdhist"] > 0) | dataframe["hist_rising"]

        # Use cleaner exit: only exit on sign change of histogram
        exit_long_clean = dataframe["macdhist"] < 0
        exit_short_clean = dataframe["macdhist"] > 0

        dataframe.loc[exit_long_clean & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "macd_hist_exit_long",
        )
        dataframe.loc[exit_short_clean & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "macd_hist_exit_short",
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
