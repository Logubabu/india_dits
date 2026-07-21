# Raw SQLite Backend

Independent FastAPI implementation of the crypto analytics API using Python's built-in `sqlite3` module and parameterized raw SQL queries only. No ORM is used.

Run from the repository root:

```powershell
.\venv\Scripts\python.exe -m pip install -r backend_raw_sqlite\requirements.txt
.\venv\Scripts\python.exe -m backend_raw_sqlite
```

It runs on `http://localhost:8001`; docs are at `http://localhost:8001/docs`.
