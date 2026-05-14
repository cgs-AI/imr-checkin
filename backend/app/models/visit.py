"""Visit model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class Visit(SQLModel, table=True):
    __tablename__ = "visits"
    __table_args__ = (
        Index("ix_visits_visitor_id", "visitor_id"),
        Index("ix_visits_host_id", "host_id"),
        Index("ix_visits_arrived_at", "arrived_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    visitor_id: UUID = Field(foreign_key="visitors.id", nullable=False)
    host_id: UUID | None = Field(default=None, foreign_key="hosts.id")
    host_name_raw: str | None = Field(default=None, max_length=200)
    arrived_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    source: str = Field(default="qr_self_checkin", nullable=False, max_length=64)
    hubspot_contact_id: str | None = Field(default=None, max_length=64)
    hubspot_note_id: str | None = Field(default=None, max_length=64)
    hubspot_synced_at: datetime | None = Field(default=None)
    host_notified_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
