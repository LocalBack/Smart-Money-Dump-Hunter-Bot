
import pytest
from fakeredis.aioredis import FakeRedis

import os
from pathlib import Path

from smartmoney_bot.collector.universe import fetch_top50
from smartmoney_bot.collector.redispub import publish, STREAM


@pytest.mark.asyncio
async def test_universe_fetch() -> None:
    os.environ["COLLECTOR_OFFLINE"] = "1"
    path = Path(__file__).parent / "fixtures" / "coingecko_top50.json"
    symbols = await fetch_top50(use_cache=True, cache_path=path)
    assert len(symbols) >= 45


@pytest.mark.asyncio
async def test_stream_insert(tmp_path: Path) -> None:
    redis = FakeRedis()
    msg = {"ts": 1, "symbol": "TEST", "feed": "ticker", "payload": {"x": 1}}
    await publish(redis, msg)
    res = await redis.xrange(STREAM, count=1)
    assert res
    await redis.close()
