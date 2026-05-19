# IMR Visitor Self Check-In

Self-service check-in system for visitors arriving at Irish Manufacturing Research (IMR). Visitors register on their own phone (QR code) or on a dedicated iPad at reception. The selected IMR host receives an email notification automatically.

**This branch (`master`) is the Proof of Concept.** The full production MVP — with HubSpot sync, Microsoft Graph directory sync, admin API, consent audit trail, rate limiting, and retention workers — lives on the `mvp` branch.

---

## What's included in the PoC

| Component | Description |
|-----------|-------------|
| `backend/` | FastAPI API — visitor storage, host search, visit submission, email notification via Microsoft Graph |
| `frontend/` | Next.js app for phone/QR check-in (port 3000) |
| `frontend-ipad/` | Next.js app for iPad kiosk (port 3001) — larger touch targets, inactivity reset |

Both frontends share the same backend. Visits are tagged `qr_self_checkin` or `ipad_kiosk` so you can tell them apart.

---

## Quick start

### 1. Start the database

```bash
docker run --rm -e POSTGRES_USER=imr -e POSTGRES_PASSWORD=imr \
  -e POSTGRES_DB=imr_checkin -p 5432:5432 postgres:16
```

### 2. Start the backend

```bash
cd backend
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
cp .env.example .env                   # edit with your values
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Health check: http://localhost:8000/healthz

### 3. Seed the host directory

The PoC uses a manually populated hosts table (no Microsoft Graph sync). Insert at least one host so visitors can search and select them:

```bash
python - <<'EOF'
import asyncio
from uuid import uuid4
from app.core.database import SessionLocal
from app.models.host import Host

async def seed():
    async with SessionLocal() as session:
        session.add(Host(
            id=uuid4(),
            display_name="Your Name",
            email="you@imr.ie",
            job_title="Your Role",
            department="Your Team",
            account_enabled=True,
        ))
        await session.commit()
        print("Host seeded.")

asyncio.run(seed())
EOF
```

### 4. Start the frontends

Phone/QR frontend:
```bash
cd frontend
npm install
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```
Opens at http://localhost:3000/checkin

iPad kiosk frontend:
```bash
cd frontend-ipad
npm install
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```
Opens at http://localhost:3001/checkin

---

## Configuration

All backend settings are environment variables. Copy `backend/.env.example` to `backend/.env` and adjust:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL DSN, e.g. `postgresql+psycopg://imr:imr@localhost:5432/imr_checkin` |
| `GRAPH_TENANT_ID` | For email | Microsoft 365 tenant ID |
| `GRAPH_CLIENT_ID` | For email | App registration client ID |
| `GRAPH_CLIENT_SECRET` | For email | App registration client secret |
| `GRAPH_SENDER_UPN` | For email | UPN of the mailbox used to send (e.g. `reception@imr.ie`) |
| `HUBSPOT_ACCESS_TOKEN` | For CRM sync | HubSpot private app token. When absent, CRM sync and pre-fill are skipped silently. |
| `CORS_ORIGINS` | Optional | Comma-separated list of allowed frontend origins |
| `SITE_NAME` | Optional | Displayed in the UI (default: `Irish Manufacturing Research`) |

If Graph credentials are not set, the backend starts and runs normally — host email notifications are skipped with a warning log. This is fine for a local demo.

---

## Running tests

```bash
cd backend
pytest
```

Tests use an in-memory SQLite database. No external services required.

---

## Check-in flow

Both frontends walk through the same steps:

1. **Welcome** — brief intro screen
2. **Privacy notice** — visitor must continue to proceed
3. **Returning visitor lookup** — optional; enter email or phone to pre-fill details
4. **Visitor details** — full name (required), email, phone, company, job title
5. **Host selection** — search by name (min 2 characters); only enabled hosts appear
6. **Review** — confirm all details before submitting
7. **Confirmation** — host notified; UI resets for next visitor

---

## Repo structure

```
backend/          FastAPI service
  app/
    routes/       checkin, visitors, hosts, visits
    models/       Visitor, Host, Visit
    services/     visitor lookup, visit creation, email notification
    integrations/ Microsoft Graph (send_mail only)
    core/         config, database, logging
  alembic/        database migrations
  tests/          pytest suite

frontend/         Phone/QR Next.js app (port 3000)
frontend-ipad/    iPad kiosk Next.js app (port 3001)
docs/             Architecture, deployment, and test planning docs
e2e/              Playwright end-to-end specs
```

---

## What's not in the PoC

See `docs/user-requirements.md` §5 for the full Stage 2 (Production MVP) feature list. In short:

- No Microsoft Graph staff directory sync (hosts seeded manually)
- No admin API or erasure workflow
- No consent audit trail
- No data retention workers
- No rate limiting
- All of the above are implemented on the `mvp` branch
