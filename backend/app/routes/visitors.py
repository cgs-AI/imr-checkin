"""Returning visitor lookup endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.integrations.hubspot_client import HubSpotClient
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

    if match:
        return VisitorLookupResponse(
            match=VisitorSummary.model_validate(match),
            matched_by=matched_by,
            ambiguous=ambiguous,
        )

    # No local record — try HubSpot by email as a fallback
    if payload.email:
        props = await HubSpotClient().get_contact_by_email(str(payload.email))
        if props:
            name_parts = [
                props.get("firstname", ""),
                props.get("lastname", ""),
            ]
            full_name = " ".join(p for p in name_parts if p).strip()
            if full_name:
                from uuid import uuid4
                stub = VisitorSummary(
                    id=uuid4(),
                    full_name=full_name,
                    email=str(payload.email),
                    phone=props.get("phone"),
                    company=props.get("company"),
                    job_title=props.get("jobtitle"),
                )
                return VisitorLookupResponse(
                    match=stub,
                    matched_by="hubspot",
                    hubspot_prefilled=True,
                )

    return VisitorLookupResponse(match=None, matched_by=None, ambiguous=ambiguous)
