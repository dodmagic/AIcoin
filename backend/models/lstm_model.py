"""PyTorch LSTM forecasting (optional dependency).

When torch is unavailable the model degrades to an EMA-momentum drift estimate
so the API stays functional.
"""
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

NAME = "lstm"

try:
    import torch  # type: ignore
    import torch.nn as nn  # type: ignore

    _HAS_TORCH = True
except Exception:  # pragma: no cover - optional heavy dep
    _HAS_TORCH = False


def available() -> bool:
    return _HAS_TORCH


def _momentum_drift(rets: np.ndarray, horizon: int) -> np.ndarray:
    """Fallback: EMA of recent returns, decaying toward the long-run mean."""
    if len(rets) == 0:
        return np.zeros(horizon)
    ema = pd.Series(rets).ewm(span=10, adjust=False).mean().iloc[-1]
    long_mean = float(np.mean(rets[-180:])) if len(rets) >= 5 else float(np.mean(rets))
    decay = np.exp(-np.arange(horizon) / 45.0)
    return long_mean + (float(ema) - long_mean) * decay


def predict(df: pd.DataFrame, horizon: int = 180) -> ForecastResult:
    close = df["close"].to_numpy(dtype=float)
    rets = log_returns(close)
    base_sigma = float(np.std(rets[-90:])) if len(rets) >= 5 else 0.02
    base_sigma = max(base_sigma, 1e-3)
    seasonal = seasonal_component(rets, 7)
    last_price = float(close[-1])
    last_time = int(df["time"].iloc[-1])

    if not _HAS_TORCH or len(rets) < 60:
        drift = _momentum_drift(rets, horizon)
        note = (
            "PyTorch not installed; approximated with momentum model"
            if not _HAS_TORCH
            else "Insufficient history for LSTM; momentum model used"
        )
        points = simulate(
            last_price, last_time, drift, base_sigma, horizon, seasonal, seed=17
        )
        return ForecastResult(NAME, horizon, points, available=_HAS_TORCH, note=note)

    drift = _train_and_forecast(rets, horizon)
    points = simulate(last_price, last_time, drift, base_sigma, horizon, seasonal, seed=17)
    return ForecastResult(NAME, horizon, points, available=True, note="LSTM (PyTorch)")


def _train_and_forecast(rets: np.ndarray, horizon: int) -> np.ndarray:  # pragma: no cover
    """Train a small LSTM on log-returns and roll the forecast forward."""
    torch.manual_seed(0)
    seq_len = 20
    x = rets.astype(np.float32)
    # Normalise.
    mean, std = float(x.mean()), float(x.std() or 1e-6)
    xn = (x - mean) / std

    samples = []
    targets = []
    for i in range(len(xn) - seq_len):
        samples.append(xn[i : i + seq_len])
        targets.append(xn[i + seq_len])
    if not samples:
        return constant_drift(mean, horizon)

    xt = torch.tensor(np.array(samples)).unsqueeze(-1)
    yt = torch.tensor(np.array(targets)).unsqueeze(-1)

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.lstm = nn.LSTM(1, 16, batch_first=True)
            self.fc = nn.Linear(16, 1)

        def forward(self, x):
            out, _ = self.lstm(x)
            return self.fc(out[:, -1, :])

    net = Net()
    opt = torch.optim.Adam(net.parameters(), lr=0.01)
    loss_fn = nn.MSELoss()
    for _ in range(60):
        opt.zero_grad()
        pred = net(xt)
        loss = loss_fn(pred, yt)
        loss.backward()
        opt.step()

    window = list(xn[-seq_len:])
    preds = []
    net.eval()
    with torch.no_grad():
        for _ in range(horizon):
            inp = torch.tensor(np.array(window[-seq_len:], dtype=np.float32)).reshape(1, seq_len, 1)
            nxt = float(net(inp).item())
            preds.append(nxt * std + mean)
            window.append(nxt)
    return np.array(preds)
