from __future__ import annotations

# mypy: ignore-errors

from dataclasses import dataclass, field

import numpy as np


@dataclass(slots=True)
class RingBuffer:
    size: int
    idx: int = 0
    full: bool = False
    price: np.ndarray = field(init=False)
    volume: np.ndarray = field(init=False)
    open_interest: np.ndarray = field(init=False)
    funding_rate: np.ndarray = field(init=False)
    liq_notional: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.price = np.zeros(self.size, dtype=np.float64)
        self.volume = np.zeros(self.size, dtype=np.float64)
        self.open_interest = np.zeros(self.size, dtype=np.float64)
        self.funding_rate = np.zeros(self.size, dtype=np.float64)
        self.liq_notional = np.zeros(self.size, dtype=np.float64)

    def update(self, frame: dict) -> None:
        self.price[self.idx] = frame.get("price", 0.0)
        self.volume[self.idx] = frame.get("volume", 0.0)
        self.open_interest[self.idx] = frame.get("open_interest", 0.0)
        self.funding_rate[self.idx] = frame.get("funding_rate", 0.0)
        self.liq_notional[self.idx] = frame.get("liquidation_notional", 0.0)
        self.idx = (self.idx + 1) % self.size
        if self.idx == 0:
            self.full = True

    def view(self, last: int) -> np.ndarray:
        if last > self.size:
            raise ValueError("view length exceeds buffer size")
        indices = (self.idx - last + np.arange(last)) % self.size
        return np.column_stack(
            (
                self.price[indices],
                self.volume[indices],
                self.open_interest[indices],
                self.funding_rate[indices],
                self.liq_notional[indices],
            )
        )
