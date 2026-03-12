# VolatilityCompressionBreakoutStrategy

## Purpose
This strategy captures volatility expansion after a compressed base. It is intended to test whether quiet consolidation in major crypto perpetuals can lead to clean directional breakout opportunities.

## Core Logic
- **Compression:** Require low `Bollinger Band width`.
- **Trigger:** Go long on a break above the rolling breakout high or short on a break below the rolling breakout low.
- **Participation filter:** `ADX` must confirm at least some directional intent.
- **Stretch filter:** `ATR %` must remain under a ceiling so the trade is not entered after expansion is already too extended.
- **Exit:** Leave when price fails back through the Bollinger midline or through the opposite breakout level.
- **Leverage:** Uses a conservative `2x`-or-less leverage callback.

## Indicators and Metrics
- **Bollinger width:** Measures compression.
- **Rolling breakout bands:** Define directional trigger levels.
- **ADX:** Confirms that expansion is not purely random noise.
- **ATR %:** Filters out already-overextended conditions.

## Why It May Work
Markets often alternate between low-volatility balance and high-volatility price discovery. Breakouts from compression can attract trend followers and cause fast repricing if the move starts from a clean base.

## Main Risk
False breakouts are common, especially in noisy sideways markets. The strategy is also vulnerable if compression ends with only a short-lived spike rather than a persistent trend.

## What To Evaluate In Backtests
- False-break frequency by pair
- Sensitivity to Bollinger width and breakout window parameters
- Whether the ATR ceiling improves entry quality
- Whether this style complements the slower daily breakout strategy
