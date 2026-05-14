"""HubSpot client for Contacts and Notes."""

from datetime import datetime
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

NOTE_ASSOCIATION_TYPE_ID = 202  # note -> contact


class HubSpotClient:
    """Minimal HubSpot client targeting the v3 Contacts + Notes APIs."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _configured(self) -> bool:
        return bool(self.settings.hubspot_access_token)

    def _headers(self) -> dict[str, str]:
        if not self._configured():
            raise RuntimeError("HubSpot access token is not configured")
        return {
            "Authorization": f"Bearer {self.settings.hubspot_access_token}",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def upsert_contact(
        self,
        *,
        email: str,
        properties: dict[str, str | None],
    ) -> str:
        """Create or update a Contact by email; returns the contact id."""
        if not self._configured():
            raise RuntimeError("HubSpot not configured")

        clean_props = {k: v for k, v in properties.items() if v is not None}
        clean_props["email"] = email
        body: dict[str, Any] = {"properties": clean_props}

        async with httpx.AsyncClient(timeout=20) as client:
            search_resp = await client.post(
                f"{self.settings.hubspot_base_url}/crm/v3/objects/contacts/search",
                headers=self._headers(),
                json={
                    "filterGroups": [
                        {
                            "filters": [
                                {"propertyName": "email", "operator": "EQ", "value": email}
                            ]
                        }
                    ],
                    "limit": 1,
                },
            )
            search_resp.raise_for_status()
            results = search_resp.json().get("results", [])

            if results:
                contact_id = results[0]["id"]
                patch_resp = await client.patch(
                    f"{self.settings.hubspot_base_url}/crm/v3/objects/contacts/{contact_id}",
                    headers=self._headers(),
                    json=body,
                )
                patch_resp.raise_for_status()
                return str(contact_id)

            create_resp = await client.post(
                f"{self.settings.hubspot_base_url}/crm/v3/objects/contacts",
                headers=self._headers(),
                json=body,
            )
            create_resp.raise_for_status()
            return str(create_resp.json()["id"])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def create_visit_note(
        self,
        *,
        contact_id: str,
        body_text: str,
        timestamp: datetime,
    ) -> str:
        if not self._configured():
            raise RuntimeError("HubSpot not configured")

        ts_ms = int(timestamp.timestamp() * 1000)
        payload = {
            "properties": {
                "hs_note_body": body_text,
                "hs_timestamp": ts_ms,
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": NOTE_ASSOCIATION_TYPE_ID,
                        }
                    ],
                }
            ],
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.settings.hubspot_base_url}/crm/v3/objects/notes",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            return str(response.json()["id"])
