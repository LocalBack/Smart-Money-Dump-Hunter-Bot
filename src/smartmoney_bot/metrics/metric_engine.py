from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from typing import Any, cast

import structlog
from redis.asyncio import Redis
from ..common.async_utils import wait_for_redis

from .buffer import RingBuffer
from .config import Config
from .formulas import compute_all_metrics

logger = structlog.get_logger(__name__)
RAW_STREAM = "market.raw"
METRIC_STREAM = "market.metrics"
GROUP = "metricscg"


async def engine_task() -> None:
    cfg = Config()
    redis = await wait_for_redis(cfg.REDIS_URL)
    try:
        await redis.xgroup_create(RAW_STREAM, GROUP, mkstream=True, id="$")
    except Exception:
        pass

    buffers: dict[str, RingBuffer] = defaultdict(lambda: RingBuffer(cfg.BUFFER_SIZE))
    last_minute: dict[str, int] = {}
    consumer = "engine"

    while True:
        res = await redis.xreadgroup(
            GROUP,
            consumer,
            streams={RAW_STREAM: ">"},
            count=1,
            block=1000,
        )
        now_ms = int(time.time() * 1000)
        await redis.set("metric_engine:hb", now_ms, ex=5)
        if not res:
            continue

        start = time.time()
        for _, msgs in res:
            for _id, fields in msgs:
                raw = fields.get("data")
                if raw is None:
                    raw = fields.get(b"data")
                if raw is None:
                    logger.warning("data field missing", fields=fields)
                    await redis.xack(RAW_STREAM, GROUP, _id)
                    continue
                data = cast(dict[str, Any], json.loads(raw))
                if data["feed"] != "kline":
                    continue
                k = data["payload"]["k"]
                if not k.get("x"):
                    continue
                symbol = data["symbol"]
                ts = int(k["t"])
                frame = {
                    "price": float(k["c"]),
                    "volume": float(k["v"]),
                    "open_interest": float(k.get("oi", 0.0)),
                    "funding_rate": float(k.get("fr", 0.0)),
                    "liquidation_notional": float(k.get("l", 0.0)),
                }
                buf = buffers[symbol]
                buf.update(frame)
                minute = ts // 60000
                if last_minute.get(symbol) == minute:
                    continue
                last_minute[symbol] = minute
                view = buf.view(cfg.BUFFER_SIZE if buf.full else buf.idx)
                metrics = compute_all_metrics(view)
                message = {
                    "ts": ts,
                    "symbol": symbol,
                    "metrics": metrics,
                }
                await redis.xadd(
                    METRIC_STREAM,
                    {"data": json.dumps(message)},
                    maxlen=100000,
                    approximate=True,
                )
        latency = (time.time() - start) * 1000
        if latency > 400:
            logger.info("latency", ms=latency)


def run() -> None:
    asyncio.run(engine_task())


if __name__ == "__main__":
    run()
