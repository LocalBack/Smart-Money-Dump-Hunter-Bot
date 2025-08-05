import os
import json
import pandas as pd
import redis

# .env'deki REDIS_URL kullanılacak
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(redis_url)
# Tüm market.raw stream verilerini oku (büyük veri için dikkat!)
rows = [json.loads(m[1][b"data"]) for m in r.xrange("market.raw", "-", "+")]
df = pd.DataFrame(rows)
# Output dosyası (tarihi ve sembolü sen belirleyebilirsin)
output = "parquets/minute_2024-03-19_BTCUSDT.parquet"
df.to_parquet(output)
print(f"Saved {len(df)} rows to {output}")
