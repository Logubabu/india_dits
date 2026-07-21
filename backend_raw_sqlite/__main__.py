import uvicorn


if __name__ == "__main__":
    uvicorn.run("backend_raw_sqlite.main:app", host="0.0.0.0", port=8001, reload=True)
