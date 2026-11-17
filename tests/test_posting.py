import httpx
import pytest
import respx
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import app, get_posting_service
from app.services.posting_service import PostingService


def get_test_settings() -> Settings:
    return Settings(
        github_gist_token="ghp_test_token_12345",
        devto_api_key="devto_test_key_12345",
        telegram_bot_token="987654321:TEST_BOT_TOKEN",
        telegram_channel_id="@test_public_channel",
        discord_webhook_url="https://discord.com/api/webhooks/111222333/test_webhook_token",
        discord_guild_id="999888777",
        mastodon_instance_url="https://mastodon.social",
        mastodon_access_token="mastodon_test_token_12345",
    )


@pytest.fixture
def client():
    test_settings = get_test_settings()
    app.dependency_overrides[get_posting_service] = lambda: PostingService(settings=test_settings)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --- 1. Input Validation Tests ---

def test_validation_rejects_message_over_200_chars(client: TestClient):
    long_message = ("A" * 185) + " https://example.com"  # > 200 karakter
    response = client.post("/posting", json={"message": long_message})
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert "200-character limit" in body["details"][0]["message"]


def test_validation_rejects_zero_links(client: TestClient):
    response = client.post(
        "/posting",
        json={"message": "Check out our latest business platform without any link included."},
    )
    assert response.status_code == 422
    assert "none was found" in response.json()["details"][0]["message"]


def test_validation_rejects_multiple_links(client: TestClient):
    response = client.post(
        "/posting",
        json={"message": "Visit https://example.com and also check https://another-example.org today!"},
    )
    assert response.status_code == 422
    assert "2 links were found" in response.json()["details"][0]["message"]


def test_validation_rejects_invalid_url_format(client: TestClient):
    response = client.post(
        "/posting",
        json={"message": "Check our site at http://invalid-domain for details."},
    )
    assert response.status_code == 422
    assert "Invalid CTA URL format" in response.json()["details"][0]["message"]


# --- 2. Multi-Platform Posting & Fault Isolation Tests ---

@respx.mock
def test_multi_platform_all_success(client: TestClient):
    respx.post("https://api.github.com/gists").mock(
        return_value=httpx.Response(201, json={"html_url": "https://gist.github.com/user/abc123"})
    )
    respx.post("https://dev.to/api/articles").mock(
        return_value=httpx.Response(201, json={"url": "https://dev.to/user/new-announcement-123"})
    )
    respx.post("https://api.telegram.org/bot987654321:TEST_BOT_TOKEN/sendMessage").mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "result": {"message_id": 42, "chat": {"username": "test_public_channel"}},
            },
        )
    )
    respx.post("https://discord.com/api/webhooks/111222333/test_webhook_token?wait=true").mock(
        return_value=httpx.Response(200, json={"id": "555666", "channel_id": "333444"})
    )
    respx.post("https://mastodon.social/api/v1/statuses").mock(
        return_value=httpx.Response(200, json={"url": "https://mastodon.social/@user/11223344"})
    )

    response = client.post(
        "/posting",
        json={
            "message": "Check out our latest business platform and grow your online visibility. https://example.com"
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["results"]) == 5

    for item in data["results"]:
        assert item["status"] == "success"
        assert item["posted_url"] is not None
        assert item["public_access"] is True
        assert item["date"] is not None
        assert item["time"] is not None
        assert item["error"] is None


@respx.mock
def test_partial_failure_continues_other_platforms(client: TestClient):
    # GitHub Gist sukses
    respx.post("https://api.github.com/gists").mock(
        return_value=httpx.Response(201, json={"html_url": "https://gist.github.com/user/abc123"})
    )
    # Dev.to gagal (401 Unauthorized)
    respx.post("https://dev.to/api/articles").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )
    # Telegram gagal (Network timeout)
    respx.post("https://api.telegram.org/bot987654321:TEST_BOT_TOKEN/sendMessage").mock(
        side_effect=httpx.ConnectTimeout("Connection timed out")
    )
    # Discord sukses
    respx.post("https://discord.com/api/webhooks/111222333/test_webhook_token?wait=true").mock(
        return_value=httpx.Response(200, json={"id": "555666", "channel_id": "333444"})
    )
    # Mastodon sukses
    respx.post("https://mastodon.social/api/v1/statuses").mock(
        return_value=httpx.Response(200, json={"url": "https://mastodon.social/@user/11223344"})
    )

    response = client.post(
        "/posting",
        json={
            "message": "Check out our latest business platform and grow your online visibility. https://example.com"
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    results_by_name = {r["platform"]: r for r in data["results"]}
    assert results_by_name["GitHub Gist"]["status"] == "success"
    assert results_by_name["Discord"]["status"] == "success"
    assert results_by_name["Mastodon"]["status"] == "success"

    assert results_by_name["Dev.to"]["status"] == "failed"
    assert "401" in results_by_name["Dev.to"]["error"]
    assert results_by_name["Telegram"]["status"] == "failed"
    assert "Network error" in results_by_name["Telegram"]["error"]