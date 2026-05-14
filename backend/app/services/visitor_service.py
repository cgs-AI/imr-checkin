"""Visitor lookup and creation logic."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.visitor import Visitor
from app.services.phone import normalise_phone
from app.services.schemas import VisitorPayload


async def lookup_visitor(
    session: AsyncSession,
    *,
    email: str | None,
    phone: str | None,
) -> tuple[Visitor | None, str | None, bool]:
    """Return (match, matched_by, ambiguous) for a returning-visitor lookup."""
    if email:
        normalised_email = email.strip().lower()
        result = await session.execute(
            select(Visitor).where(Visitor.email == normalised_email)
        )
        match = result.scalars().first()
        if match:
            return match, "email", False

    normalised_phone = normalise_phone(phone)
    if normalised_phone:
        result = await session.execute(
            select(Visitor).where(Visitor.phone == normalised_phone)
        )
        matches = result.scalars().all()
        if len(matches) == 1:
            return matches[0], "phone", False
        if len(matches) > 1:
            return None, "phone", True

    return None, None, False


async def upsert_visitor(
    session: AsyncSession,
    *,
    payload: VisitorPayload,
    existing_visitor_id: UUID | None = None,
) -> Visitor:
    """Create or update a Visitor row from the submitted payload."""
    now = datetime.utcnow()
    email = payload.email.lower() if payload.email else None
    phone = normalise_phone(payload.phone)

    visitor: Visitor | None = None
    if existing_visitor_id:
        visitor = await session.get(Visitor, existing_visitor_id)

    if visitor is None and email:
        result = await session.execute(select(Visitor).where(Visitor.email == email))
        visitor = result.scalars().first()

    if visitor is None:
        visitor = Visitor(
            full_name=payload.full_name,
            email=email,
            phone=phone,
            company=payload.company,
            job_title=payload.job_title,
            created_at=now,
            updated_at=now,
        )
        session.add(visitor)
    else:
        visitor.full_name = payload.full_name
        if email:
            visitor.email = email
        if phone:
            visitor.phone = phone
        if payload.company:
            visitor.company = payload.company
        if payload.job_title:
            visitor.job_title = payload.job_title
        visitor.updated_at = now

    await session.flush()
    return visitor
