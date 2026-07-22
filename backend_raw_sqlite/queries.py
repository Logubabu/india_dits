class Queries:
    GET_MARKET_DATA = "SELECT symbol, price, volume, timestamp FROM market_data ORDER BY timestamp ASC"
    INSERT_STRATEGY_SIGNAL = "INSERT INTO strategy_signals (symbol, signal, timestamp) VALUES (?, ?, ?)"
    INSERT_MARKET_DATA = "INSERT INTO market_data (symbol, price, volume, timestamp) VALUES (?, ?, ?, ?)"
    GET_DISTINCT_SYMBOLS = "SELECT DISTINCT symbol FROM market_data ORDER BY symbol"
    GET_PRICE_BY_SYMBOL = "SELECT symbol, price, volume, timestamp FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1"
    GET_HISTORY_BY_SYMBOL = "SELECT symbol, price, volume, timestamp FROM market_data WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?"
    GET_STRATEGY_RESULTS = "SELECT symbol, signal, timestamp FROM strategy_signals ORDER BY timestamp DESC"
    CREATE_MARKET_DATA_TABLE = """
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
        """
    