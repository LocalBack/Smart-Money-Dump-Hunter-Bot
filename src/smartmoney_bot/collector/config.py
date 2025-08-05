from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(slots=True)
class Config:
    redis_url: str = "redis://redis:6379/0"
    coin_limit: int = 2


def from_env() -> Config:
    load_dotenv()
    return Config(
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        coin_limit=int(os.getenv("COIN_LIMIT", "2")),
    )
