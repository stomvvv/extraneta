#!/bin/sh
set -e

PORT="${PORT:-80}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "==> PORT=$PORT"
echo "==> BACKEND_URL=$BACKEND_URL"

# Use sed — always available on Alpine, no dependency on gettext/envsubst
sed \
  -e "s|\${PORT}|${PORT}|g" \
  -e "s|\${BACKEND_URL}|${BACKEND_URL}|g" \
  /etc/nginx/conf.d/default.conf.template \
  > /etc/nginx/conf.d/default.conf

echo "==> Generated nginx config:"
cat /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
