from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class Config:
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    BUFFER_SIZE: int = int(os.getenv("BUFFER_SIZE", "1440"))
    ATR_PERIOD: int = int(os.getenv("ATR_PERIOD", "14"))
    WRITE_PERIOD: int = int(os.getenv("PARQUET_WRITE_PERIOD", "1"))
    PARQUET_DIR: str = os.getenv("PARQUET_DIR", "parquets")
