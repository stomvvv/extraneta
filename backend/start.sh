#!/bin/bash
# No set -e — we want the server to stay up even if migrations fail.

echo "Starting server on port ${PORT:-8000}..."
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" &
UVICORN_PID=$!

echo "Running database migrations..."
if alembic upgrade head 2>&1; then
    echo "Migrations complete."
else
    echo "WARNING: Migrations failed (exit $?) — server still running. Check DATABASE_URL / DB connectivity."
fi

# Keep the container alive as long as uvicorn is running.
# If uvicorn exits, restart it so Railway keeps the container healthy.
while true; do
    if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
        echo "uvicorn exited — restarting..."
        uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" &
        UVICORN_PID=$!
    fi
    sleep 5
done
