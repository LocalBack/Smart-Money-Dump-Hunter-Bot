from datetime import datetime

import pandas as pd

from smartmoney_bot.metrics.config import Config
from smartmoney_bot.metrics.metric_engine import write_metrics_row


def test_write_metrics_row(tmp_path) -> None:
    cfg = Config(PARQUET_DIR=str(tmp_path))
    ts = int(datetime(2024, 1, 1).timestamp() * 1000)
    msg1 = {"ts": ts, "symbol": "BTCUSDT", "price": 1.0}
    write_metrics_row(msg1, cfg)

    date_str = "20240101"
    file_path = tmp_path / f"minute_{date_str}_BTCUSDT.parquet"
    assert file_path.exists()
    df = pd.read_parquet(file_path)
    assert df.iloc[0]["price"] == 1.0

    msg2 = {"ts": ts + 60000, "symbol": "BTCUSDT", "price": 2.0}
    write_metrics_row(msg2, cfg)
    df2 = pd.read_parquet(file_path)
    assert len(df2) == 2
    assert df2.iloc[1]["price"] == 2.0

