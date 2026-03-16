#!/usr/bin/env python3
"""
AI strategy backtesting launcher (isolated from ordinary backtesting workflow).

This script only targets the FreqAI config/strategy path and does not modify
or call the ordinary backtesting config.

Examples:
  python user_data/scripts/backtest_ai.py
  python user_data/scripts/backtest_ai.py --timerange 20220101-20231231
  python user_data/scripts/backtest_ai.py --freqaimodel LightGBMRegressor
  python user_data/scripts/backtest_ai.py --export user_data/backtest_results/freqai_run.json
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG = "user_data/config.freqai.backtest.json"
DEFAULT_STRATEGY = "FreqAIRetailStrategy"
DEFAULT_MODEL = "LightGBMRegressor"
DEFAULT_TIMERANGE = "20220101-20231231"
DEFAULT_DATADIR = "user_data/data/binance"
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"


def resolve_python_executable() -> str:
    # Prefer project venv interpreter when available to avoid global env drift.
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def required_modules_for_model(freqaimodel: str) -> list[str]:
    required = ["rapidjson", "datasieve", "sklearn"]
    lower = freqaimodel.lower()
    if "lightgbm" in lower:
        required.append("lightgbm")
    if "xgboost" in lower:
        required.append("xgboost")
    return required


def preflight_check(python_exec: str, modules: list[str]) -> int:
    script = "\n".join(
        [
            "import importlib.util, sys",
            f"mods = {modules!r}",
            "missing = [m for m in mods if importlib.util.find_spec(m) is None]",
            "if missing:",
            "    print('Missing Python modules:', ', '.join(missing))",
            "    sys.exit(2)",
            "print('Preflight OK')",
        ]
    )
    result = subprocess.run([python_exec, "-c", script], cwd=REPO_ROOT)
    return result.returncode


def run_ai_backtest(
    python_exec: str,
    config: str,
    strategy: str,
    freqaimodel: str,
    timerange: str,
    datadir: str,
    timeframe: str | None,
    export: str | None,
) -> int:
    cmd: list[str] = [
        python_exec,
        "-m",
        "freqtrade",
        "backtesting",
        "--config",
        config,
        "--strategy",
        strategy,
        "--freqaimodel",
        freqaimodel,
        "--timerange",
        timerange,
        "--datadir",
        datadir,
        "--export",
        "trades",
    ]

    if timeframe:
        cmd.extend(["--timeframe", timeframe])

    if export:
        cmd.extend(["--export-filename", export])

    print("AI backtesting command:")
    print(" ".join(cmd))
    print()

    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run isolated FreqAI backtesting without touching ordinary workflow config."
    )
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="AI config path")
    parser.add_argument("--strategy", default=DEFAULT_STRATEGY, help="AI strategy class")
    parser.add_argument("--freqaimodel", default=DEFAULT_MODEL, help="FreqAI prediction model")
    parser.add_argument("--timerange", default=DEFAULT_TIMERANGE, help="Backtest timerange")
    parser.add_argument("--datadir", default=DEFAULT_DATADIR, help="Data directory")
    parser.add_argument("--timeframe", default=None, help="Optional timeframe override")
    parser.add_argument("--export", default=None, help="Optional export filename")
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip dependency preflight checks",
    )
    args = parser.parse_args()

    os.chdir(REPO_ROOT)
    python_exec = resolve_python_executable()

    if not args.skip_preflight:
        modules = required_modules_for_model(args.freqaimodel)
        preflight_code = preflight_check(python_exec, modules)
        if preflight_code != 0:
            print("\nInstall missing dependencies in the selected environment:")
            print(f"  {python_exec} -m pip install -r requirements-freqai.txt")
            raise SystemExit(preflight_code)

    code = run_ai_backtest(
        python_exec=python_exec,
        config=args.config,
        strategy=args.strategy,
        freqaimodel=args.freqaimodel,
        timerange=args.timerange,
        datadir=args.datadir,
        timeframe=args.timeframe,
        export=args.export,
    )

    raise SystemExit(code)


if __name__ == "__main__":
    main()
