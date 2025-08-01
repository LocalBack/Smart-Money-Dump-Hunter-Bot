from __future__ import annotations

from typing import TypedDict

import numba as nb
import numpy as np


class MetricResult(TypedDict):
    pdd: float
    vsr: float
    ois: float
    frd: float


@nb.njit  # type: ignore[misc]
def _pdd(prices: np.ndarray, lookback: int) -> float:
    if prices.shape[0] <= lookback:
        return 0.0
    return float((prices[-1] - prices[-lookback - 1]) / prices[-lookback - 1])


@nb.njit  # type: ignore[misc]
def _vsr(volumes: np.ndarray, lookback: int) -> float:
    vol_l = volumes[-lookback:].sum()
    median_24h = np.median(volumes[-1440:])
    if median_24h == 0:
        return 0.0
    return float(vol_l / median_24h)


@nb.njit  # type: ignore[misc]
def _ois(oi: np.ndarray, lookback: int) -> float:
    if oi.shape[0] <= lookback:
        return 0.0
    base = oi[-lookback - 1]
    if base == 0:
        return 0.0
    return float((oi[-1] - base) / base)


@nb.njit  # type: ignore[misc]
def _frd(funding: np.ndarray) -> float:
    if funding.shape[0] < 1:
        return 0.0
    avg7 = funding[-min(funding.shape[0], 10080):].mean()
    return float(funding[-1] - avg7)


def compute_all_metrics(buf: dict[str, np.ndarray], lookback: int = 15) -> MetricResult:
    prices = buf["price"]
    volumes = buf["volume"]
    oi = buf["open_interest"]
    funding = buf["funding_rate"]
    return MetricResult(
        pdd=float(_pdd(prices, lookback)),
        vsr=float(_vsr(volumes, lookback)),
        ois=float(_ois(oi, lookback)),
        frd=float(_frd(funding)),
    )
