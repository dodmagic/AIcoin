"""Model registry and dispatch."""
from __future__ import annotations

import pandas as pd

from . import arima_model, ensemble, lstm_model, prophet_model, xgboost_model
from .base import ForecastResult

MODELS = {
    "arima": arima_model.predict,
    "prophet": prophet_model.predict,
    "lstm": lstm_model.predict,
    "xgboost": xgboost_model.predict,
    "ensemble": ensemble.predict,
}

AVAILABLE_NAMES = list(MODELS.keys())


def predict(name: str, df: pd.DataFrame, horizon: int = 180) -> ForecastResult:
    name = (name or "ensemble").strip().lower()
    if name not in MODELS:
        name = "ensemble"
    return MODELS[name](df, horizon)
