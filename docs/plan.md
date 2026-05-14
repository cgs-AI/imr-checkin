# IMR Visitor Self Check-In Register — MVP Plan

## 1. Context

IMR currently captures visitor details manually at reception. This creates repeated data entry, weak visit history, and no automatic link to HubSpot or host notification.

The revised MVP is a **self-service visitor check-in web form** accessed by QR code from the visitor’s own phone.

Visitors fill in the form themselves. They may type or use their phone’s built-in keyboard dictation.

The MVP deliberately removes the complex parts of the earlier kiosk concept:

- No iPad kiosk.
- No OpenAI API key.
- No custom voice assistant.
- No custom speech recognition.
- No face recognition.
- No Teams messaging dependency.
- No receptionist-led data entry.

The goal is to prove the core operational workflow first:

1. Capture visitor details.
2. Identify returning visitors by email or phone.
3. Notify the IMR host by email.
4. Create or update the visitor Contact in HubSpot.
5. Add a visit Note to the Contact timeline in HubSpot.
6. Keep a local visit record in IMR's database.

---

## 2. MVP goal

The MVP will provide a self-service visitor check-in flow accessed through a QR code at IMR reception.

The visitor uses their own phone to fill in a guided mobile form. The form supports standard phone keyboard dictation, but IMR does not capture or process audio.

Once submitted, the system stores the visit, notifies the selected IMR host by email, and updates HubSpot by creating or updating the Contact and adding a Note for the visit.

---

## 3. MVP scope

### In scope

- QR-code entry point.
- Mobile-first web form.
- Visitor self-service check-in.
- Typing and phone-native dictation through the visitor's own keyboard.
- Returning visitor lookup by email or phone.
- Host search and autocomplete from synced IMR staff directory.
- Local PostgreSQL database for visitors and visits.
- Email notification to the selected IMR host.
- HubSpot Contact create or update.
- HubSpot Note creation for each visit.
- Basic admin tools for lookup, deletion, and support.
- Basic audit trail.
- Privacy notice and consent capture.
- Retention policy implementation.

### Out of scope

- iPad kiosk mode.
- Visitor face recognition.
- Biometric data processing.
- OpenAI Realtime.
- OpenAI API keys.
- Custom voice assistant.
- Custom browser speech recognition.
- Teams 1:1 chat messages.
- Receptionist-entered check-in.
- Analytics dashboard.
- Multi-language support.
- Full visitor badge printing.

---

## 4. User journey

### First-time visitor

1. Visitor sees a QR code at reception.
2. Visitor scans the QR code with their own phone.
3. Web form opens.
4. Visitor reads the privacy notice.
5. Visitor fills in:
   - Full name
   - Email
   - Phone
   - Company
   - Job title
   - IMR host
6. Visitor can type or use their phone keyboard dictation.
7. Host autocomplete helps the visitor select the correct IMR host.
8. Visitor reviews the details.
9. Visitor submits.
10. System confirms check-in.
11. Host receives an email notification.
12. HubSpot Contact is created or updated.
13. HubSpot Note is added to the Contact timeline.

### Returning visitor

1. Visitor scans QR code.
2. Visitor enters email or phone.
3. System finds a possible existing visitor.
4. Form pre-fills known details.
5. Visitor confirms or edits the details.
6. Visitor selects today's IMR host.
7. Visitor submits.
8. System creates a new visit record and updates HubSpot history.

---

## 5. Architecture overview

```text
Visitor phone browser
  |
  | HTTPS
  v
FastAPI backend
  |
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
iPad kiosk
Face recognition
InsightFace
pgvector
Teams chat messaging
```

---

## 6. Frontend

### Technology

- React or Next.js.
- Mobile-first responsive design.
- Accessible from the visitor's phone browser.
- No installation required.
- No PWA requirement for MVP.

### Core screens

1. **Welcome**
   - IMR visitor check-in.
   - Continue button.

2. **Privacy notice**
   - Explains what IMR collects.
   - Explains that the visitor may use their own phone's dictation.
   - Clarifies that IMR receives only submitted text, not audio.

3. **Lookup**
   - Email field.
   - Phone field.
   - Used to find returning visitors.

4. **Visitor details**
   - Full name.
   - Email.
   - Phone.
   - Company.
   - Job title.

5. **Host selection**
   - Search box.
   - Autocomplete suggestions from IMR staff directory.
   - Display name and department if available.
   - Do not expose unnecessary staff data.

6. **Review**
   - Shows all captured details.
   - Visitor can edit before submission.

7. **Confirmation**
   - Simple confirmation.
   - Suggested text: "Check-in complete. Your IMR host has been notified."

### Voice-friendly form design

The MVP does not implement speech recognition. It supports the visitor's own phone dictation by using normal input fields.

Recommended input attributes:

```html
<input type="text" autocomplete="name" />
<input type="email" inputmode="email" autocomplete="email" />
<input type="tel" inputmode="tel" autocomplete="tel" />
<input type="text" autocomplete="organization" />
<input type="text" autocomplete="organization-title" />
```

Add helper text:

```text
You can type or use your phone keyboard microphone.
```

### UX principles

- One task per screen.
- Large touch targets.
- Clear labels.
- No long paragraphs.
- Avoid staff email exposure.
- Clear edit option before submit.
- Auto-reset sensitive data after completion or timeout.

---

## 7. Backend

### Technology

- Python.
- FastAPI.
- PostgreSQL.
- SQLAlchemy or SQLModel.
- Alembic for migrations.
- Background jobs using `arq`, RQ, or Celery.
- Deployed on-prem or approved IMR hosting.

### API endpoints

| Endpoint | Purpose |
|---|---|
| `GET /checkin/config` | Returns public configuration for the check-in form |
| `POST /visitors/lookup` | Finds a returning visitor by email or phone |
| `GET /hosts?q=...` | Searches synced IMR staff directory |
| `POST /visits` | Creates visitor and visit records |
| `GET /admin/visitors` | Admin visitor lookup |
| `GET /admin/visits` | Admin visit lookup |
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

## 8. HubSpot integration

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
Source: IMR visitor self check-in form
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

## 9. Microsoft Graph integration

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

This notification was sent by the IMR visitor self check-in system.
```

### Teams messages

Teams 1:1 chat messages are out of scope for the MVP.

They may be added later using a Teams bot, Power Automate, or an IT-approved Microsoft Graph approach.

---

## 10. Data model

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
source text not null default 'qr_self_checkin'
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

## 11. Matching logic

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

## 12. Privacy and consent

### Privacy notice text

Suggested MVP wording:

```text
IMR will collect the details you submit in this form to manage your visit, notify your IMR host, and keep a record of your visit.

You may use your phone's own dictation feature to fill in the form. IMR does not receive or store audio. IMR only receives the text you submit.

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

### Retention

Proposed starting policy:

- Local visit records: 24 months.
- HubSpot Contact data: retained according to IMR CRM policy.
- HubSpot Notes: retained according to IMR CRM policy.
- Audit logs: 24 months.
- Consent events: same period as visit record or as required by IMR policy.

The final policy must be confirmed with IMR's DPO before go-live.

---

## 13. Security controls

### Public form controls

The check-in form is internet-accessible or guest-network-accessible, so it needs basic abuse protection.

Required controls:

- HTTPS only.
- Rate limiting by IP and device fingerprint.
- Server-side validation.
- CSRF protection where relevant.
- Bot protection or simple invisible challenge.
- No public staff directory dump.
- Host search only after 2 or 3 characters.
- Limit host search results.
- Daily rotating QR token if needed.
- No sensitive data in URLs.
- No visitor data stored in browser local storage.
- Auto-clear form state after submission.

### Admin controls

Admin pages must require authentication.

Admin actions should be audited:

- Visitor lookup.
- Visitor deletion.
- Visit deletion.
- Failed sync replay.
- Export request.
- Manual correction.

---

## 14. Repository layout

```text
imr-visitor-checkin/
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
   ├─ plan.md
   ├─ privacy.md
   ├─ deployment.md
   └─ test-plan.md
```

---

## 15. Phasing

### Phase 0: Foundations

Target: prepare the project for implementation.

Deliverables:

- Confirm hosting approach.
- Confirm domain name.
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
- Database migrations run.
- Secrets are stored securely.
- Privacy text has an owner for approval.

### Phase 1: Core check-in form

Target: capture visits locally.

Deliverables:

- QR check-in URL.
- Mobile-first form.
- Visitor lookup by email or phone.
- Visitor record creation.
- Visit record creation.
- Review and submit screen.
- Confirmation screen.
- Basic validation.
- Basic admin visitor lookup.

Exit criteria:

- A visitor can complete check-in from their phone.
- A visit appears in the local database.
- A returning visitor can be pre-filled.

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

### Phase 4: Hardening and go-live

Target: prepare for operational use.

Deliverables:

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
- System is ready for reception use.

---

## 16. Verification plan

### Phase 1 tests

- Scan QR code.
- Complete the form on iPhone.
- Complete the form on Android.
- Use keyboard dictation on iPhone.
- Use keyboard dictation on Android.
- Submit a new visitor.
- Submit a returning visitor.
- Confirm records in PostgreSQL.
- Confirm form clears after submission.

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

- Rate-limit repeated submissions.
- Validate malformed emails and phone numbers.
- Confirm admin authentication.
- Confirm audit events are written.
- Confirm retention job behaviour in test mode.
- Confirm deletion workflow.
- Confirm no visitor data is stored in browser local storage.

---

## 17. Open items

- Final domain name.
- Hosting location.
- HubSpot private app owner.
- Microsoft Graph permission approval.
- Email sender mailbox.
- Staff directory fields available from Graph.
- Retention period.
- DPO review owner.
- Admin users.
- Whether QR code should include a rotating token.
- Whether form should be available only on IMR guest Wi-Fi or publicly.

---

## 18. Success criteria

The MVP is successful if:

1. Visitors can self check-in from their own phone.
2. Reception does not need to enter visitor details.
3. Returning visitors do not need to re-enter all details.
4. The IMR host receives an email notification.
5. HubSpot shows the visitor as a Contact.
6. Each visit appears as a HubSpot Note.
7. IMR has a local visit history.
8. The system avoids OpenAI, iPad kiosk setup, face recognition, and Teams messaging complexity.
9. The workflow is simple enough to operate without technical support at reception.
