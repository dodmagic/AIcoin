"""Bollinger Bands and ATR (volatility indicators)."""
from __future__ import annotations

import pandas as pd

from .ma import sma


def boll(close: pd.Series, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """Bollinger Bands: middle (SMA), upper and lower bands."""
    mid = sma(close, period)
    std = close.rolling(window=period, min_periods=1).std(ddof=0)
    upper = mid + num_std * std
    lower = mid - num_std * std
    return pd.DataFrame({"middle": mid, "upper": upper, "lower": lower})


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=1).mean()
