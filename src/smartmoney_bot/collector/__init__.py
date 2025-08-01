from __future__ import annotations

import asyncio
import json
from typing import List, TypedDict

import aiohttp
import structlog
from redis.asyncio import Redis

from .binance_ws import LIQUIDATION_STREAM, TICKER_STREAM, kline_stream_url
from .config import Config
from .redispub import publish
from .universe import fetch_top50

logger = structlog.get_logger(__name__)


class Message(TypedDict):
    ts: int
    symbol: str
    feed: str
    payload: dict


class Collector:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.stop_event = asyncio.Event()
        self.redis: Redis | None = None

    async def _ticker_ws(self, redis: Redis) -> None:
        async for msg in self._ws_iter(TICKER_STREAM):
            ts = int(float(msg["E"]))
            symbol = msg["s"]
            await publish(
                redis,
                dict(Message(ts=ts, symbol=symbol, feed="ticker", payload=msg)),
            )

    async def _kline_ws(self, redis: Redis, symbols: List[str]) -> None:
        url = kline_stream_url(symbols)
        async for msg in self._ws_iter(url, key="data"):
            k = msg["k"]
            ts = int(k["t"])
            symbol = k["s"]
            await publish(
                redis,
                dict(Message(ts=ts, symbol=symbol, feed="kline", payload=msg)),
            )

    async def _liquidation_ws(self, redis: Redis) -> None:
        async for msg in self._ws_iter(LIQUIDATION_STREAM):
            o = msg["o"]
            ts = int(o["T"])
            symbol = o["s"]
            await publish(
                redis,
                dict(Message(ts=ts, symbol=symbol, feed="liquidation", payload=msg)),
            )

    async def _ws_iter(self, url: str, key: str | None = None):
        backoff = 1
        while not self.stop_event.is_set():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(url) as ws:
                        backoff = 1
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                yield data[key] if key else data
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                break
            except Exception as e:  # pragma: no cover - network issues
                logger.warning("ws error", url=url, err=str(e))
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)

    async def run(self) -> None:
        self.redis = Redis.from_url(self.cfg.redis_url)
        symbols = await fetch_top50()
        logger.info("universe", count=len(symbols))
        tasks = [
            self._ticker_ws(self.redis),
            self._kline_ws(self.redis, symbols),
            self._liquidation_ws(self.redis),
        ]
        await asyncio.gather(*[asyncio.create_task(t) for t in tasks])

    async def stop(self) -> None:
        self.stop_event.set()
        if self.redis:
            await self.redis.close()


def run() -> None:
    cfg = Config()
    collector = Collector(cfg)
    asyncio.run(collector.run())


def stop() -> None:
    pass
