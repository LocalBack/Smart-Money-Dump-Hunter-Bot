import asyncio
from typing import Any

import asyncpg
from redis import asyncio as aioredis
import structlog

log = structlog.get_logger(__name__)


async def wait_for_postgres(url: str, retries: int = 30, delay: float = 1.0) -> asyncpg.Connection:
    """Wait for Postgres to become available and return a connection."""
    for attempt in range(1, retries + 1):
        try:
            conn = await asyncpg.connect(url)
            return conn
        except Exception as exc:  # pragma: no cover - best effort connect
            log.info("postgres not ready", attempt=attempt, err=str(exc))
            await asyncio.sleep(delay)
    raise RuntimeError("Cannot connect to Postgres")


async def wait_for_redis(url: str, retries: int = 30, delay: float = 1.0) -> aioredis.Redis:
    """Wait for Redis to become available and return a client."""
    for attempt in range(1, retries + 1):
        try:
            redis = aioredis.from_url(url, decode_responses=True)
            await redis.ping()
            return redis
        except Exception as exc:  # pragma: no cover - best effort connect
            log.info("redis not ready", attempt=attempt, err=str(exc))
            await asyncio.sleep(delay)
    raise RuntimeError("Cannot connect to Redis")
