# AI Agent Handoff

## Purpose of this file
This is a continuation brief for the next AI agent working in this repository. It summarizes the user's goals, the work already completed, the current research status, important files, environment details, and the highest-value next steps.

---

## 1) User intent and working style

### Core user goal
The user wants to build a personal systematic trading research workflow on top of the `freqtrade` repository.

### Strategic context
- Long-term gateway of interest: **Hyperliquid**.
- Current practical focus: **backtesting and strategy development first**, not live deployment.
- The user explicitly wants a phased path:
  1. Backtest
  2. Dry-run
  3. Live
- The user wants strategy work done from the viewpoint of a **retail trader with limited speed and capital**.
- The user wants the process to be **research-oriented, explainable, and robust**, not optimized for flashy in-sample results.

### Important user preferences
- Be proactive.
- Avoid unnecessary questions if useful work can be done directly.
- Be careful about **overfitting**.
- Leave persistent written artifacts so future work is easy to continue.

---

## 2) What has already been done

### Repository understanding
- The repository structure was reviewed.
- Hyperliquid support was investigated early and appears to be a realistic future pathway.
- However, current research work shifted to **Binance futures backtesting** because it is easier to source data and iterate quickly.

### Environment and setup
- A local virtual environment is in use.
- Working pattern that succeeded repeatedly:
  - Use `.venv/bin/python -m freqtrade ...`
- Core dependencies were installed successfully.
- Minimal hyperopt-related dependencies were installed successfully:
  - `optuna`
  - `cmaes`
  - `filelock`

### Data and market setup
- Research market: **Binance isolated futures**
- Pairs used:
  - `BTC/USDT:USDT`
  - `ETH/USDT:USDT`
  - `SOL/USDT:USDT`
- Timeframes downloaded/used:
  - `1h`
  - `4h`
  - `1d`
- Mark/funding data was also downloaded for the futures workflow.

### Strategy implementation status
Twenty research strategies are now in `user_data/strategies/`, each with a matching `.md` explanation file.

**Original nine strategies:**

1. `DailyBreakoutTrendStrategy`
2. `EmaAdxTrendFilterStrategy`
3. `RsiBollingerMeanReversionStrategy`
4. `RegimeFilteredMeanReversionStrategy`
5. `MomentumPulseStrategy`
6. `VolatilityCompressionBreakoutStrategy`
7. `TimeSeriesMomentumVolatilityStrategy`
8. `FundingTiltMomentumStrategy`
9. `SessionFilteredMomentumStrategy`

**New strategies added (Batch 2):**

10. `DualMACrossoverVolumeStrategy` — EMA crossover with volume confirmation (4h)
11. `VWAPMeanReversionStrategy` — Rolling VWAP mean reversion in range-bound conditions (4h)
12. `ATRChannelBreakoutStrategy` — N-period channel breakout without compression requirement (1d)
13. `SupertrendFollowStrategy` — Supertrend flip-based trend following (4h)
14. `IchimokuCloudBreakoutStrategy` — Ichimoku triple-confirmation cloud breakout (4h)
15. `MACDHistogramMomentumStrategy` — MACD histogram cross with RSI filter (4h)
16. `RiskAdjustedMomentumStrategy` — Volatility-normalized Sharpe-style momentum (4h)
17. `FundingCarryLiteStrategy` — Pure funding carry (no trend required) (4h)
18. `BtcRegimeAdaptiveStrategy` — BTC macro regime filter for all pairs (4h)
19. `MarketStructureSwingStrategy` — Higher Highs / Higher Lows structure detection (1d)
20. `TrendQualityStrategy` — Composite ADX + EMA alignment + regression slope score (4h)

All strategies are futures-capable and use conservative leverage callbacks capped at `2x` or less.

### Optimization / validation work already completed
- A conservative anti-overfitting workflow was applied.
- Train/test split used:
  - In-sample: `20230101-20241231`
  - Out-of-sample: `20250101-20260311`
- Loss function chosen for hyperopt:
  - `MultiMetricHyperOptLoss`

Results:
- `DailyBreakoutTrendStrategy`
  - Hyperopt completed successfully.
  - Saved params exist.
  - Out-of-sample validation completed.
- `MomentumPulseStrategy`
  - Hyperopt was interrupted early, but produced a usable saved params file.
  - Out-of-sample validation completed.
- `VolatilityCompressionBreakoutStrategy`
  - Hyperopt attempt did **not** complete any epoch.
  - Out-of-sample validation was still run on default params.
- A second strategy batch based on `references/perp-trading-ideas.md` was then added and tested with **no tuning**.
- That batch produced two useful additions:
  - `FundingTiltMomentumStrategy`
  - `SessionFilteredMomentumStrategy`
- The plain `TimeSeriesMomentumVolatilityStrategy` was too weak and should not be prioritized.

---

## 3) Current research conclusion

### Current ranking by robustness
*Batch 1 (previously backtested):*
1. `FundingTiltMomentumStrategy`
2. `VolatilityCompressionBreakoutStrategy`
3. `SessionFilteredMomentumStrategy`
4. `DailyBreakoutTrendStrategy`
5. `EmaAdxTrendFilterStrategy`
6. `MomentumPulseStrategy`
7. `RegimeFilteredMeanReversionStrategy`
8. `RsiBollingerMeanReversionStrategy`
9. `TimeSeriesMomentumVolatilityStrategy`

*Batch 2 (not yet backtested — design-level ordering by expected robustness):*
10. `ATRChannelBreakoutStrategy` — closest to proven Turtle/Donchian system
11. `TrendQualityStrategy` — ultra-selective triple-confirmation; hard to overfit
12. `BtcRegimeAdaptiveStrategy` — macro regime filter adds genuine edge
13. `SupertrendFollowStrategy` — well-tested indicator, clean mechanical rules
14. `DualMACrossoverVolumeStrategy` — classic MA cross; volume filter improves selectivity
15. `MACDHistogramMomentumStrategy` — solid momentum logic with RSI filter
16. `RiskAdjustedMomentumStrategy` — Sharpe-style signal is theoretically sound
17. `IchimokuCloudBreakoutStrategy` — triple-confirmation but slower entries
18. `MarketStructureSwingStrategy` — conceptually strong; depends on swing clarity
19. `FundingCarryLiteStrategy` — pure carry; requires high-funding episodes
20. `VWAPMeanReversionStrategy` — requires range-bound conditions; regime-dependent

### Interpretation
- Breakout/trend logic is clearly outperforming the mean-reversion family in this current market/sample.
- `FundingTiltMomentumStrategy` is now the strongest new candidate because it held up out of sample with very low drawdown and no tuning.
- `VolatilityCompressionBreakoutStrategy` remains strong and robust.
- `SessionFilteredMomentumStrategy` is promising, especially on the short side, but is riskier than the funding-tilted model.
- `DailyBreakoutTrendStrategy` is still a credible slower candidate because it remained positive out of sample.
- `MomentumPulseStrategy` remains the clearest overfitting warning sign: decent broader-sample appearance, but weak out-of-sample generalization.
- The two mean-reversion strategies should not be prioritized unless the design thesis changes substantially.
- The plain, conservative `TimeSeriesMomentumVolatilityStrategy` did not add value and should be deprioritized.

### Most important practical takeaway
If only two strategies should move forward immediately, they are:
- `FundingTiltMomentumStrategy`
- `VolatilityCompressionBreakoutStrategy`

The next slower-timeframe candidate after those is:
- `DailyBreakoutTrendStrategy`

A low-volatility secondary watchlist candidate is:
- `EmaAdxTrendFilterStrategy`

---

## 4) Most important files to inspect first

### Research summary
- `user_data/reports/strategy_backtest_summary_2026-03-12.md`
  - This is the main performance memo for Batch 1.
  - It contains full-sample and out-of-sample summaries, ranking, and recommendations.
- `user_data/reports/perp_trading_ideas_strategy_batch_2026-03-12.md`
  - This contains the second batch built directly from `references/perp-trading-ideas.md`.
  - Read this before doing more work on the new ideas.
- `user_data/reports/new_strategy_batch_2_2026-03-12.md`
  - This covers the 11 new strategies added in Batch 2 (strategies 10–20).
  - Includes design rationale, coverage map, recommended backtesting order, and
    anti-overfitting reminders.
  - **No backtesting results yet** — this batch has not been run against data.

### Futures backtest config
- `user_data/config.backtest.binance.futures.json`
  - This is the working research config used for the strategy backtests.

### Strategy source files
**Batch 1 (9 original strategies):**
- `user_data/strategies/DailyBreakoutTrendStrategy.py`
- `user_data/strategies/EmaAdxTrendFilterStrategy.py`
- `user_data/strategies/RsiBollingerMeanReversionStrategy.py`
- `user_data/strategies/RegimeFilteredMeanReversionStrategy.py`
- `user_data/strategies/MomentumPulseStrategy.py`
- `user_data/strategies/VolatilityCompressionBreakoutStrategy.py`
- `user_data/strategies/TimeSeriesMomentumVolatilityStrategy.py`
- `user_data/strategies/FundingTiltMomentumStrategy.py`
- `user_data/strategies/SessionFilteredMomentumStrategy.py`

**Batch 2 (11 new strategies):**
- `user_data/strategies/DualMACrossoverVolumeStrategy.py`
- `user_data/strategies/VWAPMeanReversionStrategy.py`
- `user_data/strategies/ATRChannelBreakoutStrategy.py`
- `user_data/strategies/SupertrendFollowStrategy.py`
- `user_data/strategies/IchimokuCloudBreakoutStrategy.py`
- `user_data/strategies/MACDHistogramMomentumStrategy.py`
- `user_data/strategies/RiskAdjustedMomentumStrategy.py`
- `user_data/strategies/FundingCarryLiteStrategy.py`
- `user_data/strategies/BtcRegimeAdaptiveStrategy.py`
- `user_data/strategies/MarketStructureSwingStrategy.py`
- `user_data/strategies/TrendQualityStrategy.py`

### Strategy explanation docs
Each strategy also has a sidecar markdown explanation in the same folder.

### Saved hyperopt parameter files
- `user_data/strategies/DailyBreakoutTrendStrategy.json`
- `user_data/strategies/MomentumPulseStrategy.json`

### Reference document that drove the second batch
- `references/perp-trading-ideas.md`

### Tracking / git behavior
- `.gitignore`
  - Was updated so the relevant strategy files and the safe futures backtest config are no longer hidden by ignore rules.

---

## 5) Important details the next agent should know

### Live trading is not the focus right now
Do not spend time on production deployment yet unless the user explicitly pivots back there.
The current phase is still strategy research and validation.

### Use the existing environment pattern
Prefer:
- `.venv/bin/python -m freqtrade ...`

Avoid assuming `freqtrade` is globally installed or that shell activation is required.

### Current benchmark market is intentional
Even though the user originally discussed Hyperliquid, the current research benchmark is Binance futures.
That was a deliberate practical choice for data availability and backtesting speed.

### Overfitting awareness matters a lot
The user explicitly asked for caution here.
Any continuation should favor:
- small search budgets
- parameter stability checks
- out-of-sample validation
- simple logic over complexity

### Existing report already contains the main numbers
Do not recompute everything unless needed.
Read the report first, then decide what requires fresh validation.

### Funding tilt and compression breakout currently have the strongest evidence
The next agent should not lose sight of this.
If deciding where to spend the next unit of research effort, prioritize:
1. `FundingTiltMomentumStrategy`
2. `VolatilityCompressionBreakoutStrategy`
3. `DailyBreakoutTrendStrategy`

### Known implementation note
The `MomentumPulseStrategy.py` and `VolatilityCompressionBreakoutStrategy.py` files currently use tab-style indentation in the saved source. They validated successfully, but avoid unnecessary reformatting unless you are intentionally normalizing style.

---

## 6) Recommended next steps

### Highest-priority next action
**Backtest the Batch 2 strategies** to determine which ones are worth pursuing further.

The recommended order (from `user_data/reports/new_strategy_batch_2_2026-03-12.md`):
1. `ATRChannelBreakoutStrategy` (1d — closest to proven Turtle system)
2. `TrendQualityStrategy` (4h — triple-confirmation, hard to overfit)
3. `BtcRegimeAdaptiveStrategy` (4h — macro regime filter)
4. `SupertrendFollowStrategy` (4h — volatility-adaptive trailing)

### Suggested continuation sequence
1. Read `user_data/reports/strategy_backtest_summary_2026-03-12.md` (Batch 1 results)
2. Read `user_data/reports/new_strategy_batch_2_2026-03-12.md` (Batch 2 overview)
3. Download data if not present (see Section 7 for commands)
4. Run full-sample backtest for each Batch 2 strategy
5. Compare Batch 2 to Batch 1 results
6. Run conservative hyperopt on the top 3–4 Batch 2 strategies
7. Validate out of sample

### Once backtesting is done
- **If `ATRChannelBreakoutStrategy` or `TrendQualityStrategy` perform similarly to
  `VolatilityCompressionBreakoutStrategy`:** Consider running all three as a portfolio.
- **If `BtcRegimeAdaptiveStrategy` is robust:** Use it as a regime overlay for ETH/SOL
  positions in any combined portfolio.
- **If `FundingCarryLiteStrategy` shows positive carry income:** Complement it with
  `FundingTiltMomentumStrategy` as the two represent different angles on the same edge.

### Previous top candidates still prioritized
The Batch 1 ranking still stands. Continue to prioritize:
1. `FundingTiltMomentumStrategy`
2. `VolatilityCompressionBreakoutStrategy`
3. `DailyBreakoutTrendStrategy`

---

## 7) Commands / workflow notes

These are patterns that worked in the current session.

### General backtesting pattern
- Trend strategies:
  - timeframe: `1d`
  - detail timeframe: `4h`
- Faster strategies:
  - timeframe: `4h`
  - detail timeframe: `1h`

### Example command structure
Use the working config and invoke via the local environment:

- `.venv/bin/python -m freqtrade backtesting --config user_data/config.backtest.binance.futures.json --strategy <StrategyName> --timeframe <tf> --timeframe-detail <detail_tf> --timerange <range> --export none`

### Validation split used in this project
- In-sample optimization: `20230101-20241231`
- Out-of-sample validation: `20250101-20260311`

### Hyperopt guidance for continuation
Use modest epoch counts first.
The current user preference favors robust iteration over aggressive parameter mining.

---

## 8) Current repository state relevant to this work

Tracked additions/modifications relevant to the research work include:
- `.gitignore`
- `user_data/config.backtest.binance.futures.json`
- all 20 strategy `.py` files in `user_data/strategies/`
- all 20 strategy `.md` explanation files in `user_data/strategies/`
- hyperopt param json files for `DailyBreakoutTrendStrategy` and `MomentumPulseStrategy`
- `user_data/reports/strategy_backtest_summary_2026-03-12.md`
- `user_data/reports/perp_trading_ideas_strategy_batch_2026-03-12.md`
- `user_data/reports/new_strategy_batch_2_2026-03-12.md` (new)
- `references/perp-trading-ideas.md`
- this file: `AI_AGENT_HANDOFF.md`

---

## 9) If you only have 5 minutes

Read these in order:
1. `AI_AGENT_HANDOFF.md`
2. `user_data/reports/strategy_backtest_summary_2026-03-12.md` (Batch 1 backtest results)
3. `user_data/reports/new_strategy_batch_2_2026-03-12.md` (Batch 2 overview — not yet tested)
4. `user_data/strategies/FundingTiltMomentumStrategy.py` (current best from Batch 1)
5. `user_data/strategies/ATRChannelBreakoutStrategy.py` (highest-priority to test from Batch 2)

Then start with backtesting `ATRChannelBreakoutStrategy` as the first Batch 2 priority.

---

## 10) Bottom line

The project has now reached 20 strategies across a diverse set of conceptual approaches.
The triage from Batch 1 still stands — `FundingTiltMomentumStrategy` and
`VolatilityCompressionBreakoutStrategy` are the current best validated candidates.

Batch 2 adds 11 new strategies that have not yet been backtested. The **highest-priority
next step** is to run backtests on at least the top 4 Batch 2 strategies to identify
which ones perform competitively.

Strategy diversity by category (across all 20):
- Trend following / breakout: 7 strategies
- Momentum: 4 strategies
- Mean reversion: 3 strategies
- Regime filtering / adaptive: 2 strategies
- Carry / funding: 2 strategies
- Composite quality scoring: 1 strategy
- Ichimoku / classical systems: 1 strategy

Current best path:
- Keep the research disciplined and avoid overfitting
- Backtest Batch 2 in order of expected robustness
- Compare Batch 2 top performers vs Batch 1 top performers
- Only advance strategies with positive out-of-sample behavior
- Do not deploy live until at least 2–3 strategies show consistent out-of-sample results
