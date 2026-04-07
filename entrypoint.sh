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
import sys
import time

host = os.getenv("DB_HOST", "db")
port = int(os.getenv("DB_PORT", "5432"))
timeout = int(os.getenv("DB_WAIT_TIMEOUT", "60"))
sock_timeout = 2
poll_interval = 1
status_interval = 5

start = time.time()
last_status = 0.0
attempt = 0
last_err: OSError | None = None


def log(msg: str) -> None:
    print(msg, flush=True)


def try_tcp() -> bool:
    global last_err
    try:
        with socket.create_connection((host, port), timeout=sock_timeout):
            return True
    except OSError as e:
        last_err = e
        return False


log(
    f"TCP check: trying {host!r}:{port} (socket timeout {sock_timeout}s per attempt, "
    f"poll every {poll_interval}s)."
)
try:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    addrs = sorted({x[4][0] for x in infos})
    log(f"DNS: {host!r} resolves to {addrs!r}")
except OSError as e:
    log(f"DNS: could not resolve {host!r}: {e}")

while True:
    attempt += 1
    elapsed = time.time() - start
    if try_tcp():
        log(f"PostgreSQL port is open at {host}:{port} (ready after {elapsed:.1f}s, {attempt} attempt(s)).")
        break
    if elapsed > timeout:
        log(f"Timed out after {timeout}s waiting for TCP {host}:{port} ({attempt} attempts).")
        if last_err is not None:
            log(f"Last connection error: {last_err!r} ({last_err})")
        log(
            "Hint: is Postgres running? On Docker Compose, ensure the api service "
            "depends_on db with a healthcheck; on Railway, DB_HOST must match your "
            "database service (often from DATABASE_URL, not 'db')."
        )
        sys.exit(1)
    if attempt == 1:
        log(f"First failure: {last_err!r} — will retry until timeout.")
    elif elapsed - last_status >= status_interval:
        log(
            f"Still waiting ({elapsed:.0f}s / {timeout}s): {host}:{port} — last error: {last_err}"
        )
        last_status = elapsed
    time.sleep(poll_interval)
PY

  echo "Running database migrations..."
  alembic upgrade head
fi

echo "Launching Uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
