"""Shared forecasting utilities.

All forecasting models in this package express their view of the future as a
*daily log-drift* series (plus a volatility estimate). The Monte-Carlo
simulator below turns those parameters into price paths that exhibit genuine
fluctuation, seasonality and widening confidence cones - never a straight line.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

DAY_SECONDS = 86_400

# GARCH-like volatility clustering parameters (used by `simulate`).
# sigma_t mean-reverts toward the long-run level while a random shock keeps
# the path noisy so the confidence cone widens realistically.
_VOL_MEAN_REVERSION = 0.85   # weight pulling sigma back to the base level
_VOL_PERSISTENCE = 0.15      # weight kept from the previous step's sigma
_VOL_SHOCK_SCALE = 0.30      # size of the random sigma shock (x base_sigma)
_VOL_SHOCK_STD = 0.15        # std-dev of the raw shock draw
_VOL_FLOOR = 0.4             # min sigma as a multiple of base_sigma
_VOL_CEIL = 3.0              # max sigma as a multiple of base_sigma


@dataclass
class ForecastResult:
    model: str
    horizon_days: int
    predictions: List[Dict]
    metrics: Dict[str, float] = field(default_factory=dict)
    available: bool = True
    note: str = ""


def log_returns(prices: np.ndarray) -> np.ndarray:
    prices = np.asarray(prices, dtype=float)
    return np.diff(np.log(prices))


def seasonal_component(returns: np.ndarray, period: int = 7) -> np.ndarray:
    """Average return by position in a `period`-day cycle (mean-removed)."""
    if len(returns) < period * 2:
        return np.zeros(period)
    n = len(returns)
    pattern = np.zeros(period)
    counts = np.zeros(period)
    for i in range(n):
        idx = i % period
        pattern[idx] += returns[i]
        counts[idx] += 1
    pattern = np.divide(pattern, counts, out=np.zeros_like(pattern), where=counts > 0)
    return pattern - pattern.mean()


def simulate(
    last_price: float,
    last_time: int,
    drift: np.ndarray,
    base_sigma: float,
    horizon: int,
    seasonal: Optional[np.ndarray] = None,
    n_paths: int = 500,
    seed: int = 7,
) -> List[Dict]:
    """Run a Monte-Carlo simulation and return per-day prediction points.

    `drift` is an array of length `horizon` giving the expected daily log
    return. Volatility follows a simple GARCH-like clustering process so the
    cone widens realistically. Returns points with median price and the
    80%/95% confidence bounds.
    """
    rng = np.random.default_rng(seed)
    seasonal = np.zeros(7) if seasonal is None else seasonal
    period = len(seasonal) if len(seasonal) else 7

    # Volatility clustering (see module-level _VOL_* constants).
    sigma_paths = np.empty((n_paths, horizon))
    vol = np.full(n_paths, base_sigma)
    for d in range(horizon):
        shock = rng.normal(0, _VOL_SHOCK_STD, n_paths)
        vol = np.clip(
            base_sigma * _VOL_MEAN_REVERSION
            + _VOL_PERSISTENCE * vol
            + shock * base_sigma * _VOL_SHOCK_SCALE,
            base_sigma * _VOL_FLOOR,
            base_sigma * _VOL_CEIL,
        )
        sigma_paths[:, d] = vol

    z = rng.standard_normal((n_paths, horizon))
    daily = np.empty((n_paths, horizon))
    for d in range(horizon):
        seas = seasonal[d % period]
        daily[:, d] = drift[d] + seas + sigma_paths[:, d] * z[:, d]

    log_paths = np.cumsum(daily, axis=1)
    price_paths = last_price * np.exp(log_paths)

    median = np.median(price_paths, axis=0)
    lower_80 = np.percentile(price_paths, 10, axis=0)
    upper_80 = np.percentile(price_paths, 90, axis=0)
    lower_95 = np.percentile(price_paths, 2.5, axis=0)
    upper_95 = np.percentile(price_paths, 97.5, axis=0)

    points = []
    for d in range(horizon):
        ts = last_time + (d + 1) * DAY_SECONDS
        date = pd.to_datetime(ts, unit="s").strftime("%Y-%m-%d")
        points.append(
            {
                "time": int(ts),
                "date": date,
                "price": round(float(median[d]), 2),
                "lower_80": round(float(lower_80[d]), 2),
                "upper_80": round(float(upper_80[d]), 2),
                "lower_95": round(float(lower_95[d]), 2),
                "upper_95": round(float(upper_95[d]), 2),
            }
        )
    return points


def constant_drift(mu: float, horizon: int) -> np.ndarray:
    return np.full(horizon, mu)
