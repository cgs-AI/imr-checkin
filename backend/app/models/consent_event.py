"""Consent event model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ConsentEvent(SQLModel, table=True):
    __tablename__ = "consent_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    visitor_id: UUID | None = Field(default=None, foreign_key="visitors.id")
    visit_id: UUID | None = Field(default=None, foreign_key="visits.id")
    consent_type: str = Field(nullable=False, max_length=64)
    granted: bool = Field(nullable=False)
    consent_text_version: str = Field(nullable=False, max_length=64)
    captured_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    ip_address: str | None = Field(default=None, max_length=64)
    user_agent: str | None = Field(default=None, max_length=512)
