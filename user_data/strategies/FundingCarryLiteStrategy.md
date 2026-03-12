# FundingCarryLiteStrategy

## Overview

**Category:** Carry – Pure Funding Rate  
**Timeframe:** 4h (with 1h funding rate data)  
**Direction:** Long and Short  
**Complexity:** Intermediate  

---

## Conceptual Basis

Crypto perpetual futures use a **funding rate mechanism** to anchor the perpetual price near the spot price. Every 8 hours (on most exchanges), longs pay shorts (or vice versa) a small percentage of their position depending on whether the perpetual is trading at a premium or discount to spot.

When funding is **strongly positive**, the long side is crowded: many leveraged longs are paying shorts to hold their positions. This represents:
1. A direct **carry income** opportunity for short positions.
2. A **sentiment indicator**: extremely high funding often precedes liquidation cascades.

This strategy takes a pure carry perspective: unlike `FundingTiltMomentumStrategy` (which requires a trend signal), this strategy uses **only the funding rate** as its entry trigger. If funding is extreme, the trade is activated purely to collect the carry.

---

## Entry Logic

| Condition | Short | Long |
|---|---|---|
| Average funding over last 8 periods > `funding_entry_threshold` | ✓ | — |
| Average funding over last 8 periods < -`funding_entry_threshold × 0.5` | — | ✓ |

The asymmetric threshold (lower bar for long entries) reflects the structural reality that negative funding is rarer and usually signals extreme fear; when it does occur, it often precedes a sharp recovery.

---

## Exit Logic

Exit when average funding normalizes below `funding_exit_threshold`. The carry advantage has reduced — there is no reason to maintain the position once the income has dissipated.

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `funding_entry_threshold` | 0.00025 | 0.00010–0.00080 | Funding rate level to enter |
| `funding_exit_threshold` | 0.00005 | 0.00001–0.00020 | Funding level to exit |

For context: 0.0001 = 0.01% per 8h = 0.03% per day = ~11% annualized. Values above 0.0003 (0.03% per 8h) are historically unusual and represent crowded, fragile long positioning.

---

## Risk Management

- Stop-loss: -5% (funding carry income is small; directional losses should be cut quickly)
- Leverage: capped at **1.5×** (more conservative than trend strategies)
- No trailing stop

---

## Expected Behavior

- **High-funding bull run:** Generates short entries; collects carry while the long side is crowded
- **Moderate funding:** No entry — edge not large enough
- **Funding spike + trend reversal:** Ideal environment; both carry and price work in favor
- **Sustained bull with high funding:** Risk of loss; trend continues and short is squeezed despite positive carry

---

## Key Difference from FundingTiltMomentumStrategy

| | `FundingCarryLiteStrategy` | `FundingTiltMomentumStrategy` |
|---|---|---|
| Primary signal | Funding rate alone | Price momentum + EMA trend |
| Funding role | Entry trigger | Entry modifier / overlay |
| Philosophy | Carry collection | Trend + carry alignment |
| Leverage | 1.5× max | 2.0× max |
| Trade frequency | Lower (requires extreme funding) | Higher (requires trend + funding check) |

---

## Overfitting Risk

**Low.** The funding entry threshold has an obvious economic interpretation and should be calibrated based on what constitutes "extreme" funding in the historical distribution. The concept is well-established in institutional carry trading literature applied to crypto.

---

## Academic / Practitioner Support

- Perpetual funding mechanics: Binance Research and academic derivatives literature
- Funding rate as sentiment indicator: documented in crypto practitioner papers
- Carry strategies in futures: classical finance literature (Koijen et al., 2018)
