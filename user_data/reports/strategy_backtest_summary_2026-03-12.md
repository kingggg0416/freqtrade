# Strategy Backtest Summary

Date: 2026-03-12  
Market: Binance Futures  
Pairs: `BTC/USDT:USDT`, `ETH/USDT:USDT`, `SOL/USDT:USDT`  
Capital assumptions: 1000 USDT, isolated futures, max 3 open trades  

## Methodology

### Full-sample benchmark
- Trend strategies:
  - Timeframe: `1d`
  - Detail timeframe: `4h`
  - Range: `20230101-20260311`
- 4h strategies:
  - Timeframe: `4h`
  - Detail timeframe: `1h`
  - Range: `20230101-20260311`

### Anti-overfitting validation
- In-sample optimization range: `20230101-20241231`
- Out-of-sample validation range: `20250101-20260311`
- Hyperopt loss used: `MultiMetricHyperOptLoss`
- Important: only `DailyBreakoutTrendStrategy` and `MomentumPulseStrategy` received usable saved tuned parameters.
- `VolatilityCompressionBreakoutStrategy` was validated out of sample on default parameters because its hyperopt run was interrupted before any epoch completed.

## Executive Takeaway

Current ranking from a robustness perspective:
1. `VolatilityCompressionBreakoutStrategy`
2. `DailyBreakoutTrendStrategy`
3. `EmaAdxTrendFilterStrategy`
4. `MomentumPulseStrategy`
5. `RegimeFilteredMeanReversionStrategy`
6. `RsiBollingerMeanReversionStrategy`

Interpretation:
- The breakout / trend family is clearly stronger than the mean-reversion family in this market/sample.
- `VolatilityCompressionBreakoutStrategy` currently looks like the best all-around candidate because it stayed strong out of sample without any tuning.
- `DailyBreakoutTrendStrategy` also held up out of sample, though with weaker returns than its broader sample suggested.
- `MomentumPulseStrategy` degraded sharply out of sample, so it should be treated as fragile until proven otherwise.
- The mean-reversion strategies should be dropped from the active shortlist for now.

## Summary Table

| Strategy | Style | TF | Full Sample Profit | Full Sample DD | OOS Profit | OOS DD | Status |
|---|---|---:|---:|---:|---:|---:|---|
| `DailyBreakoutTrendStrategy` | Slow breakout trend | 1d | 48.21% | 10.17% | 7.51% | 14.01% | Keep |
| `EmaAdxTrendFilterStrategy` | Slow trend continuation | 1d | 5.30% | 2.90% | n/a | n/a | Watchlist |
| `RsiBollingerMeanReversionStrategy` | Mean reversion | 4h | -27.22% | 35.99% | n/a | n/a | Drop |
| `RegimeFilteredMeanReversionStrategy` | Filtered mean reversion | 4h | -15.73% | 22.42% | n/a | n/a | Drop |
| `MomentumPulseStrategy` | Momentum continuation | 4h | 16.33% | 19.65% | 1.13% | 21.67% | Research only |
| `VolatilityCompressionBreakoutStrategy` | Compression breakout | 4h | 39.93% | 14.23% | 17.62% | 10.00% | Highest priority |

## Strategy-by-Strategy Notes

### `DailyBreakoutTrendStrategy`
- Role: slower trend-following / breakout capture.
- Optimization status: tuned and saved.
- Saved parameters:
  - `adx_threshold = 18`
  - `breakout_window = 48`
  - `exit_ma_period = 25`
- In-sample hyperopt best result on `20230101-20241231`:
  - Profit: `37.88%`
  - Trades: `47`
- Full-sample benchmark:
  - Profit: `48.21%`
  - Absolute profit: `482.133 USDT`
  - Sharpe: `0.25`
  - Profit factor: `1.61`
  - Drawdown: `10.17%`
  - Long / short profit: `52.02% / -3.80%`
- Out-of-sample validation:
  - Profit: `7.51%`
  - Absolute profit: `75.11 USDT`
  - Sharpe: `0.10`
  - Profit factor: `1.20`
  - Drawdown: `14.01%`
  - Long / short profit: `5.47% / 2.04%`
- Assessment:
  - Positive out of sample, which is the main thing that matters.
  - Returns compressed materially, but it still survived the validation period.
  - Good candidate for further refinement, especially around short-side quality and trade timing.

### `EmaAdxTrendFilterStrategy`
- Role: conservative trend continuation with volatility-aware sizing.
- Optimization status: not optimized yet.
- Full-sample benchmark:
  - Profit: `5.30%`
  - Absolute profit: `52.953 USDT`
  - Sharpe: `0.08`
  - Profit factor: `2.18`
  - Drawdown: `2.90%`
  - Long / short profit: `-1.47% / 6.76%`
- Assessment:
  - Return is weak, but drawdown is very low.
  - This is not a lead strategy by itself, but it may be useful as a stabilizer in a portfolio or as a foundation for a stricter trend filter variant.
  - Worth keeping on a secondary watchlist.

### `RsiBollingerMeanReversionStrategy`
- Role: basic overextension mean reversion.
- Optimization status: not optimized.
- Full-sample benchmark:
  - Profit: `-27.22%`
  - Absolute profit: `-272.213 USDT`
  - Sharpe: `-0.50`
  - Profit factor: `0.74`
  - Drawdown: `35.99%`
  - Long / short profit: `-5.05% / -22.17%`
- Assessment:
  - Clearly not working in this futures universe.
  - Loses on both long and short sides.
  - Remove from the active research queue unless the market regime or entry logic changes substantially.

### `RegimeFilteredMeanReversionStrategy`
- Role: mean reversion with explicit ranging/trending filter.
- Optimization status: not optimized.
- Full-sample benchmark:
  - Profit: `-15.73%`
  - Absolute profit: `-157.288 USDT`
  - Sharpe: `-0.33`
  - Profit factor: `0.72`
  - Drawdown: `22.42%`
  - Long / short profit: `-0.74% / -14.99%`
- Assessment:
  - Better than the simpler mean-reversion version, but still not investable.
  - The range filter helped, but not enough.
  - Drop for now.

### `MomentumPulseStrategy`
- Role: higher-turnover momentum continuation.
- Optimization status: partially optimized; saved params came from an interrupted short run and should be treated as provisional.
- Saved parameters:
  - `adx_threshold = 30`
  - `roc_period = 13`
  - `roc_threshold = 0.034`
  - `rsi_entry = 54`
  - `rsi_exit = 43`
- In-sample hyperopt best result on `20230101-20241231`:
  - Profit: `22.76%`
  - Trades: `368`
- Full-sample benchmark:
  - Profit: `16.33%`
  - Absolute profit: `163.254 USDT`
  - Sharpe: `0.20`
  - Profit factor: `1.04`
  - Drawdown: `19.65%`
  - Long / short profit: `11.55% / 4.78%`
- Out-of-sample validation:
  - Profit: `1.13%`
  - Absolute profit: `11.268 USDT`
  - Sharpe: `0.04`
  - Profit factor: `1.01`
  - Drawdown: `21.67%`
  - Long / short profit: `-2.67% / 3.80%`
- Assessment:
  - This is the main overfitting warning in the current bench.
  - Looked decent in broader/backfit contexts, but almost all edge disappeared out of sample.
  - Keep only as a research branch, not as a deployment candidate.

### `VolatilityCompressionBreakoutStrategy`
- Role: breakout from compressed volatility bases.
- Optimization status: not optimized successfully yet.
- Full-sample benchmark:
  - Profit: `39.93%`
  - Absolute profit: `399.251 USDT`
  - Sharpe: `0.51`
  - Profit factor: `1.21`
  - Drawdown: `14.23%`
  - Long / short profit: `15.87% / 24.06%`
- Out-of-sample validation:
  - Profit: `17.62%`
  - Absolute profit: `176.215 USDT`
  - Sharpe: `0.59`
  - Profit factor: `1.23`
  - Drawdown: `10.00%`
  - Long / short profit: `-3.56% / 21.18%`
- Assessment:
  - Best current strategy on robustness grounds.
  - Strong out-of-sample performance without any parameter tuning is exactly what we want to see.
  - The edge currently appears concentrated on the short side, which is useful but should be monitored for regime dependence.
  - Highest priority candidate for the next research cycle.

## Recommended Next Steps

### Tier 1: continue
1. `VolatilityCompressionBreakoutStrategy`
   - Run a very small, conservative hyperopt next.
   - Focus on validating whether default behavior is already near-optimal.
   - Test whether short-only or asymmetric long/short handling improves robustness.
2. `DailyBreakoutTrendStrategy`
   - Explore short-side filtering and exit refinement.
   - Consider volatility or trend-regime gating to improve post-2025 behavior.

### Tier 2: optional secondary work
3. `EmaAdxTrendFilterStrategy`
   - Try a stricter version to improve return while preserving low drawdown.

### Tier 3: do not prioritize
4. `MomentumPulseStrategy`
   - Keep only if we want to study why OOS degraded.
5. `RegimeFilteredMeanReversionStrategy`
6. `RsiBollingerMeanReversionStrategy`
   - No further work unless the design thesis changes materially.

## Bottom Line

If only two strategies move forward right now, they should be:
- `VolatilityCompressionBreakoutStrategy`
- `DailyBreakoutTrendStrategy`

If one additional low-volatility diversifier is kept on the side, keep:
- `EmaAdxTrendFilterStrategy`
