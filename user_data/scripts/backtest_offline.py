#!/usr/bin/env python3
"""
Offline backtest runner for local Binance futures datasets.

This script avoids live exchange network calls by mocking market loading while
keeping normal backtesting logic and leverage-tier handling intact.

Examples:
  python user_data/scripts/backtest_offline.py
  python user_data/scripts/backtest_offline.py --strategy MomentumPulseStrategy
  python user_data/scripts/backtest_offline.py --strategy FreqAIRetailStrategy \
      --config user_data/config.freqai.backtest.json --freqaimodel LightGBMRegressor
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from unittest.mock import PropertyMock, patch


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)


_MOCK_MARKETS: dict = {
    "BTC/USDT:USDT": {
        "id": "BTCUSDT",
        "symbol": "BTC/USDT:USDT",
        "base": "BTC",
        "quote": "USDT",
        "settle": "USDT",
        "type": "swap",
        "spot": False,
        "swap": True,
        "future": True,
        "contract": True,
        "linear": True,
        "inverse": False,
        "active": True,
        "tierBased": False,
        "percentage": True,
        "taker": 0.0004,
        "maker": 0.0002,
        "contractSize": 1,
        "limits": {
            "leverage": {"min": 1, "max": 150},
            "amount": {"min": 0.001, "max": 1000},
            "price": {"min": 100, "max": 10000000},
            "cost": {"min": 5, "max": None}
        },
        "precision": {"price": 0.10, "amount": 0.001}
    },
    "ETH/USDT:USDT": {
        "id": "ETHUSDT",
        "symbol": "ETH/USDT:USDT",
        "base": "ETH",
        "quote": "USDT",
        "settle": "USDT",
        "type": "swap",
        "spot": False,
        "swap": True,
        "future": True,
        "contract": True,
        "linear": True,
        "inverse": False,
        "active": True,
        "tierBased": False,
        "percentage": True,
        "taker": 0.0004,
        "maker": 0.0002,
        "contractSize": 1,
        "limits": {
            "leverage": {"min": 1, "max": 150},
            "amount": {"min": 0.001, "max": 10000},
            "price": {"min": 1, "max": 1000000},
            "cost": {"min": 5, "max": None}
        },
        "precision": {"price": 0.01, "amount": 0.001}
    },
    "SOL/USDT:USDT": {
        "id": "SOLUSDT",
        "symbol": "SOL/USDT:USDT",
        "base": "SOL",
        "quote": "USDT",
        "settle": "USDT",
        "type": "swap",
        "spot": False,
        "swap": True,
        "future": True,
        "contract": True,
        "linear": True,
        "inverse": False,
        "active": True,
        "tierBased": False,
        "percentage": True,
        "taker": 0.0004,
        "maker": 0.0002,
        "contractSize": 1,
        "limits": {
            "leverage": {"min": 1, "max": 75},
            "amount": {"min": 0.1, "max": 1000000},
            "price": {"min": 0.001, "max": 100000},
            "cost": {"min": 5, "max": None}
        },
        "precision": {"price": 0.001, "amount": 0.1}
    }
}

_EXMS = "freqtrade.exchange.exchange.Exchange"
_BINMS = "freqtrade.exchange.binance.Binance"
_SUPPORTED_MODES = [("futures", "isolated"), ("spot", ""), ("futures", "cross")]


ALL_STRATEGIES: list[tuple[str, str]] = [
    ("FundingTiltMomentumStrategy", "1h"),
    ("VolatilityCompressionBreakoutStrategy", "4h"),
    ("MomentumPulseStrategy", "4h"),
    ("DailyBreakoutTrendStrategy", "4h"),
    ("EmaAdxTrendFilterStrategy", "4h"),
    ("RegimeFilteredMeanReversionStrategy", "4h"),
    ("RsiBollingerMeanReversionStrategy", "4h"),
    ("SessionFilteredMomentumStrategy", "4h"),
    ("TimeSeriesMomentumVolatilityStrategy", "4h")
]


def run_backtest(
    strategy: str,
    timeframe: str,
    timerange: str,
    config_path: str,
    datadir: str,
    export_filename: str | None,
    freqaimodel: str | None,
) -> None:
    if export_filename is None:
        Path("user_data/backtest_results").mkdir(parents=True, exist_ok=True)
        export_filename = f"user_data/backtest_results/{strategy.lower()}_backtest.json"

    args_list = [
        "backtesting",
        "--config",
        config_path,
        "--strategy",
        strategy,
        "--timeframe",
        timeframe,
        "--datadir",
        datadir,
        "--timerange",
        timerange,
        "--export",
        "trades",
        "--export-filename",
        export_filename,
    ]

    if freqaimodel:
        args_list.extend(["--freqaimodel", freqaimodel])

    print("=" * 72)
    print(f"Backtesting {strategy} on {timeframe} ({timerange})")
    print("=" * 72)

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

        parsed_args = Arguments(args_list).get_parsed_arg()
        config = Configuration(parsed_args, RunMode.BACKTEST).get_config()
        config["dry_run"] = True
        config["fee"] = 0.0004

        bt = Backtesting(config)
        bt.start()

    print(f"Completed: {strategy} -> {export_filename}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run freqtrade backtesting with mocked exchange market loading."
    )
    parser.add_argument(
        "--strategy",
        default=None,
        help="Single strategy class name (default: run standard strategy set)",
    )
    parser.add_argument(
        "--timeframe",
        default=None,
        help="Timeframe override (default: strategy default)",
    )
    parser.add_argument(
        "--timerange",
        default="20220101-20231231",
        help="Backtest timerange in YYYYMMDD-YYYYMMDD format",
    )
    parser.add_argument(
        "--config",
        default="user_data/config.backtest.binance.futures.json",
        help="Config path to use for backtesting",
    )
    parser.add_argument(
        "--datadir",
        default="user_data/data/binance",
        help="Data directory root",
    )
    parser.add_argument(
        "--export-filename",
        default=None,
        help="Explicit export filename",
    )
    parser.add_argument(
        "--freqaimodel",
        default=None,
        help="Optional freqai prediction model name",
    )
    args = parser.parse_args()

    if args.strategy:
        strategy_map = dict(ALL_STRATEGIES)
        tf = args.timeframe or strategy_map.get(args.strategy, "1h")
        run_backtest(
            strategy=args.strategy,
            timeframe=tf,
            timerange=args.timerange,
            config_path=args.config,
            datadir=args.datadir,
            export_filename=args.export_filename,
            freqaimodel=args.freqaimodel,
        )
        return

    for strategy, default_tf in ALL_STRATEGIES:
        tf = args.timeframe or default_tf
        try:
            run_backtest(
                strategy=strategy,
                timeframe=tf,
                timerange=args.timerange,
                config_path=args.config,
                datadir=args.datadir,
                export_filename=None,
                freqaimodel=None,
            )
        except Exception as exc:
            print(f"FAILED: {strategy}: {exc}")


if __name__ == "__main__":
    main()
