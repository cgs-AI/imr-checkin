"""HubSpot CRM client — contact upsert, visit note, and contact lookup."""

from datetime import datetime

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

CONTACTS_SEARCH = "/crm/v3/objects/contacts/search"
CONTACTS_BASE = "/crm/v3/objects/contacts"
NOTES_BASE = "/crm/v3/objects/notes"

DEFAULT_CONTACT_PROPS = ["firstname", "lastname", "phone", "company", "jobtitle"]


class HubSpotClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _configured(self) -> bool:
        return bool(self.settings.hubspot_access_token)

    def _headers(self) -> dict[str, str]:
        if not self._configured():
            raise RuntimeError("HUBSPOT_ACCESS_TOKEN is not configured")
        return {
            "Authorization": f"Bearer {self.settings.hubspot_access_token}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return self.settings.hubspot_base_url.rstrip("/") + path

    async def get_contact_by_email(
        self,
        email: str,
        properties: list[str] | None = None,
    ) -> dict[str, str] | None:
        """Return contact properties dict or None if not found / not configured."""
        if not self._configured():
            logger.warning("hubspot.skip_get_contact", reason="not_configured")
            return None

        props = properties or DEFAULT_CONTACT_PROPS
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {"propertyName": "email", "operator": "EQ", "value": email}
                    ]
                }
            ],
            "properties": props,
            "limit": 1,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                self._url(CONTACTS_SEARCH), headers=self._headers(), json=payload
            )
            response.raise_for_status()
            results = response.json().get("results", [])

        if not results:
            return None
        return results[0].get("properties", {})

    async def upsert_contact(
        self,
        *,
        email: str,
        full_name: str,
        company: str | None,
        job_title: str | None,
        phone: str | None,
    ) -> str:
        """Create or update a HubSpot contact. Returns the HubSpot contact id."""
        name_parts = full_name.strip().split(" ", 1)
        firstname = name_parts[0]
        lastname = name_parts[1] if len(name_parts) > 1 else ""

        props: dict[str, str] = {"email": email, "firstname": firstname, "lastname": lastname}
        if company:
            props["company"] = company
        if job_title:
            props["jobtitle"] = job_title
        if phone:
            props["phone"] = phone

        # search for existing contact
        search_payload = {
            "filterGroups": [
                {"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}
            ],
            "properties": ["email"],
            "limit": 1,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            search_resp = await client.post(
                self._url(CONTACTS_SEARCH), headers=self._headers(), json=search_payload
            )
            search_resp.raise_for_status()
            results = search_resp.json().get("results", [])

            if results:
                contact_id = results[0]["id"]
                patch_resp = await client.patch(
                    self._url(f"{CONTACTS_BASE}/{contact_id}"),
                    headers=self._headers(),
                    json={"properties": props},
                )
                patch_resp.raise_for_status()
                return contact_id
            else:
                create_resp = await client.post(
                    self._url(CONTACTS_BASE),
                    headers=self._headers(),
                    json={"properties": props},
                )
                create_resp.raise_for_status()
                return create_resp.json()["id"]

    async def create_visit_note(
        self,
        *,
        contact_id: str,
        body: str,
        timestamp: datetime | None = None,
    ) -> str:
        """Create a HubSpot Note associated with the given contact. Returns note id."""
        ts = timestamp or datetime.utcnow()
        payload = {
            "properties": {
                "hs_note_body": body,
                "hs_timestamp": str(int(ts.timestamp() * 1000)),
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}
                    ],
                }
            ],
        }
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                self._url(NOTES_BASE), headers=self._headers(), json=payload
            )
            response.raise_for_status()
            return response.json()["id"]
