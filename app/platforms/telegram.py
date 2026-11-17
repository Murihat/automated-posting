import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformPostResult


class TelegramPlatform(BasePlatform):
    @property
    def name(self) -> str:
        return "Telegram"

    async def post(self, message: str, cta_url: str, client: httpx.AsyncClient) -> PlatformPostResult:
        token = self.settings.telegram_bot_token
        channel_id = self.settings.telegram_channel_id

        if not token or token.startswith("123456789:") or not channel_id or channel_id == "@your_public_channel":
            return self._build_failure("Missing or unconfigured TELEGRAM_BOT_TOKEN / TELEGRAM_CHANNEL_ID")

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": channel_id,
            "text": message,
            "disable_web_page_preview": False,
        }

        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                return self._build_failure(self._extract_http_error(response))

            data = response.json()
            if not data.get("ok"):
                return self._build_failure(data.get("description", "Telegram API returned ok=false"))

            result = data.get("result", {})
            message_id = result.get("message_id")
            chat = result.get("chat", {})
            username = chat.get("username") or (channel_id.lstrip("@") if channel_id.startswith("@") else None)

            if username and message_id:
                posted_url = f"https://t.me/{username}/{message_id}"
                public_access = True
            else:
                posted_url = None
                public_access = False

            return self._build_success(posted_url=posted_url, public_access=public_access)
        except httpx.RequestError as exc:
            return self._build_failure(f"Network error: {exc}")