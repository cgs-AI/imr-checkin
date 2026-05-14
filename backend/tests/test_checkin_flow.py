"""End-to-end tests for the visitor check-in API."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.security import issue_admin_token
from app.models.host import Host
from app.models.integration_job import IntegrationJob, JobType
from app.models.visit import Visit
from app.models.visitor import Visitor


async def _make_host(session_factory) -> Host:
    async with session_factory() as session:
        host = Host(
            id=uuid4(),
            display_name="Jane Doe",
            email="jane.doe@imr.ie",
            job_title="Engineer",
            department="AI",
            account_enabled=True,
            last_synced_at=datetime.utcnow(),
        )
        session.add(host)
        await session.commit()
        return host


@pytest.mark.asyncio
async def test_checkin_config(client):
    response = await client.get("/checkin/config")
    assert response.status_code == 200
    payload = response.json()
    assert "privacy_text" in payload
    assert payload["consent_text_version"]


@pytest.mark.asyncio
async def test_first_visit_creates_records(client, session_factory, consent_payload):
    host = await _make_host(session_factory)

    body = {
        "visitor": {
            "full_name": "Carlos Garcia",
            "email": "carlos@example.com",
            "phone": "+353871234567",
            "company": "Acme Ltd",
            "job_title": "Head of AI",
        },
        "host_id": str(host.id),
        "consent": consent_payload,
    }

    response = await client.post("/visits", json=body)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["confirmation_message"].startswith("Check-in complete")

    async with session_factory() as session:
        visitors = (await session.execute(select(Visitor))).scalars().all()
        assert len(visitors) == 1
        assert visitors[0].email == "carlos@example.com"

        visits = (await session.execute(select(Visit))).scalars().all()
        assert len(visits) == 1
        assert visits[0].host_id == host.id

        jobs = (await session.execute(select(IntegrationJob))).scalars().all()
        job_types = {j.job_type for j in jobs}
        assert JobType.HOST_EMAIL.value in job_types
        assert JobType.HUBSPOT_CONTACT.value in job_types
        assert JobType.HUBSPOT_NOTE.value in job_types


@pytest.mark.asyncio
async def test_returning_visitor_lookup_by_email(client, session_factory, consent_payload):
    host = await _make_host(session_factory)
    body = {
        "visitor": {
            "full_name": "Sam Smith",
            "email": "sam@example.com",
            "phone": "+353871119999",
            "company": "Acme",
            "job_title": "PM",
        },
        "host_id": str(host.id),
        "consent": consent_payload,
    }
    await client.post("/visits", json=body)

    lookup = await client.post("/visitors/lookup", json={"email": "sam@example.com"})
    assert lookup.status_code == 200
    data = lookup.json()
    assert data["match"] is not None
    assert data["matched_by"] == "email"
    assert data["match"]["full_name"] == "Sam Smith"


@pytest.mark.asyncio
async def test_lookup_requires_email_or_phone(client):
    response = await client.post("/visitors/lookup", json={})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_visit_source_defaults_to_qr_self_checkin(client, session_factory, consent_payload):
    host = await _make_host(session_factory)
    response = await client.post(
        "/visits",
        json={
            "visitor": {"full_name": "Default Source", "email": "ds@example.com"},
            "host_id": str(host.id),
            "consent": consent_payload,
        },
    )
    assert response.status_code == 201

    async with session_factory() as session:
        visit = (await session.execute(select(Visit))).scalars().one()
        assert visit.source == "qr_self_checkin"


@pytest.mark.asyncio
async def test_visit_source_ipad_kiosk_is_recorded(client, session_factory, consent_payload):
    host = await _make_host(session_factory)
    response = await client.post(
        "/visits",
        json={
            "visitor": {"full_name": "Kiosk Visitor", "email": "kiosk@example.com"},
            "host_id": str(host.id),
            "consent": consent_payload,
            "source": "ipad_kiosk",
        },
    )
    assert response.status_code == 201

    async with session_factory() as session:
        visit = (await session.execute(select(Visit))).scalars().one()
        assert visit.source == "ipad_kiosk"


@pytest.mark.asyncio
async def test_visit_rejects_unknown_source(client, session_factory, consent_payload):
    host = await _make_host(session_factory)
    response = await client.post(
        "/visits",
        json={
            "visitor": {"full_name": "Bad", "email": "bad@example.com"},
            "host_id": str(host.id),
            "consent": consent_payload,
            "source": "smoke_signal",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_visit_without_email_skips_hubspot_jobs(client, session_factory, consent_payload):
    host = await _make_host(session_factory)
    body = {
        "visitor": {
            "full_name": "Anon Visitor",
            "phone": "+353870000000",
        },
        "host_id": str(host.id),
        "consent": consent_payload,
    }
    response = await client.post("/visits", json=body)
    assert response.status_code == 201

    async with session_factory() as session:
        jobs = (await session.execute(select(IntegrationJob))).scalars().all()
        job_types = {j.job_type for j in jobs}
        assert JobType.HOST_EMAIL.value in job_types
        assert JobType.HUBSPOT_CONTACT.value not in job_types
        assert JobType.HUBSPOT_NOTE.value not in job_types


@pytest.mark.asyncio
async def test_visit_rejects_without_consent(client, session_factory):
    host = await _make_host(session_factory)
    body = {
        "visitor": {"full_name": "Test", "email": "t@example.com"},
        "host_id": str(host.id),
        "consent": {
            "granted": False,
            "consent_text_version": "2026-05-01",
            "consent_type": "visitor_checkin",
        },
    }
    response = await client.post("/visits", json=body)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_host_search_min_chars(client, session_factory):
    await _make_host(session_factory)
    response = await client.get("/hosts", params={"q": "j"})
    assert response.status_code == 400

    response = await client.get("/hosts", params={"q": "jan"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["display_name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_host_search_excludes_disabled(client, session_factory):
    async with session_factory() as session:
        session.add(
            Host(
                id=uuid4(),
                display_name="Old Staffer",
                email="old@imr.ie",
                account_enabled=False,
                last_synced_at=datetime.utcnow(),
            )
        )
        await session.commit()
    response = await client.get("/hosts", params={"q": "old"})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_admin_requires_token(client):
    response = await client.get("/admin/visitors")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_list_visitors(client, session_factory, consent_payload):
    host = await _make_host(session_factory)
    await client.post(
        "/visits",
        json={
            "visitor": {"full_name": "Bob", "email": "bob@example.com"},
            "host_id": str(host.id),
            "consent": consent_payload,
        },
    )
    token = issue_admin_token(subject="tester@imr.ie")
    response = await client.get(
        "/admin/visitors",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_admin_can_delete_visitor(client, session_factory, consent_payload):
    host = await _make_host(session_factory)
    create = await client.post(
        "/visits",
        json={
            "visitor": {"full_name": "Bob", "email": "bob@example.com"},
            "host_id": str(host.id),
            "consent": consent_payload,
        },
    )
    visitor_id = create.json()["visitor_id"]

    token = issue_admin_token(subject="tester@imr.ie")
    response = await client.delete(
        f"/admin/visitors/{visitor_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    async with session_factory() as session:
        remaining = (await session.execute(select(Visitor))).scalars().all()
        assert remaining == []
        remaining_visits = (await session.execute(select(Visit))).scalars().all()
        assert remaining_visits == []
