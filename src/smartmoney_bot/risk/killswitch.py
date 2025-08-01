from __future__ import annotations

# mypy: ignore-errors

import os
import structlog
from redis import asyncio as aioredis

from ..alert.telegram import send_alert
from .manager import AccountState

log = structlog.get_logger(__name__)

KILLSWITCH_KEY = "killswitch:on"


class KillSwitch:
    def __init__(
        self, redis: aioredis.Redis, daily_loss_cap: float, max_dd_pct: float
    ) -> None:
        self.redis = redis
        self.daily_loss_cap = daily_loss_cap
        self.max_dd_pct = max_dd_pct

    async def monitor(self, state: AccountState) -> None:
        if await self.redis.get(KILLSWITCH_KEY) in {"1", b"1"}:
            return

        lag = int(await self.redis.get("redis:lag_ms") or 0)
        if lag > 500:
            await self._trigger("redis_lag")
            return

        if state.daily_pnl <= -self.daily_loss_cap * state.start_equity:
            await self._trigger("daily_loss_cap")
            return

        drop_pct = (state.start_equity - state.equity) / state.start_equity * 100
        if drop_pct >= self.max_dd_pct:
            await self._trigger("drawdown_limit")

    async def _trigger(self, reason: str) -> None:
        await self.redis.set(KILLSWITCH_KEY, "1")
        log.error("killswitch_activated", reason=reason)
        await send_alert("KILL-SWITCH ACTIVATED", f"reason={reason}")

    async def is_halted(self) -> bool:
        return await self.redis.get(KILLSWITCH_KEY) in {"1", b"1"}


async def unhalt(redis: aioredis.Redis, passphrase: str) -> None:
    expected = os.getenv("UNHALT_PASSPHRASE", "")
    if passphrase != expected:
        raise ValueError("bad_passphrase")
    await redis.delete(KILLSWITCH_KEY)
    log.info("killswitch_unhalted")
