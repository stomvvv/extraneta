#!/bin/bash
set -e

echo "=== ExtranEta v3 starting ==="
echo "PORT=${PORT:-8000}"
echo "DATABASE_URL prefix=${DATABASE_URL:0:20}..."
echo "ENVIRONMENT=${ENVIRONMENT:-development}"

echo "Running migrations..."
alembic upgrade head 2>&1 || echo "WARNING: Migrations failed, continuing anyway"

echo "Starting server on port ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --log-level info
