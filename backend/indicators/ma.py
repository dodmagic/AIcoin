"""Moving average indicators: SMA / EMA / WMA."""
from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window=period, min_periods=1).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential moving average."""
    return series.ewm(span=period, adjust=False).mean()


def wma(series: pd.Series, period: int) -> pd.Series:
    """Weighted moving average (linear weights)."""
    weights = pd.Series(range(1, period + 1), dtype="float64")

    def _wma(window: pd.Series) -> float:
        w = weights.iloc[: len(window)].to_numpy()
        return float((window.to_numpy() * w).sum() / w.sum())

    return series.rolling(window=period, min_periods=1).apply(_wma, raw=False)
