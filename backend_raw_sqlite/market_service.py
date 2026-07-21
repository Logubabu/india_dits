"""CoinGecko ingestion implemented with parameterized SQLite inserts."""
from datetime import datetime, timezone
import os

import httpx

from backend_raw_sqlite.queries import Queries

from .database import get_connection


async def fetch_market_data() -> dict[str, int]:
    params = {"vs_currency": os.getenv("QUOTE_CURRENCY", "usd"), "order": "market_cap_desc", "per_page": int(os.getenv("MARKET_LIMIT", "10")), "page": 1, "sparkline": "false"}
    async with httpx.AsyncClient(timeout=15) as client:
        url = os.getenv("COINGECKO_API_URL", "https://api.coingecko.com/api/v3/coins/markets")
        
        response = await client.get(url, params=params)
        response.raise_for_status()
        assets = response.json()
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    rows = [(asset["symbol"].upper(), float(asset["current_price"]), float(asset["total_volume"]), timestamp) for asset in assets if asset.get("current_price") is not None and asset.get("total_volume") is not None]
    with get_connection() as connection:
        connection.executemany(Queries.INSERT_MARKET_DATA, rows)
    return {"stored": len(rows)}
