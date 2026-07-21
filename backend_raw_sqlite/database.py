"""SQLite connection and schema lifecycle using raw SQL only."""
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crypto_market_raw.db")


def _database_path() -> str:
    if not DATABASE_URL.startswith("sqlite:///"):
        raise RuntimeError("DATABASE_URL must be a SQLite URL, e.g. sqlite:///./crypto_market_raw.db")
    return DATABASE_URL.removeprefix("sqlite:///")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(_database_path(), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def get_db():
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()


def create_tables() -> None:
    with get_connection() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                price REAL NOT NULL,
                volume REAL NOT NULL,
                timestamp TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp
                ON market_data(symbol, timestamp);
            CREATE TABLE IF NOT EXISTS strategy_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                signal TEXT NOT NULL CHECK(signal IN ('BUY', 'SELL', 'HOLD')),
                timestamp TEXT NOT NULL
            );
        """)
