"""Host model — synced from Microsoft Graph staff directory."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class Host(SQLModel, table=True):
    __tablename__ = "hosts"
    __table_args__ = (
        Index("ix_hosts_display_name", "display_name"),
        Index("ix_hosts_email", "email", unique=True),
        Index("ix_hosts_graph_user_id", "graph_user_id"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    display_name: str = Field(nullable=False, max_length=200)
    email: str = Field(nullable=False, max_length=320)
    job_title: str | None = Field(default=None, max_length=200)
    department: str | None = Field(default=None, max_length=200)
    graph_user_id: str | None = Field(default=None, max_length=128)
    account_enabled: bool = Field(default=True, nullable=False)
    last_synced_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
