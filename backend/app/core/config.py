"""Application configuration loaded from environment."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://imr:imr@localhost:5432/imr_checkin"

    redis_url: str = "redis://localhost:6379/0"

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    consent_text_version: str = "2026-05-01"
    privacy_text: str = (
        "IMR will collect the details you submit in this form to manage your visit, "
        "notify your IMR host, and keep a record of your visit. "
        "You may use your phone's own dictation feature to fill in the form. "
        "IMR does not receive or store audio. IMR only receives the text you submit. "
        "Your visit details may be stored in IMR systems, including HubSpot and "
        "Microsoft 365, for visitor management and relationship history. "
        "By continuing, you confirm that the information you provide is accurate and "
        "that you understand how it will be used."
    )

    site_name: str = "Irish Manufacturing Research"
    reception_email: str = "reception@imr.ie"

    graph_tenant_id: str | None = None
    graph_client_id: str | None = None
    graph_client_secret: str | None = None
    graph_sender_upn: str = "reception@imr.ie"

    hubspot_access_token: str | None = None
    hubspot_base_url: str = "https://api.hubapi.com"

    admin_jwt_secret: str = "change-me-in-production"
    admin_jwt_algorithm: str = "HS256"
    admin_jwt_expiry_minutes: int = 60

    visit_retention_months: int = 24
    audit_retention_months: int = 24

    host_search_min_chars: int = 2
    host_search_limit: int = 10

    rate_limit_lookup_per_minute: int = 20
    rate_limit_visits_per_hour: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
