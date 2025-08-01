# mypy: ignore-errors
import pytest

from smartmoney_bot.exec import gateway
from smartmoney_bot.risk.manager import OrderPlan


class FakeRedis:
    def __init__(self) -> None:
        self.args = None

    async def xadd(self, stream: str, data: dict) -> None:
        self.args = (stream, data)


@pytest.mark.asyncio
async def test_gateway_paper(monkeypatch) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(gateway, "REDIS", fake)
    monkeypatch.setattr(gateway, "MODE", "paper")
    plan = OrderPlan(
        symbol="TEST",
        qty=1.0,
        entry_price=100.0,
        sl_price=90.0,
        tp_price=120.0,
        side="buy",
    )
    await gateway.submit(plan)
    assert fake.args is not None
    assert fake.args[0] == "fills.paper"
