#!/usr/bin/env python3
"""
Offline Freqtrade Backtest Runner
===================================
Runs Freqtrade backtests without live exchange connectivity by:
  - Mocking exchange market loading (no API calls)
  - Using pre-cached Binance leverage tiers (binance_leverage_tiers.json)
  - Reading OHLCV, funding-rate, and mark-price from local feather files

Usage:
  python user_data/scripts/backtest_offline.py
  python user_data/scripts/backtest_offline.py --strategy FundingTiltMomentumStrategy
  python user_data/scripts/backtest_offline.py --strategy FundingTiltMomentumStrategy --timeframe 1h
  python user_data/scripts/backtest_offline.py --timerange 20230101-20231231

Requirements:
  - user_data/data/binance/futures/*.feather  (OHLCV + funding_rate + mark)
  - user_data/config.backtest.binance.futures.json
  - Strategies in user_data/strategies/

Note on data:
  If live Binance API is unreachable (blocked network), generate or use the
  pre-existing synthetic OHLCV dataset via:
    python user_data/scripts/generate_synthetic_data.py
"""
from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path
from unittest.mock import PropertyMock, patch

# Ensure freqtrade is importable
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

# ---------------------------------------------------------------------------
# Mock Binance USDT-M perpetual markets
# ---------------------------------------------------------------------------
_MOCK_MARKETS: dict = {
    "BTC/USDT:USDT": {
        "id": "BTCUSDT", "symbol": "BTC/USDT:USDT", "base": "BTC", "quote": "USDT",
        "settle": "USDT", "type": "swap", "spot": False, "swap": True, "future": True,
        "contract": True, "linear": True, "inverse": False, "active": True,
        "tierBased": False, "percentage": True, "taker": 0.0004, "maker": 0.0002,
        "contractSize": 1, "expiry": None, "strike": None, "optionType": None,
        "limits": {
            "leverage": {"min": 1, "max": 150}, "amount": {"min": 0.001, "max": 1000},
            "price": {"min": 100, "max": 10_000_000}, "cost": {"min": 5, "max": None},
        },
        "precision": {"price": 0.10, "amount": 0.001},
        "info": {
            "symbol": "BTCUSDT", "pricePrecision": "2", "quantityPrecision": "3",
            "contractType": "PERPETUAL", "status": "TRADING",
            "maintMarginPercent": "0.4", "requiredMarginPercent": "0.67",
        },
    },
    "ETH/USDT:USDT": {
        "id": "ETHUSDT", "symbol": "ETH/USDT:USDT", "base": "ETH", "quote": "USDT",
        "settle": "USDT", "type": "swap", "spot": False, "swap": True, "future": True,
        "contract": True, "linear": True, "inverse": False, "active": True,
        "tierBased": False, "percentage": True, "taker": 0.0004, "maker": 0.0002,
        "contractSize": 1, "expiry": None, "strike": None, "optionType": None,
        "limits": {
            "leverage": {"min": 1, "max": 150}, "amount": {"min": 0.001, "max": 10_000},
            "price": {"min": 1, "max": 1_000_000}, "cost": {"min": 5, "max": None},
        },
        "precision": {"price": 0.01, "amount": 0.001},
        "info": {
            "symbol": "ETHUSDT", "pricePrecision": "2", "quantityPrecision": "3",
            "contractType": "PERPETUAL", "status": "TRADING",
            "maintMarginPercent": "0.4", "requiredMarginPercent": "0.67",
        },
    },
    "SOL/USDT:USDT": {
        "id": "SOLUSDT", "symbol": "SOL/USDT:USDT", "base": "SOL", "quote": "USDT",
        "settle": "USDT", "type": "swap", "spot": False, "swap": True, "future": True,
        "contract": True, "linear": True, "inverse": False, "active": True,
        "tierBased": False, "percentage": True, "taker": 0.0004, "maker": 0.0002,
        "contractSize": 1, "expiry": None, "strike": None, "optionType": None,
        "limits": {
            "leverage": {"min": 1, "max": 75}, "amount": {"min": 0.1, "max": 1_000_000},
            "price": {"min": 0.001, "max": 100_000}, "cost": {"min": 5, "max": None},
        },
        "precision": {"price": 0.001, "amount": 0.1},
        "info": {
            "symbol": "SOLUSDT", "pricePrecision": "3", "quantityPrecision": "0",
            "contractType": "PERPETUAL", "status": "TRADING",
            "maintMarginPercent": "0.4", "requiredMarginPercent": "0.67",
        },
    },
}

_EXMS = "freqtrade.exchange.exchange.Exchange"
_BINMS = "freqtrade.exchange.binance.Binance"

_SUPPORTED_MODES = [("futures", "isolated"), ("spot", ""), ("futures", "cross")]


def run_backtest(
    strategy: str,
    timeframe: str,
    timerange: str = "20220101-20231231",
    config_path: str = "user_data/config.backtest.binance.futures.json",
    datadir: str = "user_data/data/binance",
    export_filename: str | None = None,
) -> None:
    """
    Run a single strategy backtest in offline mode.

    Parameters
    ----------
    strategy:        Freqtrade strategy class name
    timeframe:       Candle interval (e.g. "1h", "4h")
    timerange:       Date range in YYYYMMDD-YYYYMMDD format
    config_path:     Relative path to backtest config JSON
    datadir:         Root data directory (parent of futures/)
    export_filename: Custom export file path (auto-generated if None)
    """
    if export_filename is None:
        Path("user_data/backtest_results").mkdir(parents=True, exist_ok=True)
        export_filename = f"user_data/backtest_results/{strategy.lower()}_backtest.json"

    print(f"\n{'='*65}")
    print(f"  BACKTESTING : {strategy}")
    print(f"  Timeframe   : {timeframe}  |  Range: {timerange}")
    print(f"{'='*65}")

    args_list = [
        "backtesting",
        "--config", config_path,
        "--strategy", strategy,
        "--timeframe", timeframe,
        "--datadir", datadir,
        "--timerange", timerange,
        "--export", "trades",
        "--export-filename", export_filename,
    ]

    # Patch exchange network calls; let Binance.load_leverage_tiers() read
    # from the bundled binance_leverage_tiers.json when dry_run=True.
    with (
        patch(f"{_EXMS}._load_async_markets", return_value=_MOCK_MARKETS),
        patch(f"{_EXMS}.reload_markets", return_value=None),
        patch(f"{_EXMS}.markets", new_callable=PropertyMock, return_value=_MOCK_MARKETS),
        patch(f"{_EXMS}.validate_timeframes", return_value=None),
        patch(f"{_EXMS}.validate_config", return_value=None),
        patch(f"{_EXMS}.get_fee", return_value=0.0004),
        patch(
            f"{_BINMS}._supported_trading_mode_margin_pairs",
            new_callable=PropertyMock,
            return_value=_SUPPORTED_MODES,
        ),
    ):
        from freqtrade.commands import Arguments
        from freqtrade.configuration import Configuration
        from freqtrade.enums import RunMode
        from freqtrade.optimize.backtesting import Backtesting

        pargs = Arguments(args_list).get_parsed_arg()
        config = Configuration(pargs, RunMode.BACKTEST).get_config()
        # Force dry_run so Binance.load_leverage_tiers() reads its cached JSON
        config["dry_run"] = True
        config["fee"] = 0.0004

        bt = Backtesting(config)
        bt.start()

    print(f"\n✓ Completed: {strategy} → {export_filename}")


# ---------------------------------------------------------------------------
# Strategy registry: (class_name, preferred_timeframe)
# ---------------------------------------------------------------------------
ALL_STRATEGIES: list[tuple[str, str]] = [
    ("FundingTiltMomentumStrategy", "1h"),
    ("VolatilityCompressionBreakoutStrategy", "4h"),
    ("MomentumPulseStrategy", "4h"),
    ("DailyBreakoutTrendStrategy", "4h"),
    ("EmaAdxTrendFilterStrategy", "4h"),
    ("RegimeFilteredMeanReversionStrategy", "4h"),
    ("RsiBollingerMeanReversionStrategy", "4h"),
    ("SessionFilteredMomentumStrategy", "4h"),
    ("TimeSeriesMomentumVolatilityStrategy", "4h"),
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Freqtrade backtests offline (no exchange API calls required)."
    )
    parser.add_argument(
        "--strategy",
        default=None,
        help="Strategy class name to backtest (default: all strategies)",
    )
    parser.add_argument(
        "--timeframe",
        default=None,
        help="Candle interval override (default: per-strategy default)",
    )
    parser.add_argument(
        "--timerange",
        default="20220101-20231231",
        help="Date range YYYYMMDD-YYYYMMDD (default: 20220101-20231231)",
    )
    args = parser.parse_args()

    if args.strategy:
        tf_map = dict(ALL_STRATEGIES)
        timeframe = args.timeframe or tf_map.get(args.strategy, "4h")
        run_backtest(args.strategy, timeframe, timerange=args.timerange)
    else:
        for strategy, default_tf in ALL_STRATEGIES:
            timeframe = args.timeframe or default_tf
            try:
                run_backtest(strategy, timeframe, timerange=args.timerange)
            except Exception as exc:
                print(f"\n✗ {strategy} FAILED: {exc}")


if __name__ == "__main__":
    main()
