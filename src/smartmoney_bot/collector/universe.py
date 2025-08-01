from __future__ import annotations

import json
import os
from pathlib import Path
from typing import cast

import aiohttp


async def fetch_top50(
    use_cache: bool = False,
    cache_path: Path | None = None,
) -> list[str]:
    """Fetch top 50 symbols from CoinGecko or load from cache."""
    if use_cache or os.getenv("COLLECTOR_OFFLINE"):
        if not cache_path:
            raise ValueError("cache_path required when using cache")
        with cache_path.open("r") as f:
            return cast(list[str], json.load(f))

    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": "50",
        "page": "1",
        "sparkline": "false",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
    symbols = [item["symbol"].upper() + "USDT" for item in data]
    if cache_path:
        cache_path.write_text(json.dumps(symbols, indent=2))
    return symbols
