"""Host autocomplete endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.models.host import Host
from app.services.schemas import HostSummary

router = APIRouter(prefix="/hosts", tags=["hosts"])


@router.get("", response_model=list[HostSummary])
async def search_hosts(
    q: str = Query(..., min_length=1, max_length=80),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> list[HostSummary]:
    query = q.strip()
    if len(query) < settings.host_search_min_chars:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query must be at least {settings.host_search_min_chars} characters",
        )

    like = f"%{query.lower()}%"
    stmt = (
        select(Host)
        .where(Host.account_enabled.is_(True))
        .where(func.lower(Host.display_name).like(like))
        .order_by(Host.display_name)
        .limit(settings.host_search_limit)
    )
    result = await session.execute(stmt)
    hosts = result.scalars().all()
    return [HostSummary.model_validate(h) for h in hosts]
