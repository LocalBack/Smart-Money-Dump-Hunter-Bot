# mypy: ignore-errors
import pytest

from smartmoney_bot.alert.telegram import send_alert


@pytest.mark.asyncio
async def test_alert_logs(caplog) -> None:
    caplog.set_level("INFO")
    await send_alert("test", "hello")
    logs = [r.message for r in caplog.records]
    assert any("hello" in m for m in logs)
