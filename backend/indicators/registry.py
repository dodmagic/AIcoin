"""High level helpers that compute indicator bundles and trading signals."""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from . import boll as _boll
from . import kdj as _kdj
from . import macd as _macd
from . import ma as _ma
from . import rsi as _rsi
from . import volume as _vol

# Indicators that can be requested through the API.
AVAILABLE = [
    "ma",
    "ema",
    "macd",
    "kdj",
    "rsi",
    "boll",
    "atr",
    "obv",
    "vwap",
    "volume_ratio",
]


def _clean(values: pd.Series) -> List:
    """Convert a Series to a JSON safe list (NaN/inf -> None)."""
    out = []
    for v in values:
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            out.append(None)
        else:
            out.append(round(float(v), 6))
    return out


def compute(df: pd.DataFrame, types: List[str]) -> Dict[str, Dict[str, List]]:
    """Compute the requested indicators from an OHLCV dataframe.

    `df` must contain columns: time, open, high, low, close, volume.
    Returns a mapping of indicator name -> {series_name: [...]}.
    """
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]
    result: Dict[str, Dict[str, List]] = {}

    for t in types:
        t = t.strip().lower()
        if t == "ma":
            result["ma"] = {
                "ma7": _clean(_ma.sma(close, 7)),
                "ma25": _clean(_ma.sma(close, 25)),
                "ma99": _clean(_ma.sma(close, 99)),
            }
        elif t == "ema":
            result["ema"] = {
                "ema12": _clean(_ma.ema(close, 12)),
                "ema26": _clean(_ma.ema(close, 26)),
            }
        elif t == "macd":
            m = _macd.macd(close)
            result["macd"] = {
                "macd": _clean(m["macd"]),
                "signal": _clean(m["signal"]),
                "hist": _clean(m["hist"]),
            }
        elif t == "kdj":
            k = _kdj.kdj(high, low, close)
            result["kdj"] = {
                "k": _clean(k["k"]),
                "d": _clean(k["d"]),
                "j": _clean(k["j"]),
            }
        elif t == "rsi":
            result["rsi"] = {"rsi14": _clean(_rsi.rsi(close, 14))}
        elif t == "boll":
            b = _boll.boll(close)
            result["boll"] = {
                "middle": _clean(b["middle"]),
                "upper": _clean(b["upper"]),
                "lower": _clean(b["lower"]),
            }
        elif t == "atr":
            result["atr"] = {"atr14": _clean(_boll.atr(high, low, close, 14))}
        elif t == "obv":
            result["obv"] = {"obv": _clean(_vol.obv(close, volume))}
        elif t == "vwap":
            result["vwap"] = {"vwap": _clean(_vol.vwap(high, low, close, volume))}
        elif t == "volume_ratio":
            result["volume_ratio"] = {
                "volume_ratio": _clean(_vol.volume_ratio(volume))
            }

    return result


def signals(df: pd.DataFrame) -> List[Dict]:
    """Generate trading signals from MA/MACD crossovers and RSI extremes.

    Returns a list of {time, type, reason, price} dictionaries where `type`
    is one of "buy" or "sell".
    """
    close = df["close"]
    times = df["time"]
    out: List[Dict] = []

    # --- MA golden / death cross (MA7 vs MA25) ---
    fast = _ma.sma(close, 7)
    slow = _ma.sma(close, 25)
    diff = fast - slow
    prev = diff.shift(1)
    for i in range(1, len(df)):
        if pd.isna(prev.iloc[i]) or pd.isna(diff.iloc[i]):
            continue
        if prev.iloc[i] <= 0 < diff.iloc[i]:
            out.append(_sig(times.iloc[i], "buy", "MA7 上穿 MA25 (金叉)", close.iloc[i]))
        elif prev.iloc[i] >= 0 > diff.iloc[i]:
            out.append(_sig(times.iloc[i], "sell", "MA7 下穿 MA25 (死叉)", close.iloc[i]))

    # --- MACD zero-line / signal cross ---
    m = _macd.macd(close)
    md = m["macd"] - m["signal"]
    mprev = md.shift(1)
    for i in range(1, len(df)):
        if pd.isna(mprev.iloc[i]) or pd.isna(md.iloc[i]):
            continue
        if mprev.iloc[i] <= 0 < md.iloc[i]:
            out.append(_sig(times.iloc[i], "buy", "MACD 金叉", close.iloc[i]))
        elif mprev.iloc[i] >= 0 > md.iloc[i]:
            out.append(_sig(times.iloc[i], "sell", "MACD 死叉", close.iloc[i]))

    # --- RSI overbought / oversold ---
    r = _rsi.rsi(close, 14)
    rprev = r.shift(1)
    for i in range(1, len(df)):
        if pd.isna(rprev.iloc[i]) or pd.isna(r.iloc[i]):
            continue
        if rprev.iloc[i] >= 30 > r.iloc[i]:
            out.append(_sig(times.iloc[i], "buy", "RSI 跌破 30 (超卖)", close.iloc[i]))
        elif rprev.iloc[i] <= 70 < r.iloc[i]:
            out.append(_sig(times.iloc[i], "sell", "RSI 突破 70 (超买)", close.iloc[i]))

    out.sort(key=lambda s: s["time"])
    return out


def _sig(time, kind: str, reason: str, price: float) -> Dict:
    return {
        "time": int(time),
        "type": kind,
        "reason": reason,
        "price": round(float(price), 2),
    }
