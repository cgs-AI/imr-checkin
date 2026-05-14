"""Returning visitor lookup endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.schemas import VisitorLookupRequest, VisitorLookupResponse, VisitorSummary
from app.services.visitor_service import lookup_visitor

router = APIRouter(prefix="/visitors", tags=["visitors"])


@router.post("/lookup", response_model=VisitorLookupResponse)
async def lookup(
    payload: VisitorLookupRequest,
    session: AsyncSession = Depends(get_session),
) -> VisitorLookupResponse:
    if not payload.email and not payload.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email or phone is required",
        )

    match, matched_by, ambiguous = await lookup_visitor(
        session,
        email=payload.email,
        phone=payload.phone,
    )

    return VisitorLookupResponse(
        match=VisitorSummary.model_validate(match) if match else None,
        matched_by=matched_by,
        ambiguous=ambiguous,
    )
