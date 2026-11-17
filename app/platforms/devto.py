from datetime import datetime, timezone
import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformPostResult


class DevToPlatform(BasePlatform):
    API_URL = "https://dev.to/api/articles"

    @property
    def name(self) -> str:
        return "Dev.to"

    async def post(self, message: str, cta_url: str, client: httpx.AsyncClient) -> PlatformPostResult:
        api_key = self.settings.devto_api_key
        if not api_key or api_key == "your_devto_api_key":
            return self._build_failure("Missing or unconfigured DEVTO_API_KEY")

        headers = {
            "api-key": api_key,
            "Accept": "application/vnd.forem.api-v1+json",
            "Content-Type": "application/json",
        }

        # Buat judul bersih tanpa URL + suffix waktu singkat agar unik saat pengujian berulang
        clean_title = message.replace(cta_url, "").strip() or "New Announcement"
        suffix = datetime.now(timezone.utc).strftime("%H%M%S")
        title = f"{clean_title[:75]} ({suffix})"

        payload = {
            "article": {
                "title": title,
                "published": True,
                "body_markdown": f"{message}\n\nVisit link: [{cta_url}]({cta_url})",
                "tags": ["news", "announcement", "web"],
            }
        }

        try:
            response = await client.post(self.API_URL, headers=headers, json=payload)
            if response.status_code not in (200, 201):
                return self._build_failure(self._extract_http_error(response))

            data = response.json()
            return self._build_success(posted_url=data.get("url"), public_access=True)
        except httpx.RequestError as exc:
            return self._build_failure(f"Network error: {exc}")