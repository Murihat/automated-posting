import re
from typing import Literal
from pydantic import BaseModel, Field, HttpUrl, TypeAdapter, ValidationError, field_validator

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE)
_HTTP_URL_ADAPTER = TypeAdapter(HttpUrl)


class PostRequest(BaseModel):
    message: str = Field(
        ...,
        description="Short promotional message containing at most 200 characters and exactly one valid CTA URL.",
        examples=[
            "Check out our latest business platform and grow your online visibility. https://example.com"
        ],
    )

    @field_validator("message")
    @classmethod
    def validate_message_rules(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Message cannot be empty or whitespace only.")

        if len(cleaned) > 200:
            raise ValueError(
                f"Message exceeds the 200-character limit (current length: {len(cleaned)} characters)."
            )

        raw_urls = URL_PATTERN.findall(cleaned)

        if len(raw_urls) == 0:
            raise ValueError("Message must include exactly one CTA link, but none was found.")

        if len(raw_urls) > 1:
            raise ValueError(
                f"Message must include exactly one CTA link, but {len(raw_urls)} links were found."
            )

        candidate_url = raw_urls[0].rstrip(".,!?;:)")
        if candidate_url.lower().startswith("www."):
            raise ValueError(
                f"Invalid URL '{candidate_url}'. URL must include a valid scheme (http:// or https://)."
            )

        try:
            parsed = _HTTP_URL_ADAPTER.validate_python(candidate_url)
        except ValidationError as exc:
            raise ValueError(f"Invalid CTA URL format: '{candidate_url}'.") from exc

        host = parsed.host or ""
        parts = host.split(".")
        if len(parts) < 2 or not parts[-1].isalpha() or len(parts[-1]) < 2:
            raise ValueError(
                f"Invalid CTA URL format: '{candidate_url}'. A valid public domain with TLD is required."
            )

        return cleaned

    def extract_cta_url(self) -> str:
        """Helper untuk mengambil satu URL yang sudah tervalidasi dari pesan."""
        raw_urls = URL_PATTERN.findall(self.message)
        return raw_urls[0].rstrip(".,!?;:)")


class PlatformPostResult(BaseModel):
    platform: str
    status: Literal["success", "failed"]
    posted_url: str | None = None
    public_access: bool = False
    date: str | None = None
    time: str | None = None
    error: str | None = None


class PostResponse(BaseModel):
    success: bool
    results: list[PlatformPostResult]