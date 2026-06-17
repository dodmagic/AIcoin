"""XGBoost regression on technical-indicator features (optional dependency).

Falls back to scikit-learn's GradientBoostingRegressor, and finally to a
drift model, so the endpoint always works.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..indicators import ma as _ma
from ..indicators import macd as _macd
from ..indicators import rsi as _rsi
from .base import (
    ForecastResult,
    constant_drift,
    log_returns,
    seasonal_component,
    simulate,
)

NAME = "xgboost"

try:
    from xgboost import XGBRegressor  # type: ignore

    _HAS_XGB = True
except Exception:  # pragma: no cover - optional heavy dep
    _HAS_XGB = False

try:
    from sklearn.ensemble import GradientBoostingRegressor

    _HAS_SKLEARN = True
except Exception:  # pragma: no cover
    _HAS_SKLEARN = False


def available() -> bool:
    return _HAS_XGB or _HAS_SKLEARN


def _features(df: pd.DataFrame) -> pd.DataFrame:
    close = df["close"]
    feat = pd.DataFrame(index=df.index)
    feat["ret1"] = close.pct_change()
    feat["ret5"] = close.pct_change(5)
    feat["ma7"] = _ma.sma(close, 7) / close - 1
    feat["ma25"] = _ma.sma(close, 25) / close - 1
    feat["rsi"] = _rsi.rsi(close, 14) / 100.0
    feat["macd_hist"] = _macd.macd(close)["hist"] / close
    return feat


def predict(df: pd.DataFrame, horizon: int = 180) -> ForecastResult:
    close = df["close"].to_numpy(dtype=float)
    rets = log_returns(close)
    base_sigma = float(np.std(rets[-90:])) if len(rets) >= 5 else 0.02
    base_sigma = max(base_sigma, 1e-3)
    seasonal = seasonal_component(rets, 7)
    last_price = float(close[-1])
    last_time = int(df["time"].iloc[-1])

    model = _make_model()
    if model is None or len(df) < 60:
        mu = float(np.mean(rets[-90:])) if len(rets) else 0.0
        drift = constant_drift(mu, horizon)
        note = (
            "No gradient boosting backend; drift model used"
            if model is None
            else "Insufficient history; drift model used"
        )
        points = simulate(
            last_price, last_time, drift, base_sigma, horizon, seasonal, seed=19
        )
        return ForecastResult(NAME, horizon, points, available=available(), note=note)

    feat = _features(df)
    target = pd.Series(np.log(close)).diff().shift(-1)  # next-day log return
    data = feat.copy()
    data["target"] = target
    data = data.dropna()
    if len(data) < 30:
        mu = float(np.mean(rets[-90:])) if len(rets) else 0.0
        drift = constant_drift(mu, horizon)
        points = simulate(
            last_price, last_time, drift, base_sigma, horizon, seasonal, seed=19
        )
        return ForecastResult(NAME, horizon, points, available=available(), note="drift model")

    x = data.drop(columns=["target"]).to_numpy()
    y = data["target"].to_numpy()
    model.fit(x, y)

    last_feat = feat.iloc[[-1]].fillna(0.0).to_numpy()
    base_pred = float(model.predict(last_feat)[0])
    # Decay the single-step prediction toward the historical mean over horizon.
    long_mean = float(np.mean(rets[-180:])) if len(rets) >= 5 else 0.0
    decay = np.exp(-np.arange(horizon) / 40.0)
    drift = long_mean + (base_pred - long_mean) * decay

    note = "XGBoost" if _HAS_XGB else "GradientBoosting (sklearn)"
    points = simulate(last_price, last_time, drift, base_sigma, horizon, seasonal, seed=19)
    return ForecastResult(NAME, horizon, points, available=True, note=note)


def _make_model():
    if _HAS_XGB:
        return XGBRegressor(
            n_estimators=120, max_depth=3, learning_rate=0.05, n_jobs=1, verbosity=0
        )
    if _HAS_SKLEARN:
        return GradientBoostingRegressor(
            n_estimators=120, max_depth=3, learning_rate=0.05
        )
    return None
