"""Volume based indicators: OBV, VWAP and volume ratio."""
from __future__ import annotations

import numpy as np
import pandas as pd


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume."""
    direction = np.sign(close.diff().fillna(0.0))
    return (direction * volume).cumsum()


def vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """Volume Weighted Average Price (cumulative)."""
    typical = (high + low + close) / 3
    cum_vol = volume.cumsum().replace(0, pd.NA)
    return (typical * volume).cumsum() / cum_vol


def volume_ratio(volume: pd.Series, period: int = 5) -> pd.Series:
    """Volume ratio: current volume vs average of the previous `period` bars."""
    avg = volume.rolling(window=period, min_periods=1).mean()
    return volume / avg.replace(0, pd.NA)
