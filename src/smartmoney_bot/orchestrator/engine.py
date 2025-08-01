from __future__ import annotations

# mypy: ignore-errors

import os
import time
from typing import cast

from redis import asyncio as aioredis
import asyncpg
import structlog

from ..common.config import settings
from ..exec import gateway
from ..metrics.formulas import Metrics
from ..risk.manager import AccountState, PositionParams, vet_and_size
from ..risk.killswitch import KILLSWITCH_KEY, KillSwitch
from ..strategy.core import generate_signal
from ..exporter import orders_sent_total, orchestrator_latency_ms

log = structlog.get_logger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
)


async def process_once(
    redis: aioredis.Redis,
    conn: asyncpg.Connection,
    account: AccountState,
    params: PositionParams,
) -> None:
    start = time.perf_counter()
    if await redis.get(KILLSWITCH_KEY) in {"1", b"1"}:
        log.warning("killswitch_block")
        await redis.set("orchestrator:hb", "1", ex=5)
        return
    msgs = await redis.xreadgroup(
        "orchcg", "bot", {"market.metrics": ">"}, count=1, block=1000
    )
    if msgs:
        for _, entries in msgs:
            for entry_id, data in entries:
                symbol = data.get("symbol", "")
                price = float(data.get("price", 0.0))
                metrics = cast(
                    Metrics,
                    {
                        k: float(v)
                        for k, v in data.items()
                        if k not in {"symbol", "price"}
                    },
                )
                sig = generate_signal(symbol, price, metrics)
                if sig:
                    plan = vet_and_size(sig, account, params)
                    if plan:
                        await gateway.submit(plan)
                        orders_sent_total.inc()
                        await conn.execute(
                            "INSERT INTO trades_planned(symbol, side, qty, entry_price, sl_price, tp_price) VALUES($1,$2,$3,$4,$5,$6)",
                            plan.symbol,
                            plan.side,
                            plan.qty,
                            plan.entry_price,
                            plan.sl_price,
                            plan.tp_price,
                        )
            await redis.xack("market.metrics", "orchcg", entry_id)
    orchestrator_latency_ms.set((time.perf_counter() - start) * 1000)
    await redis.set("orchestrator:hb", "1", ex=5)


async def run_orchestrator() -> None:
    redis: aioredis.Redis = cast(
        aioredis.Redis,
        aioredis.from_url(
            settings.collector.redis_url, decode_responses=True
        ),  # type: ignore[no-untyped-call]
    )
    try:
        await redis.xgroup_create("market.metrics", "orchcg", id="$", mkstream=True)
    except Exception:  # pragma: no cover - group may exist
        pass
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trades_planned (
            id SERIAL PRIMARY KEY,
            ts TIMESTAMPTZ DEFAULT now(),
            symbol TEXT,
            side TEXT,
            qty DOUBLE PRECISION,
            entry_price DOUBLE PRECISION,
            sl_price DOUBLE PRECISION,
            tp_price DOUBLE PRECISION
        )
        """
    )
    account = AccountState(equity=10_000.0, start_equity=10_000.0)
    params = PositionParams(risk_pct=1.0, max_dd_pct=50.0, daily_stop=1_000.0)
    ks = KillSwitch(
        redis, float(os.getenv("DAILY_LOSS_CAP", "0.05")), params.max_dd_pct
    )
    while True:
        await process_once(redis, conn, account, params)
        await ks.monitor(account)
