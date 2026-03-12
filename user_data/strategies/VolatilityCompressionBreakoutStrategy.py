from datetime import datetime

from pandas import DataFrame

import talib.abstract as ta

from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy


class VolatilityCompressionBreakoutStrategy(IStrategy):
	"""
	Volatility-compression breakout strategy for crypto perpetuals.

	What this strategy does:
	- Waits for periods of compressed volatility before trading the subsequent expansion.
	- Uses Bollinger width and Donchian-style breakout levels to capture directional escapes.
	- Requires a minimum ADX reading so the breakout is not taken in completely dead markets.
	- Trades both long and short with mirrored rules.

	Indicators / metrics used:
	- Bollinger Band width as a compression metric
	- Rolling breakout high / low as directional triggers
	- ADX as a trend-strength filter
	- ATR % to avoid entering when expansion is already too extended

	Why this may work:
	Markets often alternate between quiet consolidation and violent expansion. If a meaningful
	breakout emerges from a low-volatility base, the move can persist as liquidity re-prices.

	Expected failure mode:
	False breaks are common, especially in noisy chop. If volatility is already expanding too far,
	late entries can also suffer poor payoff-to-risk.
	"""

	INTERFACE_VERSION = 3

	can_short = True
	timeframe = "4h"
	startup_candle_count: int = 80
	process_only_new_candles = True

	use_exit_signal = True
	exit_profit_only = False
	ignore_roi_if_entry_signal = False

	minimal_roi = {"0": 0.20}
	stoploss = -0.065
	trailing_stop = False

	breakout_window = IntParameter(15, 40, default=20, space="buy", optimize=True, load=True)
	bb_window = IntParameter(15, 30, default=20, space="buy", optimize=True, load=True)
	bb_width_ceiling = DecimalParameter(0.04, 0.20, default=0.10, decimals=3, space="buy")
	adx_threshold = IntParameter(15, 30, default=20, space="buy", optimize=True, load=True)
	atr_pct_ceiling = DecimalParameter(0.01, 0.08, default=0.04, decimals=3, space="buy")

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
		},
		"subplots": {
			"Compression": {
				"bb_width": {"color": "purple"},
				"adx": {"color": "blue"},
				"atr_pct": {"color": "orange"},
			}
		},
	}

	def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
		bb_window = int(self.bb_window.value)
		breakout_window = int(self.breakout_window.value)
		bollinger = ta.BBANDS(dataframe, timeperiod=bb_window, nbdevup=2.0, nbdevdn=2.0)
		dataframe["bb_upper"] = bollinger["upperband"]
		dataframe["bb_middle"] = bollinger["middleband"]
		dataframe["bb_lower"] = bollinger["lowerband"]
		dataframe["bb_width"] = (
			(dataframe["bb_upper"] - dataframe["bb_lower"]) / dataframe["bb_middle"]
		)
		dataframe["breakout_high"] = dataframe["high"].rolling(breakout_window).max().shift(1)
		dataframe["breakout_low"] = dataframe["low"].rolling(breakout_window).min().shift(1)
		dataframe["adx"] = ta.ADX(dataframe)
		dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
		dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
		return dataframe

	def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
		compression_ok = dataframe["bb_width"] < float(self.bb_width_ceiling.value)
		volatility_ok = dataframe["atr_pct"] < float(self.atr_pct_ceiling.value)
		trend_strength = dataframe["adx"] > self.adx_threshold.value

		long_setup = (
			(dataframe["close"] > dataframe["breakout_high"])
			& compression_ok
			& volatility_ok
			& trend_strength
			& (dataframe["volume"] > 0)
		)
		short_setup = (
			(dataframe["close"] < dataframe["breakout_low"])
			& compression_ok
			& volatility_ok
			& trend_strength
			& (dataframe["volume"] > 0)
		)

		dataframe.loc[long_setup, ["enter_long", "enter_tag"]] = (1, "compression_breakout_long")
		dataframe.loc[short_setup, ["enter_short", "enter_tag"]] = (1, "compression_breakout_short")
		return dataframe

	def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
		exit_long = (dataframe["close"] < dataframe["bb_middle"]) | (
			dataframe["close"] < dataframe["breakout_low"]
		)
		exit_short = (dataframe["close"] > dataframe["bb_middle"]) | (
			dataframe["close"] > dataframe["breakout_high"]
		)

		dataframe.loc[exit_long & (dataframe["volume"] > 0), ["exit_long", "exit_tag"]] = (
			1,
			"compression_breakout_exit_long",
		)
		dataframe.loc[
			exit_short & (dataframe["volume"] > 0), ["exit_short", "exit_tag"]
		] = (1, "compression_breakout_exit_short")
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
