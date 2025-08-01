from __future__ import annotations

import asyncio
import os
import random
from dataclasses import asdict
from typing import Any, cast

from redis import asyncio as aioredis
import ccxt.async_support as ccxt_async
import structlog

from ..common.config import settings
from ..risk.manager import OrderPlan

log = structlog.get_logger(__name__)

REDIS: aioredis.Redis = cast(
    aioredis.Redis,
    aioredis.from_url(
        settings.collector.redis_url, decode_responses=True
    ),  # type: ignore[no-untyped-call]
)

BINANCE_KEY = os.getenv("BINANCE_KEY", "")
BINANCE_SECRET = os.getenv("BINANCE_SECRET", "")
MODE = os.getenv("MODE", "paper")
MAX_SLIPPAGE_BPS = float(os.getenv("MAX_SLIPPAGE_BPS", "5"))


async def _live_client() -> Any:
    return ccxt_async.binance(
        {
            "apiKey": BINANCE_KEY,
            "secret": BINANCE_SECRET,
            "enableRateLimit": True,
        }
    )


async def submit(plan: OrderPlan) -> None:
    """Submit an order plan in paper or live mode."""
    stream = "fills.paper" if MODE == "paper" else "fills.live"
    attempts = 0
    client = None
    if MODE == "live":
        client = await _live_client()
    try:
        while attempts < 3:
            try:
                if MODE == "live" and client is not None:
                    await client.create_order(
                        plan.symbol,
                        "limit",
                        plan.side,
                        plan.qty,
                        plan.entry_price,
                        {"postOnly": True},
                    )
                    await asyncio.sleep(30)
                    open_orders = await client.fetch_open_orders(plan.symbol)
                    if open_orders:
                        slip = plan.entry_price * MAX_SLIPPAGE_BPS / 10000
                        await client.create_order(
                            plan.symbol,
                            "limit",
                            plan.side,
                            plan.qty,
                            plan.entry_price + slip,
                        )
                else:
                    await REDIS.xadd(
                        stream, {k: str(v) for k, v in asdict(plan).items()}
                    )
                break
            except Exception as exc:  # pragma: no cover - network issues
                attempts += 1
                if attempts >= 3:
                    log.error("gateway_submit_failed", error=str(exc))
                    raise
                await asyncio.sleep(random.uniform(0.5, 1.5))
    finally:
        if client:
            await client.close()
