"""Public check-in form configuration endpoint."""

from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.services.schemas import CheckinConfig

router = APIRouter(prefix="/checkin", tags=["checkin"])


@router.get("/config", response_model=CheckinConfig)
async def checkin_config(settings: Settings = Depends(get_settings)) -> CheckinConfig:
    return CheckinConfig(
        site_name=settings.site_name,
        privacy_text=settings.privacy_text,
        consent_text_version=settings.consent_text_version,
        host_search_min_chars=settings.host_search_min_chars,
    )
