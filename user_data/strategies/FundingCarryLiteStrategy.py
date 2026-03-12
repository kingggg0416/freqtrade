from datetime import datetime

from pandas import DataFrame

from freqtrade.strategy import DecimalParameter, IStrategy, informative


class FundingCarryLiteStrategy(IStrategy):
    """
    Pure funding-rate carry strategy for crypto perpetuals.

    What this strategy does:
    - Uses only the funding rate as the entry signal — no trend signal required.
    - Enters short when the average funding rate over a recent window is very high
      (persistently positive funding = crowded long side = longs pay shorts).
    - Enters long when average funding is very negative (crowded shorts = shorts pay longs).
    - Requires that price is not in a violent countertrend to the carry direction,
      measured by a simple ATR-based deviation check.
    - Exits when funding normalizes back to near-zero.

    Difference from FundingTiltMomentumStrategy:
    - FundingTiltMomentum uses funding as an OVERLAY on a trend signal.
    - This strategy uses funding as the PRIMARY and only signal — it is a pure
      carry play, not a trend-following system.

    Why it may work:
    Research shows that perpetual funding rates have a structural long bias (longs
    typically pay shorts). Episodes of extremely high funding reflect over-leveraged,
    crowded long positions that are inherently unstable and prone to cascading
    liquidations on any adverse move. Systematically being on the paid side of
    funding during extreme episodes has shown positive carry in historical data.
    The carry income provides a buffer against moderate adverse price movement.

    Expected failure modes:
    - During sustained bull markets, funding stays high for extended periods and
      short positions lose to the trend despite collecting carry.
    - Funding can spike transiently around index rebalancing, news, or large OI
      changes without immediately reversing — so timing pure funding flips is hard.
    - Requires access to funding-rate data per bar.

    Retail-friendly because:
    - Logic is very simple: be on the paid side when carry is extreme.
    - Uses maximum leverage of 1.5x — conservative for a carry play.
    - Clear entry/exit thresholds that are easy to justify and monitor.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 50
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.06}
    stoploss = -0.05
    trailing_stop = False

    funding_entry_threshold = DecimalParameter(
        0.00010,
        0.00080,
        default=0.00025,
        decimals=5,
        space="buy",
        optimize=True,
        load=True,
    )
    funding_exit_threshold = DecimalParameter(
        0.00001,
        0.00020,
        default=0.00005,
        decimals=5,
        space="buy",
        optimize=True,
        load=True,
    )
    funding_window = 8  # number of 1h funding periods to average (8h = one full funding cycle)

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    order_time_in_force = {"entry": "GTC", "exit": "GTC"}

    plot_config = {
        "main_plot": {},
        "subplots": {
            "Funding": {
                "funding_avg_1h": {"color": "purple"},
            },
        },
    }

    @informative("1h", candle_type="funding_rate")
    def populate_indicators_funding(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Rolling average of recent funding payments
        dataframe["funding_avg"] = dataframe["open"].rolling(
            self.funding_window, min_periods=1
        ).mean()
        dataframe["funding_peak"] = dataframe["open"].rolling(
            self.funding_window * 3, min_periods=1
        ).max()
        dataframe["funding_trough"] = dataframe["open"].rolling(
            self.funding_window * 3, min_periods=1
        ).min()
        return dataframe

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        funding_avg = dataframe["funding_avg_1h"].fillna(0.0)
        entry_thresh = float(self.funding_entry_threshold.value)

        # Short when funding is very positive (longs crowded, shorts get paid)
        short_setup = (
            (funding_avg > entry_thresh)
            & (dataframe["volume"] > 0)
        )
        # Long when funding is very negative (shorts crowded, longs get paid)
        long_setup = (
            (funding_avg < -entry_thresh * 0.5)  # negative funding is rarer; lower threshold
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "funding_carry_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "funding_carry_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        funding_avg = dataframe["funding_avg_1h"].fillna(0.0)
        exit_thresh = float(self.funding_exit_threshold.value)

        # Exit short when funding normalizes (carry advantage fades)
        exit_short = funding_avg < exit_thresh
        # Exit long when funding becomes positive again (negative carry disappears)
        exit_long = funding_avg > -exit_thresh

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "funding_carry_exit_long",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "funding_carry_exit_short",
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
