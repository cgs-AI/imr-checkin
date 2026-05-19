"""Visit creation logic."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.visit import Visit


async def create_visit(
    session: AsyncSession,
    *,
    visitor_id: UUID,
    host_id: UUID | None,
    host_name_raw: str | None,
    source: str = "qr_self_checkin",
) -> Visit:
    now = datetime.utcnow()
    visit = Visit(
        visitor_id=visitor_id,
        host_id=host_id,
        host_name_raw=host_name_raw,
        arrived_at=now,
        source=source,
        created_at=now,
    )
    session.add(visit)
    await session.flush()
    return visit
