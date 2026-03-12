from datetime import datetime

from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class DualMACrossoverVolumeStrategy(IStrategy):
    """
    Classic dual EMA crossover with above-average volume confirmation.

    What this strategy does:
    - Generates a long signal when the fast EMA crosses above the slow EMA AND
      volume on that bar is above a rolling average, confirming institutional
      interest or at least a genuine surge in participation.
    - Generates a short signal when the fast EMA crosses below the slow EMA
      under the same volume condition.
    - Exits when the EMA relationship reverses.

    Why it may work:
    Moving average crossovers are one of the most time-tested trend-following
    techniques across all asset classes. The volume filter adds a quality check:
    genuine breakouts tend to happen on above-average volume while false moves
    tend to occur on thin, low-conviction volume. This reduces whipsaws and
    improves the signal-to-noise ratio compared to a pure crossover system.

    Expected failure modes:
    - Choppy, sideways markets produce many false crossover signals.
    - Volume spikes can occasionally signal exhaustion rather than continuation.
    - EMA lag means entries occur after the initial move has already started.

    Retail-friendly because:
    - Only requires standard OHLCV data (no exotic data sources).
    - Logic is completely transparent and explainable.
    - 4h timeframe gives ample time to execute without requiring speed.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 120
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.15}
    stoploss = -0.06
    trailing_stop = False

    fast_period = IntParameter(8, 30, default=20, space="buy", optimize=True, load=True)
    slow_period = IntParameter(40, 100, default=60, space="buy", optimize=True, load=True)
    volume_factor = DecimalParameter(
        1.0, 2.5, default=1.5, decimals=2, space="buy", optimize=True, load=True
    )
    volume_lookback = IntParameter(10, 30, default=20, space="buy", optimize=True, load=True)

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
            "Volume": {
                "volume_ratio": {"color": "blue"},
            },
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast_p = int(self.fast_period.value)
        slow_p = int(self.slow_period.value)
        vol_lb = int(self.volume_lookback.value)

        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=fast_p)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=slow_p)

        dataframe["volume_ma"] = dataframe["volume"].rolling(vol_lb).mean()
        dataframe["volume_ratio"] = dataframe["volume"] / dataframe["volume_ma"].replace(0, 1)

        # Crossover detection: fast crosses above slow
        dataframe["cross_up"] = (dataframe["ema_fast"] > dataframe["ema_slow"]) & (
            dataframe["ema_fast"].shift(1) <= dataframe["ema_slow"].shift(1)
        )
        # Crossunder detection: fast crosses below slow
        dataframe["cross_down"] = (dataframe["ema_fast"] < dataframe["ema_slow"]) & (
            dataframe["ema_fast"].shift(1) >= dataframe["ema_slow"].shift(1)
        )

        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        volume_ok = dataframe["volume_ratio"] >= float(self.volume_factor.value)

        long_setup = dataframe["cross_up"] & volume_ok & (dataframe["volume"] > 0)
        short_setup = dataframe["cross_down"] & volume_ok & (dataframe["volume"] > 0)

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "ma_cross_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "ma_cross_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_long = dataframe["ema_fast"] < dataframe["ema_slow"]
        exit_short = dataframe["ema_fast"] > dataframe["ema_slow"]

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "ma_cross_exit_long",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "ma_cross_exit_short",
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
