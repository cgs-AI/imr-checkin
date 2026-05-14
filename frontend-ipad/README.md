# IMR visitor self check-in — iPad kiosk frontend

iPad-at-reception variant of the visitor check-in flow described in
`docs/plan-ipad-local-kiosk.md`. Each visit submitted from this app is tagged
`source = "ipad_kiosk"`.

The phone/QR variant lives at `../frontend/` and runs on port 3000 so both
versions can run side-by-side against the same backend. See
`../docs/running-both-frontends.md`.

## Differences from the phone version

- Home page copy is kiosk-style (no "use this form on your own phone").
- Large-touch styling: bigger fonts, taller buttons and inputs.
- Privacy notice uses the wording from `docs/plan-ipad-local-kiosk.md` §14
  (mentions iPad dictation and that IMR does not receive audio).
- Inactivity guard: warning modal at 90 s, full form reset at 120 s.
- Confirmation screen auto-resets after 8 s (vs 30 s on the phone app).
- Helper text reads "the iPad keyboard microphone" instead of phone.

## Development

```bash
npm install
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

Runs on `http://localhost:3001`. Make sure the backend's CORS allows that
origin (set `BACKEND_ALLOWED_ORIGINS` to include `http://localhost:3001` if
you tighten CORS).

## Screens

The check-in flow at `/checkin` walks through:

1. Welcome (home page)
2. Privacy notice
3. Returning-visitor lookup
4. Visitor details (name, email, phone, company, job title)
5. Host selection with autocomplete
6. Review
7. Confirmation

The MVP does not implement speech recognition. The form sets `autocomplete`
and `inputmode` attributes that work well with the iPad's native keyboard
dictation. No visitor data is stored in browser localStorage; the page clears
state after submission, after 8 seconds on the confirmation screen, or after
120 seconds of inactivity inside the check-in flow.
