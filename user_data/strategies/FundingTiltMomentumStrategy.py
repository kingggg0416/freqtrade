from datetime import datetime

import numpy as np
from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, informative


class FundingTiltMomentumStrategy(IStrategy):
    """
    Trend-following with a historical funding-rate overlay.

    The goal is not to predict funding itself, but to avoid crowded longs and lean into shorts
    when carry is structurally favorable.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "1h"
    startup_candle_count: int = 220
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.12}
    stoploss = -0.055
    trailing_stop = False

    lookback_hours = IntParameter(48, 144, default=96, space="buy", optimize=True, load=True)
    momentum_threshold = DecimalParameter(
        0.02, 0.10, default=0.04, decimals=3, space="buy", optimize=True, load=True
    )
    vol_ceiling = DecimalParameter(
        0.01, 0.07, default=0.035, decimals=3, space="buy", optimize=True, load=True
    )
    long_funding_cap = DecimalParameter(
        0.00005, 0.00050, default=0.00022, decimals=5, space="buy", optimize=True, load=True
    )
    short_funding_floor = DecimalParameter(
        -0.00020, 0.00020, default=-0.00002, decimals=5, space="buy", optimize=True, load=True
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
                "cum_return": {"color": "blue"},
                "realized_vol": {"color": "orange"},
            },
            "Funding": {
                "funding_mean_1h": {"color": "purple"},
            },
        },
    }

    @informative("1h", candle_type="funding_rate")
    def populate_indicators_funding(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["funding_mean"] = dataframe["open"].rolling(5, min_periods=1).mean()
        dataframe["funding_extreme"] = dataframe["open"].rolling(9, min_periods=1).max()
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        lookback = int(self.lookback_hours.value)

        dataframe["cum_return"] = dataframe["close"] / dataframe["close"].shift(lookback) - 1.0
        dataframe["log_return"] = np.log(dataframe["close"] / dataframe["close"].shift(1))
        dataframe["realized_vol"] = (
            dataframe["log_return"].rolling(lookback).std() * np.sqrt(float(lookback))
        )
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=24)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=72)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        vol_ok = dataframe["realized_vol"] < float(self.vol_ceiling.value)
        funding_mean = dataframe["funding_mean_1h"].fillna(0.0)

        long_setup = (
            (dataframe["cum_return"] > float(self.momentum_threshold.value))
            & (dataframe["ema_fast"] > dataframe["ema_slow"])
            & vol_ok
            & (funding_mean < float(self.long_funding_cap.value))
            & (dataframe["volume"] > 0)
        )
        short_setup = (
            (dataframe["cum_return"] < -float(self.momentum_threshold.value))
            & (dataframe["ema_fast"] < dataframe["ema_slow"])
            & vol_ok
            & (funding_mean > float(self.short_funding_floor.value))
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "funding_tilt_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "funding_tilt_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        funding_mean = dataframe["funding_mean_1h"].fillna(0.0)

        exit_long = (
            (dataframe["cum_return"] < 0)
            | (dataframe["ema_fast"] < dataframe["ema_slow"])
            | (funding_mean > float(self.long_funding_cap.value) * 1.35)
        )
        exit_short = (
            (dataframe["cum_return"] > 0)
            | (dataframe["ema_fast"] > dataframe["ema_slow"])
            | (funding_mean < float(self.short_funding_floor.value) - 0.00010)
        )

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "funding_tilt_long_exit",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "funding_tilt_short_exit",
        )
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
        if not self.dp:
            return proposed_stake

        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        if dataframe.empty or "funding_mean_1h" not in dataframe.columns:
            return proposed_stake

        funding_mean = float(dataframe.iloc[-1].get("funding_mean_1h", 0.0))
        stake_multiplier = 1.0

        if side == "long":
            if funding_mean > 0.00015:
                stake_multiplier = 0.75
            elif funding_mean < 0:
                stake_multiplier = 1.10
        else:
            if funding_mean > 0.00010:
                stake_multiplier = 1.20
            elif funding_mean < -0.00010:
                stake_multiplier = 0.70

        sized_stake = min(max_stake, proposed_stake * stake_multiplier)
        if min_stake is not None:
            sized_stake = max(min_stake, sized_stake)
        return float(sized_stake)

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