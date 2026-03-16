# Batch 3 Backtest Template

Date:
Timerange:
Config:

## Hard Pass Criteria

1. Total profit > 10%
2. Profit factor >= 1.15
3. Sharpe > 0.5
4. Max underwater <= 30%
5. Non-zero trades
6. No runtime errors

## Results Table

| Strategy | TF | Profit % | PF | Sharpe | Max Underwater % | Trades | Status | Decision | Delete Reason |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| BarbellTrendMomentumStrategy | 4h | | | | | | | | |
| VolatilityScaledTSMomentumStrategy | 4h | | | | | | | | |
| DonchianVolatilityBreakoutStrategy | 1d | | | | | | | | |
| PullbackAdxTrendContinuationStrategy | 4h | | | | | | | | |
| FundingAlignedTrendStrategy | 4h | | | | | | | | |
| CrisisShortTrendStrategy | 4h | | | | | | | | |
| RegimeGatedVWAPReversionStrategy | 4h | | | | | | | | |
| BollingerRsiTrendVetoStrategy | 4h | | | | | | | | |

## Notes

1. Any failed strategy must include explicit delete reason.
2. Append failures to failed_strategy_log.md before deleting strategy files.
3. Remove temporary batch artifacts after cycle completion.
