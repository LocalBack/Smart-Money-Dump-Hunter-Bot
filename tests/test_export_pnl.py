# mypy: ignore-errors
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import asyncpg
import pandas as pd
import pytest

from ops.export_pnl import export_pnl


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(pytestconfig.rootdir, "docker-compose.staging.yml")


docker_available = shutil.which("docker") is not None


@pytest.mark.skipif(not docker_available, reason="docker not available")
@pytest.mark.asyncio
async def test_export_pnl(tmp_path: Path, docker_ip, docker_services, monkeypatch):
    pg_port = docker_services.port_for("postgres", 5432)
    docker_services.wait_until_responsive(
        check=lambda: docker_services.port_for("postgres", 5432),
        timeout=60.0,
        pause=5.0,
    )
    dsn = f"postgresql://postgres:postgres@{docker_ip}:{pg_port}/postgres"
    monkeypatch.setenv("DATABASE_URL", dsn)
    conn = await asyncpg.connect(dsn)
    await conn.execute(
        "CREATE TABLE IF NOT EXISTS trades_planned (ts TIMESTAMPTZ, symbol TEXT, side TEXT, qty DOUBLE PRECISION, entry_price DOUBLE PRECISION, sl_price DOUBLE PRECISION, tp_price DOUBLE PRECISION)"
    )
    ts = datetime.utcnow()
    await conn.execute(
        "INSERT INTO trades_planned(ts, symbol, side, qty, entry_price, sl_price, tp_price) VALUES($1,$2,$3,$4,$5,$6,$7)",
        ts,
        "BTCUSDT",
        "buy",
        1.0,
        100.0,
        90.0,
        110.0,
    )
    out = tmp_path / "pnl.csv"
    await export_pnl(ts - timedelta(minutes=1), ts + timedelta(minutes=1), str(out))
    df = pd.read_csv(out)
    assert not df.empty
    await conn.close()
