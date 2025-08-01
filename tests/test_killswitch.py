# mypy: ignore-errors
import pytest
from fakeredis.aioredis import FakeRedis

from smartmoney_bot.orchestrator import engine
from smartmoney_bot.risk.killswitch import KillSwitch, KILLSWITCH_KEY
from smartmoney_bot.risk.manager import AccountState, PositionParams


class DummyGateway:
    def __init__(self) -> None:
        self.called = False

    async def submit(self, plan):
        self.called = True


class FakeConn:
    def __init__(self) -> None:
        self.executed = []

    async def execute(self, sql: str, *params):
        self.executed.append((sql, params))


@pytest.mark.asyncio
async def test_killswitch_blocks_trades(monkeypatch) -> None:
    redis = FakeRedis()
    conn = FakeConn()
    account = AccountState(equity=8000.0, start_equity=10000.0)
    params = PositionParams(risk_pct=1.0, max_dd_pct=20.0, daily_stop=1000.0)
    ks = KillSwitch(redis, daily_loss_cap=0.05, max_dd_pct=20.0)

    dummy = DummyGateway()
    monkeypatch.setattr(engine, "gateway", dummy)

    await ks.monitor(account)
    await engine.process_once(redis, conn, account, params)

    assert await redis.get(KILLSWITCH_KEY) in ("1", b"1")
    assert not dummy.called
