from contextlib import asynccontextmanager
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

from .analytics import analytics, execute_strategy
from .database import create_tables, get_db
from .market_service import fetch_market_data

scheduler = AsyncIOScheduler()


async def scheduled_fetch() -> None:
    try:
        await fetch_market_data()
    except Exception:
        pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    await scheduled_fetch()
    scheduler.add_job(scheduled_fetch, "interval", minutes=int(os.getenv("FETCH_INTERVAL_MINUTES", "5")), id="raw-market-fetch", replace_existing=True)
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Crypto Analytics Raw SQLite API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health(): return {"status": "ok"}


@app.post("/market-data/fetch")
async def fetch():
    try: return await fetch_market_data()
    except Exception as error: raise HTTPException(status_code=502, detail="Unable to fetch CoinGecko market data") from error


@app.get("/markets")
async def markets(db: sqlite3.Connection = Depends(get_db)):
    return {"markets": [row[0] for row in db.execute("SELECT DISTINCT symbol FROM market_data ORDER BY symbol").fetchall()]}


@app.get("/prices")
async def price(symbol: str, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT symbol, price, volume, timestamp FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", (symbol.upper(),)).fetchone()
    if row is None: raise HTTPException(status_code=404, detail="Symbol not found")
    return dict(row)


@app.get("/history")
async def history(symbol: str, limit: int = Query(100, ge=2, le=1000), db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT symbol, price, volume, timestamp FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?", (symbol.upper(), limit)).fetchall()
    return [dict(row) for row in reversed(rows)]


@app.get("/analytics")
async def get_analytics(window: int = Query(1, ge=1, le=1000)): return analytics(window)


@app.post("/strategy/run")
async def run_strategy(): return execute_strategy()


@app.get("/strategy/results")
async def strategy_results(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT symbol, signal, timestamp FROM strategy_signals ORDER BY timestamp DESC").fetchall()
    latest = {}
    for row in rows: latest.setdefault(row["symbol"], dict(row))
    return list(latest.values())
