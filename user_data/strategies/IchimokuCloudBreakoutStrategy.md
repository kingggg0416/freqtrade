# IchimokuCloudBreakoutStrategy

## Overview

**Category:** Trend Following – Ichimoku System  
**Timeframe:** 4h  
**Direction:** Long and Short  
**Complexity:** Intermediate  

---

## Conceptual Basis

Ichimoku Kinko Hyo ("equilibrium at a glance") is a comprehensive Japanese technical analysis system that encodes multiple timeframes of information into a single chart. It was developed by Goichi Hosoda in the 1930s–1960s and published in 1969.

The system is particularly well-suited to futures and crypto because:
1. It provides both trend direction and momentum from a single calculation.
2. The cloud (Kumo) acts as a dynamic support/resistance zone that is forward-projected.
3. Multiple confirmations must align before a valid signal is generated.

---

## Components

| Component | Calculation | Purpose |
|---|---|---|
| **Tenkan-sen** | (N-period high + N-period low) / 2 | Short-term "conversion" reference |
| **Kijun-sen** | (M-period high + M-period low) / 2 | Medium-term "baseline" |
| **Senkou Span A** | (Tenkan + Kijun) / 2, plotted M bars forward | Leading edge of cloud |
| **Senkou Span B** | (L-period high + L-period low) / 2, plotted M bars forward | Lagging edge of cloud |
| **Chikou Span** | Close, plotted M bars backward | Confirmation of past context |

---

## Entry Logic (Triple Confirmation)

### Long entry
All three conditions must be true:
1. **Above cloud:** Close > max(Senkou Span A, Span B) — price is above both cloud edges
2. **Bullish cross:** Tenkan-sen > Kijun-sen — short-term trend above medium-term
3. **Chikou confirms:** Chikou Span > close from M bars ago — historical context bullish

### Short entry
Mirror of the above:
1. Below cloud: Close < min(Span A, Span B)
2. Bearish cross: Tenkan < Kijun
3. Chikou below close from M bars ago

---

## Exit Logic

Exit when Tenkan-sen crosses back through Kijun-sen in the opposite direction. This is a faster exit signal than waiting for price to re-enter the cloud.

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `tenkan_period` | 9 | 7–15 | Tenkan-sen period |
| `kijun_period` | 26 | 20–35 | Kijun-sen period (also displacement) |
| `senkou_b_period` | 52 | 44–60 | Senkou Span B period |

Traditional parameters are 9/26/52 and are widely respected as well-calibrated for daily charts. The 4h version uses the same defaults since 4h bars approximate the same "session" resolution.

---

## Risk Management

- Stop-loss: -7%
- Leverage: capped at 2×
- No trailing stop (Tenkan/Kijun cross acts as exit)

---

## Expected Behavior

- **Strong trend:** Three-condition confirmation provides high-quality entries with good risk-reward
- **Choppy/sideways:** Price oscillates around the cloud, producing conflicting Tenkan/Kijun signals — strategy stays mostly flat
- **Transition periods:** Lagging nature of the cloud means entries are confirmed after trend is already underway

---

## Overfitting Risk

**Low.** The 9/26/52 parameters are the canonical values from decades of practitioner use. The logic is multi-confirmatory by design. The three entry conditions are independent mechanisms that each filter for a different aspect of trend quality.

---

## Academic / Practitioner Support

- Ichimoku analysis: widely documented in Japanese and international technical analysis literature
- Three-component confirmation: conceptually related to triple-screen and multi-timeframe analysis
- Kumo breakout as trend filter: used by professional and retail traders worldwide since the 1960s
