from __future__ import annotations
# mypy: ignore-errors

import shutil
from datetime import datetime
from pathlib import Path
from typing import Iterable, cast

import optuna
import typer
import yaml
from optuna import samplers
from optuna.samplers import BaseSampler

from smartmoney_bot.backtest.sim import run_backtest
from smartmoney_bot.risk.manager import PositionParams
from optuna.trial import FrozenTrial


class SobolTPESampler(BaseSampler):
    """Use random sampling for startup then TPE."""

    def __init__(self, switch_trial: int = 10) -> None:
        self.sobol: samplers.RandomSampler = samplers.RandomSampler()
        self.tpe: samplers.TPESampler = samplers.TPESampler()
        self.switch = switch_trial

    def reseed_rng(self) -> None:
        self.sobol.reseed_rng()
        self.tpe.reseed_rng()

    def infer_relative_search_space(
        self, study: optuna.Study, trial: FrozenTrial
    ) -> dict[str, optuna.distributions.BaseDistribution]:
        if trial.number < self.switch:
            return self.sobol.infer_relative_search_space(study, trial)
        return self.tpe.infer_relative_search_space(study, trial)

    def sample_relative(
        self,
        study: optuna.Study,
        trial: FrozenTrial,
        search_space: dict[str, optuna.distributions.BaseDistribution],
    ) -> dict[str, float | int | bool | str]:
        if trial.number < self.switch:
            return self.sobol.sample_relative(study, trial, search_space)
        return self.tpe.sample_relative(study, trial, search_space)

    def sample_independent(
        self,
        study: optuna.Study,
        trial: FrozenTrial,
        param_name: str,
        param_distribution: optuna.distributions.BaseDistribution,
    ) -> float | int | bool | str:
        if trial.number < self.switch:
            return cast(
                float | int | bool | str,
                self.sobol.sample_independent(
                    study, trial, param_name, param_distribution
                ),
            )
        return cast(
            float | int | bool | str,
            self.tpe.sample_independent(study, trial, param_name, param_distribution),
        )


def _objective(
    trial: optuna.Trial,
    symbols: Iterable[str],
    data_dir: Path,
) -> float:
    risk_pct = trial.suggest_float("risk_pct", 0.5, 5.0)
    max_dd = trial.suggest_float("max_dd_pct", 10.0, 80.0)
    daily_stop = trial.suggest_float("daily_stop", 100.0, 5000.0)
    params = PositionParams(risk_pct=risk_pct, max_dd_pct=max_dd, daily_stop=daily_stop)
    _, stats = run_backtest(symbols, data_dir, params)
    score = 0.6 * stats.profit_factor + 0.2 * stats.tail_ratio - 0.2 * stats.max_dd
    return score


def _save_report(study: optuna.Study, path: Path) -> None:
    try:
        fig = optuna.visualization.plot_optimization_history(study)
        fig.write_html(str(path))
        with path.open("a") as f:
            f.write(study.trials_dataframe().to_html(index=False))
    except Exception:
        path.write_text(study.trials_dataframe().to_html(index=False))


def tune(
    date_from: str,
    date_to: str,
    *,
    symbols: list[str] = typer.Option(..., "--symbols", help="Trading symbols"),
    n_trials: int = typer.Option(50, "--n_trials", help="Number of trials"),
    data_dir: Path = typer.Option(
        Path("."), "--data-dir", exists=True, file_okay=False
    ),
    apply: bool = typer.Option(False, help="Stage best config"),
) -> None:
    """Run parameter tuning."""
    sampler = SobolTPESampler()
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(lambda t: _objective(t, symbols, data_dir), n_trials=n_trials)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    proposed_dir = Path("config/proposed")
    proposed_dir.mkdir(parents=True, exist_ok=True)
    proposed_file = proposed_dir / f"{ts}.yml"
    yaml.safe_dump(study.best_params, proposed_file.open("w"))
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / f"tune_{ts}.html"
    _save_report(study, report_file)
    if apply:
        staging = Path("config/staging.yml")
        shutil.copy(proposed_file, staging)
    typer.echo(str(proposed_file))
