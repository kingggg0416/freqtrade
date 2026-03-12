from datetime import datetime

from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class SessionFilteredMomentumStrategy(IStrategy):
    """
    Momentum continuation restricted to higher-liquidity weekdays and sessions.

    This turns the seasonality/time-of-day discussion into a conservative overlay:
    keep the logic simple, but avoid opening new positions during weaker market windows.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 120
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.14}
    stoploss = -0.06
    trailing_stop = False

    roc_period = IntParameter(6, 24, default=12, space="buy", optimize=True, load=True)
    roc_threshold = DecimalParameter(
        0.01, 0.08, default=0.025, decimals=3, space="buy", optimize=True, load=True
    )
    adx_threshold = IntParameter(16, 35, default=22, space="buy", optimize=True, load=True)
    vol_ceiling = DecimalParameter(
        0.015, 0.09, default=0.05, decimals=3, space="buy", optimize=True, load=True
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
            "Momentum": {
                "roc": {"color": "purple"},
                "adx": {"color": "blue"},
                "atr_pct": {"color": "orange"},
            }
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=int(self.roc_period.value)) / 100.0
        dataframe["adx"] = ta.ADX(dataframe)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["weekday"] = dataframe["date"].dt.weekday
        dataframe["hour"] = dataframe["date"].dt.hour
        dataframe["session_ok"] = (
            dataframe["weekday"].isin([0, 1, 2, 3, 4])
            & dataframe["hour"].isin([8, 12, 16])
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        vol_ok = dataframe["atr_pct"] < float(self.vol_ceiling.value)
        session_ok = dataframe["session_ok"]

        long_setup = (
            (dataframe["ema_fast"] > dataframe["ema_slow"])
            & (dataframe["roc"] > float(self.roc_threshold.value))
            & (dataframe["adx"] > self.adx_threshold.value)
            & vol_ok
            & session_ok
            & (dataframe["volume"] > 0)
        )
        short_setup = (
            (dataframe["ema_fast"] < dataframe["ema_slow"])
            & (dataframe["roc"] < -float(self.roc_threshold.value))
            & (dataframe["adx"] > self.adx_threshold.value)
            & vol_ok
            & session_ok
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "session_momentum_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "session_momentum_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_long = (
            (dataframe["ema_fast"] < dataframe["ema_slow"])
            | (dataframe["roc"] < 0)
            | (dataframe["adx"] < self.adx_threshold.value * 0.7)
        )
        exit_short = (
            (dataframe["ema_fast"] > dataframe["ema_slow"])
            | (dataframe["roc"] > 0)
            | (dataframe["adx"] < self.adx_threshold.value * 0.7)
        )

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "session_momentum_long_exit",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "session_momentum_short_exit",
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