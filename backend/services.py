"""External market-data integration."""
from datetime import datetime, timezone
import logging
import os

import httpx

from .database import get_connection

logger = logging.getLogger(__name__)
COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"


async def fetch_crypto_data() -> dict[str, int]:
    params = {"vs_currency": os.getenv("QUOTE_CURRENCY", "usd"), "order": "market_cap_desc", "per_page": int(os.getenv("MARKET_LIMIT", "10")), "page": 1, "sparkline": "false"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
        response = await client.get(COINGECKO_MARKETS_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    captured_at = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    values = [(asset["symbol"].upper(), float(asset["current_price"]), float(asset["total_volume"]), captured_at) for asset in payload if asset.get("current_price") is not None and asset.get("total_volume") is not None]
    with get_connection() as connection:
        connection.executemany("INSERT INTO market_data (symbol, price, volume, timestamp) VALUES (?, ?, ?, ?)", values)
    logger.info("Stored market snapshot for %d assets", len(values))
    return {"stored": len(values)}
