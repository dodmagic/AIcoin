"""Data cleaning utilities for OHLCV time series."""
from __future__ import annotations

import numpy as np
import pandas as pd

OHLCV_COLUMNS = ["time", "open", "high", "low", "close", "volume"]


def clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise, deduplicate and repair an OHLCV dataframe.

    - keeps only the canonical columns
    - sorts by time, drops duplicate timestamps
    - forward/back fills missing prices, fills missing volume with 0
    - enforces high >= max(o,c) and low <= min(o,c)
    - drops non-positive prices
    """
    if df.empty:
        return df.reindex(columns=OHLCV_COLUMNS)

    df = df.copy()
    for col in OHLCV_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan
    df = df[OHLCV_COLUMNS]

    df["time"] = pd.to_numeric(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])
    df["time"] = df["time"].astype("int64")
    df = df.sort_values("time").drop_duplicates(subset="time", keep="last")

    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df[["open", "high", "low", "close"]] = (
        df[["open", "high", "low", "close"]].ffill().bfill()
    )

    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
    df["volume"] = df["volume"].clip(lower=0.0)

    # Drop rows that are still invalid (e.g. all-NaN input).
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)]

    # Enforce OHLC ordering.
    df["high"] = df[["high", "open", "close"]].max(axis=1)
    df["low"] = df[["low", "open", "close"]].min(axis=1)

    return df.reset_index(drop=True)
