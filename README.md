# Smart-Money Dump-Hunter Bot

This repository hosts the open-source implementation of the **Smart-Money Dump-Hunter** trading system. The bot focuses on exploiting forced-liquidation events on Binance using free data feeds and a deterministic risk framework.

The project is developed in phases. This repository currently contains the initial scaffold and the `collector` micro-service responsible for streaming market data into Redis Streams.

Phase 2 introduces the `metric_engine` service which consumes the raw market stream and publishes derived metrics back to Redis.

For the full architecture and strategy rationale see the `Strategy & Implementation Master Report` in the project documentation.

## Development Setup

1. Install [Poetry](https://python-poetry.org/) and run `poetry install`.
2. Copy `.env.sample` to `.env` and adjust settings if needed.
3. Run tests with `poetry run pytest`.

## Folder Structure

```
src/               # application packages
  collector/       # market data collector micro-service
  metrics/         # metric computation engine
  strategy/        # trading logic
  risk/            # risk management
  exec/            # order execution (placeholder)
  backtest/        # backtesting tools
  common/          # shared utilities (placeholder)
tests/             # pytest suite
```

## Running the Metric Engine

The metric engine service reads from `market.raw` and publishes to `market.metrics`.
You can run it with Docker Compose alongside Redis:

```yaml
version: "3"
services:
  redis:
    image: redis:7
  metrics:
    build: .
    environment:
      SERVICE: metrics.metric_engine
    depends_on:
      - redis
```

Start the engine with:

```bash
docker compose up metrics
```

## Backtesting

Run the simulator over historical parquet data:

```bash
poetry run backtest --symbols BTCUSDT SOLUSDT --from 2023-01-01 --to 2025-07-31
```

Example stats output:

| win_rate | avg_R | profit_factor | max_dd | tail_ratio |
|---------:|------:|--------------:|------:|-----------:|
| 0.55 | 2.1 | 1.7 | 0.12 | 1.5 |

## Tuning & Config

The `bot` CLI manages configuration and parameter tuning. Example commands:

```bash
# inspect current config
poetry run bot config view

# change a value
poetry run bot config set collector.coin_limit 25

# preview and apply
poetry run bot config diff
poetry run bot config apply

# run hyper-parameter tuning
poetry run bot tune 2024-01-01 2025-07-31 --symbols BTCUSDT ETHUSDT --n_trials 100
```

When executed from a CRON job with the `--apply` flag, the tuner writes the best
parameter set to `config/staging.yml` which can then be reviewed and applied.

## Running the stack locally

To bring up all services run:

```bash
docker compose up
```

Grafana is available on [http://localhost:3000](http://localhost:3000) (default `admin/admin`).
Import the dashboard from `docker/grafana-dashboard.json`.

## Staging Soak

1. Copy `env/.env.staging.example` to `env/.env.staging` and provide Binance
   testnet API keys.
2. Launch the soak stack:

   ```bash
   docker compose -f docker-compose.staging.yml up -d
   ```

3. Grafana runs at `http://localhost:3000` with the default `admin/admin`
   credentials.
4. Chaos scripts in `scripts/chaos` simulate outages. Execute them and review
   container logs to verify recovery.

