from datetime import datetime

import numpy as np
from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class TimeSeriesMomentumVolatilityStrategy(IStrategy):
    """
    Medium-horizon time-series momentum with a volatility filter.

    This strategy maps closely to the research note's core retail-friendly idea:
    trade slow directional persistence, but stand down when realized volatility is too stressed.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 160
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.18}
    stoploss = -0.07
    trailing_stop = False

    lookback_candles = IntParameter(42, 126, default=84, space="buy", optimize=True, load=True)
    momentum_threshold = DecimalParameter(
        0.03, 0.12, default=0.06, decimals=3, space="buy", optimize=True, load=True
    )
    vol_ceiling = DecimalParameter(
        0.02, 0.10, default=0.055, decimals=3, space="buy", optimize=True, load=True
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
            "ema_trend": {"color": "orange"},
        },
        "subplots": {
            "Momentum": {
                "cum_return": {"color": "green"},
                "realized_vol": {"color": "red"},
                "atr_pct": {"color": "blue"},
            }
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        lookback = int(self.lookback_candles.value)

        dataframe["cum_return"] = dataframe["close"] / dataframe["close"].shift(lookback) - 1.0
        dataframe["log_return"] = np.log(dataframe["close"] / dataframe["close"].shift(1))
        dataframe["realized_vol"] = (
            dataframe["log_return"].rolling(lookback).std() * np.sqrt(float(lookback))
        )
        dataframe["ema_trend"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        vol_ok = dataframe["realized_vol"] < float(self.vol_ceiling.value)

        long_setup = (
            (dataframe["cum_return"] > float(self.momentum_threshold.value))
            & (dataframe["close"] > dataframe["ema_trend"])
            & vol_ok
            & (dataframe["volume"] > 0)
        )
        short_setup = (
            (dataframe["cum_return"] < -float(self.momentum_threshold.value))
            & (dataframe["close"] < dataframe["ema_trend"])
            & vol_ok
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "tsmom_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "tsmom_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        vol_stress = dataframe["realized_vol"] > float(self.vol_ceiling.value) * 1.15

        exit_long = (
            (dataframe["cum_return"] < 0)
            | (dataframe["close"] < dataframe["ema_trend"])
            | vol_stress
        )
        exit_short = (
            (dataframe["cum_return"] > 0)
            | (dataframe["close"] > dataframe["ema_trend"])
            | vol_stress
        )

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "tsmom_long_exit",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "tsmom_short_exit",
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