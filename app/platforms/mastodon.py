import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformPostResult


class MastodonPlatform(BasePlatform):
    @property
    def name(self) -> str:
        return "Mastodon"

    async def post(self, message: str, cta_url: str, client: httpx.AsyncClient) -> PlatformPostResult:
        token = self.settings.mastodon_access_token
        instance = self.settings.mastodon_instance_url.rstrip("/")

        if not token or token == "your_mastodon_access_token":
            return self._build_failure("Missing or unconfigured MASTODON_ACCESS_TOKEN")

        url = f"{instance}/api/v1/statuses"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "status": message,
            "visibility": "public",
        }

        try:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code not in (200, 201):
                return self._build_failure(self._extract_http_error(response))

            data = response.json()
            return self._build_success(posted_url=data.get("url"), public_access=True)
        except httpx.RequestError as exc:
            return self._build_failure(f"Network error: {exc}")