from datetime import datetime
from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import IntParameter, IStrategy


class DailyBreakoutTrendStrategy(IStrategy):
    """
    Daily breakout trend-following strategy inspired by the strategy guide's
    "Daily Breakout Trend" research direction.

    What this strategy does:
    - Trades only long, targeting slow structural trends that a retail trader can follow.
    - Enters when price breaks above a prior N-day high.
    - Exits when trend structure weakens via an M-day moving average breach or an opposite breakout.
        - Uses ADX as a regime filter so the strategy participates more in directional
            markets than in chop.

    Indicators / metrics used:
    - Rolling N-day breakout high / low
    - M-day simple moving average as the trend exit line
    - ADX as a trend-strength filter
    - ATR as a volatility context indicator for later review and plotting

    Why this may work:
    Trend following attempts to capture underreaction and persistent flows.
    In crypto majors, large directional moves can extend far longer than most
    mean-reversion traders expect. This strategy intentionally accepts a low
    win rate in exchange for positive skew from sustained trends.

    Expected failure mode:
    Sideways ranges can produce repeated false breakouts and whipsaws.
    The ADX filter reduces, but does not eliminate, this behavior.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "1d"
    startup_candle_count: int = 70
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.50}
    stoploss = -0.10
    trailing_stop = False

    breakout_window = IntParameter(30, 70, default=50, space="buy", optimize=True, load=True)
    exit_ma_period = IntParameter(10, 30, default=20, space="sell", optimize=True, load=True)
    adx_threshold = IntParameter(18, 35, default=25, space="buy", optimize=True, load=True)

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {
            "breakout_high": {"color": "green"},
            "breakout_low": {"color": "red"},
            "exit_sma": {"color": "orange"},
        },
        "subplots": {
            "Trend": {
                "adx": {"color": "blue"},
                "atr_pct": {"color": "purple"},
            }
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Build the slow-moving indicators needed for a breakout system.

        The breakout bands are shifted by one candle so signals are based only
        on fully known history.
        This avoids lookahead bias and keeps the implementation aligned with backtest reality.
        """
        breakout_window = int(self.breakout_window.value)
        exit_ma_period = int(self.exit_ma_period.value)

        dataframe["breakout_high"] = dataframe["high"].rolling(breakout_window).max().shift(1)
        dataframe["breakout_low"] = dataframe["low"].rolling(breakout_window).min().shift(1)
        dataframe["exit_sma"] = ta.SMA(dataframe, timeperiod=exit_ma_period)
        dataframe["adx"] = ta.ADX(dataframe)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Enter when price achieves a fresh N-day breakout and trend strength is adequate.
        """
        breakout_trigger = (
            (dataframe["close"] > dataframe["breakout_high"])
            & (dataframe["close"].shift(1) <= dataframe["breakout_high"].shift(1))
        )
        trend_filter = dataframe["adx"] > self.adx_threshold.value

        dataframe.loc[
            breakout_trigger & trend_filter & (dataframe["volume"] > 0),
            ["enter_long", "enter_tag"],
        ] = (1, "n_day_breakout_adx")

        short_breakdown_trigger = (
            (dataframe["close"] < dataframe["breakout_low"])
            & (dataframe["close"].shift(1) >= dataframe["breakout_low"].shift(1))
        )

        dataframe.loc[
            short_breakdown_trigger & trend_filter & (dataframe["volume"] > 0),
            ["enter_short", "enter_tag"],
        ] = (1, "n_day_breakdown_adx")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Exit if the trend weakens enough to violate the fast moving-average guard
        or if price collapses through the opposite breakout band.
        """
        ma_exit = (
            (dataframe["close"] < dataframe["exit_sma"])
            & (dataframe["close"].shift(1) >= dataframe["exit_sma"].shift(1))
        )
        breakdown_exit = (
            (dataframe["close"] < dataframe["breakout_low"])
            & (dataframe["close"].shift(1) >= dataframe["breakout_low"].shift(1))
        )

        dataframe.loc[
            (ma_exit | breakdown_exit) & (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"],
        ] = (1, "trend_exit_or_breakdown")

        short_ma_exit = (
            (dataframe["close"] > dataframe["exit_sma"])
            & (dataframe["close"].shift(1) <= dataframe["exit_sma"].shift(1))
        )
        breakout_reclaim_exit = (
            (dataframe["close"] > dataframe["breakout_high"])
            & (dataframe["close"].shift(1) <= dataframe["breakout_high"].shift(1))
        )

        dataframe.loc[
            (short_ma_exit | breakout_reclaim_exit) & (dataframe["volume"] > 0),
            ["exit_short", "exit_tag"],
        ] = (1, "short_trend_exit_or_reclaim")

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
        Use conservative leverage to reflect the guide's retail-first risk posture.
        """
        return min(2.0, max_leverage)
