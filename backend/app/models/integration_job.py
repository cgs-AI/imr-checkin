"""Integration job tracking."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class JobType(str, Enum):
    HOST_EMAIL = "host_email"
    HUBSPOT_CONTACT = "hubspot_contact"
    HUBSPOT_NOTE = "hubspot_note"


class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD = "dead"


class IntegrationJob(SQLModel, table=True):
    __tablename__ = "integration_jobs"
    __table_args__ = (
        Index("ix_integration_jobs_visit_id", "visit_id"),
        Index("ix_integration_jobs_status", "status"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    visit_id: UUID = Field(foreign_key="visits.id", nullable=False)
    job_type: str = Field(nullable=False, max_length=64)
    status: str = Field(default=JobStatus.PENDING.value, nullable=False, max_length=32)
    attempt_count: int = Field(default=0, nullable=False)
    last_error: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
