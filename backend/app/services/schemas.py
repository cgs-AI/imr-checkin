"""Pydantic request and response schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

VisitSource = Literal["qr_self_checkin", "ipad_kiosk"]


class CheckinConfig(BaseModel):
    site_name: str
    privacy_text: str
    consent_text_version: str
    host_search_min_chars: int


class VisitorLookupRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)


class VisitorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str | None
    phone: str | None
    company: str | None
    job_title: str | None


class VisitorLookupResponse(BaseModel):
    match: VisitorSummary | None
    matched_by: str | None = None
    ambiguous: bool = False


class HostSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    department: str | None = None


class VisitorPayload(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    company: str | None = Field(default=None, max_length=200)
    job_title: str | None = Field(default=None, max_length=200)


class ConsentPayload(BaseModel):
    granted: bool
    consent_text_version: str
    consent_type: str = "visitor_checkin"


class CreateVisitRequest(BaseModel):
    visitor: VisitorPayload
    host_id: UUID | None = None
    host_name_raw: str | None = Field(default=None, max_length=200)
    consent: ConsentPayload
    existing_visitor_id: UUID | None = None
    source: VisitSource = "qr_self_checkin"


class CreateVisitResponse(BaseModel):
    visit_id: UUID
    visitor_id: UUID
    arrived_at: datetime
    confirmation_message: str


class AdminVisitorRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: str | None
    phone: str | None
    company: str | None
    job_title: str | None
    created_at: datetime
    updated_at: datetime


class AdminVisitRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    visitor_id: UUID
    host_id: UUID | None
    host_name_raw: str | None
    arrived_at: datetime
    source: str
    hubspot_contact_id: str | None
    hubspot_note_id: str | None
    hubspot_synced_at: datetime | None
    host_notified_at: datetime | None
