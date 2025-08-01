from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Config:
    redis_url: str = "redis://localhost:6379/0"
    buffer_size: int = 1440
    atr_period: int = 14

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            buffer_size=int(os.getenv("BUFFER_SIZE", "1440")),
            atr_period=int(os.getenv("ATR_PERIOD", "14")),
        )
