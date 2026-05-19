"""Tests for the HubSpot sync service (background task functions)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.hubspot import sync_visit_to_hubspot


@pytest.mark.asyncio
async def test_sync_succeeds(make_visitor, make_visit):
    visitor = await make_visitor(email="visitor@example.com")
    visit = await make_visit(visitor)

    mock_client = AsyncMock()
    mock_client._configured = MagicMock(return_value=True)
    mock_client.upsert_contact = AsyncMock(return_value="hs-123")
    mock_client.create_visit_note = AsyncMock(return_value="note-456")

    with patch("app.services.hubspot.HubSpotClient", return_value=mock_client):
        await sync_visit_to_hubspot(visitor, visit)

    mock_client.upsert_contact.assert_called_once()
    call_kwargs = mock_client.upsert_contact.call_args.kwargs
    assert call_kwargs["email"] == "visitor@example.com"
    mock_client.create_visit_note.assert_called_once()
    note_kwargs = mock_client.create_visit_note.call_args.kwargs
    assert note_kwargs["contact_id"] == "hs-123"


@pytest.mark.asyncio
async def test_sync_skips_when_no_email(make_visitor, make_visit):
    visitor = await make_visitor(email=None)
    visit = await make_visit(visitor)

    mock_client = AsyncMock()
    with patch("app.services.hubspot.HubSpotClient", return_value=mock_client):
        await sync_visit_to_hubspot(visitor, visit)

    mock_client.upsert_contact.assert_not_called()


@pytest.mark.asyncio
async def test_sync_skips_when_not_configured(make_visitor, make_visit):
    visitor = await make_visitor()
    visit = await make_visit(visitor)

    mock_client = AsyncMock()
    mock_client._configured = MagicMock(return_value=False)

    with patch("app.services.hubspot.HubSpotClient", return_value=mock_client):
        await sync_visit_to_hubspot(visitor, visit)

    mock_client.upsert_contact.assert_not_called()


@pytest.mark.asyncio
async def test_sync_logs_and_continues_on_upsert_error(make_visitor, make_visit):
    visitor = await make_visitor()
    visit = await make_visit(visitor)

    mock_client = AsyncMock()
    mock_client._configured = MagicMock(return_value=True)
    mock_client.upsert_contact = AsyncMock(
        side_effect=httpx.HTTPStatusError("500", request=None, response=None)
    )

    with patch("app.services.hubspot.HubSpotClient", return_value=mock_client):
        await sync_visit_to_hubspot(visitor, visit)

    mock_client.create_visit_note.assert_not_called()


@pytest.mark.asyncio
async def test_sync_logs_and_continues_on_note_error(make_visitor, make_visit):
    visitor = await make_visitor()
    visit = await make_visit(visitor)

    mock_client = AsyncMock()
    mock_client._configured = MagicMock(return_value=True)
    mock_client.upsert_contact = AsyncMock(return_value="hs-123")
    mock_client.create_visit_note = AsyncMock(
        side_effect=httpx.HTTPStatusError("500", request=None, response=None)
    )

    with patch("app.services.hubspot.HubSpotClient", return_value=mock_client):
        await sync_visit_to_hubspot(visitor, visit)

    mock_client.create_visit_note.assert_called_once()


@pytest.mark.asyncio
async def test_note_includes_visitor_details(make_visitor, make_visit):
    visitor = await make_visitor(email="v@example.com", full_name="Carlos Garcia")
    visit = await make_visit(visitor)

    mock_client = AsyncMock()
    mock_client._configured = MagicMock(return_value=True)
    mock_client.upsert_contact = AsyncMock(return_value="hs-abc")
    mock_client.create_visit_note = AsyncMock(return_value="note-xyz")

    with patch("app.services.hubspot.HubSpotClient", return_value=mock_client):
        await sync_visit_to_hubspot(visitor, visit)

    note_body = mock_client.create_visit_note.call_args.kwargs["body"]
    assert "Carlos Garcia" in note_body
    assert "Test Co" in note_body
