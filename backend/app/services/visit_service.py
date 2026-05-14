"""Visit creation logic and integration-job enqueueing."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.host import Host
from app.models.integration_job import IntegrationJob, JobStatus, JobType
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


async def queue_post_visit_jobs(
    session: AsyncSession,
    *,
    visit: Visit,
    visitor_has_email: bool,
    host: Host | None,
) -> list[IntegrationJob]:
    """Insert pending integration_jobs rows for downstream workers to pick up."""
    now = datetime.utcnow()
    jobs: list[IntegrationJob] = []

    if host is not None:
        jobs.append(
            IntegrationJob(
                visit_id=visit.id,
                job_type=JobType.HOST_EMAIL.value,
                status=JobStatus.PENDING.value,
                created_at=now,
                updated_at=now,
            )
        )

    if visitor_has_email:
        jobs.append(
            IntegrationJob(
                visit_id=visit.id,
                job_type=JobType.HUBSPOT_CONTACT.value,
                status=JobStatus.PENDING.value,
                created_at=now,
                updated_at=now,
            )
        )
        jobs.append(
            IntegrationJob(
                visit_id=visit.id,
                job_type=JobType.HUBSPOT_NOTE.value,
                status=JobStatus.PENDING.value,
                created_at=now,
                updated_at=now,
            )
        )

    for job in jobs:
        session.add(job)

    return jobs
