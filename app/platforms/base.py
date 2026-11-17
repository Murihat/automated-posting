from abc import ABC, abstractmethod
from datetime import datetime, timezone
import httpx
from app.config import Settings
from app.schemas import PlatformPostResult


class BasePlatform(ABC):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    @abstractmethod
    def name(self) -> str:
        """Nama resmi platform yang ditampilkan di response."""

    @abstractmethod
    async def post(self, message: str, cta_url: str, client: httpx.AsyncClient) -> PlatformPostResult:
        """Mempublikasikan pesan ke API platform dan mengembalikan hasil terstruktur."""

    def _build_success(self, posted_url: str | None, public_access: bool = True) -> PlatformPostResult:
        now = datetime.now(timezone.utc)
        return PlatformPostResult(
            platform=self.name,
            status="success",
            posted_url=posted_url,
            public_access=public_access,
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
            error=None,
        )

    def _build_failure(self, error_message: str) -> PlatformPostResult:
        return PlatformPostResult(
            platform=self.name,
            status="failed",
            posted_url=None,
            public_access=False,
            date=None,
            time=None,
            error=error_message,
        )

    @staticmethod
    def _extract_http_error(response: httpx.Response) -> str:
        try:
            data = response.json()
            if isinstance(data, dict):
                detail = data.get("message") or data.get("error") or data.get("description")
                if detail:
                    return f"HTTP {response.status_code}: {detail}"
        except ValueError:
            pass
        return f"HTTP {response.status_code}: {response.text[:180].strip() or response.reason_phrase}"