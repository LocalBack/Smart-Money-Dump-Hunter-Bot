from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..common.config import settings
from ..strategy.core import Signal


class HaltTrading(Exception):
    pass


@dataclass(slots=True)
class PositionParams:
    risk_pct: float
    max_dd_pct: float
    daily_stop: float


@dataclass(slots=True)
class AccountState:
    equity: float
    start_equity: float
    daily_pnl: float = 0.0


@dataclass(slots=True)
class OrderPlan:
    qty: float
    entry_price: float
    sl_price: float
    tp_price: float
    side: str


def vet_and_size(
    signal: Signal, account_state: AccountState, params: PositionParams
) -> Optional[OrderPlan]:
    edge = signal.p_hit_rate_est * signal.r_multiple - (1 - signal.p_hit_rate_est)
    if edge <= 0 or signal.r_multiple < 2:
        return None

    if (
        account_state.start_equity - account_state.equity
        >= params.max_dd_pct / 100 * account_state.start_equity
    ):
        raise HaltTrading("max drawdown reached")

    if -account_state.daily_pnl >= params.daily_stop:
        return None

    risk_amount = params.risk_pct / 100 * account_state.equity
    stop_dist = abs(signal.entry_price - signal.sl_price)
    if stop_dist <= 0:
        return None
    qty = risk_amount / stop_dist

    if qty < settings.risk.exchange_min_qty:
        return None

    return OrderPlan(
        qty=qty,
        entry_price=signal.entry_price,
        sl_price=signal.sl_price,
        tp_price=signal.tp_price,
        side=signal.side,
    )
