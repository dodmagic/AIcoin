"""MACD - Moving Average Convergence Divergence."""
from __future__ import annotations

import pandas as pd

from .ma import ema


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Return MACD line (DIF), signal line (DEA) and histogram.

    histogram = 2 * (dif - dea), matching the common MACD bar convention.
    """
    dif = ema(close, fast) - ema(close, slow)
    dea = ema(dif, signal)
    hist = (dif - dea) * 2
    return pd.DataFrame({"macd": dif, "signal": dea, "hist": hist})
