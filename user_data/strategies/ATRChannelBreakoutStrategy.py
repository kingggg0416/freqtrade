from datetime import datetime

from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class ATRChannelBreakoutStrategy(IStrategy):
    """
    ATR-based N-period channel breakout without a compression requirement.

    What this strategy does:
    - Tracks the rolling N-period highest high and lowest low to define a price channel.
    - Enters long when price closes above the upper channel boundary.
    - Enters short when price closes below the lower channel boundary.
    - Uses ATR to filter out entries when price is already over-extended
      (i.e., the move is too far from the channel edge relative to ATR).
    - Exits when price re-enters the mid-point of the channel (Bollinger middle basis).

    Difference from VolatilityCompressionBreakoutStrategy:
    - This strategy does NOT require volatility compression before the breakout.
    - It is suitable as a slower daily trend-following system.
    - The ADX filter is lighter, allowing earlier entries.
    - Designed for 1d timeframe to reduce noise and false signals.

    Why it may work:
    Channel breakouts are rooted in the concept that sustained price discovery at new
    N-period extremes reflects genuine supply/demand imbalances. When a market has not
    traded above a level for N days, a close above that level signals new commitment
    from buyers. The ATR over-extension filter limits chasing moves that have already
    run too far.

    Expected failure modes:
    - False breakouts at range boundaries are common; the strategy will incur whipsaw
      losses in extended sideways markets.
    - On daily bars, stop placement is wider, leading to larger per-trade risk.

    Retail-friendly because:
    - Logic is simple and well-documented in trend-following literature.
    - Daily bars require only one evaluation per day.
    - Both the signal and the stop are mechanically defined by recent price action.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "1d"
    startup_candle_count: int = 80
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.25}
    stoploss = -0.08
    trailing_stop = False

    channel_window = IntParameter(15, 55, default=30, space="buy", optimize=True, load=True)
    atr_extension_cap = DecimalParameter(
        0.02, 0.12, default=0.05, decimals=3, space="buy", optimize=True, load=True
    )
    adx_min = IntParameter(15, 30, default=20, space="buy", optimize=True, load=True)
    exit_ema_period = IntParameter(15, 40, default=20, space="sell", optimize=True, load=True)

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {
            "channel_high": {"color": "green"},
            "channel_low": {"color": "red"},
            "exit_ema": {"color": "orange"},
        },
        "subplots": {
            "ADX": {
                "adx": {"color": "blue"},
                "atr_pct": {"color": "purple"},
            }
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        ch_win = int(self.channel_window.value)
        exit_period = int(self.exit_ema_period.value)

        # Channel: use shift(1) so we only use completed bars (avoid lookahead)
        dataframe["channel_high"] = dataframe["high"].rolling(ch_win).max().shift(1)
        dataframe["channel_low"] = dataframe["low"].rolling(ch_win).min().shift(1)

        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]

        # Exit reference: EMA of close
        dataframe["exit_ema"] = ta.EMA(dataframe, timeperiod=exit_period)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        trend_present = dataframe["adx"] >= self.adx_min.value
        not_extended = dataframe["atr_pct"] < float(self.atr_extension_cap.value)

        long_setup = (
            (dataframe["close"] > dataframe["channel_high"])
            & trend_present
            & not_extended
            & (dataframe["volume"] > 0)
        )
        short_setup = (
            (dataframe["close"] < dataframe["channel_low"])
            & trend_present
            & not_extended
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "atr_channel_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "atr_channel_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exit long when price falls back below the exit EMA
        exit_long = dataframe["close"] < dataframe["exit_ema"]
        # Exit short when price rises back above the exit EMA
        exit_short = dataframe["close"] > dataframe["exit_ema"]

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "atr_channel_exit_long",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "atr_channel_exit_short",
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
