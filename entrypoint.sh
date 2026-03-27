#!/usr/bin/env sh
set -eu

echo "Starting API entrypoint..."

if [ "${PERSISTENCE_PROVIDER:-memory}" = "postgres" ]; then
  DB_HOST_CHECK="${DB_HOST:-db}"
  DB_PORT_CHECK="${DB_PORT:-5432}"
  DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"

  echo "Waiting for PostgreSQL at ${DB_HOST_CHECK}:${DB_PORT_CHECK} (timeout: ${DB_WAIT_TIMEOUT}s)..."
  python - <<'PY'
import os
import socket
import time
import sys

host = os.getenv("DB_HOST", "db")
port = int(os.getenv("DB_PORT", "5432"))
timeout = int(os.getenv("DB_WAIT_TIMEOUT", "60"))

start = time.time()
while True:
    try:
        with socket.create_connection((host, port), timeout=2):
            print("PostgreSQL is reachable.")
            break
    except OSError:
        if time.time() - start > timeout:
            print(f"Timed out waiting for PostgreSQL at {host}:{port}")
            sys.exit(1)
        time.sleep(1)
PY

  echo "Running database migrations..."
  alembic upgrade head
fi

echo "Launching Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
