"""Audit event model."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, Index
from sqlmodel import Field, SQLModel


class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_created_at", "created_at"),
        Index("ix_audit_events_target_type_target_id", "target_type", "target_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    actor: str = Field(nullable=False, max_length=200)
    action: str = Field(nullable=False, max_length=128)
    target_type: str = Field(nullable=False, max_length=64)
    target_id: UUID | None = Field(default=None)
    details: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
