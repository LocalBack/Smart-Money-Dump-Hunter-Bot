import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from smartmoney_bot.metrics.buffer import RingBuffer
from smartmoney_bot.metrics.formulas import compute_all_metrics


def test_pdd_computation() -> None:
    buf = RingBuffer(1500)
    for i in range(1485):
        buf.update(100.0, 1.0, 0.0, 0.0, 0.0)
    for _ in range(15):
        buf.update(80.0, 1.0, 0.0, 0.0, 0.0)
    view = buf.view(1500)
    metrics = compute_all_metrics(view, lookback=15)
    assert metrics["pdd"] == pytest.approx(-0.2, rel=1e-2)


def test_metric_speed(benchmark: BenchmarkFixture) -> None:
    buf = RingBuffer(1440)
    for i in range(1440):
        buf.update(float(i), 1.0, 0.0, 0.0, 0.0)
    view = buf.view(1440)

    def run() -> None:
        compute_all_metrics(view)

    benchmark(run)
    assert benchmark.stats.stats.mean < 0.05

