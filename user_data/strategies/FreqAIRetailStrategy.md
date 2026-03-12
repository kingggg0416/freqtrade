# FreqAIRetailStrategy

**Type**: FreqAI (LightGBM Regression)  
**Timeframe**: 1h  
**Can short**: Yes (long + short futures)  
**Capital context**: Designed for $1000 USDT isolated futures  
**Model**: LightGBMRegressor  

## Strategy summary

`FreqAIRetailStrategy` uses a rolling LightGBM regression model to predict the
mean forward 12-candle (12-hour) return for each pair. It enters long when the
model predicts > +1.5% and short when < -1.5%, filtering entries with an ADX
confirmation. Exits are signal-driven (prediction reversal) with a trailing stop.

## Key design decisions

| Parameter | Value | Rationale |
|---|---|---|
| `label_period_candles` | 12 | Smooth 12h target reduces noise vs single-candle |
| `train_period_days` | 60 | ~1440 training samples; balances recency vs overfitting |
| `backtest_period_days` | 7 | Weekly retraining adapts to regime shifts |
| `entry_threshold` | 0.015 (1.5%) | Filters low-confidence predictions |
| `max_leverage` | 2x | Critical for $1000 accounts — prevents margin calls |
| `stoploss` | -5% | At 2x leverage = 10% position loss max |

## Feature groups

- **Momentum**: RSI, ROC, CCI, MFI across 10/20/40-period windows
- **Trend**: EMA, SMA, ADX across 10/20/40-period windows  
- **Volatility**: ATR, Bollinger Band width, Donchian channel width
- **Volume**: Relative volume, MFI
- **Temporal**: Day of week, hour, month
- **Cross-asset**: Correlated pair RSI and ROC (BTC as correlation anchor)

## Requirements

```bash
pip install scikit-learn lightgbm datasieve
```

## Config parameter notes

| Parameter | Value | Notes |
|---|---|---|
| `timeframe` | 1h | Primary signal timeframe; `4h` in feature_parameters provides multi-TF context only |
| `live_retrain_hours` | 0 | Disabled in backtest mode; set to 8-24 for live deployment |
| `expiration_hours` | 0 | In backtest, 0 means models don't expire; in live, set to 4+ |
| `stratify_training_data` | 0 | Disabled — stratification is for classification tasks; we use regression |

## Backtesting command

```bash
python3 -m freqtrade backtesting \
  --config user_data/config.freqai.backtest.json \
  --strategy FreqAIRetailStrategy \
  --freqaimodel LightGBMRegressor \
  --timerange 20220301-20251231
```

## Research status

- ✅ Strategy code complete
- ✅ Config complete  
- ✅ Walk-forward framework validated on synthetic data
- ⬜ Validated on real market data (pending network access for data download)
- ⬜ Hyperopt for entry/exit thresholds
- ⬜ Feature refinement with funding rate

## Detailed research

See: `user_data/reports/freqai_research_report_2026-03-12.md`
