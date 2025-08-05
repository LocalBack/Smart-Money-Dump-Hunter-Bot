import os
import json
import pandas as pd
import redis

FIELDS = [
    "symbol",
    "price",
    "volume",
    "open_interest",
    "funding_rate",
    "liquidation_notional",
    "timestamp",
]
COINS = ["BTCUSDT", "ETHUSDT"]  # Coin limit: 2


def main() -> None:
    r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    rows = []
    for m in r.xrange("market.raw", "-", "+", count=1000):
        data = json.loads(m[1][b"data"])
        row = {}
        for field in FIELDS:
            value = data.get(field)
            if isinstance(value, (list, dict)):
                value = json.dumps(value)
            row[field] = value
        if row["symbol"] in COINS:
            rows.append(row)

    for symbol in COINS:
        df = pd.DataFrame([row for row in rows if row["symbol"] == symbol])
        if not df.empty:
            df = df.convert_dtypes()
            out = f"parquets/minute_2024-03-19_{symbol}.parquet"
            df.to_parquet(out)
            print(f"Saved {len(df)} rows to {out}")


if __name__ == "__main__":
    main()
