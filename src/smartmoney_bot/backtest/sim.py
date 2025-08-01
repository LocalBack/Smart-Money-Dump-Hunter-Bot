from __future__ import annotations

# mypy: ignore-errors

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Optional

import click
import pandas as pd

from ..common.config import settings
from ..metrics.buffer import RingBuffer
from ..metrics.formulas import Metrics, compute_all_metrics
from ..risk.manager import AccountState, PositionParams, vet_and_size
from ..strategy.core import Signal, generate_signal


@dataclass(slots=True)
class Trade:
    ts: int
    symbol: str
    side: str
    qty: float
    entry: float
    exit: float
    pnl: float
    r: float


@dataclass(slots=True)
class Stats:
    win_rate: float
    avg_R: float
    profit_factor: float
    max_dd: float
    tail_ratio: float


def run_backtest(
    symbols: Iterable[str],
    data_dir: Path,
    params: PositionParams,
    start_equity: float = 10_000.0,
) -> tuple[list[Trade], Stats]:
    trades: list[Trade] = []
    account = AccountState(equity=start_equity, start_equity=start_equity)
    for symbol in symbols:
        path = data_dir / f"minute_2024-03-19_{symbol}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        buf = RingBuffer(settings.metrics.buffer_size)
        open_position: Optional[Signal] = None
        entry_bar = 0
        qty = 0.0
        for i, row in df.iterrows():
            frame = {
                "price": row.close,
                "volume": row.volume,
                "open_interest": row.open_interest,
                "funding_rate": row.funding_rate,
                "liquidation_notional": row.liquidation_notional,
            }
            buf.update(frame)
            if not buf.full and buf.idx < 15:
                continue
            metrics: Metrics = compute_all_metrics(
                buf.view(buf.idx if not buf.full else buf.size)
            )
            last_price = row.close
            if open_position is None:
                sig = generate_signal(symbol, last_price, metrics)
                if sig:
                    plan = vet_and_size(sig, account, params)
                    if plan:
                        open_position = sig
                        qty = plan.qty
                        entry_bar = i
                        account.equity -= (
                            qty * last_price * settings.risk.fee_bps / 10000
                        )
            else:
                if row.low <= open_position.sl_price:
                    exit_price = open_position.sl_price
                elif row.high >= open_position.tp_price:
                    exit_price = open_position.tp_price
                elif i - entry_bar >= 90:
                    exit_price = last_price
                else:
                    continue
                pnl = (
                    exit_price - open_position.entry_price
                ) * qty - qty * exit_price * settings.risk.fee_bps / 10000
                account.equity += qty * open_position.entry_price + pnl
                account.daily_pnl += pnl
                r = pnl / (
                    abs(open_position.entry_price - open_position.sl_price) * qty
                )
                trades.append(
                    Trade(
                        ts=int(row.timestamp.value // 1_000_000_000),
                        symbol=symbol,
                        side=open_position.side,
                        qty=qty,
                        entry=open_position.entry_price,
                        exit=exit_price,
                        pnl=pnl,
                        r=r,
                    )
                )
                open_position = None
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]
    win_rate = len(wins) / len(trades) if trades else 0.0
    avg_R = sum(t.r for t in trades) / len(trades) if trades else 0.0
    profit_factor = (
        sum(t.pnl for t in wins) / abs(sum(t.pnl for t in losses))
        if losses
        else float("inf")
    )
    max_dd = max(0.0, (start_equity - account.equity) / start_equity)
    tail_ratio = (
        (max(t.r for t in wins) / abs(min(t.r for t in losses)))
        if wins and losses
        else 0.0
    )
    stats = Stats(
        win_rate=win_rate,
        avg_R=avg_R,
        profit_factor=profit_factor,
        max_dd=max_dd,
        tail_ratio=tail_ratio,
    )
    return trades, stats


@click.command()
@click.option("--symbols", multiple=True, required=True)
@click.option("--data-dir", type=click.Path(exists=True, file_okay=False), default=".")
@click.option("--from-date")
@click.option("--to-date")
@click.option("--risk-pct", default=1.0)
@click.option("--max-dd", default=20.0)
@click.option("--daily-stop", default=100.0)
@click.option("--gridsearch", is_flag=True, default=False)
def cli(
    symbols: list[str],
    data_dir: str,
    from_date: str | None,
    to_date: str | None,
    risk_pct: float,
    max_dd: float,
    daily_stop: float,
    gridsearch: bool,
) -> None:
    params = PositionParams(risk_pct=risk_pct, max_dd_pct=max_dd, daily_stop=daily_stop)
    trades, stats = run_backtest(symbols, Path(data_dir), params)
    out_csv = Path("trades.csv")
    out_json = Path("stats.json")
    pd.DataFrame([asdict(t) for t in trades]).to_csv(out_csv, index=False)
    out_json.write_text(json.dumps(asdict(stats)))
    click.echo(f"Trades written to {out_csv}, stats to {out_json}")


if __name__ == "__main__":
    cli()
