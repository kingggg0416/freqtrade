from datetime import datetime

import numpy as np
from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class SupertrendFollowStrategy(IStrategy):
    """
    Supertrend indicator trend-following strategy.

    What this strategy does:
    - Computes the Supertrend indicator, which combines ATR-based bands with price
      position to produce a binary trend signal: either uptrend or downtrend.
    - Enters long immediately when the Supertrend flips from downtrend to uptrend
      (price crosses above the upper ATR band and stays there).
    - Enters short immediately when the Supertrend flips from uptrend to downtrend.
    - Exits when the Supertrend flips back (trend reversal detected).

    How Supertrend works:
    - Upper band = (High + Low) / 2 + multiplier × ATR
    - Lower band = (High + Low) / 2 − multiplier × ATR
    - Direction is maintained: if trending up, only the lower band acts as support
      (it ratchets up but never down). If trending down, only the upper band acts as
      resistance (it ratchets down but never up).
    - A flip occurs when price closes through the active band.

    Why it may work:
    The Supertrend is a self-adjusting trailing indicator that uses recent volatility
    (ATR) to set dynamic support/resistance. Compared to simple EMA crossovers, it
    is less prone to small oscillations because the band only moves in one direction
    until a genuine reversal. It has been shown to work across multiple asset classes
    and timeframes and is popular in crypto communities.

    Expected failure modes:
    - In whipsaw (sideways/choppy) conditions, the indicator flips rapidly, leading
      to multiple losing trades in quick succession.
    - The ATR multiplier is the most sensitive parameter: too tight and it whipsaws,
      too loose and entries are excessively delayed.

    Retail-friendly because:
    - Signal is a simple up/down flip — very easy to implement and explain.
    - 4h timeframe is manageable without constant monitoring.
    - Both entry and exit are driven by the same mechanical rule.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 60
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.18}
    stoploss = -0.07
    trailing_stop = False

    st_period = IntParameter(7, 20, default=10, space="buy", optimize=True, load=True)
    st_multiplier = DecimalParameter(
        1.5, 5.0, default=3.0, decimals=1, space="buy", optimize=True, load=True
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
            "supertrend": {"color": "purple"},
        },
        "subplots": {
            "Direction": {
                "st_direction": {"color": "blue"},
            },
        },
    }

    @staticmethod
    def _compute_supertrend(
        close: np.ndarray, high: np.ndarray, low: np.ndarray, atr: np.ndarray, multiplier: float
    ):
        """Compute Supertrend using iterative state tracking."""
        n = len(close)
        hl2 = (high + low) / 2.0

        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr

        final_upper = upper_band.copy()
        final_lower = lower_band.copy()
        supertrend = np.full(n, np.nan)
        direction = np.ones(n)  # 1 = downtrend (price below), -1 = uptrend (price above)

        for i in range(1, n):
            if np.isnan(atr[i]):
                continue

            # Ratchet upper band: only tighten, never widen while in downtrend
            if upper_band[i] < final_upper[i - 1] or close[i - 1] > final_upper[i - 1]:
                final_upper[i] = upper_band[i]
            else:
                final_upper[i] = final_upper[i - 1]

            # Ratchet lower band: only rise, never fall while in uptrend
            if lower_band[i] > final_lower[i - 1] or close[i - 1] < final_lower[i - 1]:
                final_lower[i] = lower_band[i]
            else:
                final_lower[i] = final_lower[i - 1]

            prev_st = supertrend[i - 1] if not np.isnan(supertrend[i - 1]) else final_upper[i - 1]

            # Determine new direction
            if prev_st == final_upper[i - 1]:
                # Was in downtrend
                if close[i] > final_upper[i]:
                    supertrend[i] = final_lower[i]
                    direction[i] = -1  # flip to uptrend
                else:
                    supertrend[i] = final_upper[i]
                    direction[i] = 1  # stay downtrend
            else:
                # Was in uptrend
                if close[i] < final_lower[i]:
                    supertrend[i] = final_upper[i]
                    direction[i] = 1  # flip to downtrend
                else:
                    supertrend[i] = final_lower[i]
                    direction[i] = -1  # stay uptrend

        return supertrend, direction

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        period = int(self.st_period.value)
        multiplier = float(self.st_multiplier.value)
        vol_lb = int(self.volume_lookback.value)

        atr_values = ta.ATR(dataframe, timeperiod=period).values
        close = dataframe["close"].values
        high = dataframe["high"].values
        low = dataframe["low"].values

        st, direction = self._compute_supertrend(close, high, low, atr_values, multiplier)
        dataframe["supertrend"] = st
        dataframe["st_direction"] = direction

        # Flip detection
        dataframe["st_flip_up"] = (dataframe["st_direction"] == -1) & (
            dataframe["st_direction"].shift(1) == 1
        )
        dataframe["st_flip_down"] = (dataframe["st_direction"] == 1) & (
            dataframe["st_direction"].shift(1) == -1
        )

        dataframe["volume_ma"] = dataframe["volume"].rolling(vol_lb).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        long_setup = dataframe["st_flip_up"] & (dataframe["volume"] > 0)
        short_setup = dataframe["st_flip_down"] & (dataframe["volume"] > 0)

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "supertrend_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "supertrend_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Exit when trend flips
        exit_long = dataframe["st_flip_down"]
        exit_short = dataframe["st_flip_up"]

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "supertrend_exit_long",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "supertrend_exit_short",
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
