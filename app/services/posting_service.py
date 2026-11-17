import asyncio
import httpx
from app.config import Settings
from app.platforms.base import BasePlatform
from app.platforms.devto import DevToPlatform
from app.platforms.discord import DiscordPlatform
from app.platforms.github_gist import GitHubGistPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.telegram import TelegramPlatform
from app.schemas import PlatformPostResult, PostRequest, PostResponse


class PostingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.platforms: list[BasePlatform] = [
            GitHubGistPlatform(settings),
            DevToPlatform(settings),
            TelegramPlatform(settings),
            DiscordPlatform(settings),
            MastodonPlatform(settings),
        ]

    async def publish_all(self, request: PostRequest) -> PostResponse:
        cta_url = request.extract_cta_url()
        timeout = httpx.Timeout(self.settings.request_timeout)

        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [
                self._safe_publish(platform, request.message, cta_url, client)
                for platform in self.platforms
            ]
            results = await asyncio.gather(*tasks)

        any_succeeded = any(item.status == "success" for item in results)
        return PostResponse(success=any_succeeded, results=list(results))

    async def _safe_publish(
        self,
        platform: BasePlatform,
        message: str,
        cta_url: str,
        client: httpx.AsyncClient,
    ) -> PlatformPostResult:
        try:
            return await platform.post(message=message, cta_url=cta_url, client=client)
        except Exception as exc:
            return PlatformPostResult(
                platform=platform.name,
                status="failed",
                posted_url=None,
                public_access=False,
                date=None,
                time=None,
                error=f"Unexpected error: {exc}",
            )