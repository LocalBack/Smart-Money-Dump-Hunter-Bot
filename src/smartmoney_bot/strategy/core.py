from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..common.config import settings
from ..metrics.formulas import Metrics as MetricsDict


@dataclass(slots=True)
class Signal:
    symbol: str
    side: str
    entry_price: float
    sl_price: float
    tp_price: float
    p_hit_rate_est: float
    r_multiple: float


def generate_signal(
    symbol: str, last_price: float, metrics: MetricsDict
) -> Optional[Signal]:
    cfg = settings.strategy
    if not (
        metrics["pdd"] <= -0.2
        and metrics["vsr"] >= 3
        and metrics["ois"] >= 0.15
        and metrics["frd"] <= -0.02
    ):
        return None
    if not (metrics["lsi"] >= 2 or metrics["ll"] <= 0.5 * metrics["atr"]):
        return None
    if metrics["lcf"] > cfg.cost_threshold:
        return None

    entry = last_price
    sl = entry - metrics["atr"]
    r_multiple = 3.0
    tp = entry + r_multiple * (entry - sl)
    p_est = 0.4
    return Signal(
        symbol=symbol,
        side="long",
        entry_price=entry,
        sl_price=sl,
        tp_price=tp,
        p_hit_rate_est=p_est,
        r_multiple=r_multiple,
    )
