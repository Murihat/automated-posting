import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformPostResult


class DiscordPlatform(BasePlatform):
    @property
    def name(self) -> str:
        return "Discord"

    async def post(self, message: str, cta_url: str, client: httpx.AsyncClient) -> PlatformPostResult:
        webhook_url = self.settings.discord_webhook_url
        guild_id = self.settings.discord_guild_id

        if not webhook_url or "your_webhook_id" in webhook_url:
            return self._build_failure("Missing or unconfigured DISCORD_WEBHOOK_URL")

        separator = "&" if "?" in webhook_url else "?"
        target_url = f"{webhook_url}{separator}wait=true"

        try:
            response = await client.post(target_url, json={"content": message})
            if response.status_code not in (200, 201):
                return self._build_failure(self._extract_http_error(response))

            data = response.json()
            channel_id = data.get("channel_id")
            message_id = data.get("id")

            if guild_id and guild_id != "your_server_guild_id" and channel_id and message_id:
                posted_url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
            else:
                posted_url = None

            return self._build_success(posted_url=posted_url, public_access=True)
        except httpx.RequestError as exc:
            return self._build_failure(f"Network error: {exc}")