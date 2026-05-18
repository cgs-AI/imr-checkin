# Deployment notes

For a full step-by-step IMR test rollout (hardware, Phase A phone/QR, Phase B
iPad, verification checklists), see **`deployment-plan-imr-test.md`**.

## Components

- **Backend**: FastAPI app served by `uvicorn` (or `gunicorn` with the
  `uvicorn.workers.UvicornWorker`).
- **Worker**: `arq` worker running `app.workers.arq_settings.WorkerSettings`
  for scheduled jobs (directory sync, host email, HubSpot, retention).
- **Database**: PostgreSQL 14 or later.
- **Cache / queue**: Redis 6 or later (used by `arq`).
- **Frontend**: Next.js 14 (static export possible; otherwise served by
  `next start` or behind a reverse proxy).

## Environment variables

The full list lives in `backend/.env.example`. Required to operate the
full MVP:

| Variable | Notes |
|---|---|
| `DATABASE_URL` | PostgreSQL DSN, must include the `postgresql+psycopg` driver prefix. |
| `REDIS_URL` | Used by `arq` for job scheduling. |
| `GRAPH_TENANT_ID`, `GRAPH_CLIENT_ID`, `GRAPH_CLIENT_SECRET` | Azure AD app credentials with `User.Read.All` and `Mail.Send` application permissions. |
| `GRAPH_SENDER_UPN` | UPN whose mailbox is used for `sendMail`. Typically `reception@imr.ie`. |
| `HUBSPOT_ACCESS_TOKEN` | Private app token with contacts and notes scopes. |
| `ADMIN_JWT_SECRET` | Long random secret for admin bearer tokens. |
| `CORS_ORIGINS` | JSON-encoded list of allowed origins for the frontend. |

## First-time setup

1. Provision PostgreSQL, Redis.
2. Configure the Azure AD app and the HubSpot private app, capture the
   credentials.
3. Provision an Azure mailbox for `reception@imr.ie` and grant `Mail.Send`
   application permission.
4. Deploy the backend (run `alembic upgrade head` on first boot).
5. Deploy the worker.
6. Deploy the frontend with `NEXT_PUBLIC_API_BASE` set to the backend URL.
7. Generate a QR code that points to `https://<host>/checkin`.
8. Walk through the verification plan in `test-plan.md`.

## Operational concerns

- **Rate limiting** uses `slowapi`. The defaults are conservative; tune
  by setting the relevant environment variables in `Settings`.
- **Audit trail**: every admin deletion is recorded in `audit_events`.
  Visitor self-service submissions are recorded with actor
  `visitor_self_service`.
- **Retention**: enabled by default and scheduled at 03:15 daily.
- **Backups**: ensure regular PostgreSQL snapshots.
- **Secrets**: store all credentials in the IMR-approved secrets manager,
  never commit them to source control.
