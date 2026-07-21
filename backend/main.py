from contextlib import asynccontextmanager
import logging
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .analytics import get_analytics, run_strategy
from .database import create_db_and_tables, get_session
from .services import fetch_crypto_data

logging.basicConfig(level=logging.INFO)
scheduler = AsyncIOScheduler()


async def scheduled_fetch() -> None:
    try:
        await fetch_crypto_data()
    except Exception:
        logging.exception("Scheduled market-data fetch failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db_and_tables()
    await scheduled_fetch()
    scheduler.add_job(scheduled_fetch, "interval", minutes=int(os.getenv("FETCH_INTERVAL_MINUTES", "5")), id="market-fetch", replace_existing=True)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Crypto Market Analytics API", version="1.0.0", lifespan=lifespan)
origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/market-data/fetch")
async def fetch_market_data():
    try:
        return await fetch_crypto_data()
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Unable to fetch CoinGecko market data") from exc


@app.get("/markets")
async def read_markets(session = Depends(get_session)):
    markets = [row[0] for row in session.execute("SELECT DISTINCT symbol FROM market_data ORDER BY symbol").fetchall()]
    return {"markets": markets}


@app.get("/prices")
async def read_prices(symbol: str = Query(..., min_length=1), session = Depends(get_session)):
    item = session.execute("SELECT symbol, price, volume, timestamp FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", (symbol.upper(),)).fetchone()
    if item is None:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return dict(item)


@app.get("/history")
async def read_history(symbol: str, limit: int = Query(100, ge=2, le=1000), session = Depends(get_session)):
    rows = session.execute("SELECT symbol, price, volume, timestamp FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?", (symbol.upper(), limit)).fetchall()
    return [dict(row) for row in reversed(rows)]


@app.get("/analytics")
async def read_analytics(window: int = Query(1, ge=1, le=1000)):
    return get_analytics(window)


@app.post("/strategy/run")
async def trigger_strategy():
    return run_strategy()


@app.get("/strategy/results")
async def read_strategy_results(session = Depends(get_session)):
    rows = session.execute("SELECT symbol, signal, timestamp FROM strategy_signals ORDER BY timestamp DESC").fetchall()
    latest = {}
    for row in rows:
        latest.setdefault(row["symbol"], dict(row))
    return list(latest.values())
