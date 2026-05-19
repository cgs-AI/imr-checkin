"""Fire-and-forget HubSpot contact sync after a completed visit."""

from app.core.logging import get_logger
from app.integrations.hubspot_client import HubSpotClient
from app.models.visit import Visit
from app.models.visitor import Visitor

logger = get_logger(__name__)

_NOTE_TEMPLATE = """Visitor check-in at IMR

Name: {full_name}
Company: {company}
Job title: {job_title}
Phone: {phone}
Arrival: {arrived_at}
Source: {source}
"""


def _fmt(value: str | None) -> str:
    return value if value else "(not provided)"


async def sync_visit_to_hubspot(visitor: Visitor, visit: Visit) -> None:
    """Upsert the HubSpot contact and add a visit note.

    Logs and swallows errors so the check-in response is never blocked.
    Skips silently when HUBSPOT_ACCESS_TOKEN is not configured.
    """
    if not visitor.email:
        return

    client = HubSpotClient()
    if not client._configured():
        return

    try:
        contact_id = await client.upsert_contact(
            email=visitor.email,
            full_name=visitor.full_name,
            company=visitor.company,
            job_title=visitor.job_title,
            phone=visitor.phone,
        )
        logger.info("hubspot.contact_synced", visit_id=str(visit.id), contact_id=contact_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("hubspot.contact_sync_failed", visit_id=str(visit.id), error=str(exc))
        return

    note_body = _NOTE_TEMPLATE.format(
        full_name=visitor.full_name,
        company=_fmt(visitor.company),
        job_title=_fmt(visitor.job_title),
        phone=_fmt(visitor.phone),
        arrived_at=visit.arrived_at.strftime("%d %b %Y, %H:%M"),
        source=visit.source,
    )
    try:
        note_id = await client.create_visit_note(
            contact_id=contact_id,
            body=note_body,
            timestamp=visit.arrived_at,
        )
        logger.info("hubspot.note_created", visit_id=str(visit.id), note_id=note_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("hubspot.note_failed", visit_id=str(visit.id), error=str(exc))
