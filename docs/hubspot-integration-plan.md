---
name: HubSpot Integration Tests
overview: Add the missing `get_contact_by_email` method to `HubSpotClient` (capability 1 — prefill from HubSpot), write mocked unit/worker tests, and add a gated live-integration test file that runs against a real HubSpot sandbox only when HUBSPOT_ACCESS_TOKEN is explicitly set, with automatic cleanup so no test data is left behind.
todos:
  - id: add-get-contact
    content: Add `get_contact_by_email` method to `backend/app/integrations/hubspot_client.py`
    status: pending
  - id: worker-conftest
    content: Create `backend/tests/workers/conftest.py` with in-memory SQLite engine, session, and model factory fixtures
    status: pending
  - id: client-tests
    content: Write `backend/tests/test_hubspot_client.py` — 7 unit tests for `HubSpotClient` with mocked httpx
    status: pending
  - id: worker-tests
    content: Write `backend/tests/workers/test_hubspot.py` — 8 worker function tests with mocked `HubSpotClient`
    status: pending
  - id: live-tests
    content: Write `backend/tests/test_hubspot_live.py` — gated live tests against a real sandbox, skipped unless HUBSPOT_ACCESS_TOKEN is set
    status: pending
  - id: run-tests
    content: Run `pytest -q` and confirm all tests pass, including existing ones
    status: pending
isProject: false
---

# HubSpot Integration Test Plan

## Context

Two capabilities need to be exercised:

1. **Get details from returning visitors** — fetch an existing HubSpot contact by email to pre-fill the check-in form. `HubSpotClient` currently has only write operations; a `get_contact_by_email` method does not yet exist.
2. **Update/create a visit note** — already implemented (`create_visit_note` in the client, `create_hubspot_note_for_job` in the worker). Worker-level tests are entirely missing (`backend/tests/workers/` is empty on disk).

## Key files

- [`backend/app/integrations/hubspot_client.py`](backend/app/integrations/hubspot_client.py) — `HubSpotClient`; needs `get_contact_by_email`
- [`backend/app/workers/hubspot.py`](backend/app/workers/hubspot.py) — `sync_hubspot_contact_for_job`, `create_hubspot_note_for_job`
- [`backend/tests/conftest.py`](backend/tests/conftest.py) — in-memory SQLite + `AsyncClient` fixtures
- [`backend/tests/test_checkin_flow.py`](backend/tests/test_checkin_flow.py) — covers only that jobs are enqueued, not that HubSpot is called

## What needs to be built

### 1. Add `get_contact_by_email` to `HubSpotClient`

New method in `hubspot_client.py`, reusing the existing search endpoint:

```python
async def get_contact_by_email(
    self, email: str, properties: list[str] | None = None
) -> dict[str, str] | None:
    """Return contact properties dict or None if not found."""
```

- Uses `POST /crm/v3/objects/contacts/search` (same call already used inside `upsert_contact`).
- Requests `firstname`, `lastname`, `phone`, `company`, `jobtitle` by default.
- Returns `None` when `results` is empty (contact not known to HubSpot).
- Returns `None` (logs a warning, does not raise) when not configured, so the app degrades gracefully.

### 2. New test file: `backend/tests/test_hubspot_client.py`

Tests for `HubSpotClient` in isolation. All HTTP is intercepted with `unittest.mock.patch` on `httpx.AsyncClient` — **no real API calls**.

Tests to write:

- `test_not_configured_raises` — `_headers()` raises `RuntimeError` without token
- `test_upsert_contact_creates_when_not_found` — search returns empty → POST `/contacts` called, returned id returned
- `test_upsert_contact_patches_when_found` — search returns existing id → PATCH `/contacts/{id}` called, same id returned
- `test_create_visit_note_posts_with_association` — POST `/notes` with correct `hs_note_body`, `hs_timestamp`, `associations`
- `test_get_contact_by_email_returns_none_when_not_found` — search returns empty list → method returns `None`
- `test_get_contact_by_email_returns_props_when_found` — search returns a contact → method returns properties dict with `firstname`, `company`, etc.
- `test_get_contact_by_email_returns_none_when_unconfigured` — token absent → returns `None`, no exception

### 3. New test file: `backend/tests/workers/test_hubspot.py`

Tests for the two worker functions using in-memory SQLite (same engine fixture as conftest) and a **mocked `HubSpotClient`** via `unittest.mock.AsyncMock`.

Tests for `sync_hubspot_contact_for_job`:

- `test_contact_job_succeeds` — happy path: mock `upsert_contact` returns `"hs-123"`, job → SUCCEEDED, `visit.hubspot_contact_id == "hs-123"`
- `test_contact_job_dead_if_visit_missing` — job references non-existent visit → DEAD
- `test_contact_job_dead_if_no_email` — visitor has no email → DEAD
- `test_contact_job_fails_on_api_error` — `upsert_contact` raises `httpx.HTTPStatusError` → FAILED, `last_error` populated

Tests for `create_hubspot_note_for_job`:

- `test_note_job_stays_pending_without_contact_id` — `visit.hubspot_contact_id` is `None` → stays PENDING (does not call API)
- `test_note_job_succeeds` — happy path: mock `create_visit_note` returns `"note-456"`, job → SUCCEEDED, `visit.hubspot_note_id == "note-456"`
- `test_note_job_dead_if_visit_missing` — job references non-existent visit → DEAD
- `test_note_job_fails_on_api_error` — `create_visit_note` raises → FAILED

### 4. Worker conftest (`backend/tests/workers/conftest.py`)

Shared fixtures for the worker tests:

- `engine` / `session` — in-memory SQLite (reuse same pattern as root conftest)
- `make_visitor` / `make_visit` / `make_job` — lightweight factory helpers to reduce repetition

### 5. New test file: `backend/tests/test_hubspot_live.py` — gated live tests

These tests make **real HTTP calls** to HubSpot. They are skipped in all normal runs and only activate when the environment variable `HUBSPOT_ACCESS_TOKEN` is set. They must clean up after themselves.

**Skip guard (applies to every test in the file):**

```python
pytestmark = pytest.mark.skipif(
    not os.getenv("HUBSPOT_ACCESS_TOKEN"),
    reason="Set HUBSPOT_ACCESS_TOKEN to run live HubSpot tests",
)
```

**Fixture — `live_client`:** instantiates `HubSpotClient` with a `Settings` built from the real env token. Points at the real (or sandbox) `HUBSPOT_BASE_URL`.

**Fixture — `cleanup_contact` (autouse=False, yield):** collects contact ids created during the test and deletes them via `DELETE /crm/v3/objects/contacts/{id}` in the teardown, even if the test fails.

**Tests to write:**

- `test_live_get_contact_not_found` — search for a guaranteed-absent email (`pytest-live-unknown-{uuid}@imr-test.invalid`) → `get_contact_by_email` returns `None`
- `test_live_upsert_creates_contact` — upsert a new test contact with email `pytest-live-{uuid}@imr-test.invalid` → returns an id, contact exists in HubSpot; cleanup deletes it
- `test_live_upsert_patches_existing_contact` — upsert same email twice with different `company` → second call patches; cleanup deletes it
- `test_live_get_contact_returns_props` — upsert then immediately call `get_contact_by_email` → returned properties include the company we set
- `test_live_create_note` — upsert contact, then call `create_visit_note` → returns note id; cleanup deletes contact (note is auto-deleted with contact)

**How to run live tests:**

```bash
# Against production HubSpot — only use a test contact email pattern
HUBSPOT_ACCESS_TOKEN=pat-xx-... pytest backend/tests/test_hubspot_live.py -v

# Against a HubSpot sandbox (recommended)
HUBSPOT_ACCESS_TOKEN=pat-xx-... HUBSPOT_BASE_URL=https://api.hubapi.com \
  pytest backend/tests/test_hubspot_live.py -v
```

## Safety layers — protecting production HubSpot

- **Default pytest run** — `HUBSPOT_ACCESS_TOKEN` is not set → live file is entirely skipped; nothing touches the network
- **Mocked tests** — httpx is patched; no accidental real calls even if token is set
- **Test email namespace** — live tests use `pytest-live-{uuid}@imr-test.invalid`; that domain cannot collide with any real IMR contact
- **Cleanup fixture** — contacts created during live tests are deleted in teardown; no test data accumulates
- **CI** — `HUBSPOT_ACCESS_TOKEN` is not in CI secrets; live tests never run in CI
- **Recommended first-run target** — HubSpot developer sandbox portal (free), not the production IMR CRM, until you are confident the code is correct

## Execution order

```
1. Add `get_contact_by_email` to `hubspot_client.py`
2. Write `backend/tests/workers/conftest.py`
3. Write `backend/tests/test_hubspot_client.py`
4. Write `backend/tests/workers/test_hubspot.py`
5. Write `backend/tests/test_hubspot_live.py`
6. Run `pytest -q` — all existing + new mocked tests pass, live tests skipped
7. Run live tests manually against sandbox with HUBSPOT_ACCESS_TOKEN set
```
