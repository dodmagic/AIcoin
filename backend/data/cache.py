"""Lightweight SQLite cache for OHLCV candles."""
from __future__ import annotations

import os
import sqlite3
import time
from io import StringIO
from typing import Optional

import pandas as pd

DEFAULT_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour
DB_PATH = os.getenv("CACHE_DB_PATH", os.path.join(os.path.dirname(__file__), "cache.db"))


class Cache:
    """A tiny SQLite-backed cache for candle dataframes keyed by a string."""

    def __init__(self, db_path: str = DB_PATH, ttl: int = DEFAULT_TTL):
        self.db_path = db_path
        self.ttl = ttl
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ohlcv_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload   TEXT NOT NULL,
                    created   REAL NOT NULL
                )
                """
            )

    def get(self, key: str) -> Optional[pd.DataFrame]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload, created FROM ohlcv_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
        if not row:
            return None
        payload, created = row
        if self.ttl >= 0 and (time.time() - created) > self.ttl:
            return None
        try:
            return pd.read_json(StringIO(payload), orient="split")
        except ValueError:
            return None

    def set(self, key: str, df: pd.DataFrame) -> None:
        payload = df.to_json(orient="split")
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ohlcv_cache (cache_key, payload, created)"
                " VALUES (?, ?, ?)",
                (key, payload, time.time()),
            )

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM ohlcv_cache")
