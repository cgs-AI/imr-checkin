"""Gated live tests against a real HubSpot sandbox.

Skipped unless HUBSPOT_ACCESS_TOKEN is set in the environment.
Uses a unique email namespace (pytest-live-{uuid}@imr-test.invalid) that
cannot collide with real IMR contacts. All created contacts are deleted in
teardown even if a test fails.

Run against a developer sandbox (recommended):
    HUBSPOT_ACCESS_TOKEN=pat-xx-... pytest tests/test_hubspot_live.py -v
"""

import os
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio

from app.core.config import Settings
from app.integrations.hubspot_client import HubSpotClient

pytestmark = pytest.mark.skipif(
    not os.getenv("HUBSPOT_ACCESS_TOKEN"),
    reason="Set HUBSPOT_ACCESS_TOKEN to run live HubSpot tests",
)


@pytest_asyncio.fixture
async def live_client() -> HubSpotClient:
    settings = Settings()
    return HubSpotClient(settings=settings)


@pytest_asyncio.fixture
async def cleanup_contact(live_client: HubSpotClient):
    """Collect contact ids created during a test and delete them in teardown."""
    created: list[str] = []
    yield created
    for contact_id in created:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                await client.delete(
                    live_client._url(f"/crm/v3/objects/contacts/{contact_id}"),
                    headers=live_client._headers(),
                )
        except Exception:  # noqa: BLE001
            pass


@pytest.mark.asyncio
async def test_live_get_contact_not_found(live_client):
    email = f"pytest-live-unknown-{uuid4()}@imr-test.invalid"
    result = await live_client.get_contact_by_email(email)
    assert result is None


@pytest.mark.asyncio
async def test_live_upsert_creates_contact(live_client, cleanup_contact):
    email = f"pytest-live-{uuid4()}@imr-test.invalid"
    contact_id = await live_client.upsert_contact(
        email=email,
        full_name="Pytest Live",
        company="IMR Test",
        job_title="Automated Test",
        phone=None,
    )
    cleanup_contact.append(contact_id)
    assert contact_id


@pytest.mark.asyncio
async def test_live_upsert_patches_existing_contact(live_client, cleanup_contact):
    email = f"pytest-live-{uuid4()}@imr-test.invalid"
    id1 = await live_client.upsert_contact(
        email=email, full_name="Pytest Live", company="Company A", job_title=None, phone=None
    )
    cleanup_contact.append(id1)

    id2 = await live_client.upsert_contact(
        email=email, full_name="Pytest Live", company="Company B", job_title=None, phone=None
    )
    assert id1 == id2


@pytest.mark.asyncio
async def test_live_get_contact_returns_props(live_client, cleanup_contact):
    email = f"pytest-live-{uuid4()}@imr-test.invalid"
    contact_id = await live_client.upsert_contact(
        email=email, full_name="Pytest Props", company="Props Co", job_title=None, phone=None
    )
    cleanup_contact.append(contact_id)

    props = await live_client.get_contact_by_email(email)
    assert props is not None
    assert props.get("company") == "Props Co"


@pytest.mark.asyncio
async def test_live_create_note(live_client, cleanup_contact):
    email = f"pytest-live-{uuid4()}@imr-test.invalid"
    contact_id = await live_client.upsert_contact(
        email=email, full_name="Pytest Note", company=None, job_title=None, phone=None
    )
    cleanup_contact.append(contact_id)

    note_id = await live_client.create_visit_note(
        contact_id=contact_id,
        body="Live test visit note — safe to ignore.",
    )
    assert note_id
