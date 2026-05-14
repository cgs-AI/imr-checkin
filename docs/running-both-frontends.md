# Running the phone and iPad frontends side by side

The repository ships two frontends that share one backend:

| Path | Purpose | Port | `Visit.source` |
|---|---|---|---|
| `frontend/` | Phone / QR self check-in (`docs/plan.md`) | 3000 | `qr_self_checkin` |
| `frontend-ipad/` | iPad reception kiosk (`docs/plan-ipad-local-kiosk.md`) | 3001 | `ipad_kiosk` |

Both apps call the same FastAPI backend at `NEXT_PUBLIC_API_BASE`
(defaults to `http://localhost:8000`). Visits write to the same database,
distinguished by the `source` column.

## Start everything

In four terminals:

```bash
# 1. PostgreSQL + Redis already running (docker, system service, etc.)

# 2. Backend
cd backend
uv pip install -e '.[dev]'           # first time only
alembic upgrade head                 # first time only
uvicorn app.main:app --reload --port 8000

# 3. Background worker
cd backend
arq app.workers.arq_settings.WorkerSettings

# 4a. Phone frontend
cd frontend
npm install                          # first time only
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
# → http://localhost:3000

# 4b. iPad frontend
cd frontend-ipad
npm install                          # first time only
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
# → http://localhost:3001
```

The default backend CORS list includes both `http://localhost:3000` and
`http://localhost:3001`. If you override `CORS_ORIGINS` for any environment,
include both origins explicitly.

## Telling the visits apart

Visits keep a `source` value of `qr_self_checkin` or `ipad_kiosk` depending on
the frontend that submitted them. In the admin API:

```bash
curl http://localhost:8000/admin/visits \
  -H "Authorization: Bearer $TOKEN"
```

Each row includes `source`, so you can filter or group by it when comparing
the two flows for the stakeholder demo.

## What is — and isn't — different

The backend is identical for both apps. Differences live only in the
frontends:

- Home / welcome copy.
- Privacy notice wording (the iPad version uses `plan-ipad-local-kiosk.md` §14
  verbatim; the phone version uses the backend-served default).
- Touch sizing and typography (the iPad app uses bigger fonts / taller
  inputs and buttons).
- Inactivity behaviour: the iPad app shows a warning at 90 s and resets at
  120 s. The phone app does not have an inactivity guard.
- Confirmation auto-reset: 8 s (iPad) vs 30 s (phone).
- Dictation helper text mentions the iPad keyboard microphone instead of
  the visitor's phone.
- The submitted `source` value.
