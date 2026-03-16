# New Strategy Batch — Batch 2 Report

Date: 2026-03-12  
Market: Binance Futures (research target)  
Pairs: `BTC/USDT:USDT`, `ETH/USDT:USDT`, `SOL/USDT:USDT`  
Capital: 1000 USDT, isolated futures, max 3 open trades  

---

## Purpose of This Document

This document covers the 11 new strategies added to bring the total to 20. It describes the design rationale, distinguishing characteristics, and expected behavioral profile of each new strategy. Backtesting results will be added once data is available to run the test suite.

The strategies in this batch were deliberately designed to cover different conceptual areas not yet represented in the first 9 strategies.

---

## Strategy Coverage Map

### Before this batch (9 strategies)
| Strategy | Category |
|---|---|
| DailyBreakoutTrendStrategy | Slow trend/breakout |
| EmaAdxTrendFilterStrategy | EMA + ADX trend continuation |
| RsiBollingerMeanReversionStrategy | RSI mean reversion |
| RegimeFilteredMeanReversionStrategy | Filtered mean reversion |
| MomentumPulseStrategy | Price momentum |
| VolatilityCompressionBreakoutStrategy | Compression breakout |
| TimeSeriesMomentumVolatilityStrategy | Time-series momentum |
| FundingTiltMomentumStrategy | Funding overlay + trend |
| SessionFilteredMomentumStrategy | Session-aware momentum |

### Added in this batch (11 strategies)
| Strategy | Category | Timeframe |
|---|---|---|
| DualMACrossoverVolumeStrategy | MA crossover + volume | 4h |
| VWAPMeanReversionStrategy | VWAP mean reversion | 4h |
| ATRChannelBreakoutStrategy | Clean channel breakout | 1d |
| SupertrendFollowStrategy | Supertrend trailing indicator | 4h |
| IchimokuCloudBreakoutStrategy | Ichimoku cloud | 4h |
| MACDHistogramMomentumStrategy | MACD histogram momentum | 4h |
| RiskAdjustedMomentumStrategy | Volatility-normalized momentum | 4h |
| FundingCarryLiteStrategy | Pure funding carry | 4h |
| BtcRegimeAdaptiveStrategy | BTC macro regime filter | 4h |
| MarketStructureSwingStrategy | HH/HL market structure | 1d |
| TrendQualityStrategy | Composite trend quality score | 4h |

---

## New Strategy Profiles

### DualMACrossoverVolumeStrategy
- **What it does:** Classic EMA fast/slow crossover with volume confirmation filter.
- **Key differentiator from existing:** Volume required on crossover bar (existing EmaAdxTrendFilterStrategy uses ADX, not volume).
- **Regime fit:** Trending markets with high-participation breakouts.
- **Expected failure mode:** Choppy markets produce false crossovers.
- **Overfitting risk:** Very low — minimal parameters, well-tested concept.

### VWAPMeanReversionStrategy
- **What it does:** Rolling VWAP ± σ bands for mean reversion in range-bound conditions.
- **Key differentiator:** Uses volume-weighted price center; ADX gate prevents entry in trends.
- **Regime fit:** Low-ADX, range-bound markets.
- **Expected failure mode:** Breaks down when ADX filter is not tight enough.
- **Overfitting risk:** Low — 3 parameters, each with clear interpretation.

### ATRChannelBreakoutStrategy
- **What it does:** N-period channel breakout on 1d bars without compression requirement.
- **Key differentiator from VolatilityCompressionBreakout:** No squeeze requirement; simpler daily version.
- **Regime fit:** Trending markets at new N-day extremes.
- **Expected failure mode:** False breakouts at range boundaries.
- **Overfitting risk:** Very low — derived from Donchian/Turtle systems.

### SupertrendFollowStrategy
- **What it does:** Supertrend indicator flip-based entries with ATR-ratcheting trailing support/resistance.
- **Key differentiator:** Self-adapting volatility-adjusted trailing system; cleaner than pure EMA.
- **Regime fit:** Medium-to-strong trending markets.
- **Expected failure mode:** Whipsaw in sideways conditions.
- **Overfitting risk:** Low — 2 primary parameters (period, multiplier).

### IchimokuCloudBreakoutStrategy
- **What it does:** Triple-confirmation cloud breakout (above cloud + Tenkan/Kijun + Chikou).
- **Key differentiator:** Encodes multiple timeframes in one system; strictest entry filter of any strategy.
- **Regime fit:** Established, confirmed trends.
- **Expected failure mode:** Enters late; misses fast reversals.
- **Overfitting risk:** Very low — canonical 9/26/52 parameters; comprehensive confirmation logic.

### MACDHistogramMomentumStrategy
- **What it does:** MACD histogram cross + acceleration + RSI overbought/oversold filter.
- **Key differentiator:** Histogram measures momentum acceleration, not just direction.
- **Regime fit:** Trend initiation / momentum building phases.
- **Expected failure mode:** MACD whipsaws in choppy markets.
- **Overfitting risk:** Low — MACD 12/26/9 standard; RSI overbought thresholds have intuitive ranges.

### RiskAdjustedMomentumStrategy
- **What it does:** Risk-adjusted momentum score (return / realized volatility) with EMA and vol cap.
- **Key differentiator from MomentumPulseStrategy:** Normalizes by volatility — rewards smooth trends over volatile spikes.
- **Regime fit:** Low-volatility trending markets.
- **Expected failure mode:** Volatile spikes excluded (by design); misses fast trend initiations.
- **Overfitting risk:** Low — grounded in academic Sharpe-style momentum research.

### FundingCarryLiteStrategy
- **What it does:** Pure funding carry — enters short when funding is very high; long when very negative.
- **Key differentiator from FundingTiltMomentum:** No trend signal required; funding IS the signal.
- **Regime fit:** High funding rate environments (crowded long positioning).
- **Expected failure mode:** Bull runs where funding stays high while trend continues.
- **Overfitting risk:** Low — single threshold parameter with clear economic interpretation.

### BtcRegimeAdaptiveStrategy
- **What it does:** Filters all trades through the BTC macro regime (EMA50 vs EMA200).
- **Key differentiator:** Only trades alts in the direction the macro BTC regime permits.
- **Regime fit:** Well-defined BTC bull/bear regimes (not effective in BTC sideways).
- **Expected failure mode:** BTC in undefined regime (EMA50 ≈ EMA200) → few trades.
- **Overfitting risk:** Low — BTC EMA50/200 filter is not optimized; well-established regime indicator.

### MarketStructureSwingStrategy
- **What it does:** Detects HH/HL (uptrend) and LH/LL (downtrend) using rolling window comparison.
- **Key differentiator:** Measures price structure not just price level; captures trend quality from a swing perspective.
- **Regime fit:** Trending markets with clear swing structure.
- **Expected failure mode:** Spiky/noisy markets distort rolling high/low comparisons.
- **Overfitting risk:** Low — market structure concept predates modern technical analysis.

### TrendQualityStrategy
- **What it does:** Composite score from ADX + EMA alignment + linear regression slope. Enters only when all 3 agree.
- **Key differentiator:** Triple-independent-confirmation; each component is orthogonal.
- **Regime fit:** Strong, established trends with statistical and technical confirmation.
- **Expected failure mode:** Very few trades in weak-trend environments (by design).
- **Overfitting risk:** Very low — fixed EMA parameters (21/50/100); only ADX threshold and slope minimum to tune.

---

## Recommended Backtesting Order

For the next research session, prioritize backtesting in this order based on likely robustness:

### High priority (trend-following, well-evidenced)
1. `ATRChannelBreakoutStrategy` — closest to proven Turtle/Donchian system
2. `TrendQualityStrategy` — ultra-selective entry; hard to overfit
3. `BtcRegimeAdaptiveStrategy` — macro regime filter adds genuine edge
4. `SupertrendFollowStrategy` — well-tested indicator, clean mechanical rules

### Medium priority (promising but regime-dependent)
5. `DualMACrossoverVolumeStrategy` — classic; volume filter may help selectivity
6. `MACDHistogramMomentumStrategy` — solid momentum logic
7. `RiskAdjustedMomentumStrategy` — Sharpe-style signal is theoretically sound
8. `IchimokuCloudBreakoutStrategy` — triple-confirmation but slower entries
9. `MarketStructureSwingStrategy` — conceptually strong; depends on swing clarity

### Lower priority (carry/mean-reversion)
10. `FundingCarryLiteStrategy` — pure carry is interesting but requires high-funding episodes
11. `VWAPMeanReversionStrategy` — requires range-bound conditions; regime-dependent

---

## Suggested Backtesting Command Template

```bash
.venv/bin/python -m freqtrade backtesting \
  --config user_data/config.backtest.binance.futures.json \
  --strategy <StrategyName> \
  --timeframe <tf> \
  --timeframe-detail <detail_tf> \
  --timerange 20230101-20260311 \
  --export none
```

Timeframe guidance:
- Daily strategies (ATRChannelBreakout, MarketStructureSwing): `--timeframe 1d --timeframe-detail 4h`
- 4h strategies: `--timeframe 4h --timeframe-detail 1h`

Out-of-sample split to use for all strategies:
- In-sample: `20230101-20241231`
- Out-of-sample: `20250101-20260311`

---

## Anti-Overfitting Reminders

1. Always run out-of-sample validation after in-sample optimization.
2. Use `MultiMetricHyperOptLoss` for any hyperopt runs.
3. Keep epoch counts modest (50–100 epochs per strategy) — not 1000+.
4. Strategies with fewer parameters are intrinsically safer.
5. Check that OOS profit is in the same direction as IS profit (not just same magnitude).
6. EMA periods (21, 50, 100, 200) should NOT be aggressively optimized — treat as fixed.
7. Any strategy that looks dramatically better after optimization than before should be treated as suspect until confirmed on fresh data.
