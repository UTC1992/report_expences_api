#!/usr/bin/env sh
set -eu

echo "Starting API entrypoint..."

if [ "${PERSISTENCE_PROVIDER:-memory}" = "postgres" ]; then
  DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"

  echo "Waiting for PostgreSQL (timeout: ${DB_WAIT_TIMEOUT}s)..."
  python - <<'PY'
import os
import socket
import sys
import time
from urllib.parse import urlparse

timeout = int(os.getenv("DB_WAIT_TIMEOUT", "60"))


def tcp_target_from_database_url(url: str) -> tuple[str, int] | None:
    """Host and port for TCP wait, parsed from DATABASE_URL."""
    raw = url.strip()
    if not raw:
        return None
    # Normalize schemes urlparse understands
    if raw.startswith("postgresql+asyncpg://"):
        raw = "postgresql://" + raw.removeprefix("postgresql+asyncpg://")
    elif raw.startswith("postgresql+psycopg://"):
        raw = "postgresql://" + raw.removeprefix("postgresql+psycopg://")
    elif raw.startswith("postgres://"):
        raw = "postgresql://" + raw.removeprefix("postgres://")
    if not raw.startswith("postgresql://"):
        return None
    parsed = urlparse(raw)
    if not parsed.hostname:
        return None
    port = parsed.port or 5432
    return (parsed.hostname, port)


database_url = os.getenv("DATABASE_URL", "").strip()
if not database_url:
    print(
        "ERROR: DATABASE_URL is required when PERSISTENCE_PROVIDER=postgres "
        "(single URL for app, migrations, and this wait).",
        flush=True,
    )
    sys.exit(1)
parsed = tcp_target_from_database_url(database_url)
if not parsed:
    print(
        f"ERROR: DATABASE_URL is not a parseable postgres URL: {database_url!r}",
        flush=True,
    )
    sys.exit(1)
host, port = parsed
print(f"TCP wait target from DATABASE_URL: {host}:{port}", flush=True)
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
            "Hint: ensure Postgres is up and DATABASE_URL points to the right host:port "
            "(Compose: hostname is often the db service name)."
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
