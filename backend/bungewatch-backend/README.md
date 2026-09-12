# BungeWatch Backend

FastAPI core API — the single backend serving the website, WhatsApp, and USSD channels.

## Structure

```
app/
  core/       # config (env vars via pydantic-settings)
  db/         # SQLAlchemy engine/session setup + declarative base
  models/     # SQLAlchemy ORM models (one table each)
  schemas/    # Pydantic request/response shapes — deliberately separate from
              # models, so internal DB fields (e.g. raw OCR text) never leak
              # into an API response by accident
  routers/    # FastAPI route handlers — kept thin, delegate to services/
  pipeline/   # Scraping + OCR + AI summarization (NOT wired to any endpoint —
              # meant to be run as a scheduled job, since it's minutes-long
              # work and doesn't belong in a request/response cycle)
  services/   # Business logic shared across routers/pipeline (empty for now)
alembic/      # DB migrations
```

## Setup

1. Copy `.env.example` to `.env` and fill in a real `DATABASE_URL` (Postgres —
   use Docker locally so your dev environment matches production; the schema
   uses Postgres-specific JSONB columns and will NOT work on SQLite).

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Generate the initial migration and apply it:
   ```
   alembic revision --autogenerate -m "initial schema"
   alembic upgrade head
   ```

4. Run the API:
   ```
   uvicorn app.main:app --reload
   ```

5. Visit `http://localhost:8000/docs` for interactive API docs (auto-generated
   by FastAPI from the schemas in `app/schemas/`).

## What's built so far

- `GET /health` — uptime check
- `GET /bills` — list bills, filterable by status
- `GET /bills/{id}` — bill detail

## What's NOT built yet (by design — build order matters)

- Scraping/OCR pipeline logic (`app/pipeline/` is scaffolded, empty)
- AI summarization
- `POST /subscriptions`
- WhatsApp webhook router
- USSD webhook router
- Auth/admin endpoints for the human review step

## Design decisions worth knowing before you extend this

- **Async everywhere.** SQLAlchemy async + asyncpg, not sync. Any new DB code
  should use `AsyncSession`, not the sync session pattern you'll find in most
  SQLAlchemy tutorials.
- **Models vs. schemas are separate on purpose.** Never return an ORM model
  directly from a router — always map through a Pydantic schema in
  `app/schemas/`, so you control exactly what the API exposes (e.g. raw OCR
  text and reviewer IDs should never appear in a public response).
- **`reviewed_text`, not `raw_extracted_text`, is what gets summarized.**
  `Bill.raw_extracted_text` is what came out of scraping/OCR before human
  review — never feed this to the AI summarizer directly.
- **Fixed enums for `status`, `house`, etc.** — not free text — because
  scraped status strings vary in wording between sources. Map raw scraped
  text to an enum value during ingestion; keep the raw string in
  `raw_status_text` for debugging when a mapping is unclear.
