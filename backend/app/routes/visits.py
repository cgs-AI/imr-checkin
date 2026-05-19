"""Visit creation endpoint."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.host import Host
from app.services.hubspot import sync_visit_to_hubspot
from app.services.notify import send_host_notification
from app.services.schemas import CreateVisitRequest, CreateVisitResponse
from app.services.visit_service import create_visit
from app.services.visitor_service import upsert_visitor

router = APIRouter(prefix="/visits", tags=["visits"])


@router.post("", response_model=CreateVisitResponse, status_code=status.HTTP_201_CREATED)
async def submit_visit(
    payload: CreateVisitRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> CreateVisitResponse:
    if not payload.consent_granted:
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

    await session.commit()

    if host is not None:
        background_tasks.add_task(send_host_notification, visitor, host, visit)

    if visitor.email:
        background_tasks.add_task(sync_visit_to_hubspot, visitor, visit)

    return CreateVisitResponse(
        visit_id=visit.id,
        visitor_id=visitor.id,
        arrived_at=visit.arrived_at,
        confirmation_message="Check-in complete. Your IMR host has been notified.",
    )
