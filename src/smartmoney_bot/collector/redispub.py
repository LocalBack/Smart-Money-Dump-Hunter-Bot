from __future__ import annotations

import json
from typing import Any, Dict

from redis.asyncio import Redis

STREAM = "market.raw"
MAXLEN = 100000


async def publish(
    redis: Redis, message: Dict[str, Any], *, maxlen: int = MAXLEN
) -> None:
    await redis.xadd(
        STREAM, {"data": json.dumps(message)}, maxlen=maxlen, approximate=True
    )
