
import pytest
from redis.asyncio import Redis

from smartmoney_bot.collector import fetch_universe
from smartmoney_bot.collector.redispub import publish, STREAM


@pytest.mark.asyncio
async def test_universe_fetch() -> None:
    symbols = await fetch_universe(50)
    assert len(symbols) > 40


@pytest.mark.asyncio
async def test_stream_insert(tmp_path) -> None:
    redis = Redis()
    msg = {"ts": 1, "symbol": "TEST", "feed": "ticker", "payload": {"x": 1}}
    await publish(redis, msg)
    res = await redis.xrange(STREAM, count=1)
    assert res
    await redis.close()
