# IMR visitor check-in — test deployment plan

This document is the end-to-end checklist to run a **test** instance of the check-in app at IMR. Deploy in two stages:

1. **Phase A — Phone / QR** (`frontend/` on port 3000, `source = qr_self_checkin`)
2. **Phase B — iPad kiosk** (`frontend-ipad/` on port 3001, `source = ipad_kiosk`)

Both phases share **one backend**, **one database**, and **one worker**. Phase B adds hardware and a second frontend URL.

For day-to-day ops after go-live, see also `deployment.md` and `test-plan.md`.

---

## 1. What you are deploying

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend API | FastAPI + uvicorn | Visits, lookup, host search, admin |
| Background worker | `arq` + Redis | Staff sync, host email, HubSpot sync, retention |
| Database | PostgreSQL 14+ | Visitors, visits, hosts, jobs, audit |
| Queue | Redis 6+ | Job scheduling for `arq` |
| Phone frontend | Next.js 14 (`frontend/`) | QR → visitor’s own phone |
| iPad frontend | Next.js 14 (`frontend-ipad/`) | Dedicated iPad at reception |
| Reverse proxy | nginx / IIS / Traefik (IT choice) | HTTPS termination |
| Integrations | Microsoft Graph, HubSpot | Host directory, email, CRM |

**Critical:** The background worker must run continuously. Without it, check-ins are saved locally but **host emails and HubSpot updates do not run** (they are queued and processed every few minutes).

---

## 2. Decisions to make before you start

| Decision | Options | Recommendation for test |
|----------|---------|-------------------------|
| Hosting | On-prem VM, existing server, approved cloud | On-prem VM on IMR LAN |
| Public URL | Internal DNS only vs internet-facing | Internal: `https://visitor-checkin.imr.local` |
| TLS certificate | AD CS, Let’s Encrypt (if public), self-signed (lab only) | IMR internal CA so phones/iPad trust HTTPS |
| HubSpot for test | Production CRM vs sandbox | **Sandbox** first if available; otherwise production with test contacts only |
| Email sender | `reception@imr.ie` or test mailbox | Dedicated test mailbox acceptable for pilot |
| Who approves privacy text | Legal / DPO | Sign-off on `docs/privacy.md` before reception use |

Record chosen URLs here before deployment:

```text
Phone check-in URL:  https://________________________/checkin
iPad check-in URL:   https://________________________/checkin   (can be different host or path)
API base URL:        https://________________________          (backend, no trailing slash)
```

---

## 3. Hardware and materials

### Phase A — Phone / QR (minimum)

| Item | Qty | Notes |
|------|-----|--------|
| Server or VM | 1 | 4 vCPU, 8 GB RAM, 50 GB disk (comfortable for test) |
| Reception QR display | 1 | Printed poster or small stand; links to phone URL |
| Test smartphones | 2+ | One iPhone, one Android; on IMR guest or staff Wi-Fi |
| Network | — | Guest/staff Wi-Fi must reach the check-in HTTPS URL |
| (Optional) Admin laptop | 1 | For API checks, logs, DB inspection |

No dedicated iPad required for Phase A.

### Phase B — iPad kiosk (adds to Phase A)

| Item | Qty | Notes |
|------|-----|--------|
| iPad | 1 | Dedicated to reception; iPadOS current or one version behind |
| Charging cable / dock | 1 | Keep powered during opening hours |
| Floor or desk stand | 1 | Portrait orientation, stable |
| IMR Wi-Fi | — | Same network reachability as server |
| Apple ID / MDM | — | **Not required** for MVP if using Guided Access (see §10) |

### Software on the server (no extra hardware)

- Linux (Ubuntu 22.04 LTS or RHEL equivalent) or Windows Server if IT standardises on it
- Node.js 20 LTS (build/run Next.js)
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- Reverse proxy (nginx recommended in examples below)

---

## 4. Accounts, access, and third-party setup

Complete these **before** installing the app. Allow 1–3 business days for IT / admin consent flows.

### 4.1 Source code and server access

- [ ] Git access to `imr-checkin` repository
- [ ] SSH/RDP to the test server
- [ ] Firewall rules: HTTPS (443) from IMR Wi-Fi (and VPN if remote admins) to the server
- [ ] Outbound HTTPS from server to:
  - `login.microsoftonline.com`, `graph.microsoft.com`
  - `api.hubapi.com`
  - (No OpenAI or other APIs in current MVP)

### 4.2 PostgreSQL

- [ ] Create database, e.g. `imr_checkin_test`
- [ ] Create role with password; store in secrets manager
- [ ] Connection string format:

```text
postgresql+psycopg://<user>:<password>@<host>:5432/imr_checkin_test
```

### 4.3 Redis

- [ ] Instance reachable at e.g. `redis://localhost:6379/0` (or managed Redis URL)
- [ ] Not exposed to the public internet

### 4.4 Microsoft Entra ID (Azure AD) app

Used for **staff directory sync** and **host notification email**.

1. Register an app registration (single-tenant).
2. Create a client secret; store securely.
3. **Application permissions** (not delegated), then **admin consent**:
   - `User.Read.All` — sync IMR staff into local `hosts` table
   - `Mail.Send` — send mail as the reception mailbox
4. Note:
   - `GRAPH_TENANT_ID`
   - `GRAPH_CLIENT_ID`
   - `GRAPH_CLIENT_SECRET`
5. Ensure `GRAPH_SENDER_UPN` (e.g. `reception@imr.ie`) is a real mailbox and the app is allowed to send as that user (application access policy if your tenant requires it).

**Staff sync schedule:** twice daily (06:00 and 18:00). After first deploy, run a **manual sync once** (see §7.8) so host autocomplete works immediately.

### 4.5 HubSpot private app

Used for **Contact upsert** and **visit Note** on each check-in (when visitor has an email).

1. In HubSpot: Settings → Integrations → Private apps → Create.
2. Scopes (minimum):
   - CRM: contacts (read + write)
   - CRM: notes (write) / objects notes as required by your HubSpot tier
3. Copy access token → `HUBSPOT_ACCESS_TOKEN`
4. For pilot: prefer a **sandbox** portal; use test visitor emails only.

If token is missing, visits still save locally; HubSpot jobs stay `failed` until configured.

### 4.6 Admin API access (support / IT)

Admin endpoints use JWT bearer tokens (`ADMIN_JWT_SECRET`). Issue tokens from a secure machine:

```python
# Run once in backend venv on an admin machine — do not commit output
from app.core.security import issue_admin_token
print(issue_admin_token(subject="your.name@imr.ie"))
```

Use for `GET /admin/visits` and troubleshooting (see §9).

### 4.7 Privacy and reception

- [ ] DPO / legal review of `docs/privacy.md`
- [ ] Reception briefed: visitors use **their own phone** (Phase A) or **iPad** (Phase B)
- [ ] Fallback if system down: manual sign-in sheet or reception process

---

## 5. Network and HTTPS

### Requirements

- Serve the app over **HTTPS** on the IMR network (required for sensible browser behaviour and iPad trust).
- Phone and iPad must resolve the hostname (internal DNS entry).
- Certificate must be trusted on test phones and the iPad (install root CA if using internal CA).

### Example nginx layout (adjust hostnames)

```nginx
# Phone + iPad frontends (two upstreams)
upstream checkin_phone {
    server 127.0.0.1:3000;
}
upstream checkin_ipad {
    server 127.0.0.1:3001;
}

upstream checkin_api {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl;
    server_name visitor-checkin.imr.local;

    ssl_certificate     /etc/ssl/imr/visitor-checkin.crt;
    ssl_certificate_key /etc/ssl/imr/visitor-checkin.key;

    # Phase A — phone / QR
    location / {
        proxy_pass http://checkin_phone;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://checkin_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}

# Phase B — optional separate vhost for iPad
server {
    listen 443 ssl;
    server_name visitor-kiosk.imr.local;

    ssl_certificate     /etc/ssl/imr/visitor-kiosk.crt;
    ssl_certificate_key /etc/ssl/imr/visitor-kiosk.key;

    location / {
        proxy_pass http://checkin_ipad;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://checkin_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

If you expose the API on the same host under `/api`, set frontends’ `NEXT_PUBLIC_API_BASE` to `https://visitor-checkin.imr.local/api` (no trailing slash). Alternatively, serve API at `https://visitor-checkin.imr.local:8000` with CORS — same-origin via proxy is simpler.

Update `CORS_ORIGINS` to include every browser origin:

```json
["https://visitor-checkin.imr.local", "https://visitor-kiosk.imr.local"]
```

---

## 6. Environment configuration

Create `backend/.env` on the server (never commit). Example for **test**:

```env
APP_ENV=staging
LOG_LEVEL=INFO

DATABASE_URL=postgresql+psycopg://imr_checkin:***@localhost:5432/imr_checkin_test
REDIS_URL=redis://localhost:6379/0

# JSON array — all frontend origins that will call the API
CORS_ORIGINS=["https://visitor-checkin.imr.local","https://visitor-kiosk.imr.local"]

CONSENT_TEXT_VERSION=2026-05-01

GRAPH_TENANT_ID=...
GRAPH_CLIENT_ID=...
GRAPH_CLIENT_SECRET=...
GRAPH_SENDER_UPN=reception@imr.ie

HUBSPOT_ACCESS_TOKEN=...
# HUBSPOT_BASE_URL=https://api.hubapi.com

ADMIN_JWT_SECRET=<long-random-string-min-32-chars>

VISIT_RETENTION_MONTHS=24
AUDIT_RETENTION_MONTHS=24
```

Frontends (build-time variable):

```env
# frontend/.env.production.local
NEXT_PUBLIC_API_BASE=https://visitor-checkin.imr.local/api

# frontend-ipad/.env.production.local  (Phase B)
NEXT_PUBLIC_API_BASE=https://visitor-kiosk.imr.local/api
```

---

## 7. Phase A — Deploy phone / QR test

### 7.1 Install server dependencies

```bash
# Ubuntu example
sudo apt update
sudo apt install -y postgresql redis-server nginx
# Python 3.11+, Node 20 — via packages or nvm/pyenv per IMR standard
```

### 7.2 Deploy backend

```bash
cd /opt/imr-checkin/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .

cp /path/to/secure/.env .env
alembic upgrade head

# Smoke test
uvicorn app.main:app --host 127.0.0.1 --port 8000
curl -s http://127.0.0.1:8000/healthz
# Expect: {"status":"ok"}
```

### 7.3 Run backend as a service

Use systemd (or IMR equivalent). Example unit `/etc/systemd/system/imr-checkin-api.service`:

```ini
[Unit]
Description=IMR Visitor Check-In API
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=imrcheckin
WorkingDirectory=/opt/imr-checkin/backend
EnvironmentFile=/opt/imr-checkin/backend/.env
ExecStart=/opt/imr-checkin/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now imr-checkin-api
```

### 7.4 Deploy background worker

Example unit `/etc/systemd/system/imr-checkin-worker.service`:

```ini
[Unit]
Description=IMR Visitor Check-In Worker (arq)
After=network.target redis.service imr-checkin-api.service

[Service]
Type=simple
User=imrcheckin
WorkingDirectory=/opt/imr-checkin/backend
EnvironmentFile=/opt/imr-checkin/backend/.env
ExecStart=/opt/imr-checkin/backend/.venv/bin/arq app.workers.arq_settings.WorkerSettings
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now imr-checkin-worker
```

**Worker schedule (built-in):**

| Job | Interval |
|-----|----------|
| Host email | Every 2 minutes |
| HubSpot sync | Every 5 minutes |
| Staff directory sync | 06:00 and 18:00 daily |
| Retention cleanup | 03:15 daily |

### 7.5 Build and run phone frontend

```bash
cd /opt/imr-checkin/frontend
npm ci
export NEXT_PUBLIC_API_BASE=https://visitor-checkin.imr.local/api
npm run build
npm run start   # listens on 3000 — put behind nginx
```

Run under systemd or `pm2` similarly to the API.

### 7.6 Configure reverse proxy and DNS

- [ ] DNS A record: `visitor-checkin.imr.local` → server IP
- [ ] nginx (or IIS) TLS + proxy to ports 3000 and 8000
- [ ] `curl https://visitor-checkin.imr.local/api/healthz` returns OK

### 7.7 First-time staff directory sync

Do not wait until 06:00 for the first test:

```bash
cd /opt/imr-checkin/backend
source .venv/bin/activate
python -c "import asyncio; from app.workers.directory_sync import sync_staff_directory; print(asyncio.run(sync_staff_directory()))"
```

Verify hosts exist:

```bash
curl -s "https://visitor-checkin.imr.local/api/hosts?q=smith" \
  -H "Accept: application/json"
```

(Replace `smith` with a known IMR surname.)

### 7.8 Create QR code for reception

1. Final URL: `https://visitor-checkin.imr.local/checkin` (or `/` if home routes to check-in — confirm in browser).
2. Generate QR (any trusted generator; IMR marketing may have a standard).
3. Print A4/A5 poster: short instructions — “Scan to check in on your phone”.
4. Place at reception eye level.

### 7.9 Phase A verification checklist

| # | Test | Pass criteria |
|---|------|----------------|
| 1 | Health | `GET /healthz` → `ok` |
| 2 | Config | `GET /checkin/config` returns site name and privacy text |
| 3 | Wi-Fi | Phone on IMR Wi-Fi opens check-in URL without certificate warning |
| 4 | QR scan | Camera app opens same URL |
| 5 | New visitor | Full flow completes; confirmation message shown |
| 6 | Database | Row in `visits` and `visitors` (IT: SQL or admin API) |
| 7 | Host search | Typing 2+ chars shows IMR staff |
| 8 | Host email | Within ~2 min, host receives email; `host_notified_at` set on visit |
| 9 | HubSpot | Within ~5 min, Contact + Note on timeline (test email only) |
| 10 | Returning visitor | Lookup by email pre-fills form |
| 11 | No email | Submit without email — visit saved, no HubSpot jobs |
| 12 | Worker down test | Stop worker, submit visit — visit saved, jobs `pending`; restart worker — jobs complete |

**Admin spot-check** (optional):

```bash
TOKEN=<admin-jwt>
curl -s "https://visitor-checkin.imr.local/api/admin/visits?limit=5" \
  -H "Authorization: Bearer $TOKEN"
```

Check `hubspot_contact_id`, `hubspot_note_id`, `host_notified_at` on recent rows.

### 7.10 Phase A go-live at reception (pilot)

- [ ] Reception trained (QR only, no data entry by staff)
- [ ] Poster mounted
- [ ] IT contact for outages
- [ ] 1-week pilot: 5–10 real visits, daily check of failed jobs:

```sql
SELECT job_type, status, last_error, updated_at
FROM integration_jobs
WHERE status IN ('failed', 'pending')
ORDER BY updated_at DESC
LIMIT 20;
```

**Phase A exit:** Stable check-ins, emails and HubSpot acceptable, no blocking UX issues on iPhone and Android.

---

## 8. Phase B — Add iPad kiosk test

Deploy Phase B only after Phase A is stable. Reuse the same backend, database, and worker.

### 8.1 Build and deploy iPad frontend

```bash
cd /opt/imr-checkin/frontend-ipad
npm ci
export NEXT_PUBLIC_API_BASE=https://visitor-kiosk.imr.local/api
npm run build
npm run start   # port 3001
```

- [ ] Add nginx vhost `visitor-kiosk.imr.local` → port 3001
- [ ] Add origin to `CORS_ORIGINS` if not already
- [ ] Reload API service if `CORS_ORIGINS` changed

### 8.2 iPad hardware setup

1. **Reset or dedicate** — no personal Apple ID required for Guided Access MVP.
2. Connect to **IMR Wi-Fi**; forget guest networks that cannot reach internal DNS.
3. Open Safari → `https://visitor-kiosk.imr.local/checkin`
4. Accept certificate if prompted (install profile/CA first if needed).
5. **Add to Home Screen** (optional): Share → Add to Home Screen for full-screen icon.
6. Set **Auto-Lock** to Never (or 15 min) while plugged in.
7. Enable **Guided Access**:
   - Settings → Accessibility → Guided Access → On
   - Set passcode (reception + IT only)
   - Open check-in page → triple-click side button → Start Guided Access
   - Disable Home button exit, app switching, sleep if appropriate for your stand

### 8.3 Reception layout (Phase B)

| Phase A (keep) | Phase B (add) |
|----------------|---------------|
| QR poster for phones | iPad on stand at desk |
| Verbal: “Scan the QR or use the iPad” | iPad shows welcome → Start check-in |

You may run **both** during comparison; visits are distinguished by `source` (`qr_self_checkin` vs `ipad_kiosk`).

### 8.4 Phase B verification checklist

| # | Test | Pass criteria |
|---|------|----------------|
| 1 | iPad loads URL | No cert errors; welcome screen visible |
| 2 | Touch UX | Large buttons usable standing at desk |
| 3 | Full check-in | Confirmation within 8 s auto-reset to welcome |
| 4 | Inactivity | 90 s warning, 120 s reset if abandoned mid-flow |
| 5 | Dictation | iPad keyboard mic fills a field (optional) |
| 6 | Source tag | `admin/visits` shows `source: ipad_kiosk` |
| 7 | HubSpot / email | Same as Phase A |
| 8 | Guided Access | Cannot exit to home without passcode |
| 9 | Offline | Stop API — user sees failure; reception fallback works |
| 10 | Recovery | Triple-click Guided Access, enter passcode, reload if frozen |

### 8.5 Phase B pilot

- [ ] One busy morning with iPad primary, QR as backup
- [ ] Compare `qr_self_checkin` vs `ipad_kiosk` counts in admin API
- [ ] Decide production default (QR only, iPad only, or both)

---

## 9. Operations during the test period

### Daily (IT or designated owner)

- [ ] `systemctl status imr-checkin-api imr-checkin-worker`
- [ ] Check for `failed` integration jobs (SQL above)
- [ ] Spot-check last 3 visits via admin API

### Weekly

- [ ] PostgreSQL backup verified
- [ ] Review application logs for `hubspot_contact.failed`, `host_email.failed`
- [ ] Confirm staff sync ran (new hires appear in host search)

### Logs

Structured logs via structlog (stdout/journal). On systemd:

```bash
journalctl -u imr-checkin-api -f
journalctl -u imr-checkin-worker -f
```

### Known limitations (current MVP)

- No admin web UI for failed syncs — use admin API + database
- HubSpot/email delays up to a few minutes (cron intervals)
- Admin UI page at `/admin` is a placeholder only

---

## 10. Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| Phone cannot open URL | DNS, firewall, or guest Wi-Fi isolation | Fix DNS; allow LAN access; test ping/curl |
| Certificate warning | Untrusted CA | Install IMR root on phone/iPad |
| Host search empty | Directory never synced | Run manual sync (§7.7); check Graph permissions |
| No host email | Worker stopped or Graph `Mail.Send` | Start worker; check `integration_jobs.last_error` |
| No HubSpot update | No email on visitor, bad token, or worker down | Check visit email; verify token; check jobs |
| CORS error in browser | Wrong `CORS_ORIGINS` | Add exact frontend origin including `https://` |
| 429 Too many requests | Rate limit | Wait; tune limits in config if needed |
| iPad stuck on old screen | Guided Access | Exit GA with passcode; refresh Safari |

---

## 11. Rollback

1. Stop pointing reception to QR / iPad (remove poster, power off iPad).
2. `systemctl stop imr-checkin-worker imr-checkin-api` (and frontends).
3. Database retained for audit; no need to delete for rollback.
4. Revert to manual reception process.

---

## 12. Sign-off before calling it “test complete”

| Area | Owner | Signed |
|------|-------|--------|
| Server and HTTPS | IT | |
| Graph + email | IT / M365 admin | |
| HubSpot test data | CRM owner | |
| Privacy notice | DPO / Legal | |
| Phase A reception pilot | Reception manager | |
| Phase B iPad pilot | Reception manager | |
| Failed-job monitoring | IT | |

---

## 13. Quick reference — repository commands (development)

For local dry-runs before IMR deploy, see `docs/running-both-frontends.md`:

```bash
# Terminal 1 — API
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — worker
cd backend && arq app.workers.arq_settings.WorkerSettings

# Terminal 3 — phone frontend
cd frontend && NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev

# Terminal 4 — iPad frontend (Phase B)
cd frontend-ipad && NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

---

## 14. Document map

| Document | Use |
|----------|-----|
| `deployment-plan-imr-test.md` (this file) | Full IMR test rollout |
| `deployment.md` | Component summary and env vars |
| `plan.md` | Phone/QR product scope |
| `plan-ipad-local-kiosk.md` | iPad scope and Guided Access detail |
| `test-plan.md` | Test matrix |
| `privacy.md` | Legal text |
| `running-both-frontends.md` | Dev: two frontends on one backend |
