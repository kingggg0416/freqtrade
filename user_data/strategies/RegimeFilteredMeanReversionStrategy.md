# RegimeFilteredMeanReversionStrategy

## Purpose
This strategy extends the base mean-reversion model by making market regime classification explicit. It trades only when conditions look range-bound enough for reversion to be a realistic expectation, on both the long and short side.

## Core Logic
- **Ranging regime:** `ADX` must be below a threshold and the 50-period SMA slope must be near flat.
- **Entry:** Go long when price is below the lower Bollinger Band and RSI is oversold while the ranging regime is active. Go short on the mirrored overbought setup.
- **Exit:** Close when price returns toward the mean, RSI normalizes, or a hostile trend regime emerges, again using mirrored rules for shorts.
- **Leverage:** Uses a conservative `2x`-or-less leverage callback.

## Indicators and Metrics
- **Bollinger Bands:** Identify stretch away from mean.
- **RSI:** Confirms downside exhaustion.
- **ADX:** Measures whether the market is trending strongly.
- **SMA50 slope:** Measures whether the prevailing price path is flat enough for mean reversion.

## Why It May Work
The guide emphasizes that mean reversion performs better in ranging markets than in strong trends. This strategy directly encodes that idea instead of treating all oversold readings equally.

## Main Risk
Regime filters can be too late or too strict. If they are too strict, the strategy will miss profitable reversals. If they react too slowly, the strategy can still buy during the early stages of a fresh trend.

## What To Evaluate In Backtests
- Compare against the base mean-reversion strategy on identical data
- Measure reduction in catastrophic losses during persistent downtrends
- Test sensitivity of ADX and slope thresholds
- Review missed-trade cost caused by stricter filters
