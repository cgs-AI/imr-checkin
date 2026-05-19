"""Fire-and-forget host notification email."""

from datetime import datetime

from app.core.logging import get_logger
from app.integrations.graph_client import GraphClient
from app.models.host import Host
from app.models.visit import Visit
from app.models.visitor import Visitor

logger = get_logger(__name__)

_SUBJECT = "Your visitor {visitor_name} from {company} has arrived"

_BODY = """{visitor_name} has checked in at IMR.

Company: {company}
Job title: {job_title}
Phone: {phone}
Email: {email}
Arrival time: {arrival_time}

This notification was sent by the IMR visitor self check-in system.
"""


def _fmt(value: str | None) -> str:
    return value if value else "(not provided)"


async def send_host_notification(visitor: Visitor, host: Host, visit: Visit) -> None:
    """Send a notification email to the host. Logs and swallows errors so the
    check-in response is never blocked by email delivery."""
    subject = _SUBJECT.format(
        visitor_name=visitor.full_name,
        company=_fmt(visitor.company),
    )
    body = _BODY.format(
        visitor_name=visitor.full_name,
        company=_fmt(visitor.company),
        job_title=_fmt(visitor.job_title),
        phone=_fmt(visitor.phone),
        email=_fmt(visitor.email),
        arrival_time=visit.arrived_at.strftime("%d %b %Y, %H:%M"),
    )
    try:
        await GraphClient().send_mail(
            to_email=host.email,
            subject=subject,
            body_text=body,
        )
        logger.info("host_notification.sent", visit_id=str(visit.id), host=host.email)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "host_notification.failed",
            visit_id=str(visit.id),
            host=host.email,
            error=str(exc),
        )
