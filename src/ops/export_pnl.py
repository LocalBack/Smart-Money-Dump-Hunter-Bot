# mypy: ignore-errors
from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime

import asyncpg
import pandas as pd
from dateutil import parser


async def export_pnl(start: datetime, end: datetime, outfile: str) -> None:
    """Export planned trades between start and end as CSV."""
    dsn = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
    )
    conn = await asyncpg.connect(dsn)
    rows = await conn.fetch(
        """
        SELECT ts, symbol, side, qty, entry_price, sl_price, tp_price
        FROM trades_planned
        WHERE ts >= $1 AND ts < $2
        ORDER BY ts
        """,
        start,
        end,
    )
    data = []
    for r in rows:
        pnl = (
            (r["tp_price"] - r["entry_price"]) * r["qty"]
            if r["side"] == "buy"
            else (r["entry_price"] - r["tp_price"]) * r["qty"]
        )
        data.append(
            {
                "ts": r["ts"].isoformat(),
                "symbol": r["symbol"],
                "side": r["side"],
                "qty": r["qty"],
                "entry_price": r["entry_price"],
                "tp_price": r["tp_price"],
                "pnl": pnl,
            }
        )
    pd.DataFrame(data).to_csv(outfile, index=False)
    await conn.close()


def _parse_date(s: str) -> datetime:
    dt = parser.isoparse(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.utcnow().astimezone().tzinfo)
    return dt


if __name__ == "__main__":
    start = _parse_date(sys.argv[1])
    end = _parse_date(sys.argv[2])
    out = sys.argv[3]
    asyncio.run(export_pnl(start, end, out))
