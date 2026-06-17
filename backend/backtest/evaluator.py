"""Backtesting and evaluation metrics."""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from .. import models

# Crypto markets trade every day, so annualisation uses 365 days.
DAYS_PER_YEAR = 365


def metrics(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """Compute MSE / MAE / RMSE / MAPE and directional accuracy."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    err = predicted - actual
    mse = float(np.mean(err**2))
    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(mse))
    nonzero = actual != 0
    mape = (
        float(np.mean(np.abs(err[nonzero] / actual[nonzero])) * 100)
        if nonzero.any()
        else 0.0
    )

    # Directional accuracy: did we predict the sign of the day-over-day move?
    if len(actual) > 1:
        actual_dir = np.sign(np.diff(actual))
        pred_dir = np.sign(np.diff(predicted))
        directional = float(np.mean(actual_dir == pred_dir))
    else:
        directional = 0.0

    return {
        "mse": round(mse, 4),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 4),
        "directional_accuracy": round(directional, 4),
    }


def backtest(df: pd.DataFrame, model: str = "ensemble", period: int = 90) -> Dict:
    """Walk-forward style backtest.

    Trains on data up to `len - period`, forecasts `period` days ahead and
    compares against the held-out actuals.
    """
    period = max(5, min(period, len(df) // 2))
    train = df.iloc[:-period].reset_index(drop=True)
    test = df.iloc[-period:].reset_index(drop=True)

    result = models.predict(model, train, period)
    predicted = np.array([p["price"] for p in result.predictions[:period]])
    actual = test["close"].to_numpy(dtype=float)[: len(predicted)]
    predicted = predicted[: len(actual)]

    m = metrics(actual, predicted)

    points = []
    for i in range(len(actual)):
        points.append(
            {
                "time": int(test["time"].iloc[i]),
                "actual": round(float(actual[i]), 2),
                "predicted": round(float(predicted[i]), 2),
            }
        )

    return {
        "model": model,
        "period": period,
        "metrics": m,
        "points": points,
        "note": result.note,
    }


def statistics(df: pd.DataFrame, risk_free: float = 0.0) -> Dict:
    """Sharpe ratio, max drawdown, win rate, annualised volatility."""
    close = df["close"].to_numpy(dtype=float)
    rets = np.diff(close) / close[:-1]
    if len(rets) == 0:
        return {
            "sharpe": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "annual_volatility": 0.0,
            "annual_return": 0.0,
        }

    daily_rf = risk_free / DAYS_PER_YEAR
    excess = rets - daily_rf
    sharpe = (
        float(np.mean(excess) / np.std(excess) * np.sqrt(DAYS_PER_YEAR))
        if np.std(excess) > 0
        else 0.0
    )

    cum = np.cumprod(1 + rets)
    peak = np.maximum.accumulate(cum)
    drawdown = (cum - peak) / peak
    max_dd = float(drawdown.min())

    win_rate = float(np.mean(rets > 0))
    annual_vol = float(np.std(rets) * np.sqrt(DAYS_PER_YEAR))
    annual_return = float((cum[-1] ** (DAYS_PER_YEAR / len(rets))) - 1) if cum[-1] > 0 else 0.0

    return {
        "sharpe": round(sharpe, 4),
        "max_drawdown": round(max_dd, 4),
        "win_rate": round(win_rate, 4),
        "annual_volatility": round(annual_vol, 4),
        "annual_return": round(annual_return, 4),
    }
