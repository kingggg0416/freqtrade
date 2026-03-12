# EmaAdxTrendFilterStrategy

## Purpose
This strategy is a slower continuation model for retail deployment. Instead of chasing raw breakouts, it waits for an established trend, then trades continuation on either the long or short side when price reclaims or rejects the fast EMA.

## Core Logic
- **Trend regime:** Long when price is above slow EMA and fast EMA is above slow EMA. Short on the mirrored bearish structure.
- **Strength filter:** `ADX` must confirm that the market is moving with enough directional intent.
- **Entry trigger:** Price crosses back above the fast EMA while `MACD` stays above its signal line, or crosses below the fast EMA with bearish `MACD` confirmation for shorts.
- **Exit:** Leave when price invalidates the fast EMA continuation structure or `MACD` reverses.
- **Position sizing:** Stake is reduced when realized volatility is high and can increase moderately when realized volatility is low.
- **Leverage:** Uses a conservative `2x`-or-less leverage callback.

## Indicators and Metrics
- **Fast EMA / Slow EMA:** Define the primary trend.
- **ADX:** Confirms trend strength.
- **MACD:** Confirms continuation momentum.
- **20-day realized volatility:** Used for volatility-aware stake sizing.

## Why It May Work
This strategy assumes that slower trends in major crypto pairs persist and that orderly pullback-and-reclaim behavior offers better entry quality than buying extended moves. Volatility-aware sizing aims to stabilize risk when the same nominal stake would otherwise be too large for current conditions.

## Main Risk
The strategy is intentionally late. It will miss the first part of many moves and may underperform during abrupt reversals where lagging trend filters react too slowly.

## What To Evaluate In Backtests
- Whether volatility scaling improves Sharpe and drawdown versus fixed stake
- Trade frequency and average holding period
- Stability across fast/slow EMA combinations
- BTC-to-ETH portability without heavy re-optimization
