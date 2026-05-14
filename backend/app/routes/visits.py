"""Visit creation endpoint."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.consent_event import ConsentEvent
from app.models.host import Host
from app.services.audit import record_audit
from app.services.schemas import CreateVisitRequest, CreateVisitResponse
from app.services.visit_service import create_visit, queue_post_visit_jobs
from app.services.visitor_service import upsert_visitor

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("", response_model=CreateVisitResponse, status_code=status.HTTP_201_CREATED)
async def submit_visit(
    payload: CreateVisitRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> CreateVisitResponse:
    if not payload.consent.granted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent must be granted before check-in",
        )

    host: Host | None = None
    if payload.host_id is not None:
        host = await session.get(Host, payload.host_id)
        if host is None or not host.account_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected host is not available",
            )

    visitor = await upsert_visitor(
        session,
        payload=payload.visitor,
        existing_visitor_id=payload.existing_visitor_id,
    )

    visit = await create_visit(
        session,
        visitor_id=visitor.id,
        host_id=host.id if host else None,
        host_name_raw=payload.host_name_raw,
        source=payload.source,
    )

    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")[:512]

    consent = ConsentEvent(
        visitor_id=visitor.id,
        visit_id=visit.id,
        consent_type=payload.consent.consent_type,
        granted=payload.consent.granted,
        consent_text_version=payload.consent.consent_text_version,
        captured_at=datetime.utcnow(),
        ip_address=client_host,
        user_agent=user_agent or None,
    )
    session.add(consent)

    await queue_post_visit_jobs(
        session,
        visit=visit,
        visitor_has_email=visitor.email is not None,
        host=host,
    )

    await record_audit(
        session,
        actor="visitor_self_service",
        action="visit.created",
        target_type="visit",
        target_id=visit.id,
        details={
            "visitor_id": str(visitor.id),
            "host_id": str(host.id) if host else None,
            "source": visit.source,
        },
    )

    await session.commit()

    return CreateVisitResponse(
        visit_id=visit.id,
        visitor_id=visitor.id,
        arrived_at=visit.arrived_at,
        confirmation_message="Check-in complete. Your IMR host has been notified.",
    )
