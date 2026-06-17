"""KDJ stochastic oscillator."""
from __future__ import annotations

import pandas as pd


def kdj(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 9,
    k_smooth: int = 3,
    d_smooth: int = 3,
) -> pd.DataFrame:
    """Return K, D and J lines.

    RSV = (close - lowest_low) / (highest_high - lowest_low) * 100
    K = EMA(RSV), D = EMA(K), J = 3K - 2D
    """
    lowest = low.rolling(window=period, min_periods=1).min()
    highest = high.rolling(window=period, min_periods=1).max()
    denom = (highest - lowest).replace(0, pd.NA)
    rsv = ((close - lowest) / denom * 100).fillna(50.0)

    k = rsv.ewm(alpha=1 / k_smooth, adjust=False).mean()
    d = k.ewm(alpha=1 / d_smooth, adjust=False).mean()
    j = 3 * k - 2 * d
    return pd.DataFrame({"k": k, "d": d, "j": j})
