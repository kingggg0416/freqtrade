# Batch 2 Backtesting Run

Date: 2026-03-16

Range: 20230101-20260311

Bias audit status: Ichimoku strategy was corrected for look-ahead bias before rerun.

Running ATRChannelBreakoutStrategy (tf=1d detail=4h)
```text
│ Absolute profit │ 110.293 USDT │
│ Total profit % │ 11.03% │
│ Profit factor │ 1.22 │
│ Max % of account underwater │ 12.95% │
```

Running TrendQualityStrategy (tf=4h detail=1h)
```text
│ Absolute profit │ 121.023 USDT │
│ Total profit % │ 12.10% │
│ Profit factor │ 1.02 │
│ Max % of account underwater │ 33.87% │
```

Running BtcRegimeAdaptiveStrategy (tf=4h detail=1h)
```text
│ Absolute profit │ 489.097 USDT │
│ Total profit % │ 48.91% │
│ Profit factor │ 1.06 │
│ Max % of account underwater │ 28.74% │
```

Running SupertrendFollowStrategy (tf=4h detail=1h)
- Status: FAILED or no summary parsed
┃ Enter Tag ┃ Entries ┃ Avg Profit % ┃ Tot Profit USDT ┃ Tot Profit % ┃ Avg Duration ┃  Win  Draw  Loss  Win% ┃
┡━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│     TOTAL │       0 │          0.0 │           0.000 │          0.0 │         0:00 │    0     0     0     0 │
└───────────┴─────────┴──────────────┴─────────────────┴──────────────┴──────────────┴────────────────────────┘
                                               EXIT REASON STATS                                               
┏━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Exit Reason ┃ Exits ┃ Avg Profit % ┃ Tot Profit USDT ┃ Tot Profit % ┃ Avg Duration ┃  Win  Draw  Loss  Win% ┃
┡━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│       TOTAL │     0 │          0.0 │           0.000 │          0.0 │         0:00 │    0     0     0     0 │
└─────────────┴───────┴──────────────┴─────────────────┴──────────────┴──────────────┴────────────────────────┘
                                                      MIXED TAG STATS                                                       
┏━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Enter Tag ┃ Exit Reason ┃ Trades ┃ Avg Profit % ┃ Tot Profit USDT ┃ Tot Profit % ┃ Avg Duration ┃  Win  Draw  Loss  Win% ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│     TOTAL │             │      0 │          0.0 │           0.000 │          0.0 │         0:00 │    0     0     0     0 │
└───────────┴─────────────┴────────┴──────────────┴─────────────────┴──────────────┴──────────────┴────────────────────────┘
No trades made. Your starting balance was 1000 USDT, and your stake was 150 USDT.

Backtested 2023-01-11 00:00:00 -> 2026-03-11 00:00:00 | Max open trades : 3
                                                              STRATEGY SUMMARY                                                               
┏━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃                 Strategy ┃ Trades ┃ Avg Profit % ┃ Tot Profit USDT ┃ Tot Profit % ┃ Avg Duration ┃  Win  Draw  Loss  Win% ┃      Drawdown ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ SupertrendFollowStrategy │      0 │         0.00 │           0.000 │          0.0 │         0:00 │    0     0     0     0 │ 0 USDT  0.00% │
└──────────────────────────┴────────┴──────────────┴─────────────────┴──────────────┴──────────────┴────────────────────────┴───────────────┘

Running DualMACrossoverVolumeStrategy (tf=4h detail=1h)
```text
│ Absolute profit │ -68.79 USDT │
│ Total profit % │ -6.88% │
│ Profit factor │ 0.90 │
│ Max % of account underwater │ 15.62% │
```

Running MACDHistogramMomentumStrategy (tf=4h detail=1h)
```text
│ Absolute profit │ 187.801 USDT │
│ Total profit % │ 18.78% │
│ Profit factor │ 1.03 │
│ Max % of account underwater │ 49.80% │
```

Running RiskAdjustedMomentumStrategy (tf=4h detail=1h)
```text
│ Absolute profit │ 132.028 USDT │
│ Total profit % │ 13.20% │
│ Profit factor │ 1.37 │
│ Max % of account underwater │ 8.51% │
```

Running IchimokuCloudBreakoutStrategy (tf=4h detail=1h)
```text
│ Absolute profit │ 551.203 USDT │
│ Total profit % │ 55.12% │
│ Profit factor │ 1.08 │
│ Max % of account underwater │ 21.32% │
```

Running MarketStructureSwingStrategy (tf=1d detail=4h)
```text
│ Absolute profit │ 432.122 USDT │
│ Total profit % │ 43.21% │
│ Profit factor │ 1.11 │
│ Max % of account underwater │ 30.56% │
```

Running FundingCarryLiteStrategy (tf=4h detail=1h)
- Status: FAILED or no summary parsed
2026-03-16 13:51:48,970 - freqtrade.loggers - INFO - Logfile configured
2026-03-16 13:51:48,970 - freqtrade.loggers - INFO - Verbosity set to 0
2026-03-16 13:51:48,971 - freqtrade.configuration.configuration - INFO - Parameter -i/--timeframe detected ... Using timeframe: 4h ...
2026-03-16 13:51:48,971 - freqtrade.configuration.configuration - INFO - Using max_open_trades: 3 ...
2026-03-16 13:51:48,972 - freqtrade.configuration.configuration - INFO - Parameter --timeframe-detail detected, using 1h for intra-candle backtesting ...
2026-03-16 13:51:48,972 - freqtrade.configuration.configuration - INFO - Parameter --timerange detected: 20230101-20260311 ...
2026-03-16 13:51:48,973 - freqtrade.configuration.configuration - INFO - Using user-data directory: /workspaces/freqtrade/user_data ...
2026-03-16 13:51:48,973 - freqtrade.configuration.configuration - INFO - Using data directory: /workspaces/freqtrade/user_data/data/binance ...
2026-03-16 13:51:48,974 - freqtrade.configuration.configuration - INFO - Parameter --export detected: none ...
2026-03-16 13:51:48,974 - freqtrade.configuration.configuration - INFO - Parameter --cache=day detected ...
2026-03-16 13:51:48,975 - freqtrade.configuration.configuration - INFO - Filter trades by timerange: 20230101-20260311
2026-03-16 13:51:48,975 - freqtrade.exchange.check_exchange - INFO - Checking exchange...
2026-03-16 13:51:48,985 - freqtrade.exchange.check_exchange - INFO - Exchange "binance" is officially supported by the Freqtrade development team.
2026-03-16 13:51:48,985 - freqtrade.configuration.configuration - INFO - Using pairlist from configuration.
2026-03-16 13:51:48,986 - freqtrade.configuration.config_validation - INFO - Validating configuration ...
2026-03-16 13:51:48,988 - freqtrade.commands.optimize_commands - INFO - Starting freqtrade in Backtesting mode
2026-03-16 13:51:48,989 - freqtrade.exchange.exchange - INFO - Instance is running with dry_run enabled
2026-03-16 13:51:48,989 - freqtrade.exchange.exchange - INFO - Using CCXT 4.5.43
2026-03-16 13:51:48,990 - freqtrade.exchange.exchange - INFO - Applying additional ccxt config: {'options': {'defaultType': 'swap'}}
2026-03-16 13:51:49,004 - freqtrade.exchange.exchange - INFO - Applying additional ccxt config: {'options': {'defaultType': 'swap'}}
2026-03-16 13:51:49,026 - freqtrade.exchange.exchange - INFO - Using Exchange "Binance"
2026-03-16 13:51:50,160 - freqtrade.resolvers.exchange_resolver - INFO - Using resolved exchange 'Binance'...
2026-03-16 13:51:50,163 - freqtrade.resolvers.iresolver - INFO - Using resolved strategy FundingCarryLiteStrategy from '/workspaces/freqtrade/user_data/strategies/FundingCarryLiteStrategy.py'...
2026-03-16 13:51:50,163 - freqtrade.strategy.hyper - INFO - Found no parameter file.
2026-03-16 13:51:50,164 - freqtrade - ERROR - Informative timeframe must be equal or higher than strategy timeframe!

Running VWAPMeanReversionStrategy (tf=4h detail=1h)
```text
│ Absolute profit │ -456.117 USDT │
│ Total profit % │ -45.61% │
│ Profit factor │ 0.74 │
│ Max % of account underwater │ 54.80% │
```

Bias audit notes (2026-03-16):
- `IchimokuCloudBreakoutStrategy` had a future-data leak from negative shift usage in Chikou logic and was fixed.
- The old Ichimoku result (`228.65%`) is invalid and replaced by the rerun result above.
- Lookahead-analysis run is currently inconclusive for this strategy due too few trades in the selected timerange (`too few trades caught (0/1)`).
- Workspace scan for similar explicit patterns (`shift(-N)`, negative diff/pct_change, centered rolling windows) found no additional matches in `user_data/strategies/*.py`.

