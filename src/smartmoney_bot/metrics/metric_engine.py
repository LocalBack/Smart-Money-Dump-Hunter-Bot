from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog

from ..common.async_utils import wait_for_redis
from .buffer import RingBuffer
from .config import Config
from .formulas import compute_all_metrics

logger = structlog.get_logger(__name__)
RAW_STREAM = "market.raw"
METRIC_STREAM = "market.metrics"
GROUP = "metricscg"


def write_metrics_row(message: dict[str, Any], cfg: Config) -> None:
    """Append metric row to a daily symbol parquet file."""

    date_str = datetime.utcfromtimestamp(message["ts"] / 1000).strftime("%Y%m%d")
    root = Path(cfg.PARQUET_DIR)
    root.mkdir(parents=True, exist_ok=True)
    file_path = root / f"minute_{date_str}_{message['symbol']}.parquet"

    df = pd.DataFrame([message])
    table = pa.Table.from_pandas(df, preserve_index=False)
    if file_path.exists():
        existing = pq.read_table(file_path)
        table = pa.concat_tables([existing, table])
    pq.write_table(table, file_path)


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
                message: dict[str, Any] = {
                    "ts": ts,
                    "symbol": symbol,
                    "price": frame["price"],
                    **metrics,
                }
                await redis.xadd(
                    METRIC_STREAM,
                    message,
                    maxlen=100000,
                    approximate=True,
                )
                if minute % cfg.WRITE_PERIOD == 0:
                    write_metrics_row(message, cfg)
        latency = (time.time() - start) * 1000
        if latency > 400:
            logger.info("latency", ms=latency)


def run() -> None:
    asyncio.run(engine_task())


if __name__ == "__main__":
    run()
