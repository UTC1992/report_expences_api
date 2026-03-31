# Report Expences API — agent notes

## Stack

- **FastAPI** + **Pydantic Settings** (`app/core/config.py`)
- **PostgreSQL** via **SQLAlchemy 2 async** (`asyncpg`); **Alembic** for migrations
- **OpenAI** for chat expense parsing (`POST /api/v1/chat/process_expense`); `api_key` optional per request, fallback `OPENAI_API_KEY` on server

## Env

- **`.env`** is gitignored; copy from **`.env.example`**
- **Production:** set **`DATABASE_URL`** only (Railway/host env). Prefer **`postgresql+asyncpg://...`**
- **Local dev:** optional `DB_*` when `DATABASE_URL` is empty
- **`PERSISTENCE_PROVIDER`:** `memory` | `postgres` — choose storage backend; `entrypoint.sh` runs Alembic only when `postgres`

## Run

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Docker:** `docker compose up --build` — includes Postgres + `entrypoint.sh` (wait DB → `alembic upgrade head` → uvicorn)

## API prefix

Routes under **`/api/v1`** (see `API_PREFIX` in config).

## Key endpoints

- `POST /api/v1/chat/process_expense` — body: `text`, `provider`, optional `api_key`
- `POST /api/v1/expenses/import` — batch invoices/expenses
- `GET /api/v1/expenses` — filters: `start_date`, `end_date`, `category`, `provider_name`, `min_amount`, `max_amount`, `search`
- `GET /health`

## Architecture

- **`app/core/`** — config, DB session factory, DI helpers, logging, RFC7807 errors
- **`app/modules/expenses/`** — `domain` (entities, repo protocols), `application` (use cases, dedup), `infrastructure` (ORM, repos, OpenAI), `api` (routes/schemas)

## Migrations

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

Requires `DATABASE_URL` or complete `DB_*` / sync URL for Alembic.
