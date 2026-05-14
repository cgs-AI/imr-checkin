"""Send host notification emails for completed visits."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations.graph_client import GraphClient
from app.models.host import Host
from app.models.integration_job import IntegrationJob, JobStatus, JobType
from app.models.visit import Visit
from app.models.visitor import Visitor

logger = get_logger(__name__)

SUBJECT_TEMPLATE = "Your visitor {visitor_name} from {company} has arrived"

BODY_TEMPLATE = """{visitor_name} has checked in at IMR.

Company: {company}
Job title: {job_title}
Phone: {phone}
Email: {email}
Arrival time: {arrival_time}

This notification was sent by the IMR visitor self check-in system.
"""


def _format(value: str | None) -> str:
    return value if value else "(not provided)"


async def send_host_email_for_job(session: AsyncSession, job: IntegrationJob) -> None:
    """Process one host-email job. Updates job status in place; caller commits."""
    visit = await session.get(Visit, job.visit_id)
    if visit is None or visit.host_id is None:
        job.status = JobStatus.DEAD.value
        job.last_error = "Visit or host missing"
        job.updated_at = datetime.utcnow()
        return

    host = await session.get(Host, visit.host_id)
    visitor = await session.get(Visitor, visit.visitor_id)
    if host is None or visitor is None:
        job.status = JobStatus.DEAD.value
        job.last_error = "Host or visitor missing"
        job.updated_at = datetime.utcnow()
        return

    subject = SUBJECT_TEMPLATE.format(
        visitor_name=visitor.full_name,
        company=_format(visitor.company),
    )
    body = BODY_TEMPLATE.format(
        visitor_name=visitor.full_name,
        company=_format(visitor.company),
        job_title=_format(visitor.job_title),
        phone=_format(visitor.phone),
        email=_format(visitor.email),
        arrival_time=visit.arrived_at.strftime("%d %b %Y, %H:%M"),
    )

    job.status = JobStatus.IN_PROGRESS.value
    job.attempt_count += 1
    job.updated_at = datetime.utcnow()

    try:
        await GraphClient().send_mail(
            to_email=host.email,
            subject=subject,
            body_text=body,
        )
    except Exception as exc:  # noqa: BLE001
        job.status = JobStatus.FAILED.value
        job.last_error = str(exc)[:2000]
        job.updated_at = datetime.utcnow()
        logger.warning("host_email.failed", visit_id=str(visit.id), error=str(exc))
        return

    visit.host_notified_at = datetime.utcnow()
    job.status = JobStatus.SUCCEEDED.value
    job.last_error = None
    job.updated_at = datetime.utcnow()
    logger.info("host_email.sent", visit_id=str(visit.id), host_email=host.email)


async def run_pending_host_emails(max_jobs: int = 20) -> int:
    """Pick up pending HOST_EMAIL jobs and process them."""
    settings = get_settings()  # noqa: F841  reserved for future per-tenant routing
    processed = 0
    from app.core.database import SessionLocal

    async with SessionLocal() as session:
        stmt = (
            select(IntegrationJob)
            .where(IntegrationJob.job_type == JobType.HOST_EMAIL.value)
            .where(IntegrationJob.status.in_([JobStatus.PENDING.value, JobStatus.FAILED.value]))
            .limit(max_jobs)
        )
        jobs = (await session.execute(stmt)).scalars().all()
        for job in jobs:
            await send_host_email_for_job(session, job)
            processed += 1
        await session.commit()
    return processed
