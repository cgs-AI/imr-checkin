# IMR visitor self check-in — backend

FastAPI service for the visitor check-in flow. Provides:

- Visitor and visit storage (PostgreSQL via SQLModel + Alembic)
- Public check-in endpoints: `/checkin/config`, `/visitors/lookup`, `/hosts`, `/visits`
- Host notification email via Microsoft Graph (sent as a background task after each check-in)

This is the **PoC backend**. No workers, no queues, no Redis required.

## Local development

```bash
cd backend
uv venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
cp .env.example .env                   # edit with your values
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Tests

```bash
pytest
```

Uses an in-memory SQLite database. No external services needed.

## Configuration

Key environment variables (see `.env.example` for the full list):

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL DSN |
| `GRAPH_TENANT_ID` | Microsoft 365 tenant — required for host email |
| `GRAPH_CLIENT_ID` | App registration client ID |
| `GRAPH_CLIENT_SECRET` | App registration client secret |
| `GRAPH_SENDER_UPN` | Mailbox used to send notifications (e.g. `reception@imr.ie`) |
| `SITE_NAME` | Site name shown in the UI |
| `PRIVACY_TEXT` | Full privacy notice text |

When Graph credentials are not configured the backend starts normally and skips email with a warning log.

## Seeding hosts

The PoC does not sync the staff directory from Microsoft 365. Add hosts directly:

```python
# run from the backend/ directory with the venv active
import asyncio
from uuid import uuid4
from app.core.database import SessionLocal
from app.models.host import Host

async def seed():
    async with SessionLocal() as session:
        session.add(Host(
            id=uuid4(),
            display_name="Jane Doe",
            email="jane.doe@imr.ie",
            job_title="Engineer",
            department="AI Lab",
            account_enabled=True,
        ))
        await session.commit()

asyncio.run(seed())
```
