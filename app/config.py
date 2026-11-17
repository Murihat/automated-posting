from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Automated Multi-Platform Posting System"
    app_env: str = "development"
    request_timeout: float = 15.0

    # GitHub Gist
    github_gist_token: str | None = None

    # Dev.to
    devto_api_key: str | None = None

    # Telegram
    telegram_bot_token: str | None = None
    telegram_channel_id: str | None = None

    # Discord
    discord_webhook_url: str | None = None
    discord_guild_id: str | None = None

    # Mastodon
    mastodon_instance_url: str = "https://mastodon.social"
    mastodon_access_token: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()