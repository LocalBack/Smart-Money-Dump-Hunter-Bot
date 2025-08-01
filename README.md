# Smart-Money Dump-Hunter Bot

This repository hosts the open-source implementation of the **Smart-Money Dump-Hunter** trading system. The bot focuses on exploiting forced-liquidation events on Binance using free data feeds and a deterministic risk framework.

The project is developed in phases. This repository currently contains the initial scaffold and the `collector` micro-service responsible for streaming market data into Redis Streams.

For the full architecture and strategy rationale see the `Strategy & Implementation Master Report` in the project documentation.

## Development Setup

1. Install [Poetry](https://python-poetry.org/) and run `poetry install`.
2. Copy `.env.sample` to `.env` and adjust settings if needed.
3. Run tests with `poetry run pytest`.

## Folder Structure

```
src/               # application packages
  collector/       # market data collector micro-service
  metrics/         # metric computation (placeholder)
  strategy/        # trading logic (placeholder)
  risk/            # risk management (placeholder)
  exec/            # order execution (placeholder)
  backtest/        # backtesting tools (placeholder)
  common/          # shared utilities (placeholder)
tests/             # pytest suite
```
