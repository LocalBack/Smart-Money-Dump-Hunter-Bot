# mypy: ignore-errors
from dotenv import dotenv_values


def test_env_live_example() -> None:
    data = dotenv_values("env/.env.live.example")
    assert data.get("MODE") == "live"
    assert float(data.get("MAX_LEVERAGE", "0")) <= 2
