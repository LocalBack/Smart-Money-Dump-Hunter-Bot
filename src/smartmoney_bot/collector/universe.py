from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, cast

import aiohttp


async def fetch_top50(
    use_cache: bool = False, cache_path: Path | None = None
) -> List[str]:
    offline = use_cache or os.getenv("COLLECTOR_OFFLINE") == "1"
    if cache_path is None:
        cache_path = Path(__file__).with_name("coingecko_top50.json")
    if offline:
        with cache_path.open() as f:
            return cast(List[str], json.load(f))

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
    with cache_path.open("w") as f:
        json.dump(symbols, f)
    return symbols
