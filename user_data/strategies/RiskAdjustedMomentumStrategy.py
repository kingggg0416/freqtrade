from datetime import datetime

import numpy as np
from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class RiskAdjustedMomentumStrategy(IStrategy):
    """
    Risk-adjusted (volatility-normalized) momentum strategy.

    What this strategy does:
    - Computes each pair's momentum score as: cumulative return / realized volatility
      over a rolling lookback window. This is similar to a Sharpe-style signal.
    - Enters long when the normalized score is strongly positive (price trended up
      relative to how volatile it has been — genuine, sustained appreciation).
    - Enters short when the score is strongly negative.
    - Adds an EMA trend filter to ensure the trade direction matches the broader trend.
    - Exits when the normalized score crosses back toward zero.

    Conceptual basis in cross-sectional momentum:
    In academic cross-sectional momentum research, assets are ranked by risk-adjusted
    recent returns and portfolios go long top-ranked and short bottom-ranked assets.
    Here, that concept is applied per-pair: each pair is measured against its own
    volatility-adjusted history rather than relative to other pairs.

    Why it may work:
    Volatility normalization prevents the strategy from chasing assets that moved a
    lot purely because of high recent volatility (which is mean-reverting). By
    requiring that the move is large relative to the typical noise, the signal
    becomes more selective and persistent. This is supported by academic work showing
    that volatility-scaled momentum strategies outperform raw-return momentum.

    Expected failure modes:
    - Momentum reversal (crowded momentum trade unwinding) is a known risk.
    - Low-volatility regimes can make the threshold hard to reach, reducing trades.
    - Computation of realized volatility from limited history can be noisy.

    Retail-friendly because:
    - All calculations use standard OHLCV data.
    - The concept (strong move per unit of noise) is intuitively clear.
    - 4h timeframe gives a good balance of signal frequency and noise filtering.
    """

    INTERFACE_VERSION = 3

    can_short = True
    timeframe = "4h"
    startup_candle_count: int = 150
    process_only_new_candles = True

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    minimal_roi = {"0": 0.15}
    stoploss = -0.06
    trailing_stop = False

    lookback = IntParameter(30, 100, default=60, space="buy", optimize=True, load=True)
    score_threshold = DecimalParameter(
        0.5, 3.0, default=1.5, decimals=2, space="buy", optimize=True, load=True
    )
    ema_trend_period = IntParameter(30, 100, default=50, space="buy", optimize=True, load=True)
    vol_cap = DecimalParameter(
        0.03, 0.15, default=0.08, decimals=3, space="buy", optimize=True, load=True
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
            "Momentum Score": {
                "norm_momentum": {"color": "blue"},
            },
            "Volatility": {
                "realized_vol": {"color": "red"},
            },
        },
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        lb = int(self.lookback.value)
        ema_p = int(self.ema_trend_period.value)

        # Cumulative return over lookback
        dataframe["cum_return"] = dataframe["close"] / dataframe["close"].shift(lb) - 1.0

        # Realized annualized volatility over lookback
        log_ret = np.log(dataframe["close"] / dataframe["close"].shift(1))
        dataframe["realized_vol"] = log_ret.rolling(lb).std() * np.sqrt(float(lb))

        # Risk-adjusted momentum score: return / volatility (higher = better risk-adj trend)
        dataframe["norm_momentum"] = dataframe["cum_return"] / dataframe["realized_vol"].replace(
            0, np.nan
        )

        # Broad trend filter
        dataframe["ema_trend"] = ta.EMA(dataframe, timeperiod=ema_p)

        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        thresh = float(self.score_threshold.value)
        vol_cap = float(self.vol_cap.value)

        # Avoid entering when volatility is already very high
        vol_ok = dataframe["realized_vol"] < vol_cap

        long_setup = (
            (dataframe["norm_momentum"] > thresh)
            & (dataframe["close"] > dataframe["ema_trend"])
            & vol_ok
            & (dataframe["volume"] > 0)
        )
        short_setup = (
            (dataframe["norm_momentum"] < -thresh)
            & (dataframe["close"] < dataframe["ema_trend"])
            & vol_ok
            & (dataframe["volume"] > 0)
        )

        dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "risk_adj_mom_long")
        dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "risk_adj_mom_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        thresh = float(self.score_threshold.value)

        # Exit when score falls below half threshold (momentum decaying)
        exit_long = (dataframe["norm_momentum"] < thresh * 0.3) | (
            dataframe["close"] < dataframe["ema_trend"]
        )
        exit_short = (dataframe["norm_momentum"] > -thresh * 0.3) | (
            dataframe["close"] > dataframe["ema_trend"]
        )

        dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
            1,
            "risk_adj_mom_exit_long",
        )
        dataframe.loc[exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]] = (
            1,
            "risk_adj_mom_exit_short",
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
