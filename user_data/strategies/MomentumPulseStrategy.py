from datetime import datetime

from pandas import DataFrame

import talib.abstract as ta
from technical import qtpylib

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class MomentumPulseStrategy(IStrategy):
	"""
	Momentum continuation strategy for liquid crypto perpetuals.

	What this strategy does:
	- Looks for strong directional impulse rather than slow trend persistence.
	- Requires trend alignment, positive rate-of-change, and rising ADX before entering.
	- Trades both long and short, but only after the market has already shown directional force.
	- Exits when the impulse fades back through a fast EMA or RSI normalizes against the trade.

	Indicators / metrics used:
	- EMA 20 / EMA 50 for directional alignment
	- RSI for momentum state
	- ROC for impulse confirmation
	- ADX for trend-strength confirmation

	Why this may work:
	Momentum continuation can persist in liquid futures markets when trend followers and late
	repositioning traders reinforce the same move. This strategy attempts to participate only
	when trend, momentum, and rate of change point in the same direction.

	Expected failure mode:
	Impulse strategies can suffer after exhaustion spikes and violent reversals. They also
	struggle during slow, range-bound conditions where momentum signals repeatedly fail.
	"""

	INTERFACE_VERSION = 3

	can_short = True
	timeframe = "4h"
	startup_candle_count: int = 80
	process_only_new_candles = True

	use_exit_signal = True
	exit_profit_only = False
	ignore_roi_if_entry_signal = False

	minimal_roi = {"0": 0.18}
	stoploss = -0.06
	trailing_stop = False

	rsi_entry = IntParameter(52, 68, default=58, space="buy", optimize=True, load=True)
	rsi_exit = IntParameter(40, 55, default=48, space="sell", optimize=True, load=True)
	roc_period = IntParameter(5, 15, default=9, space="buy", optimize=True, load=True)
	roc_threshold = DecimalParameter(0.01, 0.08, default=0.03, decimals=3, space="buy")
	adx_threshold = IntParameter(18, 35, default=23, space="buy", optimize=True, load=True)

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
				"rsi": {"color": "purple"},
				"roc": {"color": "orange"},
				"adx": {"color": "blue"},
			}
		},
	}

	def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
		dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=20)
		dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=50)
		dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
		dataframe["roc"] = ta.ROC(dataframe, timeperiod=int(self.roc_period.value)) / 100.0
		dataframe["adx"] = ta.ADX(dataframe)
		dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
		dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
		return dataframe

	def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
		long_setup = (
			(dataframe["ema_fast"] > dataframe["ema_slow"])
			& (dataframe["close"] > dataframe["ema_fast"])
			& (dataframe["rsi"] > self.rsi_entry.value)
			& (dataframe["roc"] > float(self.roc_threshold.value))
			& (dataframe["adx"] > self.adx_threshold.value)
			& (dataframe["volume"] > 0)
		)
		short_setup = (
			(dataframe["ema_fast"] < dataframe["ema_slow"])
			& (dataframe["close"] < dataframe["ema_fast"])
			& (dataframe["rsi"] < 100 - self.rsi_entry.value)
			& (dataframe["roc"] < -float(self.roc_threshold.value))
			& (dataframe["adx"] > self.adx_threshold.value)
			& (dataframe["volume"] > 0)
		)

		dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "momentum_pulse_long")
		dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "momentum_pulse_short")
		return dataframe

	def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
		exit_long = (
			qtpylib.crossed_below(dataframe["close"], dataframe["ema_fast"])
			| (dataframe["rsi"] < self.rsi_exit.value)
		)
		exit_short = (
			qtpylib.crossed_above(dataframe["close"], dataframe["ema_fast"])
			| (dataframe["rsi"] > 100 - self.rsi_exit.value)
		)

		dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
			1,
			"momentum_fade_long",
		)
		dataframe.loc[
			exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]
		] = (1, "momentum_fade_short")
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
