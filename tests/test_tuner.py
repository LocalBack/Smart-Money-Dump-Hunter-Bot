# mypy: ignore-errors
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from typer.testing import CliRunner

from cli.config_cli import app


def _generate_data(symbols: list[str], data_dir: Path) -> None:
    start = datetime(2024, 3, 19)
    rows = []
    for i in range(200):
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
    df = pd.DataFrame(rows)
    for sym in symbols:
        df.to_parquet(data_dir / f"minute_2024-03-19_{sym}.parquet")


def test_tuner_runs(tmp_path, monkeypatch) -> None:
    symbols = ["AAA"]
    _generate_data(symbols, tmp_path)
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "tune",
            "2024-01-01",
            "2025-07-31",
            "--symbols",
            symbols[0],
            "--n_trials",
            "50",
            "--data-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    proposed = list((Path("config/proposed")).glob("*.yml"))
    assert proposed
