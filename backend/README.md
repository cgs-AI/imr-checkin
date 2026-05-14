# IMR visitor self check-in — backend

FastAPI service for the visitor check-in flow described in
`docs/plan.md`. Provides:

- Visitor and visit storage (PostgreSQL via SQLModel + Alembic)
- Public check-in endpoints (`/checkin/config`, `/visitors/lookup`,
  `/hosts`, `/visits`)
- Admin endpoints behind a JWT bearer token
- Background workers (`arq`) for host email, HubSpot Contact / Note
  sync, staff directory sync, and retention cleanup

## Local development

```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env
# edit .env with local credentials
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

In a second shell, run the worker:

```bash
arq app.workers.arq_settings.WorkerSettings
```

## Tests

```bash
pytest
```

Tests use an in-memory SQLite database and the FastAPI ASGI transport.
Integration with Microsoft Graph and HubSpot is exercised through the
job queue and is not invoked by the test suite.

## Configuration

All configuration lives in environment variables documented in
`.env.example`. Notable settings:

- `DATABASE_URL`: PostgreSQL DSN.
- `GRAPH_*`: Microsoft Graph app credentials. When unset the directory
  sync and host-email workers log a warning and become no-ops.
- `HUBSPOT_ACCESS_TOKEN`: Private app token. When unset HubSpot jobs
  raise and are kept as `failed` for retry.
- `ADMIN_JWT_SECRET`: HMAC secret for admin bearer tokens. Issue tokens
  programmatically via `app.core.security.issue_admin_token`.
