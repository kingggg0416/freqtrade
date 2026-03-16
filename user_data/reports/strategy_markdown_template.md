# <StrategyName>

## Purpose
This strategy <one-sentence objective>. It is intended to test whether <market behavior hypothesis> in <market/timeframe context> can lead to <expected edge>.

## Core Logic
- **Primary condition:** <main setup condition>.
- **Trigger:** Go long when <long trigger> or short when <short trigger>.
- **Participation filter:** <filter that confirms trade quality, e.g. ADX/volume/regime>.
- **Stretch filter:** <filter preventing late/overextended entries>.
- **Exit:** <clear long/short exit rule>.
- **Leverage:** Uses a conservative `<max leverage>`-or-less leverage callback.

## Indicators and Metrics
- **<Indicator 1>:** <what it measures>.
- **<Indicator 2>:** <what it measures>.
- **<Indicator 3>:** <what it measures>.
- **<Indicator 4>:** <what it measures>.

## Why It May Work
<Brief, plain-language explanation of market mechanism and why this signal should produce an edge.>

## Main Risk
<Primary failure mode in one paragraph: when and why this strategy can break down.>

## What To Evaluate In Backtests
- <Key diagnostic #1>
- <Key diagnostic #2>
- <Key diagnostic #3>
- <Key diagnostic #4>

## Validation Gate
- Must satisfy: Profit > 10%
- Must satisfy: Profit factor >= 1.15
- Must satisfy: Sharpe > 0.5
- Must satisfy: Max underwater <= 30%
- Must satisfy: Non-zero trades and no runtime errors

## Delete Reason Format (If Failed)
- **Delete reason:** <exact violated rule(s)>
- **Anti-repeat tags:** <tag1>, <tag2>, <tag3>
