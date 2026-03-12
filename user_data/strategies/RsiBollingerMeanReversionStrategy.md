# RsiBollingerMeanReversionStrategy

## Purpose
This strategy implements the guide's slow mean-reversion idea for liquid crypto perpetuals. It is designed to trade temporary overshoots on both sides rather than predict major turning points.

## Core Logic
- **Entry:** Go long when price closes below the lower Bollinger Band and RSI is oversold. Go short on the mirrored overbought condition above the upper band.
- **Regime veto:** Allow entries only when price is above the 50-period SMA or ADX suggests the market is not strongly trending.
- **Exit:** Close when price reverts toward the Bollinger mid-band or RSI normalizes, with mirrored rules for shorts.
- **Leverage:** Uses a conservative `2x`-or-less leverage callback.

## Indicators and Metrics
- **Bollinger Bands:** Measure stretch versus rolling mean.
- **RSI:** Measures short-term exhaustion.
- **SMA50:** Basic directional veto.
- **ADX:** Avoids the most strongly trending breakdowns.

## Why It May Work
Crypto majors often overshoot in short panic bursts and then partially retrace once forced selling cools. Requiring both price stretch and momentum exhaustion aims to isolate those episodes.

## Main Risk
The main failure mode is buying into a genuine breakdown rather than a temporary dislocation. Even with a regime veto, trends can remain stronger and longer than the model expects.

## What To Evaluate In Backtests
- Win rate and average win / average loss
- Whether regime veto improves drawdown meaningfully
- Sensitivity to RSI threshold and Bollinger width
- Performance in strong downtrends versus range periods
