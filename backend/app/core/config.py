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

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:3001",
        ]
    )

    privacy_text: str = (
        "IMR will collect the details you submit in this form to manage your visit, "
        "notify your IMR host, and keep a record of your visit. "
        "You may use your phone's own dictation feature to fill in the form. "
        "IMR does not receive or store audio. IMR only receives the text you submit. "
        "By continuing, you confirm that the information you provide is accurate and "
        "that you understand how it will be used."
    )

    site_name: str = "Irish Manufacturing Research"

    graph_tenant_id: str | None = None
    graph_client_id: str | None = None
    graph_client_secret: str | None = None
    graph_sender_upn: str = "reception@imr.ie"

    host_search_min_chars: int = 2
    host_search_limit: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
