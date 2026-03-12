# Perp Trading Ideas Strategy Batch

Date: 2026-03-12  
Source brief: `references/perp-trading-ideas.md`  
Market: Binance isolated futures  
Pairs: `BTC/USDT:USDT`, `ETH/USDT:USDT`, `SOL/USDT:USDT`  
Capital assumptions: 1000 USDT, max 3 open trades, conservative leverage  

## Objective

Build additional strategies directly from the perpetual-futures idea document, test them without tuning, and judge them with explicit overfitting awareness.

## Overfitting policy used

- No hyperopt was run for this batch.
- Strategies were evaluated first on a broader sample, then on a holdout window.
- The main decision criterion is out-of-sample behavior, not full-sample headline return.

Ranges used:
- Full sample: `20230101-20260311` or `20260312` depending on timeframe coverage
- Out of sample: `20250101-20260311` or `20260312` depending on timeframe coverage

## Implemented strategies

1. `TimeSeriesMomentumVolatilityStrategy`
   - Idea source: medium-horizon time-series momentum
   - Timeframe: `4h`
   - Design: binary medium-horizon trend signal plus volatility filter

2. `FundingTiltMomentumStrategy`
   - Idea source: trend-following with funding overlay
   - Timeframe: `1h`
   - Design: slow momentum plus historical funding-rate filter and mild funding-aware stake scaling

3. `SessionFilteredMomentumStrategy`
   - Idea source: time-of-day / seasonality as an overlay
   - Timeframe: `4h`
   - Design: momentum continuation with restricted weekday session entries

## Results summary

| Strategy | TF | Full Sample Profit | Full Sample DD | OOS Profit | OOS DD | Read |
|---|---:|---:|---:|---:|---:|---|
| `TimeSeriesMomentumVolatilityStrategy` | 4h | 0.69% | 1.54% | -0.91% | 0.91% | Too weak |
| `FundingTiltMomentumStrategy` | 1h | 27.45% | 2.14% | 6.74% | 1.18% | Strong candidate |
| `SessionFilteredMomentumStrategy` | 4h | 14.16% | 28.17% | 20.20% | 13.78% | Promising but riskier |

## Strategy notes

### `TimeSeriesMomentumVolatilityStrategy`
- Full sample:
  - Profit: `0.69%`
  - Absolute profit: `6.898 USDT`
  - Sharpe: `0.01`
  - Profit factor: `1.25`
  - Drawdown: `1.54%`
- Out of sample:
  - Profit: `-0.91%`
  - Absolute profit: `-9.087 USDT`
  - Sharpe: `-0.15`
  - Profit factor: `0.17`
  - Drawdown: `0.91%`
- Assessment:
  - The idea is too conservative in its current form.
  - Low drawdown is nice, but the strategy is not producing enough edge to justify capital allocation.
  - Drop from the active shortlist unless redesigned substantially.

### `FundingTiltMomentumStrategy`
- Full sample:
  - Profit: `27.45%`
  - Absolute profit: `274.525 USDT`
  - Sharpe: `0.45`
  - Profit factor: `2.42`
  - Drawdown: `2.14%`
  - Long / short profit: `23.78% / 3.67%`
- Out of sample:
  - Profit: `6.74%`
  - Absolute profit: `67.431 USDT`
  - Sharpe: `0.37`
  - Profit factor: `2.23`
  - Drawdown: `1.18%`
  - Long / short profit: `7.07% / -0.32%`
- Assessment:
  - This is the best new strategy from the batch.
  - It held up out of sample with unusually low drawdown for a futures system.
  - The edge appears mostly long-side in this sample, so the short-side funding tilt may still need refinement.
  - Important caution: because it runs on `1h`, execution assumptions matter more than for the slower 4h and 1d systems.

### `SessionFilteredMomentumStrategy`
- Full sample:
  - Profit: `14.16%`
  - Absolute profit: `141.555 USDT`
  - Sharpe: `0.21`
  - Profit factor: `1.04`
  - Drawdown: `28.17%`
  - Long / short profit: `1.62% / 12.53%`
- Out of sample:
  - Profit: `20.20%`
  - Absolute profit: `202.008 USDT`
  - Sharpe: `0.78`
  - Profit factor: `1.14`
  - Drawdown: `13.78%`
  - Long / short profit: `-8.47% / 28.67%`
- Assessment:
  - Stronger than expected out of sample.
  - The edge is heavily concentrated in short trades.
  - Drawdown is much better out of sample than in the broader sample, which is encouraging, but it is still materially riskier than the funding-tilted model.
  - Keep for further research, especially as a bearish-regime specialist.

## Comparison against the existing research bench

New ranking across the most relevant current candidates:
1. `FundingTiltMomentumStrategy`
2. `VolatilityCompressionBreakoutStrategy`
3. `SessionFilteredMomentumStrategy`
4. `DailyBreakoutTrendStrategy`
5. `EmaAdxTrendFilterStrategy`

Interpretation:
- The new batch improved the bench materially.
- The funding overlay idea appears genuinely useful, not just theoretically interesting.
- Session filtering may be helping by preventing low-quality entries, especially on the short side.
- The plain medium-horizon momentum version did not add value in its current conservative form.

## Recommended next steps

1. Run a very small, conservative hyperopt on `FundingTiltMomentumStrategy` only.
2. Re-run out-of-sample validation immediately after any tuning.
3. Test whether `SessionFilteredMomentumStrategy` improves further as a short-only or asymmetric long/short system.
4. Do not spend more time on `TimeSeriesMomentumVolatilityStrategy` unless the logic is redesigned.

## Bottom line

From the new strategies built off `references/perp-trading-ideas.md`, the one clearly worth advancing is:
- `FundingTiltMomentumStrategy`

The second one worth keeping in active research is:
- `SessionFilteredMomentumStrategy`

The pure, conservative time-series momentum implementation did not justify continuation.