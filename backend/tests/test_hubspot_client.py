"""Unit tests for HubSpotClient — all HTTP calls mocked."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.integrations.hubspot_client import HubSpotClient


def _client(token: str | None = "test-token") -> HubSpotClient:
    settings = MagicMock(spec=Settings)
    settings.hubspot_access_token = token
    settings.hubspot_base_url = "https://api.hubapi.com"
    return HubSpotClient(settings=settings)


def _mock_response(json_data: dict, status_code: int = 200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


@pytest.mark.asyncio
async def test_not_configured_raises():
    client = _client(token=None)
    with pytest.raises(RuntimeError, match="HUBSPOT_ACCESS_TOKEN"):
        client._headers()


@pytest.mark.asyncio
async def test_upsert_contact_creates_when_not_found():
    client = _client()
    search_resp = _mock_response({"results": []})
    create_resp = _mock_response({"id": "hs-new-123"})

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(side_effect=[search_resp, create_resp])

    with patch("app.integrations.hubspot_client.httpx.AsyncClient", return_value=mock_http):
        contact_id = await client.upsert_contact(
            email="new@example.com",
            full_name="Alice Smith",
            company="Acme",
            job_title="Engineer",
            phone="+353871234567",
        )

    assert contact_id == "hs-new-123"
    assert mock_http.post.call_count == 2


@pytest.mark.asyncio
async def test_upsert_contact_patches_when_found():
    client = _client()
    search_resp = _mock_response({"results": [{"id": "hs-existing-456"}]})
    patch_resp = _mock_response({"id": "hs-existing-456"})

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=search_resp)
    mock_http.patch = AsyncMock(return_value=patch_resp)

    with patch("app.integrations.hubspot_client.httpx.AsyncClient", return_value=mock_http):
        contact_id = await client.upsert_contact(
            email="existing@example.com",
            full_name="Bob Jones",
            company="Beta Corp",
            job_title=None,
            phone=None,
        )

    assert contact_id == "hs-existing-456"
    mock_http.patch.assert_called_once()


@pytest.mark.asyncio
async def test_create_visit_note_posts_with_association():
    client = _client()
    note_resp = _mock_response({"id": "note-789"})

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=note_resp)

    with patch("app.integrations.hubspot_client.httpx.AsyncClient", return_value=mock_http):
        note_id = await client.create_visit_note(
            contact_id="hs-123",
            body="Visitor arrived at IMR.",
        )

    assert note_id == "note-789"
    call_kwargs = mock_http.post.call_args.kwargs
    payload = call_kwargs["json"]
    assert payload["properties"]["hs_note_body"] == "Visitor arrived at IMR."
    assert payload["associations"][0]["to"]["id"] == "hs-123"


@pytest.mark.asyncio
async def test_get_contact_by_email_returns_none_when_not_found():
    client = _client()
    search_resp = _mock_response({"results": []})

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=search_resp)

    with patch("app.integrations.hubspot_client.httpx.AsyncClient", return_value=mock_http):
        result = await client.get_contact_by_email("unknown@example.com")

    assert result is None


@pytest.mark.asyncio
async def test_get_contact_by_email_returns_props_when_found():
    client = _client()
    props = {"firstname": "Alice", "lastname": "Smith", "company": "Acme", "jobtitle": "Engineer", "phone": "+353871234567"}
    search_resp = _mock_response({"results": [{"id": "hs-123", "properties": props}]})

    mock_http = AsyncMock()
    mock_http.__aenter__ = AsyncMock(return_value=mock_http)
    mock_http.__aexit__ = AsyncMock(return_value=False)
    mock_http.post = AsyncMock(return_value=search_resp)

    with patch("app.integrations.hubspot_client.httpx.AsyncClient", return_value=mock_http):
        result = await client.get_contact_by_email("alice@example.com")

    assert result is not None
    assert result["firstname"] == "Alice"
    assert result["company"] == "Acme"


@pytest.mark.asyncio
async def test_get_contact_by_email_returns_none_when_unconfigured():
    client = _client(token=None)
    result = await client.get_contact_by_email("anyone@example.com")
    assert result is None
