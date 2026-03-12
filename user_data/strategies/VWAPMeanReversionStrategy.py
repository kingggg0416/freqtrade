from datetime import datetime

import numpy as np
from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class VWAPMeanReversionStrategy(IStrategy):
    """
    Rolling VWAP mean-reversion strategy for range-bound markets.

    What this strategy does:
    - Computes a rolling Volume-Weighted Average Price (VWAP) over a configurable
      lookback window using bar-level price and volume data.
    - Adds standard-deviation bands around the VWAP (similar to Bollinger Bands
      but anchored to the volume-weighted center).
    - Enters long when price is significantly below the VWAP lower band in a
      low-volatility environment (expecting reversion toward VWAP).
    - Enters short when price is significantly above the VWAP upper band.
    - Requires that the market is not trending strongly (ADX below a threshold),
      since mean reversion works poorly in strong trends.

    Why it may work:
    In crypto, large institutional participants, market makers, and arbitrageurs
    often use VWAP as a reference price. When price deviates materially from VWAP
    in a range-bound market, it tends to attract counter-pressure and revert.
    This is consistent with intraday mean-reversion evidence documented in crypto
    and traditional markets during quiet, low-trend conditions.

    Expected failure modes:
    - Strong directional trends render VWAP deviations persistent, not transient.
    - Breakout events (news, liquidation cascades) can extend far beyond bands.
    - Works best in narrow ranges; all mean-reversion strategies suffer in trending regimes.

    Retail-friendly because:
    - VWAP is directly computable from standard OHLCV candles.
    - Entries are at extremes (below/above bands), giving clear price context.
    - 4h timeframe is practical for retail execution.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 80
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.08}
    stoploss = -0.05
    trailing_stop = False

    vwap_lookback = IntParameter(20, 60, default=40, space="buy", optimize=True, load=True)
    band_sigma = DecimalParameter(
        1.0, 3.0, default=2.0, decimals=1, space="buy", optimize=True, load=True
    )
    adx_max = IntParameter(15, 35, default=25, space="buy", optimize=True, load=True)

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {
            "vwap": {"color": "orange"},
            "vwap_upper": {"color": "red"},
            "vwap_lower": {"color": "green"},
        },
        "subplots": {
            "ADX": {
                "adx": {"color": "blue"},
            },
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        lb = int(self.vwap_lookback.value)

        typical_price = (dataframe["high"] + dataframe["low"] + dataframe["close"]) / 3
        vp = typical_price * dataframe["volume"]

        rolling_vp = vp.rolling(lb).sum()
        rolling_vol = dataframe["volume"].rolling(lb).sum().replace(0, np.nan)

        dataframe["vwap"] = rolling_vp / rolling_vol

        # Standard deviation of typical price around VWAP
        deviation = typical_price - dataframe["vwap"]
        rolling_std = deviation.rolling(lb).std()

        sigma = float(self.band_sigma.value)
        dataframe["vwap_upper"] = dataframe["vwap"] + sigma * rolling_std
        dataframe["vwap_lower"] = dataframe["vwap"] - sigma * rolling_std

        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Require non-trending market
        low_trend = dataframe["adx"] < self.adx_max.value

        long_setup = (
            (dataframe["close"] < dataframe["vwap_lower"])
            & low_trend
            & (dataframe["volume"] > 0)
        )
        short_setup = (
            (dataframe["close"] > dataframe["vwap_upper"])
            & low_trend
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "vwap_reversion_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "vwap_reversion_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exit when price reverts back to VWAP
        exit_long = dataframe["close"] >= dataframe["vwap"]
        exit_short = dataframe["close"] <= dataframe["vwap"]

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "vwap_reversion_exit_long",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "vwap_reversion_exit_short",
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
        return min(1.5, max_leverage)
