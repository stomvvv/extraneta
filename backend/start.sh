#!/bin/bash
set -e

echo "Starting server on port ${PORT:-8000}..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} &
UVICORN_PID=$!

echo "Running database migrations..."
if alembic upgrade head; then
    echo "Migrations complete."
else
    echo "WARNING: Migrations failed — server still starting. Check DATABASE_URL."
fi

wait $UVICORN_PID
