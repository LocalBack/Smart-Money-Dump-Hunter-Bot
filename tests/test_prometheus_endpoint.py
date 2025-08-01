# mypy: ignore-errors
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from smartmoney_bot import exporter


@pytest.mark.asyncio
async def test_prometheus_endpoint_returns_gauges() -> None:
    exporter.orchestrator_latency_ms.set(1.23)
    app = web.Application()
    app.router.add_get("/metrics", exporter.handle_metrics)
    server = TestServer(app)
    await server.start_server()
    client = TestClient(server)
    await client.start_server()
    resp = await client.get("/metrics")
    text = await resp.text()
    await client.close()
    assert resp.status == 200
    assert "orchestrator_latency_ms" in text
