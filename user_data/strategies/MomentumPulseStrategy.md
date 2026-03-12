# MomentumPulseStrategy

## Purpose
This strategy represents a momentum-continuation research direction. It is designed for liquid crypto futures where directional impulse can persist for several candles once trend and momentum align.

## Core Logic
- **Trend alignment:** `EMA20` must be above `EMA50` for longs and below for shorts.
- **Impulse filter:** `ROC` must exceed a positive threshold for longs or a negative threshold for shorts.
- **Momentum confirmation:** `RSI` and `ADX` must confirm that the move has real force.
- **Exit:** Leave when price loses the fast EMA or RSI fades back against the trade.
- **Leverage:** Uses a conservative `2x`-or-less leverage callback.

## Indicators and Metrics
- **EMA20 / EMA50:** Primary directional structure.
- **RSI:** Momentum state and exit normalization.
- **ROC:** Direct measure of price impulse.
- **ADX:** Filters for meaningful directional strength.

## Why It May Work
Momentum can persist when market participants chase price and reduce inventory asymmetrically. The strategy tries to enter only when trend structure, momentum, and rate-of-change all point in the same direction.

## Main Risk
This style often enters late. Sharp exhaustion spikes and reversal candles can hurt performance quickly, especially after already-extended moves.

## What To Evaluate In Backtests
- Whether momentum continuation survives fees and slippage assumptions
- Long vs short asymmetry across BTC, ETH, and SOL
- Sensitivity to the ROC threshold and ADX filter
- Whether drawdowns cluster during range-bound periods
