# Failed Strategy Log

Date: 2026-03-16
Scope: Batch 2 strategies (11 total)
Timerange: 20230101-20260311

## Active Quality Gate (used for deletion)

A strategy must pass all rules below:

1. Total profit > 10%
2. Profit factor >= 1.15
3. Sharpe > 0.5
4. Max % of account underwater <= 30%
5. No runtime error
6. Must produce trades (non-zero)

Result for this cycle: 0/11 passed.

## Deleted Strategies and Reasons

1. ATRChannelBreakoutStrategy
- Metrics: Profit 11.03%, PF 1.22, Sharpe 0.09, Underwater 12.95%
- Delete reason: Sharpe 0.09 <= 0.5 (insufficient risk-adjusted performance).
- Anti-repeat tags: low-risk-adjusted-trend, weak-sharpe

2. BtcRegimeAdaptiveStrategy
- Metrics: Profit 48.91%, PF 1.06, Sharpe 0.56, Underwater 28.74%
- Delete reason: Profit factor 1.06 < 1.15 (edge too weak after costs/slippage tolerance).
- Anti-repeat tags: high-return-low-pf, unstable-edge

3. DualMACrossoverVolumeStrategy
- Metrics: Profit -6.88%, PF 0.90, Sharpe -0.09, Underwater 15.62%
- Delete reason: Negative profit and PF < 1.15.
- Anti-repeat tags: crossover-whipsaw, negative-expectancy

4. FundingCarryLiteStrategy
- Metrics: N/A (backtest runtime failure)
- Delete reason: Runtime error (informative timeframe must be equal or higher than strategy timeframe).
- Anti-repeat tags: informative-timeframe-mismatch, operational-failure

5. IchimokuCloudBreakoutStrategy
- Metrics (post-bias-fix): Profit 55.12%, PF 1.08, Sharpe 0.62, Underwater 21.32%
- Delete reason: Profit factor 1.08 < 1.15 (quality gate fail).
- Anti-repeat tags: high-return-low-pf, strict-confirmation-low-efficiency

6. MACDHistogramMomentumStrategy
- Metrics: Profit 18.78%, PF 1.03, Sharpe 0.32, Underwater 49.80%
- Delete reason: Sharpe <= 0.5, PF < 1.15, and underwater > 30%.
- Anti-repeat tags: momentum-whipsaw, excessive-drawdown, low-sharpe

7. MarketStructureSwingStrategy
- Metrics: Profit 43.21%, PF 1.11, Sharpe 0.42, Underwater 30.56%
- Delete reason: Sharpe <= 0.5, PF < 1.15, and underwater > 30%.
- Anti-repeat tags: structure-lag, drawdown-breach, low-sharpe

8. RiskAdjustedMomentumStrategy
- Metrics: Profit 13.20%, PF 1.37, Sharpe 0.18, Underwater 8.51%
- Delete reason: Sharpe 0.18 <= 0.5.
- Anti-repeat tags: low-risk-adjusted-return, weak-sharpe

9. SupertrendFollowStrategy
- Metrics: 0 trades
- Delete reason: Zero-trade strategy in test horizon (non-deployable as-is).
- Anti-repeat tags: signal-starvation, over-restrictive-trigger

10. TrendQualityStrategy
- Metrics: Profit 12.10%, PF 1.02, Sharpe 0.13, Underwater 33.87%
- Delete reason: Sharpe <= 0.5, PF < 1.15, and underwater > 30%.
- Anti-repeat tags: over-filtered-entry, low-pf, drawdown-breach

11. VWAPMeanReversionStrategy
- Metrics: Profit -45.61%, PF 0.74, Sharpe -0.95, Underwater 54.80%
- Delete reason: Negative profit, PF < 1.15, Sharpe <= 0.5, and underwater > 30%.
- Anti-repeat tags: mean-reversion-regime-mismatch, deep-drawdown, negative-expectancy

## Notes for Next Development Cycle

1. Avoid approving strategies with high headline return but PF below 1.15.
2. Reject low-trade or zero-trade designs unless the trigger logic is relaxed and revalidated.
3. Prioritize risk-adjusted robustness (Sharpe > 0.5) before considering optimization.
4. Treat mean-reversion concepts as regime-specific and require explicit trend filters plus drawdown controls.

---

Date: 2026-03-16
Scope: Batch 3 strategies (8 total)
Timerange: 20230101-20260311

Result for this cycle: 0/8 passed.

## Deleted Strategies and Reasons (Batch 3)

1. BarbellTrendMomentumStrategy
- Metrics: Profit -1.15%, PF 1.00, Sharpe -0.01, Underwater 32.48%
- Delete reason: Profit <= 10%, PF < 1.15, Sharpe <= 0.5, and underwater > 30%.
- Anti-repeat tags: barbell-trend-low-edge, drawdown-breach, weak-sharpe

2. VolatilityScaledTSMomentumStrategy
- Metrics: Profit 14.12%, PF 1.21, Sharpe 0.22, Underwater 13.02%
- Delete reason: Sharpe 0.22 <= 0.5.
- Anti-repeat tags: low-risk-adjusted-return, weak-sharpe

3. DonchianVolatilityBreakoutStrategy
- Metrics: Profit 24.84%, PF 1.44, Sharpe 0.23, Underwater 10.49%
- Delete reason: Sharpe 0.23 <= 0.5.
- Anti-repeat tags: breakout-low-sharpe, unstable-path-quality

4. PullbackAdxTrendContinuationStrategy
- Metrics: Profit -0.05%, PF 1.00, Sharpe -0.00, Underwater 32.55%
- Delete reason: Profit <= 10%, PF < 1.15, Sharpe <= 0.5, and underwater > 30%.
- Anti-repeat tags: pullback-no-edge, drawdown-breach, weak-sharpe

5. FundingAlignedTrendStrategy
- Metrics: Profit -85.65%, PF 0.90, Sharpe -1.20, Underwater 86.38%
- Delete reason: Severe quality failure across all rules (negative profit, PF < 1.15, Sharpe <= 0.5, underwater > 30%).
- Anti-repeat tags: funding-filter-instability, deep-drawdown, negative-expectancy

6. CrisisShortTrendStrategy
- Metrics: Profit 5.29%, PF 1.01, Sharpe 0.07, Underwater 34.13%
- Delete reason: Profit <= 10%, PF < 1.15, Sharpe <= 0.5, and underwater > 30%.
- Anti-repeat tags: short-bias-low-edge, drawdown-breach, weak-sharpe

7. RegimeGatedVWAPReversionStrategy
- Metrics: Profit -4.01%, PF 0.94, Sharpe -0.08, Underwater 19.14%
- Delete reason: Profit <= 10%, PF < 1.15, and Sharpe <= 0.5.
- Anti-repeat tags: reversion-regime-mismatch, negative-expectancy, weak-sharpe

8. BollingerRsiTrendVetoStrategy
- Metrics: Profit 2.01%, PF 1.19, Sharpe 0.04, Underwater 6.44%
- Delete reason: Profit <= 10% and Sharpe <= 0.5.
- Anti-repeat tags: controlled-reversion-low-return, weak-sharpe
