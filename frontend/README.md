# IMR visitor self check-in — frontend

Mobile-first Next.js app for the visitor self check-in flow described in
`docs/plan.md`.

## Development

```bash
npm install
NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev
```

The app expects the backend FastAPI service to be reachable at
`NEXT_PUBLIC_API_BASE`. CORS is configured on the backend to allow
`http://localhost:3000` by default.

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
and `inputmode` attributes that work well with each phone's native keyboard
dictation. No visitor data is stored in browser localStorage; the page
clears state after submission or after 30 seconds on the confirmation
screen.
