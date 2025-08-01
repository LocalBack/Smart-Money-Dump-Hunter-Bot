from __future__ import annotations

import numpy as np


class RingBuffer:
    def __init__(self, size: int) -> None:
        self.size = size
        self.price = np.zeros(size, dtype=np.float64)
        self.volume = np.zeros(size, dtype=np.float64)
        self.open_interest = np.zeros(size, dtype=np.float64)
        self.funding_rate = np.zeros(size, dtype=np.float64)
        self.liq_notional = np.zeros(size, dtype=np.float64)
        self.index = 0
        self.full = False

    def update(
        self,
        price: float,
        volume: float,
        open_interest: float,
        funding_rate: float,
        liq_notional: float,
    ) -> None:
        i = self.index
        self.price[i] = price
        self.volume[i] = volume
        self.open_interest[i] = open_interest
        self.funding_rate[i] = funding_rate
        self.liq_notional[i] = liq_notional
        i = (i + 1) % self.size
        self.full = self.full or i == 0
        self.index = i

    def view(self, last: int) -> dict[str, np.ndarray]:
        if last > self.size:
            raise ValueError("too many bars requested")
        start = (self.index - last) % self.size
        if not self.full and start < self.index:
            sl = slice(start, self.index)
            return {
                "price": self.price[sl],
                "volume": self.volume[sl],
                "open_interest": self.open_interest[sl],
                "funding_rate": self.funding_rate[sl],
                "liq_notional": self.liq_notional[sl],
            }
        if start < self.index:
            sl = slice(start, self.index)
            return {
                "price": self.price[sl],
                "volume": self.volume[sl],
                "open_interest": self.open_interest[sl],
                "funding_rate": self.funding_rate[sl],
                "liq_notional": self.liq_notional[sl],
            }
        # wrapped
        def cat(arr: np.ndarray) -> np.ndarray:
            return np.concatenate([arr[start:], arr[: self.index]])

        return {
            "price": cat(self.price),
            "volume": cat(self.volume),
            "open_interest": cat(self.open_interest),
            "funding_rate": cat(self.funding_rate),
            "liq_notional": cat(self.liq_notional),
        }
