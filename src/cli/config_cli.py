from __future__ import annotations

import difflib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
import yaml

from smartmoney_bot.common.config import Settings

app = typer.Typer(help="SmartMoney Bot CLI")
config_app = typer.Typer()
app.add_typer(config_app, name="config")

try:
    from tuner.engine import tune

    app.command()(tune)
except Exception:  # pragma: no cover - optional
    pass

CONFIG_DIR = Path("config")
LIVE_FILE = CONFIG_DIR / "live.yml"
STAGING_FILE = CONFIG_DIR / "staging.yml"
HISTORY_DIR = CONFIG_DIR / "history"


def _ensure_live() -> None:
    if not LIVE_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        settings = Settings()
        data = {
            "collector": {
                "redis_url": settings.collector.redis_url,
                "coin_limit": settings.collector.coin_limit,
            },
            "metrics": {
                "redis_url": settings.metrics.redis_url,
                "buffer_size": settings.metrics.buffer_size,
                "atr_period": settings.metrics.atr_period,
            },
            "strategy": {"cost_threshold": settings.strategy.cost_threshold},
            "risk": {
                "fee_bps": settings.risk.fee_bps,
                "exchange_min_qty": settings.risk.exchange_min_qty,
            },
        }
        LIVE_FILE.write_text(yaml.safe_dump(data))


def _load(path: Path) -> dict[str, Any]:
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data))


def _set_in(data: dict[str, Any], keys: list[str], value: Any) -> None:
    cur = data
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    cur[keys[-1]] = value


@config_app.command("view")
def view() -> None:
    """Show current configuration (staging if exists)."""
    _ensure_live()
    target = STAGING_FILE if STAGING_FILE.exists() else LIVE_FILE
    typer.echo(target.read_text())


@config_app.command("set")
def set_value(key: str, value: str) -> None:
    """Stage a configuration value."""
    _ensure_live()
    data = _load(LIVE_FILE)
    if STAGING_FILE.exists():
        data = _load(STAGING_FILE)
    try:
        parsed = yaml.safe_load(value)
    except Exception:
        parsed = value
    _set_in(data, key.split("."), parsed)
    try:
        Settings(**data)  # validate if pydantic available
    except Exception:
        pass
    _save(STAGING_FILE, data)


@config_app.command("diff")
def diff() -> None:
    """Show staged diff versus live configuration."""
    _ensure_live()
    if not STAGING_FILE.exists():
        typer.echo("No staged changes")
        raise typer.Exit()
    live = LIVE_FILE.read_text().splitlines()
    staged = STAGING_FILE.read_text().splitlines()
    res = "\n".join(
        difflib.unified_diff(live, staged, fromfile="live", tofile="staging")
    )
    typer.echo(res)


@config_app.command("apply")
def apply() -> None:
    """Apply staged configuration to live file and version previous."""
    _ensure_live()
    if not STAGING_FILE.exists():
        typer.echo("Nothing to apply")
        raise typer.Exit()
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    if LIVE_FILE.exists():
        shutil.copy(LIVE_FILE, HISTORY_DIR / f"live_{ts}.yml")
    shutil.move(STAGING_FILE, LIVE_FILE)
    typer.echo("Applied configuration")
