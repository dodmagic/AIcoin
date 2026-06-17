"""FastAPI application entry point.

Run locally with:
    uvicorn backend.main:app --reload --port 8000
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

app = FastAPI(
    title="AIcoin Quant Backend",
    description="比特币量化分析与价格预测 API (ARIMA / Prophet / LSTM / XGBoost / Ensemble)",
    version="1.0.0",
)

# CORS so the GitHub Pages frontend can call the backend.
_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()] or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "AIcoin Quant Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "/api/klines",
            "/api/indicators",
            "/api/predict",
            "/api/backtest",
            "/api/signals",
            "/api/stats",
            "/api/models",
        ],
        "disclaimer": "仅供学习研究，不构成投资建议。",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
