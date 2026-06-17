"""ARIMA / SARIMA forecasting via statsmodels (with graceful fallback)."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from .base import (
    ForecastResult,
    constant_drift,
    log_returns,
    seasonal_component,
    simulate,
)

NAME = "arima"

try:
    from statsmodels.tsa.arima.model import ARIMA as _ARIMA

    _HAS_STATSMODELS = True
except Exception:  # pragma: no cover
    _HAS_STATSMODELS = False


def predict(df: pd.DataFrame, horizon: int = 180) -> ForecastResult:
    close = df["close"].to_numpy(dtype=float)
    rets = log_returns(close)
    base_sigma = float(np.std(rets[-90:])) if len(rets) >= 5 else 0.02
    base_sigma = max(base_sigma, 1e-3)
    seasonal = seasonal_component(rets, 7)
    last_price = float(close[-1])
    last_time = int(df["time"].iloc[-1])

    mu = float(np.mean(rets[-90:])) if len(rets) else 0.0
    drift = constant_drift(mu, horizon)
    note = "ARIMA unavailable (statsmodels missing); using drift model"

    if _HAS_STATSMODELS and len(rets) >= 30:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = _ARIMA(rets, order=(2, 0, 2))
                fit = model.fit()
                fc = np.asarray(fit.forecast(steps=horizon), dtype=float)
            drift = fc
            note = "ARIMA(2,0,2) on log-returns"
        except Exception:
            note = "ARIMA fit failed; using drift model"

    points = simulate(last_price, last_time, drift, base_sigma, horizon, seasonal, seed=11)
    return ForecastResult(NAME, horizon, points, available=True, note=note)
