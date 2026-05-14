"""Retention cleanup job per Section 12."""

from datetime import datetime, timedelta

from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.audit_event import AuditEvent
from app.models.consent_event import ConsentEvent
from app.models.integration_job import IntegrationJob
from app.models.visit import Visit

logger = get_logger(__name__)


async def retention_cleanup(now: datetime | None = None) -> dict[str, int]:
    """Delete visits, consent events, integration jobs, and audit events past retention."""
    settings = get_settings()
    now = now or datetime.utcnow()
    visit_cutoff = now - timedelta(days=settings.visit_retention_months * 30)
    audit_cutoff = now - timedelta(days=settings.audit_retention_months * 30)

    deleted = {"visits": 0, "consent_events": 0, "integration_jobs": 0, "audit_events": 0}

    async with SessionLocal() as session:
        old_visit_ids_stmt = select(Visit.id).where(Visit.arrived_at < visit_cutoff)
        old_visit_ids = [row[0] for row in (await session.execute(old_visit_ids_stmt)).all()]

        if old_visit_ids:
            res = await session.execute(
                delete(IntegrationJob).where(IntegrationJob.visit_id.in_(old_visit_ids))
            )
            deleted["integration_jobs"] = res.rowcount or 0

            res = await session.execute(
                delete(ConsentEvent).where(ConsentEvent.visit_id.in_(old_visit_ids))
            )
            deleted["consent_events"] = res.rowcount or 0

            res = await session.execute(delete(Visit).where(Visit.id.in_(old_visit_ids)))
            deleted["visits"] = res.rowcount or 0

        res = await session.execute(
            delete(AuditEvent).where(AuditEvent.created_at < audit_cutoff)
        )
        deleted["audit_events"] = res.rowcount or 0

        await session.commit()

    logger.info("retention_cleanup.completed", **deleted)
    return deleted
