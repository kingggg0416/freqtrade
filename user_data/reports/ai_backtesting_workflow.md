# AI Backtesting Workflow (Isolated)

This workflow is intentionally separated from ordinary backtesting.

## Isolation guarantee

- Ordinary workflow keeps using `user_data/config.backtest.binance.futures.json`.
- AI workflow uses only `user_data/config.freqai.backtest.json`.
- AI runs are launched with `user_data/scripts/backtest_ai.py`.
- Existing ordinary backtesting commands and strategies are unchanged.

## Prerequisites

1. Install FreqAI dependencies (if missing):
   - `scikit-learn`
   - `lightgbm`
   - `xgboost`
   - `datasieve`
2. Ensure local futures data exists in `user_data/data/binance/futures`.
3. Ensure your environment can run `python -m freqtrade`.

Recommended bootstrap in this repository:

```bash
.venv/bin/python -m pip install -r requirements-freqai.txt
```

If you use the launcher script, it auto-prefers `.venv/bin/python` and runs a
dependency preflight check before starting backtests.

## Data acquisition (real Binance futures)

```bash
python3 -m freqtrade download-data \
  --config user_data/config.freqai.backtest.json \
  --timeframes 1h 4h \
  --timerange 20220101-20260301 \
  --pairs BTC/USDT:USDT ETH/USDT:USDT SOL/USDT:USDT
```

## Run AI backtesting

```bash
python user_data/scripts/backtest_ai.py
```

Custom run:

```bash
python user_data/scripts/backtest_ai.py \
  --timerange 20230101-20231231 \
  --freqaimodel LightGBMRegressor \
  --export user_data/backtest_results/freqai_2023.json
```

Validated run in this workspace:

```bash
python user_data/scripts/backtest_ai.py --timerange 20230401-20230930
```

Why this window was used:

- Current local futures data starts at `2023-01-01`.
- FreqAI setup uses a long startup/training warmup, so very early timeranges can fail.
- Start from April 2023 (or download more pre-history) for stable retraining cycles.

## Ordinary backtesting remains separate

Use your normal command path for ordinary strategies:

```bash
python3 -m freqtrade backtesting \
  --config user_data/config.backtest.binance.futures.json \
  --strategy MomentumPulseStrategy \
  --timerange 20220101-20231231 \
  --datadir user_data/data/binance
```

## Optional batch/offline runner

If you want mock-market offline execution for your existing strategy set:

```bash
python user_data/scripts/backtest_offline.py
```

For AI strategy through the offline runner:

```bash
python user_data/scripts/backtest_offline.py \
  --strategy FreqAIRetailStrategy \
  --config user_data/config.freqai.backtest.json \
  --freqaimodel LightGBMRegressor
```
