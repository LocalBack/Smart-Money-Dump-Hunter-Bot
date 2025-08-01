from __future__ import annotations

from typing import TypedDict

import numpy as np
from numba import njit  # type: ignore


class Metrics(TypedDict):
    pdd: float
    vsr: float
    ois: float
    frd: float
    atr: float
    ll: float
    lva: float
    lsi: float
    lcf: float


@njit
def _mean(arr: np.ndarray) -> float:
    return float(arr.sum() / len(arr))


@njit
def compute_pdd(prices: np.ndarray) -> float:
    if prices.shape[0] <= 15:
        return 0.0
    base = prices[-15]
    if base == 0.0:
        return 0.0
    return float((prices[-1] - base) / base)


def compute_all_metrics(data: np.ndarray) -> Metrics:
    prices = data[:, 0]
    volumes = data[:, 1]
    oi = data[:, 2]
    fr = data[:, 3]
    liq = data[:, 4]

    pdd = compute_pdd(prices)
    vsr = volumes[-1] / _mean(volumes[-15:]) if volumes.shape[0] >= 15 else 0.0
    ois = oi[-1] / _mean(oi[-15:]) if oi.shape[0] >= 15 else 0.0
    frd = fr[-1] - fr[-2] if fr.shape[0] >= 2 else 0.0
    atr = np.mean(np.abs(np.diff(prices[-14:]))) if prices.shape[0] >= 14 else 0.0
    ll = liq[-1] / (_mean(liq[-15:]) or 1.0) if liq.shape[0] >= 15 else 0.0
    lva = volumes[-1] - volumes[-2] if volumes.shape[0] >= 2 else 0.0
    lsi = 0.0
    lcf = 0.0
    return {
        "pdd": float(pdd),
        "vsr": float(vsr),
        "ois": float(ois),
        "frd": float(frd),
        "atr": float(atr),
        "ll": float(ll),
        "lva": float(lva),
        "lsi": float(lsi),
        "lcf": float(lcf),
    }
