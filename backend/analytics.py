"""Analytics and isolated rule-based strategy functions."""
from collections import defaultdict
from datetime import datetime, timezone
from statistics import mean

from .database import get_connection


def _assets_by_symbol() -> dict[str, list[dict]]:
    with get_connection() as connection:
        rows = connection.execute("SELECT symbol, price, volume, timestamp FROM market_data ORDER BY timestamp").fetchall()
    assets: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        assets[row["symbol"]].append(dict(row))
    return assets


def get_analytics(window: int = 1) -> list[dict]:
    results = []
    for symbol, rows in _assets_by_symbol().items():
        latest, previous = rows[-1], rows[max(0, len(rows) - 1 - max(1, window))]
        comparable = len(rows) > window
        price_change = (latest["price"] / previous["price"] - 1) * 100 if comparable and previous["price"] else 0.0
        volume_change = (latest["volume"] / previous["volume"] - 1) * 100 if comparable and previous["volume"] else 0.0
        results.append({"symbol": symbol, "current_price": latest["price"], "price_change_pct": round(price_change, 2), "volume_change_pct": round(volume_change, 2), "trend": "UP" if price_change > 0 else "DOWN" if price_change < 0 else "FLAT"})
    return sorted(results, key=lambda item: item["price_change_pct"], reverse=True)


def run_strategy() -> dict:
    assets = _assets_by_symbol()
    if not assets:
        return {"status": "error", "message": "No stored market data. Fetch data first.", "signals": []}
    signals = []
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
    with get_connection() as connection:
        for symbol, rows in assets.items():
            prices = [float(row["price"]) for row in rows]
            signal = "HOLD"
            if len(prices) >= 6:
                previous_fast, latest_fast = mean(prices[-3:-1]), mean(prices[-2:])
                previous_slow, latest_slow = mean(prices[-6:-1]), mean(prices[-5:])
                signal = "BUY" if previous_fast <= previous_slow and latest_fast > latest_slow else "SELL" if previous_fast >= previous_slow and latest_fast < latest_slow else "HOLD"
            connection.execute("INSERT INTO strategy_signals (symbol, signal, timestamp) VALUES (?, ?, ?)", (symbol, signal, now))
            signals.append({"symbol": symbol, "signal": signal})
    return {"status": "success", "signals": signals}
