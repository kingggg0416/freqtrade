from datetime import datetime

from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, informative


class BtcRegimeAdaptiveStrategy(IStrategy):
    """
    BTC regime-adaptive momentum strategy for ETH and SOL.

    What this strategy does:
    - Uses BTC's trend direction as a macro regime filter.
    - For each pair, only takes long positions when BTC is in an uptrend
      (BTC EMA50 > EMA200) and the pair itself shows momentum.
    - Only takes short positions when BTC is in a downtrend.
    - This reflects the high cross-asset correlation in crypto: when BTC breaks
      down, almost all altcoins follow; when BTC is strong, altcoins ride the wave.

    When trading BTC/USDT:USDT itself:
    - The informative BTC data equals the pair's own data.
    - The strategy degrades to a standard EMA-momentum filter (perfectly valid).

    Why it may work:
    Crypto markets are highly correlated with BTC. Historical analysis shows that
    the majority of altcoin gains occur during BTC uptrend periods, and the majority
    of altcoin losses occur during BTC downtrends. By filtering positions to match
    the macro BTC regime, we reduce the frequency of going against the dominant
    force in the market. This is a systematic implementation of the widely used
    intuition: "trade alts only when BTC is strong."

    Expected failure modes:
    - BTC regime lags price: transitions can take many bars to confirm.
    - Altcoin-specific fundamental events (listings, protocol failures) can dominate
      regardless of BTC regime.
    - If all three pairs are in the same regime, the filter may cause periods of zero
      open trades.

    Retail-friendly because:
    - The concept of using BTC as a market barometer is widely understood.
    - Regime identification via EMA cross is simple and transparent.
    - 4h timeframe reduces noise compared to shorter intervals.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 220
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.15}
    stoploss = -0.065
    trailing_stop = False

    # Pair-level momentum parameters
    momentum_lookback = IntParameter(20, 80, default=48, space="buy", optimize=True, load=True)
    momentum_threshold = DecimalParameter(
        0.02, 0.10, default=0.04, decimals=3, space="buy", optimize=True, load=True
    )
    pair_ema_fast = IntParameter(15, 40, default=24, space="buy", optimize=True, load=True)
    pair_ema_slow = IntParameter(50, 120, default=72, space="buy", optimize=True, load=True)

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {
            "pair_ema_fast_val": {"color": "green"},
            "pair_ema_slow_val": {"color": "red"},
        },
        "subplots": {
            "BTC Regime": {
                "btc_uptrend_4h": {"color": "blue"},
            },
            "Momentum": {
                "pair_cum_return": {"color": "purple"},
            },
        },
    }

    @informative("4h", "BTC/USDT:USDT")
    def populate_indicators_btc(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """Compute BTC regime indicators (EMA50 vs EMA200)."""
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["uptrend"] = (dataframe["ema50"] > dataframe["ema200"]).astype(int)
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        lb = int(self.momentum_lookback.value)
        fast_p = int(self.pair_ema_fast.value)
        slow_p = int(self.pair_ema_slow.value)

        # Per-pair momentum
        dataframe["pair_cum_return"] = dataframe["close"] / dataframe["close"].shift(lb) - 1.0

        # Per-pair EMA trend
        dataframe["pair_ema_fast_val"] = ta.EMA(dataframe, timeperiod=fast_p)
        dataframe["pair_ema_slow_val"] = ta.EMA(dataframe, timeperiod=slow_p)

        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        thresh = float(self.momentum_threshold.value)

        # BTC regime from informative (column name: uptrend_BTC/USDT:USDT_4h)
        # The informative decorator renames columns with pair and timeframe suffix
        btc_col = "uptrend_BTC/USDT:USDT_4h"
        if btc_col not in dataframe.columns:
            # Fallback: pair IS BTC, use own uptrend indicator
            btc_uptrend = (dataframe["pair_ema_fast_val"] > dataframe["pair_ema_slow_val"]).astype(
                int
            )
        else:
            btc_uptrend = dataframe[btc_col].fillna(0)

        pair_trend_up = dataframe["pair_ema_fast_val"] > dataframe["pair_ema_slow_val"]
        pair_trend_down = dataframe["pair_ema_fast_val"] < dataframe["pair_ema_slow_val"]

        long_setup = (
            (btc_uptrend == 1)
            & (dataframe["pair_cum_return"] > thresh)
            & pair_trend_up
            & (dataframe["volume"] > 0)
        )
        short_setup = (
            (btc_uptrend == 0)
            & (dataframe["pair_cum_return"] < -thresh)
            & pair_trend_down
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "btc_regime_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "btc_regime_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        btc_col = "uptrend_BTC/USDT:USDT_4h"
        if btc_col not in dataframe.columns:
            btc_uptrend = (dataframe["pair_ema_fast_val"] > dataframe["pair_ema_slow_val"]).astype(
                int
            )
        else:
            btc_uptrend = dataframe[btc_col].fillna(0)

        # Exit long when BTC regime flips to down or pair EMA flips
        exit_long = (btc_uptrend == 0) | (
            dataframe["pair_ema_fast_val"] < dataframe["pair_ema_slow_val"]
        )
        # Exit short when BTC regime flips to up or pair EMA flips
        exit_short = (btc_uptrend == 1) | (
            dataframe["pair_ema_fast_val"] > dataframe["pair_ema_slow_val"]
        )

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "btc_regime_exit_long",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "btc_regime_exit_short",
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
