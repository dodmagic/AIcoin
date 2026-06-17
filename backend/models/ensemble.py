"""Ensemble model: weighted fusion of the individual forecasters."""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from . import arima_model, lstm_model, prophet_model, xgboost_model
from .base import ForecastResult

NAME = "ensemble"

# Relative weights for fusion; available models are renormalised at runtime.
WEIGHTS = {
    "arima": 1.0,
    "prophet": 1.0,
    "lstm": 1.0,
    "xgboost": 1.0,
}


def predict(df: pd.DataFrame, horizon: int = 180) -> ForecastResult:
    members = {
        "arima": arima_model.predict(df, horizon),
        "prophet": prophet_model.predict(df, horizon),
        "lstm": lstm_model.predict(df, horizon),
        "xgboost": xgboost_model.predict(df, horizon),
    }

    keys = ["price", "lower_80", "upper_80", "lower_95", "upper_95"]
    weights = np.array([WEIGHTS[m] for m in members])
    weights = weights / weights.sum()

    n = horizon
    fused: List[Dict] = []
    template = members["arima"].predictions
    for d in range(n):
        point = {"time": template[d]["time"], "date": template[d]["date"]}
        for key in keys:
            vals = np.array([members[m].predictions[d][key] for m in members])
            point[key] = round(float(np.dot(weights, vals)), 2)
        fused.append(point)

    used = [m for m, r in members.items() if r.available]
    note = "Weighted ensemble of: " + (", ".join(used) if used else "approximations")
    return ForecastResult(NAME, horizon, fused, available=True, note=note)
