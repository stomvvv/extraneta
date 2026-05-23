#!/bin/sh
set -e

export PORT="${PORT:-80}"
export BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "Starting nginx on port $PORT, proxying /api/ to $BACKEND_URL"

envsubst '${PORT} ${BACKEND_URL}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
