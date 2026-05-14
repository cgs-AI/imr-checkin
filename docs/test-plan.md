# Test plan

This plan mirrors Section 16 of `plan.md` and lists how each test is
covered by automated tests, manual tests, or staging verification.

## Phase 1: Core check-in form

| Test | Coverage |
|---|---|
| Scan QR code | Manual at reception |
| Complete form on iPhone | Manual on staging |
| Complete form on Android | Manual on staging |
| Use keyboard dictation on iPhone | Manual on staging |
| Use keyboard dictation on Android | Manual on staging |
| Submit a new visitor | `tests/test_checkin_flow.py::test_first_visit_creates_records` |
| Submit a returning visitor | `test_returning_visitor_lookup_by_email` |
| Confirm records in PostgreSQL | Database inspection on staging |
| Confirm form clears after submission | `ConfirmationStep` resets state; verify manually |

## Phase 2: Host directory and email notification

| Test | Coverage |
|---|---|
| Search by first or surname | `test_host_search_min_chars` |
| Search ambiguous host name | Backend returns ranked list; manual UX check |
| Inactive staff hidden | `test_host_search_excludes_disabled` |
| Email sent on submit | Manual: trigger `run_pending_host_emails` after a visit in staging |
| Retry on email failure | `app/workers/notify.py` marks jobs `failed` for re-pickup; verify via admin `integration_jobs` view |

## Phase 3: HubSpot integration

| Test | Coverage |
|---|---|
| HubSpot Contact creation on new email | Staging integration test against HubSpot sandbox |
| HubSpot Contact update on existing email | Same |
| HubSpot Note creation | Same |
| Note associated with Contact | Same — association type id 202 |
| Skip HubSpot when visitor has no email | `test_visit_without_email_skips_hubspot_jobs` |
| Retry on HubSpot failure | Worker retains `failed` status for next run |

## Phase 4: Hardening

| Test | Coverage |
|---|---|
| Rate-limit repeated submissions | `slowapi` is wired into the app middleware; verify with `ab`/`hey` |
| Validate malformed email/phone | Pydantic `EmailStr` and `phonenumbers` normalisation |
| Admin authentication | `test_admin_requires_token`, `test_admin_can_list_visitors` |
| Audit events written | `test_admin_can_delete_visitor` (records `visitor.deleted`); visits emit `visit.created` |
| Retention job behaviour | Manual test by setting `visit_retention_months=0` in a staging env and running `retention_cleanup()` |
| Deletion workflow | `test_admin_can_delete_visitor` |
| No visitor data in browser localStorage | Code review: `frontend/app/checkin/page.tsx` keeps state in React only |
