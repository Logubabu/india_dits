FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend_raw_sqlite/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend_raw_sqlite /app/backend_raw_sqlite
RUN mkdir -p /app/data

EXPOSE 8001

CMD ["uvicorn", "backend_raw_sqlite.main:app", "--host", "0.0.0.0", "--port", "8001"]
