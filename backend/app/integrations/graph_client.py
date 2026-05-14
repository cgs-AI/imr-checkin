"""Microsoft Graph client for staff directory sync and sendMail."""

from collections.abc import AsyncIterator
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

USER_FIELDS = "id,displayName,mail,userPrincipalName,jobTitle,department,accountEnabled"


class GraphClient:
    """Minimal Microsoft Graph client backed by client_credentials flow."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._token: str | None = None

    def _configured(self) -> bool:
        return bool(
            self.settings.graph_tenant_id
            and self.settings.graph_client_id
            and self.settings.graph_client_secret
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _fetch_token(self) -> str:
        if not self._configured():
            raise RuntimeError("Microsoft Graph credentials are not configured")
        url = TOKEN_URL.format(tenant=self.settings.graph_tenant_id)
        data = {
            "client_id": self.settings.graph_client_id,
            "client_secret": self.settings.graph_client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(url, data=data)
            response.raise_for_status()
            payload = response.json()
        token = payload.get("access_token")
        if not isinstance(token, str):
            raise RuntimeError("Graph token response missing access_token")
        return token

    async def _auth_headers(self) -> dict[str, str]:
        if self._token is None:
            self._token = await self._fetch_token()
        return {"Authorization": f"Bearer {self._token}"}

    async def iter_users(self) -> AsyncIterator[dict[str, Any]]:
        if not self._configured():
            logger.warning("graph.skip_user_sync", reason="not_configured")
            return
        url: str | None = f"{GRAPH_BASE}/users?$select={USER_FIELDS}&$top=100"
        async with httpx.AsyncClient(timeout=30) as client:
            while url:
                headers = await self._auth_headers()
                response = await client.get(url, headers=headers)
                if response.status_code == 401:
                    self._token = None
                    headers = await self._auth_headers()
                    response = await client.get(url, headers=headers)
                response.raise_for_status()
                payload = response.json()
                for user in payload.get("value", []):
                    yield user
                url = payload.get("@odata.nextLink")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def send_mail(
        self,
        *,
        to_email: str,
        subject: str,
        body_text: str,
    ) -> None:
        if not self._configured():
            logger.warning("graph.skip_send_mail", reason="not_configured", to=to_email)
            return
        url = f"{GRAPH_BASE}/users/{self.settings.graph_sender_upn}/sendMail"
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body_text},
                "toRecipients": [{"emailAddress": {"address": to_email}}],
            },
            "saveToSentItems": False,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            headers = await self._auth_headers()
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 401:
                self._token = None
                headers = await self._auth_headers()
                response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
