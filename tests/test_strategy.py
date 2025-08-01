# mypy: ignore-errors
from smartmoney_bot.strategy.core import generate_signal


def test_generate_signal() -> None:
    metrics = {
        "pdd": -0.25,
        "vsr": 3.5,
        "ois": 0.2,
        "frd": -0.03,
        "atr": 1.0,
        "ll": 0.1,
        "lva": 0.0,
        "lsi": 2.5,
        "lcf": 50000.0,
    }
    sig = generate_signal("TEST", 100.0, metrics)
    assert sig is not None
