# IMR Visitor Check-In Kiosk Lite — MVP Plan

## 1. Context

IMR currently captures visitor details manually at reception. This creates repeated data entry, weak visit history, and no automatic link to HubSpot or host notification.

This revised MVP uses a dedicated iPad at reception. The visitor completes the check-in process directly on the iPad. The application is served from a local IMR server.

The visitor may type or use the iPad's built-in keyboard dictation to fill in form fields. IMR does not build or operate a custom voice recognition system.

The MVP deliberately avoids the complex parts of the original kiosk concept:

- No OpenAI API key.
- No OpenAI Realtime.
- No custom voice assistant.
- No custom speech recognition.
- No face recognition.
- No biometric data processing.
- No Teams messaging dependency.
- No QR-code flow.
- No receptionist-led data entry.

The goal is to prove the core visitor workflow first:

1. Visitor self check-in on a controlled IMR device.
2. Returning visitor lookup by email or phone.
3. Host selection from IMR staff directory.
4. Host notification by email.
5. HubSpot Contact create or update.
6. HubSpot Note creation for each visit.
7. Local visit history in IMR's database.

---

## 2. MVP goal

The MVP will provide a self-service visitor check-in kiosk on an iPad at IMR reception.

The iPad will open a secure web application hosted on an IMR-controlled server. Visitors will fill in a guided form using typing or the iPad's built-in keyboard dictation.

Once submitted, the system will store the visit, notify the selected IMR host by email, and update HubSpot by creating or updating the Contact and adding a Note for the visit.

---

## 3. MVP scope

### In scope

- Dedicated reception iPad.
- Local or IMR-hosted web application.
- iPad browser-based check-in form.
- Guided Access kiosk lockdown.
- Visitor self-service check-in.
- Typing and iPad-native keyboard dictation.
- Returning visitor lookup by email or phone.
- Host search and autocomplete from synced IMR staff directory.
- Local PostgreSQL database for visitors and visits.
- Email notification to the selected IMR host.
- HubSpot Contact create or update.
- HubSpot Note creation for each visit.
- Auto-reset after submission or inactivity.
- Basic admin tools for lookup, failed syncs, deletion, and support.
- Basic audit trail.
- Privacy notice and consent capture.
- Retention policy implementation.

### Out of scope

- QR-code check-in.
- OpenAI Realtime.
- OpenAI API keys.
- Custom voice assistant.
- Custom browser speech recognition.
- Face recognition.
- Face embeddings.
- Visitor photos.
- Teams 1:1 chat messages.
- Native iPad app.
- Badge printing.
- Analytics dashboard.
- Multi-language support.

---

## 4. User journey

### First-time visitor

1. Visitor arrives at reception.
2. Visitor sees the iPad check-in screen.
3. Visitor taps Start check-in.
4. Visitor reads the privacy notice.
5. Visitor enters:
   - Full name
   - Email
   - Phone
   - Company
   - Job title
   - IMR host
6. Visitor may type or use the iPad keyboard microphone.
7. Host autocomplete helps the visitor select the correct IMR host.
8. Visitor reviews the details.
9. Visitor submits.
10. System confirms check-in.
11. Host receives an email notification.
12. HubSpot Contact is created or updated.
13. HubSpot Note is added to the Contact timeline.
14. The iPad clears the session and returns to the welcome screen.

### Returning visitor

1. Visitor taps Start check-in.
2. Visitor enters email or phone.
3. System searches the local visitor database.
4. If a clear match is found, known fields are pre-filled.
5. Visitor confirms or edits the details.
6. Visitor selects today's IMR host.
7. Visitor submits.
8. System creates a new visit record and updates HubSpot history.

---

## 5. Architecture overview

```text
Reception iPad
  |
  | IMR Wi-Fi or LAN
  | HTTPS
  v
Local IMR server
  |
  |-- Frontend web app
  |-- FastAPI backend
  |-- PostgreSQL
  |-- Microsoft Graph staff directory sync
  |-- Microsoft Graph sendMail
  |-- HubSpot Contacts API
  |-- HubSpot Notes API
```

### Removed from architecture

```text
OpenAI Realtime
OpenAI API key
WebRTC audio flow
Custom speech recognition
Visitor phone QR flow
Face recognition
InsightFace
pgvector
Teams chat messaging
```

---

## 6. iPad setup

### Recommended setup for MVP

- One dedicated iPad at reception.
- Safari or browser shortcut opened directly to the check-in page.
- Guided Access enabled to keep the iPad on the check-in app.
- iPad connected to IMR Wi-Fi.
- Charger permanently connected or available.
- Physical stand at reception.
- Passcode known only to reception or IT.

### Guided Access

Guided Access should be used for the MVP to keep the iPad locked to the check-in app.

Recommended settings:

- Disable Home button exit without passcode.
- Disable app switching.
- Disable unnecessary hardware buttons.
- Keep keyboard available.
- Keep touch enabled.
- Set auto-lock policy appropriate for reception.
- Test recovery process if the app freezes.

### Production option

For longer-term deployment, IMR may use Mobile Device Management to control:

- Wi-Fi configuration.
- Browser homepage.
- App restrictions.
- Automatic updates.
- Remote wipe.
- Device compliance.

MDM is not required for the MVP if Guided Access is acceptable.

---

## 7. Network and hosting

### Hosting option

The app should run on an IMR-controlled server.

Possible options:

1. On-prem VM.
2. Small local server.
3. Internal Kubernetes or container platform if available.
4. Approved IMR cloud environment if IT prefers it.

For this MVP, the simplest option is an on-prem VM or small server running:

- Frontend.
- FastAPI backend.
- PostgreSQL.
- Background worker.
- Reverse proxy.

### HTTPS requirement

Use HTTPS even on the local network.

Avoid:

```text
http://192.168.1.20:3000
```

Prefer:

```text
https://visitor-checkin.imr.local
```

or:

```text
https://visitors.imr.ie/checkin
```

The iPad must trust the certificate.

This avoids browser security issues and keeps the setup close to production.

### Offline behaviour

The MVP should not attempt complex offline sync.

If the server is unavailable, the iPad should show:

```text
Check-in is temporarily unavailable. Please contact reception.
```

---

## 8. Frontend

### Technology

- React or Next.js.
- Browser-based web app.
- Touch-first iPad layout.
- No PWA requirement for MVP.
- No native iPad app requirement.

### Core screens

1. Welcome
   - IMR visitor check-in.
   - Start check-in button.

2. Privacy notice
   - Explains what IMR collects.
   - Explains that the visitor may use iPad dictation.
   - Clarifies that IMR receives only submitted text, not audio.

3. Lookup
   - Email field.
   - Phone field.
   - Used to find returning visitors.

4. Visitor details
   - Full name.
   - Email.
   - Phone.
   - Company.
   - Job title.

5. Host selection
   - Search box.
   - Autocomplete suggestions from IMR staff directory.
   - Display name and department if available.
   - Do not expose unnecessary staff data.

6. Review
   - Shows all captured details.
   - Visitor can edit before submission.

7. Confirmation
   - Suggested text: Check-in complete. Your IMR host has been notified.

8. Error state
   - Used for network, validation, or server errors.
   - Clear instruction to contact reception.

### Voice-friendly form design

The MVP does not implement speech recognition. It supports the iPad's own dictation by using normal input fields.

Recommended input attributes:

```html
<input type="text" autocomplete="name" />
<input type="email" inputmode="email" autocomplete="email" />
<input type="tel" inputmode="tel" autocomplete="tel" />
<input type="text" autocomplete="organization" />
<input type="text" autocomplete="organization-title" />
```

Helper text:

```text
You can type or use the iPad keyboard microphone.
```

### UX principles

- One task per screen.
- Large touch targets.
- Clear labels.
- Minimal text.
- Clear edit option before submit.
- No staff email exposure unless required.
- No visitor data stored in browser local storage.
- Auto-reset after submission.
- Auto-reset after inactivity.

### Inactivity timeout

Suggested behaviour:

- After 90 seconds of inactivity, show a warning.
- After 120 seconds of inactivity, clear the form and return to the welcome screen.

---

## 9. Backend

### Technology

- Python.
- FastAPI.
- PostgreSQL.
- SQLAlchemy or SQLModel.
- Alembic for migrations.
- Background jobs using `arq`, RQ, or Celery.
- Reverse proxy using Nginx or Caddy.

### API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /checkin/config` | Returns public configuration for the check-in app |
| `POST /visitors/lookup` | Finds a returning visitor by email or phone |
| `GET /hosts?q=...` | Searches synced IMR staff directory |
| `POST /visits` | Creates visitor and visit records |
| `GET /admin/visitors` | Admin visitor lookup |
| `GET /admin/visits` | Admin visit lookup |
| `POST /admin/integration-jobs/{id}/retry` | Retry failed HubSpot or email job |
| `DELETE /admin/visitors/{id}` | Delete visitor data where legally appropriate |

### Background jobs

| Job | Purpose |
|---|---|
| `sync_staff_directory` | Pulls IMR users from Microsoft Graph |
| `send_host_email` | Sends host notification email |
| `sync_hubspot_contact` | Creates or updates HubSpot Contact |
| `create_hubspot_visit_note` | Adds one Note to the HubSpot Contact timeline |
| `retention_cleanup` | Deletes or anonymises records according to retention policy |

---

## 10. HubSpot integration

HubSpot should be updated in two steps.

### Step 1: Contact create or update

Use email as the main identifier.

Update stable Contact fields only:

```text
firstname
lastname
email
phone
company
jobtitle
```

If email is missing, the MVP should store the visit locally and skip automatic HubSpot sync.

### Step 2: Create a Note for the visit

Each check-in creates one HubSpot Note associated with the Contact.

Example Note body:

```text
IMR visitor check-in

Visitor: Carlos Garcia
Company: Irish Manufacturing Research
Job title: Head of AI Strategy
Host: Jane Doe
Arrival time: 14 May 2026, 10:32
Source: IMR reception iPad check-in
```

This gives HubSpot a clear visit history without changing the HubSpot schema.

### Why Notes rather than Contact description

Do not append visit history into the Contact description field.

HubSpot Notes are better because:

- Each visit becomes a separate timeline event.
- The Contact record stays readable.
- The history is easier to audit.
- No custom HubSpot schema is required.
- The system avoids creating one long unstructured text field.

---

## 11. Microsoft Graph integration

### Staff directory sync

A scheduled job pulls IMR staff users from Microsoft Graph into a local `hosts` table.

Recommended local fields:

```text
display_name
email
job_title
department
user_principal_name
account_enabled
last_synced_at
```

Only active staff should appear in host search.

### Host notification email

When a visit is submitted, the backend sends an email to the selected host.

Email sender:

```text
reception@imr.ie
```

Suggested subject:

```text
Your visitor {visitor_name} from {company} has arrived
```

Suggested body:

```text
{visitor_name} has checked in at IMR.

Company: {company}
Job title: {job_title}
Phone: {phone}
Email: {email}
Arrival time: {arrival_time}

This notification was sent by the IMR visitor check-in kiosk.
```

### Teams messages

Teams 1:1 chat messages are out of scope for the MVP.

They may be added later using a Teams bot, Power Automate, or an IT-approved Microsoft Graph approach.

---

## 12. Data model

### visitors

```text
id uuid primary key
full_name text not null
email text nullable
phone text nullable
company text nullable
job_title text nullable
created_at timestamptz not null
updated_at timestamptz not null
```

### visits

```text
id uuid primary key
visitor_id uuid references visitors(id)
host_id uuid references hosts(id)
host_name_raw text nullable
arrived_at timestamptz not null
source text not null default 'ipad_kiosk'
hubspot_contact_id text nullable
hubspot_note_id text nullable
hubspot_synced_at timestamptz nullable
host_notified_at timestamptz nullable
created_at timestamptz not null
```

### hosts

```text
id uuid primary key
display_name text not null
email text not null
job_title text nullable
department text nullable
graph_user_id text nullable
account_enabled boolean not null
last_synced_at timestamptz not null
```

### consent_events

```text
id uuid primary key
visitor_id uuid nullable
visit_id uuid nullable
consent_type text not null
granted boolean not null
consent_text_version text not null
captured_at timestamptz not null
ip_address inet nullable
user_agent text nullable
```

### integration_jobs

```text
id uuid primary key
visit_id uuid references visits(id)
job_type text not null
status text not null
attempt_count int not null default 0
last_error text nullable
created_at timestamptz not null
updated_at timestamptz not null
```

### audit_events

```text
id uuid primary key
actor text not null
action text not null
target_type text not null
target_id uuid nullable
details jsonb nullable
created_at timestamptz not null
```

---

## 13. Matching logic

### Returning visitor lookup

Primary lookup:

```text
email
```

Secondary lookup:

```text
phone
```

Rules:

1. If email matches exactly, pre-fill visitor details.
2. If phone matches exactly and there is only one result, pre-fill visitor details.
3. If phone matches multiple records, do not auto-select.
4. If there is no match, create a new visitor.
5. If a visitor updates their email or phone, keep an audit record.

### Duplicate handling

The MVP should not try to solve all duplicate cases automatically.

Admin users should be able to review and merge records later if needed.

---

## 14. Privacy and consent

### Privacy notice text

Suggested MVP wording:

```text
IMR will collect the details you submit in this form to manage your visit, notify your IMR host, and keep a record of your visit.

You may use the iPad's built-in dictation feature to fill in the form. IMR does not receive or store audio. IMR only receives the text you submit.

Your visit details may be stored in IMR systems, including HubSpot and Microsoft 365, for visitor management and relationship history.

By continuing, you confirm that the information you provide is accurate and that you understand how it will be used.
```

### Data minimisation

The MVP collects only:

- Name.
- Email.
- Phone.
- Company.
- Job title.
- IMR host.
- Visit timestamp.
- Consent event.
- Browser metadata needed for security and audit.

The MVP does not collect:

- Audio.
- Face images.
- Face embeddings.
- Government ID.
- Location beyond the selected IMR site.
- Visitor photo.

### Shared-device privacy controls

Because the iPad is shared, the app must:

- Clear all form data after submission.
- Clear all form data after inactivity.
- Avoid browser local storage for visitor data.
- Disable browser autofill where it may expose previous visitor data.
- Avoid saving form values in browser history.
- Avoid showing previous visitor suggestions from the browser.
- Keep returning visitor lookup server-side only.

Recommended form attributes:

```html
<form autocomplete="off">
```

For fields where browser autocomplete creates privacy risk on the shared iPad, set:

```html
autocomplete="off"
```

### Retention

Proposed starting policy:

- Local visit records: 24 months.
- HubSpot Contact data: retained according to IMR CRM policy.
- HubSpot Notes: retained according to IMR CRM policy.
- Audit logs: 24 months.
- Consent events: same period as visit record or as required by IMR policy.

The final policy must be confirmed with IMR's DPO before go-live.

---

## 15. Security controls

### Kiosk controls

Required controls:

- HTTPS only.
- Trusted certificate on the iPad.
- Guided Access enabled.
- Admin pages inaccessible from kiosk flow.
- Kiosk route limited to check-in workflow.
- Auto-reset after inactivity.
- No visitor data stored in browser local storage.
- No sensitive data in URLs.
- Form state cleared on submit.
- Form state cleared on timeout.

### Server controls

Required controls:

- Server-side validation.
- Rate limiting.
- CSRF protection where relevant.
- Strict CORS policy.
- Bot protection if exposed beyond IMR network.
- No public staff directory dump.
- Host search only after 2 or 3 characters.
- Limit host search results.
- Audit log for admin actions.
- Secure secret storage.
- Separate admin authentication.

### Admin controls

Admin pages must require authentication.

Admin actions should be audited:

- Visitor lookup.
- Visitor deletion.
- Visit deletion.
- Failed sync replay.
- Export request.
- Manual correction.
- Staff directory sync trigger.

---

## 16. Repository layout

```text
imr-visitor-kiosk/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ routes/
│  │  │  ├─ checkin.py
│  │  │  ├─ visitors.py
│  │  │  ├─ visits.py
│  │  │  ├─ hosts.py
│  │  │  └─ admin.py
│  │  ├─ models/
│  │  ├─ workers/
│  │  │  ├─ directory_sync.py
│  │  │  ├─ hubspot.py
│  │  │  ├─ notify.py
│  │  │  └─ retention.py
│  │  ├─ integrations/
│  │  │  ├─ graph_client.py
│  │  │  └─ hubspot_client.py
│  │  └─ services/
│  ├─ alembic/
│  ├─ tests/
│  └─ pyproject.toml
├─ frontend/
│  ├─ app/
│  │  ├─ checkin/
│  │  ├─ admin/
│  │  └─ components/
│  ├─ package.json
│  └─ README.md
└─ docs/
   ├─ plan-ipad-local-kiosk.md
   ├─ privacy.md
   ├─ deployment.md
   ├─ ipad-setup.md
   └─ test-plan.md
```

---

## 17. Phasing

### Phase 0: Foundations

Target: prepare the project for implementation.

Deliverables:

- Confirm iPad device.
- Confirm iPad stand and charging approach.
- Confirm hosting approach.
- Confirm domain name.
- Confirm certificate approach.
- Create repository.
- Set up backend skeleton.
- Set up frontend skeleton.
- Set up PostgreSQL.
- Draft privacy notice.
- Confirm HubSpot private app access.
- Confirm Microsoft Graph permissions.
- Confirm email sender mailbox.

Exit criteria:

- App can be deployed to a test environment.
- iPad can access the app over HTTPS.
- Database migrations run.
- Secrets are stored securely.
- Privacy text has an owner for approval.

### Phase 1: Core iPad check-in form

Target: capture visits locally.

Deliverables:

- iPad-friendly check-in page.
- Welcome screen.
- Privacy notice.
- Visitor lookup by email or phone.
- Visitor record creation.
- Visit record creation.
- Review and submit screen.
- Confirmation screen.
- Auto-reset after submission.
- Auto-reset after inactivity.
- Basic validation.
- Basic admin visitor lookup.

Exit criteria:

- A visitor can complete check-in on the iPad.
- A visit appears in the local database.
- A returning visitor can be pre-filled.
- The app clears visitor data after submission and timeout.

### Phase 2: Host directory and email notification

Target: notify the right IMR host.

Deliverables:

- Microsoft Graph staff directory sync.
- Local `hosts` table.
- Host autocomplete.
- Host email notification.
- Notification status tracking.
- Retry handling for failed email sends.

Exit criteria:

- Visitor can select a host.
- Host receives email after check-in.
- Failed notifications are visible to admin.

### Phase 3: HubSpot integration

Target: update CRM history.

Deliverables:

- HubSpot Contact create or update by email.
- HubSpot Note creation per visit.
- Association between Note and Contact.
- Local sync status fields.
- Retry handling.
- Admin view of failed HubSpot syncs.

Exit criteria:

- A submitted visit creates or updates a HubSpot Contact.
- A visit Note appears on the Contact timeline.
- Failed syncs can be retried.

### Phase 4: Kiosk hardening and go-live

Target: prepare for operational use.

Deliverables:

- Guided Access setup.
- iPad recovery procedure.
- HTTPS certificate validated on iPad.
- Rate limiting.
- Input validation hardening.
- Audit logging.
- Retention cleanup job.
- Admin deletion workflow.
- Error pages.
- Monitoring and logs.
- User acceptance testing.
- DPO sign-off.
- Go-live checklist.

Exit criteria:

- Privacy and retention approved.
- Core workflow tested.
- Admin can support failed cases.
- Kiosk can recover from common failure modes.
- System is ready for reception use.

---

## 18. Verification plan

### Phase 1 tests

- Open check-in app on iPad.
- Complete the form using touch keyboard.
- Complete at least one field using iPad dictation.
- Submit a new visitor.
- Submit a returning visitor.
- Confirm records in PostgreSQL.
- Confirm form clears after submission.
- Confirm form clears after inactivity timeout.
- Confirm browser back button does not expose previous visitor details.

### Phase 2 tests

- Search for host by first name.
- Search for host by surname.
- Search for ambiguous host name.
- Confirm inactive staff do not appear.
- Submit visit and confirm host receives email.
- Simulate email failure and confirm retry behaviour.

### Phase 3 tests

- Submit visitor with new email and confirm HubSpot Contact creation.
- Submit visitor with existing email and confirm Contact update.
- Confirm HubSpot Note creation.
- Confirm Note is associated with the Contact.
- Submit visitor without email and confirm HubSpot sync is skipped.
- Simulate HubSpot failure and confirm retry behaviour.

### Phase 4 tests

- Enable Guided Access and confirm kiosk cannot exit without passcode.
- Restart iPad and recover kiosk.
- Disconnect Wi-Fi and confirm clear error message.
- Reconnect Wi-Fi and confirm recovery.
- Validate malformed emails and phone numbers.
- Confirm admin authentication.
- Confirm audit events are written.
- Confirm retention job behaviour in test mode.
- Confirm deletion workflow.
- Confirm no visitor data is stored in browser local storage.

---

## 19. Open items

- Exact iPad model.
- iPad stand and physical location.
- Charging and cable management.
- Wi-Fi network to use.
- Final domain name.
- Certificate approach.
- Hosting location.
- HubSpot private app owner.
- Microsoft Graph permission approval.
- Email sender mailbox.
- Staff directory fields available from Graph.
- Retention period.
- DPO review owner.
- Admin users.
- Whether the app should be accessible only from IMR network.
- Whether a fallback paper process remains during pilot.

---

## 20. Success criteria

The MVP is successful if:

1. Visitors can self check-in on the iPad.
2. Reception does not need to enter visitor details.
3. Returning visitors do not need to re-enter all details.
4. The IMR host receives an email notification.
5. HubSpot shows the visitor as a Contact.
6. Each visit appears as a HubSpot Note.
7. IMR has a local visit history.
8. The system avoids OpenAI, custom speech recognition, face recognition, QR-code dependency, and Teams messaging complexity.
9. The iPad resets safely between visitors.
10. The workflow is simple enough to operate at reception without technical support.
