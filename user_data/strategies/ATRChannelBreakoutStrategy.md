# ATRChannelBreakoutStrategy

## Overview

**Category:** Trend Following – Channel Breakout  
**Timeframe:** 1d  
**Direction:** Long and Short  
**Complexity:** Beginner  

---

## Conceptual Basis

An N-period price channel tracks the highest high and lowest low over a rolling window. When price closes above the upper channel boundary, it has achieved a new N-period extreme — signaling that the market has moved into territory that was previously considered resistance. Similarly, a close below the lower channel signals a new N-period low.

This strategy captures these structural breakouts on daily bars, a timeframe that filters out most intraday noise while still allowing meaningful participation in multi-day and multi-week trends.

**Key difference from `VolatilityCompressionBreakoutStrategy`:**  
That strategy requires Bollinger Band compression *before* the breakout (squeeze then expansion). This strategy makes no such requirement — it simply looks for a clean close through a new N-day channel extreme with trend confirmation. It is more permissive and captures a broader set of breakouts.

---

## Entry Logic

| Condition | Long | Short |
|---|---|---|
| Close > N-period high (shifted 1 bar back to avoid lookahead) | ✓ | — |
| Close < N-period low (shifted 1 bar back) | — | ✓ |
| ADX ≥ `adx_min` (trend has direction) | ✓ | ✓ |
| ATR% < `atr_extension_cap` (not already over-extended) | ✓ | ✓ |

The ATR extension cap prevents chasing moves that have already run very far in a single bar (e.g., after gap-opens or sudden spikes). If daily ATR-to-price is extreme, the risk-reward of entering has worsened significantly.

---

## Exit Logic

Exit when price falls back below (for longs) or rises back above (for shorts) an EMA of the close. This provides a smooth, lagging exit that avoids being knocked out by single-bar spikes while still reacting to genuine reversals.

---

## Parameters (default / search range)

| Parameter | Default | Range | Meaning |
|---|---|---|---|
| `channel_window` | 30 | 15–55 | N-period for high/low channel |
| `atr_extension_cap` | 0.05 | 0.02–0.12 | Max ATR% to allow entry |
| `adx_min` | 20 | 15–30 | Minimum ADX |
| `exit_ema_period` | 20 | 15–40 | EMA for exit signal |

---

## Risk Management

- Stop-loss: -8% (daily bars = wider stops needed)
- Leverage: capped at 2×
- No trailing stop (EMA-based exit handles the progression)

---

## Expected Behavior

- **Trending bull market:** Few but high-quality long entries; follows trend for multi-week periods
- **Trending bear market:** Short entries at breakdown points
- **Sideways/ranging:** False breakouts at channel edges; main source of loss

---

## Overfitting Risk

**Low.** Channel breakout systems are among the oldest documented trading strategies (e.g., Donchian's 4-week rule, the Turtle Trading system). The concept is robust across decades and asset classes. The four parameters are all interpretable and do not require fine-tuning.
