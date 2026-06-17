"""Fetch Bitcoin OHLCV data from CoinGecko / Binance with caching + fallback."""
from __future__ import annotations

import os
from typing import Optional

import numpy as np
import pandas as pd

try:  # requests is a declared dependency but guard anyway for test envs.
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore

from .cache import Cache
from .cleaner import clean_ohlcv

COINGECKO_BASE = os.getenv("COINGECKO_BASE", "https://api.coingecko.com/api/v3")
DAY_SECONDS = 86_400
_cache = Cache()


def get_klines(
    days: int = 365,
    interval: str = "1d",
    use_cache: bool = True,
    allow_network: bool = True,
) -> pd.DataFrame:
    """Return a cleaned OHLCV dataframe for Bitcoin.

    Tries the cache first, then CoinGecko, and finally falls back to a
    deterministic synthetic series so the API is always usable offline.
    """
    key = f"btc:{days}:{interval}"
    if use_cache:
        cached = _cache.get(key)
        if cached is not None and not cached.empty:
            return cached

    if os.getenv("AICOIN_DISABLE_NETWORK", "").lower() in ("1", "true", "yes"):
        allow_network = False

    df: Optional[pd.DataFrame] = None
    if allow_network and requests is not None:
        try:
            df = _fetch_coingecko(days)
        except Exception:
            df = None

    if df is None or df.empty:
        df = _synthetic(days)

    df = clean_ohlcv(df)
    if use_cache and not df.empty:
        _cache.set(key, df)
    return df


def _fetch_coingecko(days: int) -> pd.DataFrame:
    """Fetch OHLC + volume from CoinGecko and merge into one dataframe."""
    ohlc_url = f"{COINGECKO_BASE}/coins/bitcoin/ohlc"
    chart_url = f"{COINGECKO_BASE}/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": str(days)}

    ohlc_res = requests.get(ohlc_url, params=params, timeout=15)
    ohlc_res.raise_for_status()
    ohlc = ohlc_res.json()

    chart_res = requests.get(chart_url, params=params, timeout=15)
    chart_res.raise_for_status()
    volumes = chart_res.json().get("total_volumes", [])

    rows = []
    for item in ohlc:
        ts, o, h, l, c = item
        rows.append(
            {
                "time": int(ts) // 1000,
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": np.nan,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    if volumes:
        vol_df = pd.DataFrame(volumes, columns=["time", "volume"])
        vol_df["time"] = (vol_df["time"] // 1000).astype("int64")
        # Map each candle to the closest available volume sample by day.
        vol_df["day"] = vol_df["time"] // DAY_SECONDS
        df["day"] = df["time"] // DAY_SECONDS
        vol_map = vol_df.groupby("day")["volume"].mean()
        df["volume"] = df["day"].map(vol_map)
        df = df.drop(columns=["day"])

    return df


def _synthetic(days: int, seed: int = 42) -> pd.DataFrame:
    """Deterministic synthetic OHLCV series with trend + seasonality + noise."""
    rng = np.random.default_rng(seed)
    n = max(int(days), 30)
    now = int(pd.Timestamp.now(tz="UTC").timestamp())
    start = now - n * DAY_SECONDS

    t = np.arange(n)
    trend = 0.0008 * t  # gentle upward drift in log space
    seasonal = 0.05 * np.sin(2 * np.pi * t / 90)  # ~quarterly cycle
    shocks = rng.normal(0, 0.02, n)
    log_price = np.log(45000) + trend + seasonal + np.cumsum(shocks)
    close = np.exp(log_price)

    rows = []
    prev = close[0]
    for i in range(n):
        c = close[i]
        o = prev
        high = max(o, c) * (1 + abs(rng.normal(0, 0.01)))
        low = min(o, c) * (1 - abs(rng.normal(0, 0.01)))
        vol = float(rng.uniform(1e10, 6e10))
        rows.append(
            {
                "time": start + i * DAY_SECONDS,
                "open": float(o),
                "high": float(high),
                "low": float(low),
                "close": float(c),
                "volume": vol,
            }
        )
        prev = c
    return pd.DataFrame(rows)
