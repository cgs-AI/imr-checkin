"""HubSpot Contact and Note sync workers."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.integrations.hubspot_client import HubSpotClient
from app.models.host import Host
from app.models.integration_job import IntegrationJob, JobStatus, JobType
from app.models.visit import Visit
from app.models.visitor import Visitor

logger = get_logger(__name__)

NOTE_TEMPLATE = """IMR visitor check-in

Visitor: {visitor_name}
Company: {company}
Job title: {job_title}
Host: {host_name}
Arrival time: {arrival_time}
Source: IMR visitor self check-in form
"""


def _fmt(value: str | None) -> str:
    return value if value else "(not provided)"


async def sync_hubspot_contact_for_job(session: AsyncSession, job: IntegrationJob) -> None:
    visit = await session.get(Visit, job.visit_id)
    if visit is None:
        job.status = JobStatus.DEAD.value
        job.last_error = "Visit missing"
        job.updated_at = datetime.utcnow()
        return
    visitor = await session.get(Visitor, visit.visitor_id)
    if visitor is None or not visitor.email:
        job.status = JobStatus.DEAD.value
        job.last_error = "Visitor or email missing"
        job.updated_at = datetime.utcnow()
        return

    job.status = JobStatus.IN_PROGRESS.value
    job.attempt_count += 1
    job.updated_at = datetime.utcnow()

    parts = (visitor.full_name or "").strip().split(" ", 1)
    firstname = parts[0] if parts else ""
    lastname = parts[1] if len(parts) > 1 else ""

    properties = {
        "firstname": firstname,
        "lastname": lastname,
        "phone": visitor.phone,
        "company": visitor.company,
        "jobtitle": visitor.job_title,
    }

    try:
        contact_id = await HubSpotClient().upsert_contact(
            email=visitor.email,
            properties=properties,
        )
    except Exception as exc:  # noqa: BLE001
        job.status = JobStatus.FAILED.value
        job.last_error = str(exc)[:2000]
        job.updated_at = datetime.utcnow()
        logger.warning("hubspot_contact.failed", visit_id=str(visit.id), error=str(exc))
        return

    visit.hubspot_contact_id = contact_id
    visit.hubspot_synced_at = datetime.utcnow()
    job.status = JobStatus.SUCCEEDED.value
    job.last_error = None
    job.updated_at = datetime.utcnow()
    logger.info("hubspot_contact.synced", visit_id=str(visit.id), contact_id=contact_id)


async def create_hubspot_note_for_job(session: AsyncSession, job: IntegrationJob) -> None:
    visit = await session.get(Visit, job.visit_id)
    if visit is None:
        job.status = JobStatus.DEAD.value
        job.last_error = "Visit missing"
        job.updated_at = datetime.utcnow()
        return
    if not visit.hubspot_contact_id:
        job.status = JobStatus.PENDING.value
        job.last_error = "Awaiting hubspot_contact sync"
        job.updated_at = datetime.utcnow()
        return

    visitor = await session.get(Visitor, visit.visitor_id)
    host = await session.get(Host, visit.host_id) if visit.host_id else None
    if visitor is None:
        job.status = JobStatus.DEAD.value
        job.last_error = "Visitor missing"
        job.updated_at = datetime.utcnow()
        return

    job.status = JobStatus.IN_PROGRESS.value
    job.attempt_count += 1
    job.updated_at = datetime.utcnow()

    body = NOTE_TEMPLATE.format(
        visitor_name=visitor.full_name,
        company=_fmt(visitor.company),
        job_title=_fmt(visitor.job_title),
        host_name=host.display_name if host else _fmt(visit.host_name_raw),
        arrival_time=visit.arrived_at.strftime("%d %b %Y, %H:%M"),
    )

    try:
        note_id = await HubSpotClient().create_visit_note(
            contact_id=visit.hubspot_contact_id,
            body_text=body,
            timestamp=visit.arrived_at,
        )
    except Exception as exc:  # noqa: BLE001
        job.status = JobStatus.FAILED.value
        job.last_error = str(exc)[:2000]
        job.updated_at = datetime.utcnow()
        logger.warning("hubspot_note.failed", visit_id=str(visit.id), error=str(exc))
        return

    visit.hubspot_note_id = note_id
    job.status = JobStatus.SUCCEEDED.value
    job.last_error = None
    job.updated_at = datetime.utcnow()
    logger.info("hubspot_note.created", visit_id=str(visit.id), note_id=note_id)


async def run_pending_hubspot_jobs(max_jobs: int = 20) -> int:
    """Pick up pending HubSpot jobs (contacts first, then notes)."""
    from app.core.database import SessionLocal

    processed = 0
    async with SessionLocal() as session:
        contact_stmt = (
            select(IntegrationJob)
            .where(IntegrationJob.job_type == JobType.HUBSPOT_CONTACT.value)
            .where(IntegrationJob.status.in_([JobStatus.PENDING.value, JobStatus.FAILED.value]))
            .limit(max_jobs)
        )
        for job in (await session.execute(contact_stmt)).scalars().all():
            await sync_hubspot_contact_for_job(session, job)
            processed += 1

        note_stmt = (
            select(IntegrationJob)
            .where(IntegrationJob.job_type == JobType.HUBSPOT_NOTE.value)
            .where(IntegrationJob.status.in_([JobStatus.PENDING.value, JobStatus.FAILED.value]))
            .limit(max_jobs)
        )
        for job in (await session.execute(note_stmt)).scalars().all():
            await create_hubspot_note_for_job(session, job)
            processed += 1

        await session.commit()
    return processed
