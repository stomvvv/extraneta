#!/bin/bash
set -e

echo "Starting server on port ${PORT:-8000}..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} &
UVICORN_PID=$!

# If migrations fail, kill uvicorn and exit so Railway marks deploy as failed
trap "kill $UVICORN_PID 2>/dev/null; exit 1" ERR

echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."

wait $UVICORN_PID
