from __future__ import annotations

import asyncio
import os
import time

from redis import asyncio as aioredis
import asyncpg

from ..common.async_utils import wait_for_postgres
import structlog

from .telegram import send_alert

log = structlog.get_logger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/postgres")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")


async def watch_trades(conn: asyncpg.Connection) -> None:
    last_id = 0
    while True:
        rows = await conn.fetch("SELECT id, symbol, side, qty FROM trades_planned WHERE id > $1", last_id)
        for row in rows:
            await send_alert("trade_planned", f"{row['symbol']} {row['side']} {row['qty']}")
            last_id = row["id"]
        await asyncio.sleep(1)


async def watch_heartbeats(redis: aioredis.Redis) -> None:
    services = ["collector", "metric_engine", "orchestrator"]
    while True:
        now = int(time.time() * 1000)
        for svc in services:
            ts = await redis.get(f"{svc}:hb")
            if ts is None or now - int(ts) > 10000:
                await send_alert("heartbeat", f"{svc} missed heartbeat")
        await asyncio.sleep(5)


async def run() -> None:
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
    conn = await wait_for_postgres(DATABASE_URL)
    await asyncio.gather(watch_trades(conn), watch_heartbeats(redis))


if __name__ == "__main__":
    asyncio.run(run())

