# Batch 3 Governance

Date: 2026-03-16
Market: Binance Futures
Pairs: BTC/USDT:USDT, ETH/USDT:USDT, SOL/USDT:USDT

## Hard Pass Criteria

A strategy passes only if all are true:

1. Total profit > 10%
2. Profit factor >= 1.15
3. Sharpe > 0.5
4. Max % account underwater <= 30%
5. Non-zero trades
6. No runtime errors

## Development Constraints

1. Keep parameter count low and interpretable.
2. Avoid lookahead patterns: no negative shift, no global mean/min/max without rolling windows.
3. Use informative timeframe >= strategy timeframe.
4. Prefer 4h and 1d systems to reduce noise and turnover.
5. Do not optimize before baseline and OOS checks.
6. Document each new strategy using the template in `user_data/reports/strategy_markdown_template.md`.

## Validation Funnel

1. Baseline backtest for all candidates.
2. Keep top candidates by pass criteria and trade sufficiency.
3. Run IS/OOS validation.
4. Run pair-level robustness checks.

## Deletion Policy

1. Failed strategies are logged with explicit reasons in failed_strategy_log.md.
2. Failed strategy .py and .md files are deleted after logging.
3. Temporary batch artifacts are removed after each cycle.
