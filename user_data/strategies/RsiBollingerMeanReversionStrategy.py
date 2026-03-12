from datetime import datetime
from pandas import DataFrame

import talib.abstract as ta
from technical import qtpylib

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class RsiBollingerMeanReversionStrategy(IStrategy):
    """
    RSI + Bollinger Band mean-reversion strategy for slower crypto backtests.

    What this strategy does:
    - Buys temporary downside stretches rather than chasing strength.
    - Requires both a Bollinger-band extension and an oversold RSI reading.
    - Uses a light regime veto so the strategy is less likely to buy into severe downtrends.
    - Exits on reversion back toward the Bollinger mid-band or on RSI normalization.

    Indicators / metrics used:
    - Bollinger Bands for price stretch relative to a rolling mean
    - RSI for short-term exhaustion
    - SMA50 and ADX as a basic trend / regime veto

    Why this may work:
    On slower timeframes, liquid crypto pairs often overshoot during short-lived panic moves,
    then revert once forced selling subsides. The combination of Bollinger stretch and RSI
    exhaustion attempts to isolate these dislocations while avoiding the worst trend environments.

    Expected failure mode:
    The strategy can still catch falling knives if trend filters are too loose.
    Strong directional selloffs can keep price pinned below the lower band for longer than expected.
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
    stoploss = -0.05
    trailing_stop = False

    bb_period = IntParameter(15, 30, default=20, space="buy", optimize=True, load=True)
    bb_stddev = DecimalParameter(1.5, 2.5, default=2.0, decimals=1, space="buy", optimize=True)
    rsi_period = IntParameter(10, 21, default=14, space="buy", optimize=True, load=True)
    rsi_entry = IntParameter(20, 35, default=30, space="buy", optimize=True, load=True)
    rsi_exit = IntParameter(45, 65, default=52, space="sell", optimize=True, load=True)
    adx_range_ceiling = IntParameter(20, 35, default=25, space="buy", optimize=True, load=True)

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {
            "bb_lowerband": {"color": "green"},
            "bb_middleband": {"color": "orange"},
            "bb_upperband": {"color": "red"},
            "sma_50": {"color": "white"},
        },
        "subplots": {
            "MR": {
                "rsi": {"color": "purple"},
                "adx": {"color": "blue"},
            }
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Build the price-stretch and regime-veto indicators used by the mean-reversion setup.
        """
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe),
            window=int(self.bb_period.value),
            stds=float(self.bb_stddev.value),
        )
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]
        dataframe["bb_upperband"] = bollinger["upper"]

        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=int(self.rsi_period.value))
        dataframe["adx"] = ta.ADX(dataframe)
        dataframe["sma_50"] = ta.SMA(dataframe, timeperiod=50)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Enter only when price is stretched, momentum is exhausted, and the
        market is not strongly trending down.
        """
        price_stretch = dataframe["close"] < dataframe["bb_lowerband"]
        exhaustion = dataframe["rsi"] < self.rsi_entry.value
        regime_ok = (dataframe["close"] > dataframe["sma_50"]) | (
            dataframe["adx"] < self.adx_range_ceiling.value
        )

        dataframe.loc[
            price_stretch & exhaustion & regime_ok & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "bb_rsi_reversion")

        short_price_stretch = dataframe["close"] > dataframe["bb_upperband"]
        short_exhaustion = dataframe["rsi"] > (100 - self.rsi_entry.value)
        short_regime_ok = (dataframe["close"] < dataframe["sma_50"]) | (
            dataframe["adx"] < self.adx_range_ceiling.value
        )

        dataframe.loc[
            short_price_stretch & short_exhaustion & short_regime_ok & (dataframe["volume"] > 0),
            ["enter_short", "enter_tag"],
        ] = (1, "bb_rsi_short_reversion")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit once price has reverted toward the middle band or RSI has normalized.
        """
        revert_to_mean = qtpylib.crossed_above(dataframe["close"], dataframe["bb_middleband"])
        momentum_normalized = dataframe["rsi"] > self.rsi_exit.value

        dataframe.loc[
            (revert_to_mean | momentum_normalized) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "midband_or_rsi_normalized")

        short_revert_to_mean = qtpylib.crossed_below(dataframe["close"], dataframe["bb_middleband"])
        short_momentum_normalized = dataframe["rsi"] < (100 - self.rsi_exit.value)

        dataframe.loc[
            (short_revert_to_mean | short_momentum_normalized) & (dataframe["volume"] > 0),
            ["exit_short", "exit_tag"],
        ] = (1, "short_midband_or_rsi_normalized")

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
        """
        Use conservative 2x-or-less leverage for early futures backtests.
        """
        return min(2.0, max_leverage)
