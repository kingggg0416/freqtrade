# MarketStructureSwingStrategy

## Overview

**Category:** Trend Following – Market Structure / Price Action  
**Timeframe:** 1d  
**Direction:** Long and Short  
**Complexity:** Intermediate  

---

## Conceptual Basis

Market structure is a foundational concept in price action trading, rooted in Dow Theory (1900s) and later formalized in Wyckoff Analysis and Smart Money Concepts. The core principle:

- **Uptrend** = series of Higher Highs (HH) and Higher Lows (HL)
- **Downtrend** = series of Lower Highs (LH) and Lower Lows (LL)

A **structural shift** — from LH/LL to HH/HL — often marks the beginning of a genuine new trend, not just a short-term bounce. This is because market makers and institutional participants are demonstrably changing behavior when successive swing extremes begin forming in a new direction.

This strategy detects structural conditions using a systematic, vectorized approach:
- Rolling `swing_window`-bar highest highs and lowest lows are computed.
- These are compared to the same metrics from `lookback_bars` bars ago.
- If current rolling highs are above past rolling highs = Higher Highs.
- If current rolling lows are above past rolling lows = Higher Lows.

---

## Entry Logic

### Long (uptrend structure)
All must be true:
1. Higher Highs: current N-bar high > same measure from M bars ago
2. Higher Lows: current N-bar low > same measure from M bars ago
3. HH margin > `structure_score_min` (structural break is meaningful, not trivial)
4. Close > EMA trend (macro context confirms direction)
5. ADX ≥ `adx_min` (trend has genuine momentum)

### Short (downtrend structure)
Mirrored: Lower Highs, Lower Lows, significant margin, below EMA, ADX confirmed.

---

## Exit Logic

Exit when the opposite structure appears (Lower Highs for long positions; Higher Highs for short positions), or when price crosses the EMA trend line against the position.

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `swing_window` | 5 | 3–10 | Rolling window for swing high/low |
| `lookback_bars` | 15 | 10–30 | How far back to compare structure |
| `adx_min` | 20 | 15–30 | Minimum ADX |
| `trend_ema` | 50 | 30–80 | EMA for macro trend filter |
| `structure_score_min` | 0.005 | 0.001–0.03 | Minimum % margin for structural break |

---

## Risk Management

- Stop-loss: -8% (daily bars require wider stops)
- Leverage: capped at 2×
- No trailing stop

---

## Expected Behavior

- **Trending market:** Structure confirms early in the trend; strategy enters and holds until structure breaks
- **Early-stage trend:** Catches the first confirmatory HH/HL or LH/LL formation
- **Ranging market:** Structure is ambiguous or alternating; low signal frequency
- **Volatile/spiky market:** Single large wicks can temporarily distort rolling high/low values

---

## Overfitting Risk

**Low.** Market structure is a conceptual framework with a long practitioner history. The rolling comparison approach is a simplification of manual swing identification but retains the key insight. The `swing_window` and `lookback_bars` parameters are interpretable (small swing window = more sensitive to short-term swings; larger lookback = compares to further back in history). Avoid curve-fitting `structure_score_min` to be too tight.

---

## Academic / Practitioner Support

- Dow Theory: Charles Dow (1900s), foundational framework for modern technical analysis
- Wyckoff Analysis: Richard Wyckoff (1930s), swing points and market structure
- Smart Money Concepts: contemporary retail/institutional framework using structural highs and lows
- Quantitative evidence: rolling high/low channel systems documented in systematic trend-following literature
