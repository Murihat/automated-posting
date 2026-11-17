import httpx
from app.platforms.base import BasePlatform
from app.schemas import PlatformPostResult


class GitHubGistPlatform(BasePlatform):
    API_URL = "https://api.github.com/gists"

    @property
    def name(self) -> str:
        return "GitHub Gist"

    async def post(self, message: str, cta_url: str, client: httpx.AsyncClient) -> PlatformPostResult:
        token = self.settings.github_gist_token
        if not token or token.startswith("ghp_your_"):
            return self._build_failure("Missing or unconfigured GITHUB_GIST_TOKEN")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        payload = {
            "description": message[:100],
            "public": True,
            "files": {
                "announcement.md": {
                    "content": f"{message}\n\nLearn more: {cta_url}\n"
                }
            },
        }

        try:
            response = await client.post(self.API_URL, headers=headers, json=payload)
            if response.status_code != 201:
                return self._build_failure(self._extract_http_error(response))

            data = response.json()
            return self._build_success(posted_url=data.get("html_url"), public_access=True)
        except httpx.RequestError as exc:
            return self._build_failure(f"Network error: {exc}")