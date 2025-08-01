"""Collector service entrypoint for Docker and CLI.

This module exposes a minimal `main` function that loads configuration
from environment variables and starts the collector defined in
``smartmoney_bot.collector``.
"""
from __future__ import annotations

import asyncio
import structlog

from . import Collector
from .config import from_env

logger = structlog.get_logger(__name__)


def main() -> None:
    """Load configuration from environment and run the collector."""
    cfg = from_env()
    collector = Collector(cfg)
    logger.info("starting", redis_url=cfg.redis_url, coin_limit=cfg.coin_limit)
    try:
        asyncio.run(collector.run())
    except KeyboardInterrupt:
        logger.info("stopping")
        if collector.redis:
            asyncio.run(collector.redis.close())


if __name__ == "__main__":
    main()
