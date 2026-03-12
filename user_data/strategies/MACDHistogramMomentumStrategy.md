# MACDHistogramMomentumStrategy

## Overview

**Category:** Momentum – MACD Histogram  
**Timeframe:** 4h  
**Direction:** Long and Short  
**Complexity:** Beginner to Intermediate  

---

## Conceptual Basis

The MACD (Moving Average Convergence Divergence) indicator is one of the most widely studied momentum indicators. The **histogram** — the difference between the MACD line and its signal line — is particularly useful because it directly measures the acceleration or deceleration of momentum:

- A positive histogram means the MACD line is above its signal: momentum is building.
- A histogram crossing from negative to positive means momentum has just shifted from bearish to bullish.
- A histogram that is both crossing into positive territory AND increasing (accelerating) provides stronger evidence of a genuine momentum shift.

The strategy pairs this with an RSI filter to avoid entering long positions when price is already extended and overbought (or short positions when oversold), which historically tend to produce lower-quality entries.

---

## Entry Logic

### Long Entry
All three conditions must be true:
1. MACD histogram crosses from negative to positive (bullish crossing)
2. Current histogram bar is larger than the previous bar (momentum accelerating)
3. RSI < `rsi_overbought` (not already overbought)

### Short Entry
Mirror of the above:
1. MACD histogram crosses from positive to negative
2. Current histogram is more negative than previous bar (momentum accelerating bearishly)
3. RSI > `rsi_oversold` (not already oversold)

---

## Exit Logic

Exit when the MACD histogram flips sign (i.e., turns negative for longs, positive for shorts). This is a clean, objective exit rule.

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `macd_fast` | 12 | 8–20 | Fast EMA period |
| `macd_slow` | 26 | 20–35 | Slow EMA period |
| `macd_signal` | 9 | 5–15 | MACD signal line period |
| `rsi_period` | 14 | 10–21 | RSI computation period |
| `rsi_overbought` | 70 | 65–85 | RSI ceiling for long entry |
| `rsi_oversold` | 30 | 15–35 | RSI floor for short entry |

Standard MACD parameters (12/26/9) are the most well-tested defaults across all markets.

---

## Risk Management

- Stop-loss: -5.5%
- Leverage: capped at 2×
- No trailing stop

---

## Expected Behavior

- **Trending market:** Produces a signal near trend initiations when MACD builds momentum; exits cleanly when momentum fades
- **Choppy market:** MACD histogram oscillates rapidly, producing noisy signals — RSI filter helps reduce some of these
- **Overbought entries:** RSI filter prevents the most common trap of buying late into a rally

---

## Overfitting Risk

**Low to moderate.** MACD is extremely well-studied. The RSI filter adds 2 parameters but both have well-understood operating ranges (overbought: 65–80, oversold: 20–35). Avoid optimizing RSI thresholds too aggressively on short windows, as this risks data mining. The standard 70/30 levels are defensible without optimization.

---

## Academic / Practitioner Support

- MACD: Gerald Appel (1979); extensively studied in academic and practitioner literature
- MACD histogram momentum: widely documented as a signal of trend initiation
- RSI overbought/oversold filtering: improves entry timing across multiple asset classes
