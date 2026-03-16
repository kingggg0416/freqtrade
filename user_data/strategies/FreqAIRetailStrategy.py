import logging
from functools import reduce

import talib.abstract as ta
from pandas import DataFrame
from technical import qtpylib

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


logger = logging.getLogger(__name__)


class FreqAIRetailStrategy(IStrategy):
    """
    Retail-focused FreqAI strategy for Binance futures.

    The model predicts a forward mean return over the configured label horizon.
    Entries are gated by model confidence and ADX trend strength.
    """

    INTERFACE_VERSION = 3

    minimal_roi = {"0": 0.20, "480": 0.10, "960": 0.05, "1440": -1}
    stoploss = -0.05
    trailing_stop = True
    trailing_stop_positive = 0.02
    trailing_stop_positive_offset = 0.04
    trailing_only_offset_is_reached = True

    timeframe = "1h"
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    can_short = True
    startup_candle_count: int = 50

    entry_threshold = DecimalParameter(0.005, 0.04, default=0.015, space="buy", optimize=True)
    exit_threshold = DecimalParameter(0.001, 0.02, default=0.005, space="sell", optimize=True)
    adx_filter = IntParameter(15, 35, default=20, space="buy", optimize=True)

    plot_config = {
        "main_plot": {},
        "subplots": {
            "prediction": {"&-s_close": {"color": "blue"}},
            "predict_gate": {"do_predict": {"color": "brown"}},
            "adx": {"%-adx-period": {"color": "green"}},
        },
    }

    def feature_engineering_expand_all(
        self, dataframe: DataFrame, period: int, metadata: dict, **kwargs
    ) -> DataFrame:
        dataframe["%-ema-period"] = ta.EMA(dataframe, timeperiod=period)
        dataframe["%-sma-period"] = ta.SMA(dataframe, timeperiod=period)

        dataframe["%-rsi-period"] = ta.RSI(dataframe, timeperiod=period)
        dataframe["%-roc-period"] = ta.ROC(dataframe, timeperiod=period)
        dataframe["%-cci-period"] = ta.CCI(dataframe, timeperiod=period)

        dataframe["%-adx-period"] = ta.ADX(dataframe, timeperiod=period)
        dataframe["%-atr-period"] = ta.ATR(dataframe, timeperiod=period)

        bollinger = qtpylib.bollinger_bands(
            qtpylib.typical_price(dataframe), window=period, stds=2.0
        )
        dataframe["%-bb_width-period"] = (
            bollinger["upper"] - bollinger["lower"]
        ) / bollinger["mid"]
        dataframe["%-close-bb_lower-period"] = dataframe["close"] / bollinger["lower"]
        dataframe["%-close-bb_upper-period"] = dataframe["close"] / bollinger["upper"]

        dataframe["%-relative_volume-period"] = (
            dataframe["volume"] / dataframe["volume"].rolling(period).mean()
        )
        dataframe["%-mfi-period"] = ta.MFI(dataframe, timeperiod=period)

        return dataframe

    def feature_engineering_expand_basic(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        dataframe["%-pct-change"] = dataframe["close"].pct_change()
        dataframe["%-raw_volume"] = dataframe["volume"]
        dataframe["%-raw_price"] = dataframe["close"]
        dataframe["%-hl_ratio"] = (dataframe["high"] - dataframe["low"]) / dataframe["close"]
        dataframe["%-close_open_ratio"] = (
            dataframe["close"] - dataframe["open"]
        ) / dataframe["open"]
        return dataframe

    def feature_engineering_standard(
        self, dataframe: DataFrame, metadata: dict, **kwargs
    ) -> DataFrame:
        dataframe["%-day_of_week"] = dataframe["date"].dt.dayofweek
        dataframe["%-hour_of_day"] = dataframe["date"].dt.hour
        dataframe["%-month"] = dataframe["date"].dt.month

        dataframe["%-close_norm_20"] = (
            dataframe["close"] / dataframe["close"].rolling(20).mean() - 1
        )
        dataframe["%-close_norm_50"] = (
            dataframe["close"] / dataframe["close"].rolling(50).mean() - 1
        )

        period = 20
        dataframe["%-donchian_width"] = (
            dataframe["high"].rolling(period).max() - dataframe["low"].rolling(period).min()
        ) / dataframe["close"]

        return dataframe

    def set_freqai_targets(self, dataframe: DataFrame, metadata: dict, **kwargs) -> DataFrame:
        label_period = self.freqai_info["feature_parameters"]["label_period_candles"]

        dataframe["&-s_close"] = (
            dataframe["close"].shift(-label_period).rolling(label_period).mean()
            / dataframe["close"]
            - 1
        )
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return self.freqai.start(dataframe, metadata, self)

    def populate_entry_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        threshold = self.entry_threshold.value
        adx_min = self.adx_filter.value

        adx_col = "%-adx-period_1h"
        if adx_col not in df.columns:
            adx_col = "%-adx-period"

        long_conditions = [
            df["do_predict"] == 1,
            df["&-s_close"] > threshold,
            df[adx_col] > adx_min,
        ]
        df.loc[reduce(lambda x, y: x & y, long_conditions), ["enter_long", "enter_tag"]] = (
            1,
            "freqai_long",
        )

        short_conditions = [
            df["do_predict"] == 1,
            df["&-s_close"] < -threshold,
            df[adx_col] > adx_min,
        ]
        df.loc[reduce(lambda x, y: x & y, short_conditions), ["enter_short", "enter_tag"]] = (
            1,
            "freqai_short",
        )

        return df

    def populate_exit_trend(self, df: DataFrame, metadata: dict) -> DataFrame:
        threshold = self.exit_threshold.value

        long_exit = [df["do_predict"] == 1, df["&-s_close"] < -threshold]
        df.loc[reduce(lambda x, y: x & y, long_exit), "exit_long"] = 1

        short_exit = [df["do_predict"] == 1, df["&-s_close"] > threshold]
        df.loc[reduce(lambda x, y: x & y, short_exit), "exit_short"] = 1

        return df

    def leverage(
        self,
        pair: str,
        current_time,
        current_rate: float,
        proposed_leverage: float,
        max_leverage: float,
        entry_tag,
        side: str,
        **kwargs,
    ) -> float:
        return min(proposed_leverage, 2.0)

    def confirm_trade_entry(
        self,
        pair: str,
        order_type: str,
        amount: float,
        rate: float,
        time_in_force: str,
        current_time,
        entry_tag,
        side: str,
        **kwargs,
    ) -> bool:
        df, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if df.empty:
            return True

        last_candle = df.iloc[-1].squeeze()
        tolerance = 0.003
        if side == "long" and rate > last_candle["close"] * (1 + tolerance):
            return False
        if side == "short" and rate < last_candle["close"] * (1 - tolerance):
            return False
        return True

    def custom_stoploss(
        self,
        pair: str,
        trade,
        current_time,
        current_rate: float,
        current_profit: float,
        after_fill: bool,
        **kwargs,
    ) -> float:
        if current_profit < 0.01:
            return -0.05
        if current_profit > 0.05:
            return max(self.stoploss, -current_profit * 0.40)
        return self.stoploss
