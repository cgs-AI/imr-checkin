"""End-to-end tests for the visitor check-in API (PoC)."""

from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models.host import Host
from app.models.visit import Visit
from app.models.visitor import Visitor


async def _make_host(session_factory, *, enabled: bool = True) -> Host:
    async with session_factory() as session:
        host = Host(
            id=uuid4(),
            display_name="Jane Doe",
            email="jane.doe@imr.ie",
            job_title="Engineer",
            department="AI",
            account_enabled=enabled,
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
    assert "site_name" in payload
    assert "host_search_min_chars" in payload


@pytest.mark.asyncio
async def test_first_visit_creates_records(client, session_factory):
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
        "consent_granted": True,
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


@pytest.mark.asyncio
async def test_returning_visitor_lookup_by_email(client, session_factory):
    host = await _make_host(session_factory)
    await client.post(
        "/visits",
        json={
            "visitor": {
                "full_name": "Sam Smith",
                "email": "sam@example.com",
                "phone": "+353871119999",
                "company": "Acme",
                "job_title": "PM",
            },
            "host_id": str(host.id),
            "consent_granted": True,
        },
    )

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
async def test_visit_source_defaults_to_qr_self_checkin(client, session_factory):
    host = await _make_host(session_factory)
    response = await client.post(
        "/visits",
        json={
            "visitor": {"full_name": "Default Source", "email": "ds@example.com"},
            "host_id": str(host.id),
            "consent_granted": True,
        },
    )
    assert response.status_code == 201

    async with session_factory() as session:
        visit = (await session.execute(select(Visit))).scalars().one()
        assert visit.source == "qr_self_checkin"


@pytest.mark.asyncio
async def test_visit_source_ipad_kiosk_is_recorded(client, session_factory):
    host = await _make_host(session_factory)
    response = await client.post(
        "/visits",
        json={
            "visitor": {"full_name": "Kiosk Visitor", "email": "kiosk@example.com"},
            "host_id": str(host.id),
            "consent_granted": True,
            "source": "ipad_kiosk",
        },
    )
    assert response.status_code == 201

    async with session_factory() as session:
        visit = (await session.execute(select(Visit))).scalars().one()
        assert visit.source == "ipad_kiosk"


@pytest.mark.asyncio
async def test_visit_rejects_unknown_source(client, session_factory):
    host = await _make_host(session_factory)
    response = await client.post(
        "/visits",
        json={
            "visitor": {"full_name": "Bad", "email": "bad@example.com"},
            "host_id": str(host.id),
            "consent_granted": True,
            "source": "smoke_signal",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_visit_rejects_without_consent(client, session_factory):
    host = await _make_host(session_factory)
    response = await client.post(
        "/visits",
        json={
            "visitor": {"full_name": "Test", "email": "t@example.com"},
            "host_id": str(host.id),
            "consent_granted": False,
        },
    )
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
    await _make_host(session_factory, enabled=False)
    response = await client.get("/hosts", params={"q": "jane"})
    assert response.status_code == 200
    assert response.json() == []
