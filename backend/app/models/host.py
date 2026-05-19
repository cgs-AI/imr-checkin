"""Host model — manually seeded staff directory."""

from uuid import UUID, uuid4

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class Host(SQLModel, table=True):
    __tablename__ = "hosts"
    __table_args__ = (
        Index("ix_hosts_display_name", "display_name"),
        Index("ix_hosts_email", "email", unique=True),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    display_name: str = Field(nullable=False, max_length=200)
    email: str = Field(nullable=False, max_length=320)
    job_title: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=200)
    account_enabled: bool = Field(default=True, nullable=False)
