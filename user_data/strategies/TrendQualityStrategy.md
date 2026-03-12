# TrendQualityStrategy

## Overview

**Category:** Trend Following – Composite Quality Score  
**Timeframe:** 4h  
**Direction:** Long and Short  
**Complexity:** Intermediate to Advanced  

---

## Conceptual Basis

Most trend-following strategies use a single indicator or simple combination to define a trend. The risk: any single indicator can fire in non-trending conditions. This strategy takes a different approach: it computes a **composite trend quality score** from three independent, conceptually distinct lenses:

1. **ADX Strength** — measures the *strength* of a trend (ADX ≥ 25 indicates a strong trend, regardless of direction)
2. **EMA Alignment** — measures *multi-timeframe trend consistency* (EMA21 > EMA50 > EMA100 = all timeframes aligned bullish)
3. **Linear Regression Slope** — measures the *mathematical direction of price* over the lookback window (positive slope = statistically significant upward trend)

Each component contributes 0 or 1 to the score. Entry only fires when **all three components agree** (score = 3). This triple-confirmation approach is deliberately conservative and focuses on high-quality, high-conviction trend setups.

---

## Score Calculation

### Uptrend Score (max 3)

| Component | Score +1 if... |
|---|---|
| ADX | ADX ≥ `adx_threshold` |
| EMA Alignment | EMA21 > EMA50 AND EMA50 > EMA100 (both stacked) |
| Linear Regression Slope | Normalized slope > `linreg_slope_min` |

### Downtrend Score (max 3)

| Component | Score +1 if... |
|---|---|
| ADX | ADX ≥ `adx_threshold` |
| EMA Alignment | EMA21 < EMA50 AND EMA50 < EMA100 (both stacked bearish) |
| Linear Regression Slope | Normalized slope < -`linreg_slope_min` |

---

## Entry Logic

- **Long:** Uptrend score = 3 (all three components bullish)
- **Short:** Downtrend score = 3 (all three components bearish)

---

## Exit Logic

Exit when the composite quality score for the held direction falls to or below `exit_score_threshold`. The position is held as long as at least 2 of the 3 components still agree (with default threshold = 1, exit triggers when only 1 or fewer components agree).

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `adx_threshold` | 25 | 20–40 | Minimum ADX for trend strength |
| `linreg_period` | 20 | 15–40 | Lookback for linear regression slope |
| `linreg_slope_min` | 0.003 | 0.001–0.010 | Minimum normalized slope to score |
| `exit_score_threshold` | 1 | 1–2 | Exit when score ≤ this |

The EMA periods (21, 50, 100) are fixed at well-established values and not optimized to prevent overfitting.

---

## Risk Management

- Stop-loss: -6.5%
- Leverage: capped at 2×
- No trailing stop

---

## Expected Behavior

- **Strong trending market:** All three score components align; strategy enters and holds through the trend
- **Weak trend:** Score of 2/3 — strategy stays flat even if a single indicator is firing
- **Choppy/sideways:** ADX low, EMAs mixed, slope near zero — score rarely reaches 3
- **Early trend detection:** Linear regression slope can pick up a nascent trend before EMAs fully align

---

## Overfitting Risk

**Very low.** The three components are fully independent in their measurement approaches. The EMA periods are fixed at widely-used values. Only ADX threshold and slope minimum require tuning — both have clear, intuitive interpretation. The binary score (either 3/3 or no entry) prevents marginal, low-confidence entries from sneaking through.

---

## Academic / Practitioner Support

- ADX as trend strength filter: J. Welles Wilder (1978), widely validated
- Multi-timeframe EMA alignment: standard in multi-timeframe analysis; independently supported by systematic trend-following literature
- Linear regression slope as trend direction: classical time-series regression; used in quantitative finance for trend identification
- Triple-confirmation systems: related to Alexander Elder's "Triple Screen" methodology
