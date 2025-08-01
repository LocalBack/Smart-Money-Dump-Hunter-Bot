from __future__ import annotations

# mypy: ignore-errors

import json
from typing import Any, Dict

from redis.asyncio import Redis

STREAM = "market.raw"
MAXLEN = 100000


async def publish(redis: Redis, message: Dict[str, Any]) -> None:
    await redis.xadd(
        STREAM, {"data": json.dumps(message)}, maxlen=MAXLEN, approximate=True
    )
