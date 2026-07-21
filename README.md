# Crypto Market Data & Analytics

A small full-stack application that ingests the top cryptocurrency markets from CoinGecko, stores time-series snapshots in SQLite, computes simple market analytics, and produces moving-average trading signals.

## Stack

- Backend: Python 3.9+, FastAPI, SQLite, APScheduler
- Frontend: React, TypeScript, Vite, Recharts
- Market data: CoinGecko `/coins/markets` public API

## Quick start

Open two terminals from the repository root.

### Docker (recommended local deployment)

With Docker Desktop running, start the full stack from the repository root:

```powershell
docker compose up --build
```

Available services:
- Frontend: `http://localhost:8080`
- Main backend API and Swagger docs: `http://localhost:8000/docs`
- Raw SQLite backend API and Swagger docs: `http://localhost:8001/docs`

The Compose volumes `crypto_data` and `crypto_data_raw` keep the SQLite databases between restarts. Stop the services with `docker compose down`; use `docker compose down -v` only when you deliberately want to delete the stored market history.

### Local PostgreSQL database (optional)

To run PostgreSQL only, use the separate database Compose file:

```powershell
docker compose -f docker-compose.db.yml up -d
```

It exposes PostgreSQL on `localhost:5432` and persists data in the `postgres_data` Docker volume. The current application is intentionally configured for SQLite, so use this service only when extending the persistence layer to PostgreSQL.

### Backend

1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies and start the main API:

   ```powershell
   python -m pip install -r backend/requirements.txt
   python -m backend
   ```

3. The main API starts at `http://localhost:8000`; interactive API documentation is at `/docs`.

To run the raw SQLite variant locally instead:

```powershell
python -m pip install -r backend_raw_sqlite/requirements.txt
python -m backend_raw_sqlite
```

That service runs at `http://localhost:8001`; interactive API documentation is at `/docs`.

The initial snapshot is fetched during startup and subsequent snapshots run every five minutes. Use `POST /market-data/fetch` or the frontend **Fetch market data** button to request one immediately.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (normally `http://localhost:5173`).

## Environment configuration

Both applications include a working local `.env` and a matching `.env.example` template.

| File | Main settings |
| --- | --- |
| `backend/.env` | `DATABASE_URL`, `CORS_ORIGINS`, fetch interval, market count, quote currency |
| `frontend/.env` | `VITE_API_BASE_URL` |

For a remote deployment, set `CORS_ORIGINS` to the deployed frontend URL and point `VITE_API_BASE_URL` to the deployed API. Do not put secrets in a `VITE_` variable: Vite exposes those values to the browser.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /markets` | Symbols with stored snapshots |
| `GET /prices?symbol=BTC` | Latest price and volume |
| `GET /history?symbol=BTC&limit=100` | Chronological price/volume series |
| `GET /analytics?window=1` | Ranked price and volume changes plus trend |
| `POST /market-data/fetch` | Fetch and persist a CoinGecko snapshot |
| `POST /strategy/run` | Execute and persist strategy signals |
| `GET /strategy/results` | Latest signal per asset |

## Architecture and strategy

The FastAPI service owns ingestion, SQLite persistence, analytics, and strategy execution. APScheduler invokes the same async ingestion function used by the manual fetch endpoint. The React client only consumes the API; it contains no mock market data.

Analytics compares the newest value for each asset with the value `window` snapshots earlier, then ranks assets by price change. The isolated strategy module uses a 2-period fast moving average and 5-period slow moving average:

- BUY: fast average crosses above slow average
- SELL: fast average crosses below slow average
- HOLD: no crossover or insufficient history

## Assumptions and limitations

- CoinGecko's public API can rate-limit requests; the default five-minute interval is intentionally conservative.
- SQLite and the in-process scheduler are appropriate for this assignment and a single application instance, but production would normally use PostgreSQL plus a separate worker/scheduler.
- Multiple snapshots are needed before meaningful analytics and moving-average crossover signals are available.
- Prices and volume are fetched as current market snapshots rather than historical candles.

## Possible improvements

- Add a cache and exponential retry/backoff for the external API.
- Support configurable strategy windows and more indicators.
- Add authentication, alerting, and WebSocket/polling updates.
- Add unit/integration tests and migrate persistence to PostgreSQL for production.
