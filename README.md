# Personal Financial Data Sync

A low-friction personal finance ingestion service for continuously pulling transaction data from connected financial accounts into Postgres.

This project is intentionally small and boring:

- FastAPI backend
- Plaid Link for account connection
- Plaid `/transactions/sync` for incremental updates
- Postgres for durable storage
- Raw + normalized transaction tables
- Cron-friendly sync command

## Why this shape

The key design choice is storing both raw and cleaned data. Raw transaction JSON is the source of truth; cleaned/normalized rows are disposable derived state. That makes it possible to fix bugs, improve categorization, or change schemas without reconnecting accounts.

## Plaid flow

1. Backend creates a Link token.
2. Browser opens Plaid Link.
3. Plaid returns a public token.
4. Backend exchanges the public token for an access token and item ID.
5. Backend stores the item and later calls `/transactions/sync` using the saved cursor.

## Local setup

```bash
cp .env.example .env
docker compose up -d db
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Open `http://localhost:8000`.

## Environment variables

See `.env.example`.

For first development, use Plaid Sandbox credentials. Sandbox is free and test-only. Production requires Plaid approval.

## Useful commands

```bash
# Run one sync pass for all connected Plaid items
python -m app.sync

# Start API server
uvicorn app.main:app --reload
```

## Production notes

For personal use, the simplest continuous deployment is:

- Host API on Render/Railway/Fly.io
- Use managed Postgres
- Run `python -m app.sync` every 6-24 hours via cron/scheduled job
- Add HTTPS before using real Plaid Link credentials

## Non-goals

- No credential scraping
- No trading
- No financial advice
- No multi-user auth beyond a single configured personal user ID

## Safety warning

Plaid access tokens are sensitive. Do not commit `.env`, database dumps, or logs containing tokens.
