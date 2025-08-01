from __future__ import annotations

from typing import Iterable
import os


BASE_WS_URL = os.getenv(
    "BINANCE_BASE_WS_URL", "wss://stream.binance.com:9443/stream?streams="
)
LIQUIDATION_STREAM = os.getenv(
    "BINANCE_LIQUIDATION_STREAM", "wss://fstream.binance.com/ws/!forceOrder@arr"
)
TICKER_STREAM = os.getenv(
    "BINANCE_TICKER_STREAM", "wss://stream.binance.com:9443/ws/!miniTicker@arr"
)


def kline_stream_url(symbols: Iterable[str]) -> str:
    streams = "/".join(f"{s.lower()}@kline_1m" for s in symbols)
    return BASE_WS_URL + streams
