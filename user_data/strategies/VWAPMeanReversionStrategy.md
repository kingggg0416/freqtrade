# VWAPMeanReversionStrategy

## Overview

**Category:** Mean Reversion – VWAP-Based  
**Timeframe:** 4h  
**Direction:** Long and Short  
**Complexity:** Intermediate  

---

## Conceptual Basis

Volume-Weighted Average Price (VWAP) is widely used by institutional traders as a benchmark price. Market participants — including algorithmic market makers — actively reference VWAP to assess whether price is "cheap" or "expensive" relative to recent trading activity.

In calm, range-bound market conditions, significant deviations below VWAP attract buyers (buy the dip to VWAP) and significant deviations above VWAP attract sellers. This creates a gravitational pull back toward VWAP that can be systematically exploited.

The strategy adapts this institutional concept to a retail-accessible bar-level rolling VWAP, computed from standard OHLCV candle data.

---

## Why Not Standard Bollinger Bands?

Standard Bollinger Bands use a simple moving average as the center. VWAP uses volume-weighted price, which is more representative of where the "true" trading center was. In high-volume environments (e.g., after a large news-driven move), VWAP adjusts quickly to reflect the new accepted price level, while SMA lags more.

---

## Entry Logic

| Condition | Long | Short |
|---|---|---|
| Close below VWAP lower band | ✓ | — |
| Close above VWAP upper band | — | ✓ |
| ADX < `adx_max` (not trending hard) | ✓ | ✓ |

The ADX filter is critical: mean reversion strategies fail in trending markets. The ADX gate ensures this strategy only fires when the market is range-bound or weakly directional.

---

## Exit Logic

Exit when price reverts back to the VWAP center line (neutral zone).

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `vwap_lookback` | 40 | 20–60 | VWAP computation window (bars) |
| `band_sigma` | 2.0 | 1.0–3.0 | Standard deviation multiplier for bands |
| `adx_max` | 25 | 15–35 | Maximum ADX to allow entry |

---

## Risk Management

- Stop-loss: -5% (tighter than trend strategies; mean reversion setups should be close to right quickly)
- Leverage: capped at 1.5× (more conservative; carry/reversion trades warrant caution)
- No trailing stop

---

## Expected Behavior

- **Quiet, range-bound:** Generates regular signals with good win rates
- **Trending:** ADX filter suppresses most entries; rare misfires stopped out early
- **Spike / crash:** Fast price move pushes far through bands — strategy enters but can lose if trend continues

---

## Overfitting Risk

**Low to moderate.** Mean reversion strategies are naturally more regime-dependent than trend-following. The ADX filter helps, but the strategy should be monitored for regime shifts (e.g., if the market enters a sustained bull trend, mean reversion strategies underperform). Parameters should not be tuned aggressively on in-sample data.

---

## Academic / Practitioner Support

- VWAP deviation mean reversion: documented in equities and futures literature
- Intraday and session VWAP effects in crypto: acknowledged in practitioner literature
- Low-ADX environments as filters for mean-reversion strategies: standard systematic trading practice
