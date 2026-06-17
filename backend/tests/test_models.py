"""Tests for indicators, models, backtest and the API."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.backtest import evaluator
from backend.data import fetcher
from backend.data.cleaner import clean_ohlcv
from backend.indicators import registry
from backend.main import app
from backend import models

client = TestClient(app)


@pytest.fixture(scope="module")
def df():
    return fetcher.get_klines(days=400, allow_network=False)


def test_synthetic_data_is_clean(df):
    assert not df.empty
    assert (df["high"] >= df[["open", "close"]].max(axis=1)).all()
    assert (df["low"] <= df[["open", "close"]].min(axis=1)).all()
    assert (df["close"] > 0).all()


def test_cleaner_fixes_ordering():
    raw = pd.DataFrame(
        {
            "time": [3, 1, 2, 2],
            "open": [10, 10, 10, 10],
            "high": [9, 11, 12, 12],  # high below open on first row
            "low": [11, 9, 8, 8],
            "close": [10, 10, 11, 11],
            "volume": [None, 5, 5, 5],
        }
    )
    cleaned = clean_ohlcv(raw)
    assert list(cleaned["time"]) == [1, 2, 3]  # sorted + deduped
    assert (cleaned["high"] >= cleaned["low"]).all()
    assert cleaned["volume"].notna().all()


def test_indicators_compute_all(df):
    data = registry.compute(df, registry.AVAILABLE)
    for name in ["ma", "ema", "macd", "kdj", "rsi", "boll", "atr", "obv", "vwap"]:
        assert name in data
    # MACD histogram should contain finite values.
    hist = [h for h in data["macd"]["hist"] if h is not None]
    assert len(hist) > 0


def test_rsi_bounds(df):
    rsi_vals = registry.compute(df, ["rsi"])["rsi"]["rsi14"]
    vals = [v for v in rsi_vals if v is not None]
    assert all(0 <= v <= 100 for v in vals)


def test_signals_have_valid_types(df):
    sigs = registry.signals(df)
    assert isinstance(sigs, list)
    for s in sigs:
        assert s["type"] in ("buy", "sell")
        assert "reason" in s


@pytest.mark.parametrize("model", ["arima", "prophet", "lstm", "xgboost", "ensemble"])
def test_models_produce_wavy_predictions(df, model):
    result = models.predict(model, df, horizon=120)
    assert len(result.predictions) == 120
    prices = np.array([p["price"] for p in result.predictions])
    # Predictions must fluctuate, i.e. not a perfectly straight line.
    diffs = np.diff(prices)
    assert np.std(diffs) > 0
    # Direction should change at least once (not monotonic).
    signs = np.sign(diffs)
    signs = signs[signs != 0]
    assert len(set(signs.tolist())) > 1


def test_confidence_bands_are_ordered(df):
    result = models.predict("ensemble", df, horizon=60)
    for p in result.predictions:
        assert p["lower_95"] <= p["lower_80"] <= p["price"]
        assert p["price"] <= p["upper_80"] <= p["upper_95"]


def test_backtest_metrics(df):
    bt = evaluator.backtest(df, "ensemble", period=60)
    for key in ["mse", "mae", "rmse", "mape", "directional_accuracy"]:
        assert key in bt["metrics"]
    assert len(bt["points"]) > 0


def test_statistics(df):
    s = evaluator.statistics(df)
    for key in ["sharpe", "max_drawdown", "win_rate", "annual_volatility"]:
        assert key in s
    assert s["max_drawdown"] <= 0


# --- API endpoint tests ---------------------------------------------------


def test_api_klines():
    r = client.get("/api/klines?days=120")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] > 0
    assert len(body["candles"]) == body["count"]


def test_api_indicators():
    r = client.get("/api/indicators?type=macd,rsi,kdj&days=120")
    assert r.status_code == 200
    body = r.json()
    assert "macd" in body["indicators"]
    assert "rsi" in body["indicators"]


def test_api_predict():
    r = client.get("/api/predict?model=ensemble&horizon=90&days=200")
    assert r.status_code == 200
    body = r.json()
    assert body["horizon_days"] == 90
    assert len(body["predictions"]) == 90
    assert "mae" in body["metrics"]


def test_api_backtest():
    r = client.get("/api/backtest?model=arima&period=45&days=200")
    assert r.status_code == 200
    assert "directional_accuracy" in r.json()["metrics"]


def test_api_signals():
    r = client.get("/api/signals?days=200")
    assert r.status_code == 200
    assert "signals" in r.json()


def test_api_stats():
    r = client.get("/api/stats?days=200")
    assert r.status_code == 200
    assert "sharpe" in r.json()["stats"]


def test_api_models_listing():
    r = client.get("/api/models")
    assert r.status_code == 200
    assert "ensemble" in r.json()["models"]
