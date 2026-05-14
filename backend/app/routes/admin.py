"""Admin endpoints: visitor and visit lookup, deletion."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import require_admin
from app.models.audit_event import AuditEvent  # noqa: F401  for migration awareness
from app.models.consent_event import ConsentEvent
from app.models.integration_job import IntegrationJob
from app.models.visit import Visit
from app.models.visitor import Visitor
from app.services.audit import record_audit
from app.services.schemas import AdminVisitRow, AdminVisitorRow

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/visitors", response_model=list[AdminVisitorRow])
async def list_visitors(
    q: str | None = Query(default=None, max_length=200),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[AdminVisitorRow]:
    stmt = select(Visitor).order_by(Visitor.created_at.desc()).limit(limit).offset(offset)
    if q:
        needle = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                Visitor.email.ilike(needle),
                Visitor.full_name.ilike(needle),
                Visitor.phone.ilike(needle),
                Visitor.company.ilike(needle),
            )
        )
    result = await session.execute(stmt)
    return [AdminVisitorRow.model_validate(v) for v in result.scalars().all()]


@router.get("/visits", response_model=list[AdminVisitRow])
async def list_visits(
    visitor_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[AdminVisitRow]:
    stmt = select(Visit).order_by(Visit.arrived_at.desc()).limit(limit).offset(offset)
    if visitor_id is not None:
        stmt = stmt.where(Visit.visitor_id == visitor_id)
    result = await session.execute(stmt)
    return [AdminVisitRow.model_validate(v) for v in result.scalars().all()]


@router.delete("/visitors/{visitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visitor(
    visitor_id: UUID,
    admin_subject: str = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    visitor = await session.get(Visitor, visitor_id)
    if visitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")

    visits_result = await session.execute(select(Visit).where(Visit.visitor_id == visitor_id))
    visit_ids = [v.id for v in visits_result.scalars().all()]

    if visit_ids:
        jobs_stmt = select(IntegrationJob).where(IntegrationJob.visit_id.in_(visit_ids))
        for job in (await session.execute(jobs_stmt)).scalars().all():
            await session.delete(job)

        consents_stmt = select(ConsentEvent).where(ConsentEvent.visit_id.in_(visit_ids))
        for consent in (await session.execute(consents_stmt)).scalars().all():
            await session.delete(consent)

        for visit in (await session.execute(select(Visit).where(Visit.id.in_(visit_ids)))).scalars().all():
            await session.delete(visit)

    consents_stmt = select(ConsentEvent).where(ConsentEvent.visitor_id == visitor_id)
    for consent in (await session.execute(consents_stmt)).scalars().all():
        await session.delete(consent)

    await session.delete(visitor)

    await record_audit(
        session,
        actor=admin_subject,
        action="visitor.deleted",
        target_type="visitor",
        target_id=visitor_id,
        details={"visit_count": len(visit_ids)},
    )

    await session.commit()
