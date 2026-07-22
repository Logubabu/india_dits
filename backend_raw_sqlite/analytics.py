"""Analytics and strategy calculations backed by raw SQLite SELECT/INSERT statements."""
from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean

from backend_raw_sqlite.queries import Queries
from .database import get_connection


def _assets() -> dict[str, list[dict]]:
    with get_connection() as connection:
        rows = connection.execute(Queries.GET_MARKET_DATA).fetchall()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["symbol"]].append(dict(row))
    return grouped


def analytics(num: int) -> list[dict]:
    output = []
    for symbol, rows in _assets().items():
        latest, previous = rows[-1], rows[max(0, len(rows) - num - 1)]
        compare_value = len(rows) > num
        price_change = ((latest["price"] / previous["price"]) - 1) * 100 if compare_value and previous["price"] else 0
        volume_change = ((latest["volume"] / previous["volume"]) - 1) * 100 if compare_value and previous["volume"] else 0
        output.append({"symbol": symbol, "current_price": latest["price"], "price_change_pct": round(price_change, 2), "volume_change_pct": round(volume_change, 2), "trend": "UP" if price_change > 0 else "DOWN" if price_change < 0 else "FLAT"})
    return sorted(output, key=lambda item: item["price_change_pct"], reverse=True)


def execute_strategy() -> dict:
    assets = _assets()
    if not assets:
        return {"status": "error", "message": "No stored market data. Fetch data first.", "signals": []}
    timestamp = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    signals = []
    with get_connection() as connection:
        for symbol, rows in assets.items():
            prices = [float(row["price"]) for row in rows]
            signal = "HOLD"
            if len(prices) >= 6:
                old_fast, new_fast = mean(prices[-3:-1]), mean(prices[-2:])
                old_slow, new_slow = mean(prices[-6:-1]), mean(prices[-5:])
                signal = "BUY" if old_fast <= old_slow and new_fast > new_slow else "SELL" if old_fast >= old_slow and new_fast < new_slow else "HOLD"
            connection.execute(Queries.INSERT_STRATEGY_SIGNAL, (symbol, signal, timestamp))
            signals.append({"symbol": symbol, "signal": signal})
    return {"status": "success", "signals": signals}
