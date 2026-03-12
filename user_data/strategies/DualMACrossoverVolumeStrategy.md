# DualMACrossoverVolumeStrategy

## Overview

**Category:** Trend Following – Moving Average Crossover  
**Timeframe:** 4h  
**Direction:** Long and Short  
**Complexity:** Beginner  

---

## Conceptual Basis

Moving average crossovers are one of the most time-tested trend-following techniques in systematic trading. The core idea: when a faster EMA crosses above a slower EMA, price momentum has shifted upward and it often precedes sustained directional moves.

The key addition in this strategy is **volume confirmation**. False crossovers typically occur on thin, low-conviction volume. Genuine breakouts — driven by real participant buying or selling pressure — tend to occur with above-average volume. Requiring that volume exceeds its rolling mean by a minimum factor filters out a large portion of whipsaw trades.

---

## Entry Logic

| Condition | Long | Short |
|---|---|---|
| Fast EMA crosses above Slow EMA | ✓ | — |
| Fast EMA crosses below Slow EMA | — | ✓ |
| Volume ≥ `volume_factor` × rolling average | ✓ | ✓ |

The crossover must occur on the same bar as the volume spike to prevent stale signal entries.

---

## Exit Logic

Exit when the fast EMA crosses back through the slow EMA in the opposite direction. This is a clean, mechanical exit without ambiguity.

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `fast_period` | 20 | 8–30 | Bars for fast EMA |
| `slow_period` | 60 | 40–100 | Bars for slow EMA |
| `volume_factor` | 1.5 | 1.0–2.5 | Volume multiple required |
| `volume_lookback` | 20 | 10–30 | Lookback for volume average |

---

## Risk Management

- Stop-loss: -6% hard stop
- Leverage: capped at 2×
- No trailing stop (relies on EMA flip for exit)

---

## Expected Behavior

- **Bull market:** Generates long signals after confirmed trend initiations; fewer short signals
- **Bear market:** Generates short signals at breakdowns
- **Sideways / choppy:** Many false crossovers; this is the strategy's main failure mode

---

## Overfitting Risk

**Low.** The moving average crossover concept is extremely well-tested across decades and asset classes. The volume filter is a single additional check with an intuitive interpretation. Only 4 parameters require tuning. The default parameters are reasonable starting points and should not require aggressive optimization.

---

## Academic / Practitioner Support

- Moving average trend following: documented across equities, futures, and crypto
- Volume-price relationship: high volume breakouts have higher follow-through probability (Lo and Wang, 2000)
- Crypto-specific: time-series momentum in crypto shows significance over 1–8 week horizons
