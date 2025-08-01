# mypy: ignore-errors
from pathlib import Path

import yaml
from typer.testing import CliRunner

from cli.config_cli import app


def test_config_cycle(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(app, ["config", "view"])
    assert "collector" in result.stdout

    result = runner.invoke(app, ["config", "set", "collector.coin_limit", "25"])
    assert result.exit_code == 0

    diff = runner.invoke(app, ["config", "diff"])
    assert "coin_limit" in diff.stdout

    runner.invoke(app, ["config", "apply"])
    cfg = yaml.safe_load(Path("config/live.yml").read_text())
    assert cfg["collector"]["coin_limit"] == 25
