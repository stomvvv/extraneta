#!/bin/bash
set -e

echo "Running migrations..."
alembic upgrade head || echo "WARNING: Migrations failed, continuing anyway"

echo "Starting server on port ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
