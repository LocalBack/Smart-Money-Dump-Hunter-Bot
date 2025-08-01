from __future__ import annotations

# mypy: ignore-errors

from typing import Any

try:
    from pydantic import BaseModel, BaseSettings, Field
except Exception:  # pragma: no cover - fallback if pydantic stubs missing
    BaseModel = BaseSettings = object  # type: ignore

    def Field(*args: Any, **kwargs: Any) -> Any:  # type: ignore
        return kwargs.get("default")


class CollectorConfig(BaseModel):
    redis_url: str = Field(default="redis://localhost:6379/0")
    coin_limit: int = Field(default=50)


class MetricsConfig(BaseModel):
    redis_url: str = Field(default="redis://localhost:6379/0")
    buffer_size: int = Field(default=1440)
    atr_period: int = Field(default=14)


class StrategyConfig(BaseModel):
    cost_threshold: float = Field(default=1_000_000.0)


class RiskConfig(BaseModel):
    fee_bps: float = Field(default=0.1)
    exchange_min_qty: float = Field(default=0.001)


class Settings(BaseSettings):
    collector: CollectorConfig = CollectorConfig()
    metrics: MetricsConfig = MetricsConfig()
    strategy: StrategyConfig = StrategyConfig()
    risk: RiskConfig = RiskConfig()

    class Config:
        env_nested_delimiter = "__"


settings = Settings()
