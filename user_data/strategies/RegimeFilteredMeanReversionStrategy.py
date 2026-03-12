from datetime import datetime
from pandas import DataFrame

import talib.abstract as ta
from technical import qtpylib

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class RegimeFilteredMeanReversionStrategy(IStrategy):
    """
    Regime-filtered mean-reversion strategy.

    What this strategy does:
    - Trades only when the market looks range-bound rather than strongly directional.
    - Uses ADX and moving-average slope to classify whether a ranging regime is active.
    - Buys downside dislocations only after the ranging filter agrees with the setup.
    - Exits at the mean or when a fresh trend regime emerges against the position.

    Indicators / metrics used:
    - Bollinger Bands for deviation from mean
    - RSI for oversold confirmation
    - ADX for trend intensity
    - SMA50 slope for directional persistence / flatness

    Why this may work:
    Mean reversion tends to work best when markets oscillate around a fair value rather than trend.
    By explicitly filtering for low-trend conditions, the strategy tries to avoid the guide's core
    failure mode of buying into persistent breakdowns.

    Expected failure mode:
    Regime classification is never perfect. The strategy may miss profitable reversions if the
    filter is too strict, or still enter bad trades if a new trend begins before ADX reacts.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 90
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.10}
    stoploss = -0.045
    trailing_stop = False

    bb_period = IntParameter(15, 30, default=20, space="buy", optimize=True, load=True)
    bb_stddev = DecimalParameter(1.5, 2.5, default=2.0, decimals=1, space="buy", optimize=True)
    rsi_entry = IntParameter(20, 35, default=28, space="buy", optimize=True, load=True)
    rsi_exit = IntParameter(45, 65, default=55, space="sell", optimize=True, load=True)
    adx_ranging_threshold = IntParameter(20, 35, default=25, space="buy", optimize=True)
    adx_trending_threshold = IntParameter(26, 40, default=32, space="sell", optimize=True)
    slope_threshold = DecimalParameter(0.001, 0.010, default=0.004, decimals=3, space="buy")

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
            "Regime": {
                "adx": {"color": "blue"},
                "sma_50_slope": {"color": "purple"},
                "rsi": {"color": "brown"},
            }
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Build mean-reversion signals together with explicit regime classification metrics.
        """
        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe),
            window=int(self.bb_period.value),
            stds=float(self.bb_stddev.value),
        )
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]
        dataframe["bb_upperband"] = bollinger["upper"]

        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx"] = ta.ADX(dataframe)
        dataframe["sma_50"] = ta.SMA(dataframe, timeperiod=50)
        dataframe["sma_50_slope"] = dataframe["sma_50"].pct_change().fillna(0.0)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Enter only when both the mean-reversion setup and the ranging-regime filter align.
        """
        ranging_regime = (
            (dataframe["adx"] < self.adx_ranging_threshold.value)
            & (dataframe["sma_50_slope"].abs() < float(self.slope_threshold.value))
        )
        stretched = dataframe["close"] < dataframe["bb_lowerband"]
        exhausted = dataframe["rsi"] < self.rsi_entry.value

        dataframe.loc[
            ranging_regime & stretched & exhausted & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "range_regime_reversion")

        short_stretched = dataframe["close"] > dataframe["bb_upperband"]
        short_exhausted = dataframe["rsi"] > (100 - self.rsi_entry.value)

        dataframe.loc[
            ranging_regime & short_stretched & short_exhausted & (dataframe["volume"] > 0),
            ["enter_short", "enter_tag"],
        ] = (1, "range_regime_short_reversion")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit either on normal mean reversion or when the market shifts into a hostile trend regime.
        """
        mean_reversion_exit = (
            qtpylib.crossed_above(dataframe["close"], dataframe["bb_middleband"])
            | (dataframe["rsi"] > self.rsi_exit.value)
        )
        hostile_regime_exit = (
            (dataframe["adx"] > self.adx_trending_threshold.value)
            & (dataframe["close"] < dataframe["sma_50"])
        )

        dataframe.loc[
            (mean_reversion_exit | hostile_regime_exit) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "mean_reversion_complete_or_regime_shift")

        short_mean_reversion_exit = (
            qtpylib.crossed_below(dataframe["close"], dataframe["bb_middleband"])
            | (dataframe["rsi"] < (100 - self.rsi_exit.value))
        )
        hostile_short_regime_exit = (
            (dataframe["adx"] > self.adx_trending_threshold.value)
            & (dataframe["close"] > dataframe["sma_50"])
        )

        dataframe.loc[
            (short_mean_reversion_exit | hostile_short_regime_exit) & (dataframe["volume"] > 0),
            ["exit_short", "exit_tag"],
        ] = (1, "short_reversion_complete_or_regime_shift")

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
