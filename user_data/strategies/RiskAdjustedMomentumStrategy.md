# RiskAdjustedMomentumStrategy

## Overview

**Category:** Momentum – Volatility-Normalized (Sharpe-Style Signal)  
**Timeframe:** 4h  
**Direction:** Long and Short  
**Complexity:** Intermediate  

---

## Conceptual Basis

Standard time-series momentum strategies look at raw cumulative returns over a lookback window. A key weakness: a coin that moved +40% in a volatile week scores the same as a coin that moved +40% in a steady, low-volatility trend. But the volatile move is far less reliable as a signal — high-volatility environments mean-revert more often.

This strategy normalizes momentum by realized volatility, producing a **Sharpe-style momentum score**:

```
score = cumulative_return / realized_volatility
```

A high positive score means the asset trended up *with* low volatility — a "smooth" uptrend. This is more likely to continue than a volatile spike of the same magnitude.

This concept is derived directly from **cross-sectional momentum research**, where assets are ranked by risk-adjusted returns. Applied per-pair, each coin is judged against its own historical risk rather than relative to other pairs.

---

## Entry Logic

| Condition | Long | Short |
|---|---|---|
| Normalized score > `score_threshold` | ✓ | — |
| Normalized score < -`score_threshold` | — | ✓ |
| Close > EMA trend (broader direction) | ✓ | — |
| Close < EMA trend | — | ✓ |
| Realized volatility < `vol_cap` | ✓ | ✓ |

The volatility cap prevents entering during crisis periods where volatility spikes and momentum signals become unreliable.

---

## Exit Logic

Exit when the normalized score falls below a fraction of the entry threshold (momentum decaying) OR the price crosses the EMA trend line against the position.

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `lookback` | 60 | 30–100 | Return and volatility window (bars) |
| `score_threshold` | 1.5 | 0.5–3.0 | Minimum risk-adjusted score to enter |
| `ema_trend_period` | 50 | 30–100 | EMA for macro trend filter |
| `vol_cap` | 0.08 | 0.03–0.15 | Max realized vol to allow entry |

---

## Risk Management

- Stop-loss: -6%
- Leverage: capped at 2×
- No trailing stop

---

## Expected Behavior

- **Smooth trend:** Generates signals during sustained directional moves with manageable volatility
- **Volatile spike:** Suppressed by vol cap — no entry during crisis/extreme volatility
- **Choppy market:** Low score magnitude prevents most entries

---

## Overfitting Risk

**Low.** The risk-adjusted momentum framework is grounded in academic momentum research. The Sharpe score interpretation is intuitive. The vol cap is a coarse filter with a broad range. Avoid over-tuning `score_threshold` on short windows; a value of 1.0–2.0 is conceptually sound across most scenarios.

---

## Academic / Practitioner Support

- Volatility-scaled momentum: Moreira and Muir (2017), "Volatility-Managed Portfolios"
- Risk-adjusted returns for momentum signals: Asness et al. (2013)
- Crypto-specific: Daniel and Hirshleifer (2015) framework applied to digital assets in recent literature
