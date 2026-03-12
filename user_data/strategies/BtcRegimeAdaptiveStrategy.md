# BtcRegimeAdaptiveStrategy

## Overview

**Category:** Regime Filtering – BTC-Anchored Macro Framework  
**Timeframe:** 4h  
**Direction:** Long and Short  
**Complexity:** Intermediate  

---

## Conceptual Basis

Crypto markets are uniquely characterized by Bitcoin dominance: BTC sets the macro risk tone for almost all other assets. Historical evidence consistently shows:

- When BTC is in an uptrend: altcoins (ETH, SOL, etc.) participate in bull runs
- When BTC breaks down: altcoins typically sell off faster and harder than BTC itself

This strategy systematizes that intuition: it only takes long positions on any pair when BTC is in a confirmed uptrend (EMA50 above EMA200), and only takes short positions when BTC is in a confirmed downtrend. The pair-level entry is then filtered through a momentum and EMA condition to ensure the individual coin is also moving in the same direction as BTC.

**For BTC itself:** The informative data equals BTC's own data, so the strategy degrades to a standard EMA-momentum strategy on BTC — which is a perfectly valid result.

---

## Data Sources

Uses `@informative("4h", "BTC/USDT:USDT")` to access BTC's 4h candles within ETH and SOL strategy runs. This is a built-in freqtrade feature that merges cross-pair data with automatic column renaming.

---

## Entry Logic

| Condition | Long | Short |
|---|---|---|
| BTC EMA50 > BTC EMA200 (macro uptrend) | ✓ | — |
| BTC EMA50 < BTC EMA200 (macro downtrend) | — | ✓ |
| Pair cumulative return > `momentum_threshold` | ✓ | — |
| Pair cumulative return < -`momentum_threshold` | — | ✓ |
| Pair fast EMA > slow EMA | ✓ | — |
| Pair fast EMA < slow EMA | — | ✓ |

All three conditions must align (BTC regime + pair momentum + pair EMA).

---

## Exit Logic

Exit when either:
- The BTC regime flips (macro environment changes)
- The pair's own EMA alignment reverses

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `momentum_lookback` | 48 | 20–80 | Bars for pair momentum computation |
| `momentum_threshold` | 0.04 | 0.02–0.10 | Minimum return magnitude to enter |
| `pair_ema_fast` | 24 | 15–40 | Fast EMA for pair trend |
| `pair_ema_slow` | 72 | 50–120 | Slow EMA for pair trend |

BTC regime uses fixed EMA 50 / 200 (not optimized) to maintain interpretability and reduce overfitting.

---

## Risk Management

- Stop-loss: -6.5%
- Leverage: capped at 2×
- No trailing stop

---

## Expected Behavior

- **Bull market with BTC leadership:** Both BTC and altcoins trending up; strategy generates long signals on all pairs
- **Bear market:** BTC regime gates off long signals; strategy takes short signals on altcoin weakness
- **Altcoin decoupling (rare):** BTC up but ETH/SOL down — strategy still only allows longs for ETH/SOL (but pair EMA filter will prevent entry if the pair is weak)

---

## Overfitting Risk

**Low.** The BTC regime filter uses well-established EMA 50/200 golden cross / death cross logic (not optimized). The pair-level parameters have wide, intuitively defensible ranges. The triple-condition requirement naturally reduces overfitting by making entries rare enough to avoid curve-fitting.

---

## Academic / Practitioner Support

- Cross-asset correlation in crypto: extensively documented (BTC beta framework)
- Regime-adaptive strategies: Mulvey and Kim (2009); applied to crypto in recent literature
- Golden cross / death cross macro filters: classic trend-following literature, used by institutional and retail traders globally
