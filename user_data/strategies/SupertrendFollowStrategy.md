# SupertrendFollowStrategy

## Overview

**Category:** Trend Following – Adaptive Trailing Indicator  
**Timeframe:** 4h  
**Direction:** Long and Short  
**Complexity:** Beginner to Intermediate  

---

## Conceptual Basis

Supertrend is a popular technical indicator that creates a volatility-adaptive trailing support/resistance level. It is computed using ATR to determine the distance from the midpoint of each bar's range to the upper and lower bands. The direction is maintained by ratcheting: when the indicator is acting as support (uptrend), it can only move up, never down. When acting as resistance (downtrend), it can only move down, never up.

A **trend flip** occurs when price closes through the active band, at which point the indicator switches from acting as resistance to support (or vice versa). This flip is the entry signal.

---

## How the Supertrend is Computed

1. `HL2 = (High + Low) / 2`
2. `ATR` computed over `st_period` bars
3. `Upper band = HL2 + multiplier × ATR`
4. `Lower band = HL2 - multiplier × ATR`
5. Bands are ratcheted: upper band only tightens in downtrend; lower band only rises in uptrend
6. When close > upper band → switch to uptrend, use lower band as support
7. When close < lower band → switch to downtrend, use upper band as resistance

---

## Entry Logic

| Condition | Long | Short |
|---|---|---|
| Supertrend flips from downtrend to uptrend (bullish flip) | ✓ | — |
| Supertrend flips from uptrend to downtrend (bearish flip) | — | ✓ |

---

## Exit Logic

Exit when the Supertrend flips in the opposite direction (the same signal that would open a new trade in the other direction).

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `st_period` | 10 | 7–20 | ATR period for Supertrend |
| `st_multiplier` | 3.0 | 1.5–5.0 | ATR multiplier for band width |
| `volume_lookback` | 20 | 10–30 | Volume MA window (informational) |

The ATR multiplier is the most critical parameter:
- **Low multiplier (1.5–2.5):** Tight bands, more frequent flips, more trades, more whipsaws
- **High multiplier (3.5–5.0):** Wide bands, fewer flips, holds trends longer, larger stops

---

## Risk Management

- Stop-loss: -7% (the Supertrend line itself acts as a trailing reference, but a hard stop protects against gaps)
- Leverage: capped at 2×
- No trailing stop (exits managed by Supertrend flip)

---

## Expected Behavior

- **Trending market:** Enters near the start of each trend, holds through the move, exits at reversal
- **Choppy/sideways:** Multiple rapid flips produce consecutive small losses (the main failure mode)
- **Volatile spike:** May flip erroneously on a single spike bar and flip back quickly

---

## Overfitting Risk

**Low.** Supertrend is a well-studied indicator with only two primary parameters (period and multiplier). The conceptual basis is intuitive and mathematically transparent. The iterative computation is non-trivially implemented but the underlying logic is straightforward.

---

## Academic / Practitioner Support

- Supertrend is used extensively by retail traders on crypto, equities, and forex
- ATR-based trailing systems: documented in trend-following literature
- The concept of ratcheting stops based on volatility is a core component of the classic AHL (trend-following) approach
