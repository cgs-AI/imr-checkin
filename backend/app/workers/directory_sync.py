"""Sync staff directory from Microsoft Graph into the local hosts table."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.integrations.graph_client import GraphClient
from app.models.host import Host

logger = get_logger(__name__)


async def sync_staff_directory() -> int:
    """Pull staff from Graph and upsert into the local hosts table.

    Returns the number of rows touched.
    """
    client = GraphClient()
    touched = 0
    now = datetime.utcnow()

    async with SessionLocal() as session:
        async for user in client.iter_users():
            email = user.get("mail") or user.get("userPrincipalName")
            if not email:
                continue
            display_name = user.get("displayName") or email
            graph_user_id = user.get("id")
            job_title = user.get("jobTitle")
            department = user.get("department")
            account_enabled = bool(user.get("accountEnabled", True))

            result = await session.execute(select(Host).where(Host.email == email))
            host = result.scalars().first()
            if host is None:
                host = Host(
                    id=uuid4(),
                    display_name=display_name,
                    email=email,
                    job_title=job_title,
                    department=department,
                    graph_user_id=graph_user_id,
                    account_enabled=account_enabled,
                    last_synced_at=now,
                )
                session.add(host)
            else:
                host.display_name = display_name
                host.job_title = job_title
                host.department = department
                host.graph_user_id = graph_user_id
                host.account_enabled = account_enabled
                host.last_synced_at = now

            touched += 1

        await session.commit()
    logger.info("directory_sync.completed", touched=touched)
    return touched
