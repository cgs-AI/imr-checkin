"""Audit event helper."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_event import AuditEvent


async def record_audit(
    session: AsyncSession,
    *,
    actor: str,
    action: str,
    target_type: str,
    target_id: UUID | None = None,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    session.add(event)
    return event
