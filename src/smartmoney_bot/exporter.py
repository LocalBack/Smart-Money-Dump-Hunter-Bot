from __future__ import annotations

from aiohttp import web
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest

orders_sent_total = Counter("orders_sent_total", "Total orders sent")
orders_filled_total = Counter("orders_filled_total", "Total orders filled")
orchestrator_latency_ms = Gauge(
    "orchestrator_latency_ms", "Latency of orchestrator loop in ms"
)


async def handle_metrics(request: web.Request) -> web.StreamResponse:
    data = generate_latest()
    return web.Response(body=data, headers={"Content-Type": CONTENT_TYPE_LATEST})


def run_exporter(port: int = 8000) -> None:
    app = web.Application()
    app.router.add_get("/metrics", handle_metrics)
    web.run_app(app, port=port)
