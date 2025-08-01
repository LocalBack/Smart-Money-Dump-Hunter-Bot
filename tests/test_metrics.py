import pytest

from smartmoney_bot.metrics.buffer import RingBuffer
from smartmoney_bot.metrics.formulas import compute_all_metrics


def generate_bar(price: float) -> dict:
    return {
        "price": price,
        "volume": 1.0,
        "open_interest": 1.0,
        "funding_rate": 0.0,
        "liquidation_notional": 0.0,
    }


def test_pdd_calculation() -> None:
    buf = RingBuffer(1500)
    price = 100.0
    for _ in range(1499):
        buf.update(generate_bar(price))
    buf.update(generate_bar(price * 0.8))
    data = buf.view(1500)
    metrics = compute_all_metrics(data)
    assert metrics["pdd"] == pytest.approx(-0.2, abs=0.01)


def test_metrics_speed(benchmark) -> None:
    buf = RingBuffer(1440)
    for i in range(1440):
        buf.update(generate_bar(float(i)))
    data = buf.view(1440)
    result = benchmark(lambda: compute_all_metrics(data))
    assert result
    assert benchmark.stats.stats.mean < 0.05
