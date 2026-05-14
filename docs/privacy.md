# Privacy notice (visitor self check-in)

This document captures the working text shown to visitors when they begin
the self check-in flow. The final wording must be approved by IMR's DPO
before go-live.

## Notice shown on screen

> IMR will collect the details you submit in this form to manage your
> visit, notify your IMR host, and keep a record of your visit.
>
> You may use your phone's own dictation feature to fill in the form.
> IMR does not receive or store audio. IMR only receives the text you
> submit.
>
> Your visit details may be stored in IMR systems, including HubSpot and
> Microsoft 365, for visitor management and relationship history.
>
> By continuing, you confirm that the information you provide is
> accurate and that you understand how it will be used.

The current text version identifier is recorded in
`Settings.consent_text_version` (default `2026-05-01`). Whenever the
wording changes the identifier must change. Every check-in records the
text version in `consent_events.consent_text_version` so that historical
consent can be tied back to the exact wording that was shown.

## What IMR collects

- Full name
- Email
- Phone
- Company
- Job title
- Selected IMR host
- Arrival timestamp
- Consent event (granted / not granted, text version, IP, user agent)

## What IMR does not collect

- Audio
- Visitor photos
- Face embeddings
- Government ID
- Location beyond the IMR site

## Retention

Default retention (configurable):

- Visit and consent records: 24 months
- Audit events: 24 months
- HubSpot data: governed by IMR's CRM retention policy

Retention cleanup is implemented in `app/workers/retention.py` and runs
on the `arq` cron schedule.

## Right to erasure

Admin users can delete a visitor (and all linked visits, consent events
and integration jobs) via `DELETE /admin/visitors/{id}`. The action is
recorded as an audit event with the admin's subject identifier.
