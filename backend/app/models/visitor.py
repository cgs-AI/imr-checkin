"""Visitor model."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class Visitor(SQLModel, table=True):
    __tablename__ = "visitors"
    __table_args__ = (
        Index("ix_visitors_email", "email"),
        Index("ix_visitors_phone", "phone"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    full_name: str = Field(nullable=False, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=64)
    company: str | None = Field(default=None, max_length=200)
    job_title: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
