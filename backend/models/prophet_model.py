"""Facebook Prophet forecasting (optional dependency)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import (
    ForecastResult,
    constant_drift,
    log_returns,
    seasonal_component,
    simulate,
)

NAME = "prophet"

try:
    from prophet import Prophet  # type: ignore

    _HAS_PROPHET = True
except Exception:  # pragma: no cover - optional heavy dep
    _HAS_PROPHET = False


def available() -> bool:
    return _HAS_PROPHET


def predict(df: pd.DataFrame, horizon: int = 180) -> ForecastResult:
    close = df["close"].to_numpy(dtype=float)
    rets = log_returns(close)
    base_sigma = float(np.std(rets[-90:])) if len(rets) >= 5 else 0.02
    base_sigma = max(base_sigma, 1e-3)
    seasonal = seasonal_component(rets, 7)
    last_price = float(close[-1])
    last_time = int(df["time"].iloc[-1])

    if not _HAS_PROPHET:
        mu = float(np.mean(rets[-90:])) if len(rets) else 0.0
        drift = constant_drift(mu, horizon)
        points = simulate(
            last_price, last_time, drift, base_sigma, horizon, seasonal, seed=13
        )
        return ForecastResult(
            NAME,
            horizon,
            points,
            available=False,
            note="Prophet not installed; approximated with drift model",
        )

    ts = pd.to_datetime(df["time"], unit="s")
    pdf = pd.DataFrame({"ds": ts, "y": close})
    m = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
    m.fit(pdf)
    future = m.make_future_dataframe(periods=horizon, freq="D")
    forecast = m.predict(future).tail(horizon)
    yhat = forecast["yhat"].to_numpy(dtype=float)

    # Convert the Prophet level forecast into a daily drift series.
    levels = np.concatenate([[last_price], yhat])
    drift = np.diff(np.log(np.clip(levels, 1e-6, None)))
    points = simulate(last_price, last_time, drift, base_sigma, horizon, seasonal, seed=13)
    return ForecastResult(NAME, horizon, points, available=True, note="Prophet")
