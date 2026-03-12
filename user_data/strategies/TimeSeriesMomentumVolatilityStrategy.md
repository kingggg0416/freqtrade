# TimeSeriesMomentumVolatilityStrategy

## Purpose
This strategy implements the document's medium-horizon time-series momentum idea in a simple retail-friendly way. It trades only when medium-term direction is clear and realized volatility is still contained.

## Core Logic
- Entry long when cumulative return over a medium lookback is sufficiently positive.
- Entry short on the mirrored negative return condition.
- Require price to remain on the correct side of a trend EMA.
- Require realized volatility to stay below a ceiling so the strategy avoids highly stressed regimes.
- Exit when momentum collapses, the EMA trend breaks, or volatility becomes too unstable.

## Why It May Work
Crypto perpetuals often trend over multi-day windows because of underreaction, retail herding, and slow repricing. A volatility filter tries to avoid the worst liquidation-driven environments where momentum signals become fragile.

## Main Risk
It can still suffer during abrupt trend reversals or noisy sideways conditions where medium-horizon returns stay elevated just before the move fails.