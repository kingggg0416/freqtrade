# DailyBreakoutTrendStrategy

## Purpose
This strategy implements the guide's daily breakout trend idea for a retail trader who cannot compete on speed. It is built to capture large directional moves in liquid crypto perpetuals by entering on fresh breakouts in either direction.

## Core Logic
- **Entry:** Go long when price closes above the prior N-day high, or go short when price closes below the prior N-day low.
- **Trend filter:** Require `ADX` above a threshold so the breakout happens in a market already showing directional strength.
- **Exit:** Close longs when price loses the exit moving average or breaks down through the opposite band. Close shorts on the mirrored reclaim conditions.
- **Leverage:** Uses a conservative `2x`-or-less leverage callback for early futures testing.

## Indicators and Metrics
- **Rolling breakout high / low:** Defines structural trend continuation and structural failure.
- **Simple moving average:** Fast exit line to reduce drawdown when the trend cools.
- **ADX:** Used to separate directional environments from chop.
- **ATR %:** Included for chart review and later risk analysis.

## Why It May Work
Breakout trend strategies attempt to profit from underreaction and flow persistence. When BTC or ETH starts a meaningful move, it often travels farther than expected because market participants gradually reprice rather than fully adjust immediately.

## Main Risk
The core failure mode is chop. In sideways markets, price can repeatedly poke above prior highs and then reverse. The ADX filter is the main defense against this behavior.

## What To Evaluate In Backtests
- Sharpe ratio after realistic costs
- Maximum drawdown during range-bound periods
- Win rate versus payoff skew
- Parameter stability across nearby breakout and exit windows
- Results on BTC first, then ETH with minimal re-tuning
