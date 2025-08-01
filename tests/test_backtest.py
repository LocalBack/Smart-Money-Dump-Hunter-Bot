# mypy: ignore-errors
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from smartmoney_bot.backtest.sim import run_backtest
from smartmoney_bot.risk.manager import PositionParams


def test_backtest_runs(tmp_path: Path) -> None:
    start = datetime(2024, 3, 19)
    rows = []
    for i in range(181):
        ts = start + timedelta(minutes=i)
        rows.append(
            {
                "timestamp": ts,
                "open": 100.0,
                "high": 100.1,
                "low": 99.9,
                "close": 100.0,
                "volume": 1.0,
                "open_interest": 1.0,
                "funding_rate": 0.0,
                "liquidation_notional": 1.0,
            }
        )
    ts = start + timedelta(minutes=181)
    rows.append(
        {
            "timestamp": ts,
            "open": 80.0,
            "high": 80.0,
            "low": 79.0,
            "close": 80.0,
            "volume": 100.0,
            "open_interest": 100.0,
            "funding_rate": -0.03,
            "liquidation_notional": 0.0,
        }
    )
    ts = start + timedelta(minutes=182)
    rows.append(
        {
            "timestamp": ts,
            "open": 80.0,
            "high": 85.0,
            "low": 79.0,
            "close": 84.0,
            "volume": 100.0,
            "open_interest": 100.0,
            "funding_rate": -0.03,
            "liquidation_notional": 0.0,
        }
    )
    for i in range(183, 200):
        ts = start + timedelta(minutes=i)
        rows.append(
            {
                "timestamp": ts,
                "open": 80.0,
                "high": 80.1,
                "low": 79.9,
                "close": 80.0,
                "volume": 1.0,
                "open_interest": 1.0,
                "funding_rate": 0.0,
                "liquidation_notional": 1.0,
            }
        )
    df = pd.DataFrame(rows)
    data_path = tmp_path / "minute_2024-03-19_SOL.parquet"
    df.to_parquet(data_path)
    data_dir = tmp_path
    trades, stats = run_backtest(
        ["SOL"],
        data_dir,
        PositionParams(risk_pct=1.0, max_dd_pct=50.0, daily_stop=1000.0),
    )
    assert len(trades) >= 1
    assert isinstance(stats.win_rate, float)
