#!/usr/bin/env python3
"""
Binance Futures Data Downloader / Synthetic Data Generator
===========================================================
Attempts to download real OHLCV data from Binance's public data repository
(https://data.binance.vision) via HTTPS, with no API key required.

If the network is unavailable (e.g. sandbox / firewall), falls back to
generating realistic synthetic OHLCV data calibrated to 2022-2023 actual
BTC / ETH / SOL price anchors (bear market, FTX collapse, 2023 recovery).

Output (feather format, freqtrade-compatible):
  user_data/data/binance/futures/
    BTC_USDT_USDT-1h-futures.feather
    BTC_USDT_USDT-4h-futures.feather
    BTC_USDT_USDT-1d-futures.feather
    BTC_USDT_USDT-1h-funding_rate.feather
    BTC_USDT_USDT-1h-mark.feather
    (same for ETH and SOL)

Usage:
  python user_data/scripts/generate_synthetic_data.py
  python user_data/scripts/generate_synthetic_data.py --no-download  # skip Binance attempt
  python user_data/scripts/generate_synthetic_data.py --start 20210101 --end 20231231
"""
from __future__ import annotations

import argparse
import io
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple
import sys

import numpy as np
import pandas as pd

# Try to import requests / urllib3 (optional: only needed for real download)
try:
    import requests  # type: ignore
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── output directory ──────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "user_data" / "data" / "binance" / "futures"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── column order expected by freqtrade feather handler ────────────────────────
OHLCV_COLS = ["date", "open", "high", "low", "close", "volume"]

# ── Binance USDT-M public data root ──────────────────────────────────────────
BINANCE_DATA_ROOT = "https://data.binance.vision/data/futures/um/monthly/klines"


class AssetSpec(NamedTuple):
    symbol: str          # freqtrade pair symbol, e.g. "BTC/USDT:USDT"
    binance_sym: str     # Binance REST symbol, e.g. "BTCUSDT"
    stem: str            # feather filename stem, e.g. "BTC_USDT_USDT"
    # Key (date, price) anchors for synthetic fallback
    anchors: list[tuple[str, float]]
    vol_annual: float    # approximate annualised volatility


ASSETS = [
    AssetSpec(
        symbol="BTC/USDT:USDT",
        binance_sym="BTCUSDT",
        stem="BTC_USDT_USDT",
        anchors=[
            ("2021-01-01", 29_300),
            ("2021-11-10", 68_000),  # ATH
            ("2022-01-01", 46_200),
            ("2022-06-15", 20_500),  # LUNA crash
            ("2022-11-11", 15_700),  # FTX collapse
            ("2022-12-31", 16_600),
            ("2023-04-01", 28_500),
            ("2023-12-31", 42_000),
        ],
        vol_annual=0.72,
    ),
    AssetSpec(
        symbol="ETH/USDT:USDT",
        binance_sym="ETHUSDT",
        stem="ETH_USDT_USDT",
        anchors=[
            ("2021-01-01",  730),
            ("2021-11-10", 4_800),  # ATH
            ("2022-01-01", 3_680),
            ("2022-06-15", 1_100),
            ("2022-11-11", 1_100),
            ("2022-12-31", 1_200),
            ("2023-04-01", 1_900),
            ("2023-12-31", 2_280),
        ],
        vol_annual=0.88,
    ),
    AssetSpec(
        symbol="SOL/USDT:USDT",
        binance_sym="SOLUSDT",
        stem="SOL_USDT_USDT",
        anchors=[
            ("2021-01-01",   1.8),
            ("2021-11-06", 259.0),  # ATH
            ("2022-01-01", 168.0),
            ("2022-06-15",  32.0),
            ("2022-11-11",  13.0),  # FTX collapse (FTX held large SOL)
            ("2022-12-31",  10.0),
            ("2023-04-01",  20.0),
            ("2023-12-31", 102.0),
        ],
        vol_annual=1.20,
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# Real Binance download
# ─────────────────────────────────────────────────────────────────────────────

def _download_binance_klines(
    binance_sym: str,
    interval: str,
    year: int,
    month: int,
    timeout: int = 15,
) -> pd.DataFrame | None:
    """Download one month of klines from data.binance.vision; returns None on failure."""
    if not HAS_REQUESTS:
        return None
    url = (
        f"{BINANCE_DATA_ROOT}/{binance_sym}/{interval}/"
        f"{binance_sym}-{interval}-{year}-{month:02d}.zip"
    )
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        return None

    try:
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        csv_name = zf.namelist()[0]
        df = pd.read_csv(
            zf.open(csv_name),
            header=None,
            usecols=[0, 1, 2, 3, 4, 5],
            names=["date", "open", "high", "low", "close", "volume"],
        )
        df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df[OHLCV_COLS].reset_index(drop=True)
    except Exception:
        return None


def download_real_data(spec: AssetSpec, start: str, end: str) -> dict[str, pd.DataFrame] | None:
    """
    Attempt to download all timeframes for one asset from Binance public API.
    Returns a dict keyed by interval string, or None if download unavailable.
    """
    start_dt = pd.Timestamp(start, tz="UTC")
    end_dt = pd.Timestamp(end, tz="UTC")

    frames: dict[str, list[pd.DataFrame]] = {"1h": [], "4h": [], "1d": []}
    any_success = False

    cur = start_dt
    while cur <= end_dt:
        for interval in ("1h", "4h", "1d"):
            chunk = _download_binance_klines(
                spec.binance_sym, interval, cur.year, cur.month
            )
            if chunk is not None:
                chunk = chunk[
                    (chunk["date"] >= start_dt) & (chunk["date"] <= end_dt)
                ]
                frames[interval].append(chunk)
                any_success = True
        # advance month
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1, day=1)
        else:
            cur = cur.replace(month=cur.month + 1, day=1)

    if not any_success:
        return None

    result = {}
    for interval, parts in frames.items():
        if parts:
            result[interval] = (
                pd.concat(parts)
                .drop_duplicates("date")
                .sort_values("date")
                .reset_index(drop=True)
            )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Synthetic fallback
# ─────────────────────────────────────────────────────────────────────────────

def _make_hourly_price_path(spec: AssetSpec, start: str, end: str) -> np.ndarray:
    """Interpolate anchor prices + GBM noise to produce a 1-hour close series."""
    rng = np.random.default_rng(abs(hash(spec.stem)) % (2**32))

    dates_1h = pd.date_range(start=pd.Timestamp(start, tz="UTC"),
                             end=pd.Timestamp(end, tz="UTC"),
                             freq="1h")
    n = len(dates_1h)

    anchor_series = pd.Series(
        {pd.Timestamp(d, tz="UTC"): np.log(float(p)) for d, p in spec.anchors}
    ).sort_index()
    baseline = anchor_series.reindex(dates_1h).interpolate(method="time")
    # fill any remaining NaN edges
    baseline = baseline.ffill().bfill()

    dt = 1 / 8760  # 1 h in years
    sigma_h = spec.vol_annual * np.sqrt(dt)
    noise_scale = 0.35  # 35% random walk vs 65% trend following
    cumulative_noise = noise_scale * np.cumsum(rng.normal(0.0, sigma_h, n))

    log_prices = baseline.values + cumulative_noise
    return np.exp(log_prices)


def _ohlcv_from_closes(closes: np.ndarray, dates: pd.DatetimeIndex,
                       base_vol_usd: float, rng: np.random.Generator,
                       sigma_h: float) -> pd.DataFrame:
    """Build a realistic OHLCV DataFrame from a close price array."""
    n = len(closes)
    spread = rng.exponential(sigma_h * 0.5, n) * closes
    highs = closes + spread
    lows = closes - spread * rng.uniform(0.3, 0.7, n)
    opens = closes * np.exp(rng.normal(0, sigma_h * 0.3, n))

    highs = np.maximum(highs, np.maximum(opens, closes))
    lows = np.minimum(lows, np.minimum(opens, closes))
    lows = np.maximum(lows, closes * 0.001)  # floor

    avg_price = closes.mean()
    vol_per_bar = base_vol_usd / closes / avg_price
    volume = vol_per_bar * rng.lognormal(0, 0.5, n)

    return pd.DataFrame(
        {"date": dates, "open": opens, "high": highs,
         "low": lows, "close": closes, "volume": volume}
    ).reset_index(drop=True)


def generate_synthetic_data(spec: AssetSpec, start: str, end: str) -> dict[str, pd.DataFrame]:
    """Generate synthetic OHLCV for 1h / 4h / 1d from price anchors."""
    rng = np.random.default_rng(abs(hash(spec.stem)) % (2**32))
    sigma_h = spec.vol_annual * np.sqrt(1 / 8760)

    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")

    closes_1h = _make_hourly_price_path(spec, start, end)
    dates_1h = pd.date_range(start=start_ts, end=end_ts, freq="1h")[:len(closes_1h)]

    base_vol = {"BTC": 25e9, "ETH": 12e9, "SOL": 2e9}[spec.stem.split("_")[0]]
    df1h = _ohlcv_from_closes(closes_1h[:len(dates_1h)], dates_1h, base_vol, rng, sigma_h)

    # Resample to 4h and 1d via pandas
    df1h_indexed = df1h.set_index("date")
    df4h = df1h_indexed.resample("4h").agg(
        {"open": "first", "high": "max", "low": "min",
         "close": "last", "volume": "sum"}
    ).dropna().reset_index()
    df1d = df1h_indexed.resample("1d").agg(
        {"open": "first", "high": "max", "low": "min",
         "close": "last", "volume": "sum"}
    ).dropna().reset_index()

    return {"1h": df1h, "4h": df4h, "1d": df1d}


# ─────────────────────────────────────────────────────────────────────────────
# Funding-rate & mark-price helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_funding_rate(df1h: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Synthetic funding rate: small random values every hour."""
    rng = np.random.default_rng(seed)
    n = len(df1h)
    rate = rng.normal(0.0001, 0.00015, n).clip(-0.001, 0.001)
    return pd.DataFrame({
        "date": df1h["date"],
        "open": rate, "high": rate, "low": rate, "close": rate,
        "volume": np.zeros(n),
    }).reset_index(drop=True)


def make_mark_price(df1h: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Mark price: OHLCV ≈ spot with tiny basis noise."""
    rng = np.random.default_rng(seed + 1)
    noise = rng.normal(0, 0.001, len(df1h))
    df = df1h.copy()
    df["open"] = df["open"] * (1 + noise)
    df["high"] = df["high"] * (1 + np.abs(noise))
    df["low"] = df["low"] * (1 - np.abs(noise))
    df["close"] = df["close"] * (1 + noise)
    return df.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def process_asset(
    spec: AssetSpec,
    start: str,
    end: str,
    no_download: bool,
) -> None:
    print(f"\n── {spec.symbol} ─────────────────────────────────────────────")

    frames: dict[str, pd.DataFrame] | None = None

    if not no_download:
        print("  Attempting Binance public data download …", end=" ", flush=True)
        frames = download_real_data(spec, start, end)
        if frames:
            print("✓ Downloaded real data")
        else:
            print("✗ Unavailable (network blocked or timeout)")

    if frames is None:
        print("  Generating realistic synthetic data …", end=" ", flush=True)
        frames = generate_synthetic_data(spec, start, end)
        print("✓")

    seed = abs(hash(spec.stem)) % (2**32)

    for interval, df in frames.items():
        out_path = DATA_DIR / f"{spec.stem}-{interval}-futures.feather"
        df[OHLCV_COLS].to_feather(out_path)
        cl = df["close"]
        print(f"  {interval}: {len(df):>5} rows  "
              f"${cl.min():>10.2f} – ${cl.max():>10.2f}  "
              f"(start ${cl.iloc[0]:>10.2f}, end ${cl.iloc[-1]:>10.2f})")

    # Auxiliary futures data (only 1h needed)
    df1h = frames["1h"]
    fr_path = DATA_DIR / f"{spec.stem}-1h-funding_rate.feather"
    make_funding_rate(df1h, seed)[OHLCV_COLS].to_feather(fr_path)
    mk_path = DATA_DIR / f"{spec.stem}-1h-mark.feather"
    make_mark_price(df1h, seed)[OHLCV_COLS].to_feather(mk_path)
    print(f"  funding_rate + mark price saved")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download real Binance OHLCV data or generate realistic synthetic "
            "data for backtesting.  Outputs feather files compatible with freqtrade."
        )
    )
    parser.add_argument(
        "--start", default="20220101",
        help="Start date YYYYMMDD (default: 20220101)"
    )
    parser.add_argument(
        "--end", default="20231231",
        help="End date YYYYMMDD (default: 20231231)"
    )
    parser.add_argument(
        "--no-download", action="store_true",
        help="Skip Binance download attempt; go straight to synthetic generation"
    )
    args = parser.parse_args()

    start = f"{args.start[:4]}-{args.start[4:6]}-{args.start[6:]}"
    end = f"{args.end[:4]}-{args.end[4:6]}-{args.end[6:]}"

    print(f"Output directory : {DATA_DIR}")
    print(f"Date range       : {start} → {end}")
    print(f"Download attempt : {'disabled' if args.no_download else 'enabled'}")

    for spec in ASSETS:
        process_asset(spec, start, end, no_download=args.no_download)

    print(f"\n✓ Done.  Files written to {DATA_DIR}")
    print(
        "\nNext step – run backtests:\n"
        "  python user_data/scripts/backtest_offline.py\n"
    )


if __name__ == "__main__":
    main()
