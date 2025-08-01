from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict

import structlog
from redis.asyncio import Redis

from .buffer import RingBuffer
from .config import Config
from .formulas import compute_all_metrics

logger = structlog.get_logger(__name__)

RAW_STREAM = "market.raw"
METRIC_STREAM = "market.metrics"
GROUP = "metricscg"
CONSUMER = "worker"
HEARTBEAT_KEY = "metric_engine:hb"


def _ensure_group(redis: Redis) -> None:
    async def inner() -> None:
        try:
            await redis.xgroup_create(RAW_STREAM, GROUP, mkstream=True)
        except Exception:
            pass
    asyncio.get_event_loop().run_until_complete(inner())


async def engine(cfg: Config, stop: asyncio.Event) -> None:
    redis = Redis.from_url(cfg.redis_url)
    try:
        await redis.xgroup_create(RAW_STREAM, GROUP, mkstream=True)
    except Exception:
        pass
    buffers: dict[str, RingBuffer] = defaultdict(lambda: RingBuffer(cfg.buffer_size))
    last_minute: dict[str, int] = defaultdict(int)
    while not stop.is_set():
        res = await redis.xreadgroup(
            GROUP,
            CONSUMER,
            streams={RAW_STREAM: ">"},
            count=100,
            block=1000,
        )
        if not res:
            continue
        for _stream, msgs in res:
            for _id, fields in msgs:
                raw = json.loads(fields["data"])
                symbol = raw["symbol"]
                feed = raw["feed"]
                ts = raw["ts"]
                if feed != "kline":
                    continue
                k = raw["payload"]["k"]
                price = float(k["c"])
                vol = float(k["v"])
                buffers[symbol].update(price, vol, 0.0, 0.0, 0.0)
                minute = ts // 60000
                if minute != last_minute[symbol]:
                    data = compute_all_metrics(buffers[symbol].view(cfg.buffer_size))
                    out = {"ts": ts, "symbol": symbol, "metrics": data}
                    await redis.xadd(
                        METRIC_STREAM,
                        {"data": json.dumps(out)},
                        maxlen=100000,
                        approximate=True,
                    )
                    latency = int(time.time() * 1000) - ts
                    if latency > 400:
                        logger.info("latency", ms=latency)
                    last_minute[symbol] = minute
        await redis.set(HEARTBEAT_KEY, int(time.time()), ex=5)
    await redis.close()


def run() -> None:
    cfg = Config.from_env()
    stop = asyncio.Event()
    asyncio.run(engine(cfg, stop))


if __name__ == "__main__":
    run()
