#!/bin/sh
set -e
echo "Running Alembic migrations..."
cd /app/backend
alembic upgrade head
echo "Starting Uvicorn..."
cd /app
exec uvicorn backend.src.main:app --host 0.0.0.0 --port 8000
