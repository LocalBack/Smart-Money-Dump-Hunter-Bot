import pytest

from smartmoney_bot.orchestrator import engine
from smartmoney_bot.risk.manager import AccountState, PositionParams


class FakeRedis:
    def __init__(self) -> None:
        self.added = []
        self.acked = []
        self.values = {}

    async def xreadgroup(self, *args, **kwargs):
        return [
            [
                "market.metrics",
                [
                    [
                        "1-0",
                        {
                            "symbol": "TEST",
                            "price": "100",
                            "pdd": "-0.25",
                            "vsr": "3",
                            "ois": "0.2",
                            "frd": "-0.03",
                            "atr": "1",
                            "ll": "0.1",
                            "lva": "0",
                            "lsi": "2",
                            "lcf": "50000",
                        },
                    ]
                ],
            ]
        ]

    async def xack(self, *args):
        self.acked.append(args)

    async def set(self, *args, **kwargs):
        pass


class FakeConn:
    def __init__(self) -> None:
        self.executed = []

    async def execute(self, sql: str, *params):
        self.executed.append((sql, params))


class DummyGateway:
    def __init__(self) -> None:
        self.called = False

    async def submit(self, plan):
        self.called = True


@pytest.mark.asyncio
async def test_orchestrator_process_once(monkeypatch) -> None:
    redis = FakeRedis()
    conn = FakeConn()
    account = AccountState(equity=10000.0, start_equity=10000.0)
    params = PositionParams(risk_pct=1.0, max_dd_pct=50.0, daily_stop=1000.0)
    dummy = DummyGateway()
    monkeypatch.setattr(engine, "gateway", dummy)
    await engine.process_once(redis, conn, account, params)
    assert dummy.called
    assert conn.executed
