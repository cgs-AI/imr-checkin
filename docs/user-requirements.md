# User requirements — IMR visitor self check-in

**Document version:** 1.1  
**Status:** Restructured into two delivery stages  
**Audience:** Product owners, reception, IT, DPO/Legal, software team  
**Related documents:** [plan.md](plan.md), [plan-ipad-local-kiosk.md](plan-ipad-local-kiosk.md), [privacy.md](privacy.md), [handoff-imr-test.md](handoff-imr-test.md)

---

## 1. Purpose

IMR needs visitors to register their own arrival at reception without staff re-typing details. The system must notify the IMR employee being visited, keep a local visit history, and sync relationship data to HubSpot where appropriate.

This document states **what users must be able to do** and **what the system must do**. Requirements are split into two delivery stages:

- **Stage 1 — Proof of Concept (PoC):** validates the core visitor self-check-in flow end to end. Minimum infrastructure; manually seeded staff list; no CRM sync; no automated test suite.
- **Stage 2 — Production MVP:** adds compliance, CRM integration, automated directory sync, retention, erasure, admin tooling, and a full test battery required before go-live.

---

## 2. Problem statement

Today, reception often captures visitor details manually. That leads to duplicate effort, incomplete visit history, delayed host awareness, and inconsistent CRM records.

The solution provides **self-service check-in** through either:

- **Phase A — Phone / QR:** the visitor scans a QR code and completes a form on their own phone.
- **Phase B — iPad kiosk:** the visitor completes the same logical flow on a dedicated iPad at the desk.

Both channels share one backend, one database, and the same integrations.

---

## 3. User roles

| Role | Description |
|------|-------------|
| **Visitor** | Person arriving at IMR who completes the check-in form. |
| **IMR host** | IMR employee being visited; selected from the staff directory; receives email when notified. |
| **Reception staff** | Points visitors to the QR poster or iPad; does not enter visitor data in the MVP. |
| **IT / operations** | Deploys servers, TLS, workers, monitors failed background jobs. |
| **Admin / support** | Uses authenticated admin API to list or delete visitor data (no full admin UI yet). |
| **DPO / Legal** | Approves privacy notice text and consent version before go-live. |
| **CRM owner** | Owns HubSpot test/production configuration. |

---

## 4. Stage 1 — Proof of Concept requirements

Requirements use **UR-** identifiers. All Stage 1 requirements are **Must** (blocking for the PoC to be usable).

### 4.1 Entry and configuration

| ID | Requirement |
|----|-------------|
| UR-1.1 | The system shall expose a check-in URL for the phone/QR channel reachable from IMR guest Wi-Fi over HTTPS. |
| UR-1.2 | The system shall expose a separate check-in URL for the iPad kiosk channel over HTTPS. |
| UR-1.3 | On load, the check-in app shall retrieve public configuration: site name, privacy notice text, and minimum characters for host search. |
| UR-1.4 | If configuration cannot be loaded, the visitor shall see a clear error and a way to retry (e.g. reload). |

### 4.2 Privacy notice

| ID | Requirement |
|----|-------------|
| UR-2.1 | Before collecting personal data, the visitor shall see the privacy notice (wording per [privacy.md](privacy.md)). |
| UR-2.2 | The visitor shall not proceed without explicitly continuing after reading the notice. |

### 4.3 Returning visitor lookup

| ID | Requirement |
|----|-------------|
| UR-3.1 | The visitor may identify as returning by entering **email** and/or **phone**, or skip and continue as a new visitor. |
| UR-3.2 | The system shall search the local visitor database by email (normalised) or phone (normalised to E.164 where valid). |
| UR-3.3 | If exactly one local match is found, the form shall pre-fill name, email, phone, company, and job title for review and edit. |
| UR-3.4 | If multiple visitors share the same phone number, the system shall not auto-select a match; the visitor shall enter details manually. |
| UR-3.5 | If no local match is found and the visitor provided an email, the system shall query HubSpot CRM for a matching contact and pre-fill details if found (`hubspot_prefilled` flag returned). |
| UR-3.6 | If no local or HubSpot match is found, the visitor shall continue with empty or self-entered fields. |

### 4.4 Visitor details

| ID | Requirement |
|----|-------------|
| UR-4.1 | The visitor shall enter **full name** (required). |
| UR-4.2 | The visitor may enter email, phone, company, and job title. |
| UR-4.3 | Email and phone shall be validated/normalised before save (invalid email rejected). |
| UR-4.4 | The visitor shall be able to use the device keyboard; on phone and iPad, native dictation may be used — IMR does not record audio, only submitted text. |
| UR-4.5 | Helper text shall indicate that dictation is available via the device keyboard. |

### 4.5 Host selection

| ID | Requirement |
|----|-------------|
| UR-5.1 | The visitor shall search for their IMR host by name (minimum 2 characters by default). |
| UR-5.2 | Search results shall list enabled staff from a seeded host directory (display name, optional department). For the PoC, this directory may be populated manually rather than synced from Microsoft 365. |
| UR-5.3 | Disabled or removed accounts shall not appear in search results. |
| UR-5.4 | The visitor shall select one host before continuing. |
| UR-5.5 | Submitting with an invalid or disabled host ID shall be rejected with a clear error. |

### 4.6 Review and submit

| ID | Requirement |
|----|-------------|
| UR-6.1 | Before submit, the visitor shall review name, contact details, company, job title, and selected host. |
| UR-6.2 | The visitor shall confirm check-in with a single explicit action. |
| UR-6.3 | On success, the visitor shall see a confirmation message that the host has been notified. |
| UR-6.4 | After confirmation, the UI shall clear sensitive fields for the next visitor (phone: manual "Done" or auto-reset after ~30 s; iPad: reset via inactivity or completion flow). |
| UR-6.5 | Each visit shall be tagged with source `qr_self_checkin` (phone) or `ipad_kiosk` (iPad). |

### 4.7 iPad kiosk-specific behaviour

| ID | Requirement |
|----|-------------|
| UR-7.1 | If the visitor is idle during an active check-in step, a warning shall appear after **90 seconds**. |
| UR-7.2 | If idle continues, the form shall reset to the welcome/privacy step after **120 seconds** total from last activity. |
| UR-7.3 | Touch targets and layout shall be usable when standing at the reception desk. |

### 4.8 Host notification

| ID | Requirement |
|----|-------------|
| UR-8.1 | After check-in, the system shall send an email to the selected host's address (as a background task; visitor is not blocked). |
| UR-8.2 | The email shall include visitor name, company, job title, phone, email, and arrival time. |

### 4.9 HubSpot CRM sync

| ID | Requirement |
|----|-------------|
| UR-9.1 | If the visitor provided an email, the system shall create or update a HubSpot Contact after check-in (background task). |
| UR-9.2 | The system shall add a visit Note on the HubSpot contact timeline with visitor details and arrival time. |
| UR-9.3 | If the visitor did not provide an email, HubSpot sync shall not run; the visit is still stored locally. |
| UR-9.4 | If HubSpot is not configured (`HUBSPOT_ACCESS_TOKEN` absent), CRM sync is skipped silently — check-in is unaffected. |

### 4.10 Local data storage

| ID | Requirement |
|----|-------------|
| UR-10.1 | Each visit shall be stored locally with visitor details, host reference, arrival time, and source. |
| UR-10.2 | A health endpoint (`/healthz`) shall be available for basic uptime monitoring. |

---

## 5. Stage 2 — Production MVP requirements

These requirements are required before go-live on production but are **not** needed for the PoC to be validated.

### 5.1 Consent audit trail

| ID | Priority | Requirement |
|----|----------|-------------|
| UR-S2-1.1 | Must | Each successful check-in shall record a consent event: granted flag, consent text version, timestamp, IP address, and user agent. |
| UR-S2-1.2 | Must | When privacy wording changes, operations shall update the consent text version so new check-ins are tied to the new wording. |

### 5.2 Staff directory sync

| ID | Priority | Requirement |
|----|----------|-------------|
| UR-S2-2.1 | Must | IMR staff eligible as hosts shall be synced periodically from Microsoft Graph into the local host directory. |
| UR-S2-2.2 | Must | Sync shall update display name, email, job title, department, and enabled flag. |
| UR-S2-2.3 | Should | IT may trigger a manual sync before go-live if the scheduled job has not yet run. |

### 5.3 HubSpot retry and visibility

| ID | Priority | Requirement |
|----|----------|-------------|
| UR-S2-3.1 | Should | Failed HubSpot sync attempts shall be retryable; status and last error shall be visible in the database for IT support. |
| UR-S2-3.2 | Should | HubSpot data retention follows IMR CRM policy, not automatically purged by this application. |

### 5.4 Administration and data subject rights

| ID | Priority | Requirement |
|----|----------|-------------|
| UR-S2-4.1 | Must | Authorised admins shall list visitors and visits via authenticated API (JWT bearer). |
| UR-S2-4.2 | Must | Admins shall search visitors by name, email, phone, or company. |
| UR-S2-4.3 | Must | Admins shall delete a visitor and all linked visits, consent records, and integration jobs (erasure workflow). |
| UR-S2-4.4 | Must | Deletion shall write an audit event (`visitor.deleted`). |
| UR-S2-4.5 | Should | A full admin web UI is not required; support uses API + SQL per [api.md](api.md). |

### 5.5 Retention and audit

| ID | Priority | Requirement |
|----|----------|-------------|
| UR-S2-5.1 | Must | Visit and consent data shall be deleted after a configurable retention period (default **24 months**). |
| UR-S2-5.2 | Must | Audit events shall be deleted after a configurable period (default **24 months**). |
| UR-S2-5.3 | Must | Each new visit shall create an audit record (`visit.created`) with visitor id, host id, and source. |
| UR-S2-5.4 | Should | HubSpot data retention follows IMR CRM policy, not automatically purged by this application. |

### 5.6 Abuse prevention

| ID | Priority | Requirement |
|----|----------|-------------|
| UR-S2-6.1 | Must | Visitor lookup shall be rate-limited per client IP (default 20 requests per minute). |
| UR-S2-6.2 | Must | Visit submission shall be rate-limited per client IP (default 30 requests per hour). |
| UR-S2-6.3 | Must | Rate-limited clients shall receive HTTP 429 with a clear message. |

### 5.7 iPad operational hardening

| ID | Priority | Requirement |
|----|----------|-------------|
| UR-S2-7.1 | Should | Reception shall lock the iPad with Guided Access (or equivalent) so visitors cannot leave the check-in app — operational procedure, not application code. |

---

## 6. Non-functional requirements

| ID | Stage | Area | Requirement |
|----|-------|------|-------------|
| NFR-1 | PoC | Security | All visitor and API traffic over HTTPS on IMR networks; secrets not in source control. |
| NFR-2 | MVP | Security | Admin endpoints require bearer token; public endpoints do not expose staff emails beyond search UX. |
| NFR-3 | PoC | Privacy | No audio, photos, biometrics, or government ID collected. |
| NFR-4 | PoC | Privacy | Check-in state held in browser memory only (not localStorage). |
| NFR-5 | MVP | Availability | Reception can fall back to manual process if API or worker is down. |
| NFR-6 | PoC | Performance | Host search returns within normal LAN/Wi-Fi latency; submit responds without waiting for email completion. |
| NFR-7 | PoC | Operability | Health endpoint (`/healthz`) for monitoring. |
| NFR-8 | PoC | Compatibility | Phone flow tested on iOS and Android browsers; iPad flow on Safari. |
| NFR-9 | MVP | Maintainability | Automated test battery: pytest, frontend build/typecheck, Playwright E2E per [test-plan.md](test-plan.md). |

---

## 7. User journeys (summary)

### 7.1 First-time visitor (phone)

1. Scan QR at reception → open check-in page.
2. Read privacy notice → Continue.
3. Choose "new visitor" or skip lookup.
4. Enter details → search and select host → review → Check in.
5. See confirmation; host receives email; HubSpot updated if email provided *(Stage 2)*.

### 7.2 Returning visitor (phone)

1. Scan QR → privacy → enter email or phone on lookup step.
2. If one local match → details pre-filled → edit if needed → host → review → submit.
3. Same downstream notifications as first-time.

### 7.3 Visitor at iPad

Same logical steps as phone, with `ipad_kiosk` source, inactivity warning/reset, and no QR.

### 7.4 Reception (no data entry)

- Direct visitors to QR and/or iPad.
- Monitor for outages; escalate to IT using deployment runbooks.
- During pilot, verify sample visits in HubSpot and host inboxes per [integration-testing.md](integration-testing.md) *(Stage 2)*.

### 7.5 Admin / IT support *(Stage 2)*

- Issue admin JWT; query `/admin/visitors` and `/admin/visits`.
- Delete visitor on erasure request.
- Inspect `integration_jobs` for failed HubSpot or email sync.

---

## 8. Out of scope (both stages)

| Item | Notes |
|------|--------|
| Receptionist-led check-in | Visitors self-serve only. |
| HubSpot pre-fill on lookup | Planned; see [plan_hubspot_prefill.md](plan_hubspot_prefill.md). |
| Admin web dashboard | API only; placeholder page. |
| Visitor badge printing | — |
| Multi-language UI | English only. |
| Analytics / reporting dashboard | Use DB, HubSpot, or admin API. |
| Teams chat notifications | Email only. |
| Custom voice assistant / IMR speech capture | Device dictation only. |
| Face recognition / photos | — |
| Native mobile or iPad app | Web only. |
| Real-time production DR / multi-site | Single IMR test/staging deployment model in docs. |

---

## 9. Acceptance criteria

### 9.1 PoC sign-off

PoC is acceptable when, on IMR test infrastructure:

1. **Phase A:** QR check-in completes on iPhone and Android; visit stored in database; host email received.
2. **Phase B:** iPad check-in completes; `source` is `ipad_kiosk`; inactivity reset behaves as specified.
3. **HubSpot:** for a visitor with email, a HubSpot Contact is created/updated and a visit Note appears on the timeline.
4. **HubSpot pre-fill:** a visitor with an existing HubSpot record (but no local record) has their details pre-filled on the lookup step.
5. **Reception smoke test:** a real staff member completes the flow and confirms it is usable.

### 9.2 Production MVP sign-off

MVP is acceptable when, in addition to the PoC criteria:

1. **Privacy:** DPO signs off notice text and consent version.
2. **CRM:** HubSpot Contact and Note created for a test visitor with email, within documented windows.
3. **Directory:** Microsoft Graph sync running on schedule; disabled accounts excluded from search.
4. **Operations:** No blocking failed jobs without owner; IT monitoring query in place.
5. **Automated tests:** CI green (backend, frontends, E2E) on main branch.
6. **Sign-off table** in deployment plan §12 completed by named owners.

---

## 10. Traceability

| User need | Primary implementation | Stage |
|-----------|------------------------|-------|
| Self check-in | `frontend/`, `frontend-ipad/` | PoC |
| Local returning match | `POST /visitors/lookup` | PoC |
| Host search | `GET /hosts` | PoC |
| Host email | `workers/notify.py` | PoC |
| Graph directory sync | `workers/directory_sync.py` | MVP |
| HubSpot sync (post-visit) | `services/hubspot.py` + `integrations/hubspot_client.py` | PoC |
| HubSpot pre-fill (lookup) | `routes/visitors.py` + `integrations/hubspot_client.py` | PoC |
| Consent / privacy audit | `PrivacyStep`, `consent_events` | MVP |
| Erasure | `DELETE /admin/visitors/{id}` | MVP |
| Retention | `workers/retention.py` | MVP |
| Rate limits | SlowAPI on lookup/visits | MVP |

---

## 11. Document history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-05-19 | Initial URSD aligned to shipped MVP (phone + iPad, API, workers, no HubSpot pre-fill, no admin UI). |
| 1.1 | 2026-05-19 | Restructured into Stage 1 (PoC) and Stage 2 (Production MVP). Stage 1 covers the core check-in flow; Stage 2 covers consent audit, CRM, directory sync, retention, erasure, admin API, and automated tests. |
