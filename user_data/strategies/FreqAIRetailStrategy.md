# FreqAIRetailStrategy

Type: FreqAI (LightGBM regression)
Timeframe: 1h
Can short: yes
Intended account profile: small retail futures account

## Summary

FreqAIRetailStrategy predicts forward mean return over the configured label horizon,
then enters only when prediction confidence and ADX trend strength align. It is built
for walk-forward retraining through FreqAI and conservative leverage control.

## Key design choices

- Model target: forward mean return using label_period_candles
- Entry threshold: configurable with hyperoptable buy parameter
- Exit threshold: configurable with hyperoptable sell parameter
- Trend gate: ADX minimum filter before entries
- Risk controls: leverage cap at 2x, fixed stoploss, trailing stop, slippage guard

## Feature groups

- Trend: EMA, SMA, ADX
- Momentum: RSI, ROC, CCI, MFI
- Volatility: ATR, Bollinger width, Donchian width
- Structure: high-low ratio, close-open ratio
- Time context: day-of-week, hour-of-day, month

## Run examples

```bash
python3 -m freqtrade backtesting \
  --config user_data/config.freqai.backtest.json \
  --strategy FreqAIRetailStrategy \
  --freqaimodel LightGBMRegressor \
  --timerange 20220101-20231231
```

## Notes

- This strategy expects local futures data to be present in user_data/data/binance.
- Use freqtrade download-data against Binance futures for data acquisition.
- Keep leverage conservative while validating on fresh out-of-sample windows.
