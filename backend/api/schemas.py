"""Pydantic response models for the API."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class Candle(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class KlinesResponse(BaseModel):
    symbol: str = "BTCUSD"
    interval: str
    days: int
    count: int
    candles: List[Candle]


class IndicatorsResponse(BaseModel):
    days: int
    times: List[int]
    indicators: Dict[str, Dict[str, List[Optional[float]]]]


class PredictionPoint(BaseModel):
    time: int
    date: str
    price: float
    lower_80: float
    upper_80: float
    lower_95: float
    upper_95: float


class PredictResponse(BaseModel):
    model: str
    horizon_days: int
    available: bool
    note: str
    predictions: List[PredictionPoint]
    metrics: Dict[str, float]


class BacktestPoint(BaseModel):
    time: int
    actual: float
    predicted: float


class BacktestResponse(BaseModel):
    model: str
    period: int
    metrics: Dict[str, float]
    points: List[BacktestPoint]
    note: str


class Signal(BaseModel):
    time: int
    type: str
    reason: str
    price: float


class SignalsResponse(BaseModel):
    days: int
    count: int
    signals: List[Signal]


class StatsResponse(BaseModel):
    days: int
    stats: Dict[str, float]
