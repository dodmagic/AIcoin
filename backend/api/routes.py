"""REST API routes."""
from __future__ import annotations

from fastapi import APIRouter, Query

from .. import models
from ..backtest import evaluator
from ..data import fetcher
from ..indicators import registry
from . import schemas

router = APIRouter(prefix="/api")


@router.get("/klines", response_model=schemas.KlinesResponse)
def klines(
    days: int = Query(365, ge=1, le=2000),
    interval: str = Query("1d"),
):
    df = fetcher.get_klines(days=days, interval=interval)
    candles = [
        schemas.Candle(
            time=int(r.time),
            open=float(r.open),
            high=float(r.high),
            low=float(r.low),
            close=float(r.close),
            volume=float(r.volume),
        )
        for r in df.itertuples(index=False)
    ]
    return schemas.KlinesResponse(
        interval=interval, days=days, count=len(candles), candles=candles
    )


@router.get("/indicators", response_model=schemas.IndicatorsResponse)
def indicators(
    type: str = Query("ma,macd,rsi", description="Comma separated indicator names"),
    days: int = Query(365, ge=1, le=2000),
):
    df = fetcher.get_klines(days=days)
    requested = [t for t in (type or "").split(",") if t.strip()]
    if not requested:
        requested = registry.AVAILABLE
    data = registry.compute(df, requested)
    return schemas.IndicatorsResponse(
        days=days, times=[int(t) for t in df["time"]], indicators=data
    )


@router.get("/predict", response_model=schemas.PredictResponse)
def predict(
    model: str = Query("ensemble"),
    horizon: int = Query(180, ge=1, le=730),
    days: int = Query(365, ge=60, le=2000),
):
    df = fetcher.get_klines(days=days)
    result = models.predict(model, df, horizon)

    # Provide in-sample backtest metrics so the UI can show accuracy.
    try:
        bt = evaluator.backtest(df, result.model, min(90, len(df) // 3))
        metrics = bt["metrics"]
    except Exception:
        metrics = {}

    return schemas.PredictResponse(
        model=result.model,
        horizon_days=result.horizon_days,
        available=result.available,
        note=result.note,
        predictions=result.predictions,
        metrics=metrics,
    )


@router.get("/backtest", response_model=schemas.BacktestResponse)
def backtest(
    model: str = Query("ensemble"),
    period: int = Query(90, ge=5, le=730),
    days: int = Query(365, ge=60, le=2000),
):
    df = fetcher.get_klines(days=days)
    result = evaluator.backtest(df, model, period)
    return schemas.BacktestResponse(**result)


@router.get("/signals", response_model=schemas.SignalsResponse)
def signals(days: int = Query(365, ge=30, le=2000)):
    df = fetcher.get_klines(days=days)
    sigs = registry.signals(df)
    return schemas.SignalsResponse(days=days, count=len(sigs), signals=sigs)


@router.get("/stats", response_model=schemas.StatsResponse)
def stats(days: int = Query(365, ge=30, le=2000)):
    df = fetcher.get_klines(days=days)
    s = evaluator.statistics(df)
    return schemas.StatsResponse(days=days, stats=s)


@router.get("/models")
def list_models():
    """List forecasting models and whether their heavy backend is installed."""
    from ..models import lstm_model, prophet_model, xgboost_model

    return {
        "models": models.AVAILABLE_NAMES,
        "availability": {
            "arima": True,
            "prophet": prophet_model.available(),
            "lstm": lstm_model.available(),
            "xgboost": xgboost_model.available(),
            "ensemble": True,
        },
    }
