## Author & Copyright

**Author:** Muhamad Rizal Hidayat  
**License:** All Rights Reserved — Evaluation Use Only  

Copyright © 2026 **Muhamad Rizal Hidayat**. This repository is shared publicly strictly for technical portfolio and recruitment evaluation purposes. Any commercial use, redistribution, or integration into production systems without explicit written permission from the author is strictly prohibited.

# Automated Multi-Platform Posting System

A production-ready **FastAPI** REST API service that validates short promotional messages and concurrently broadcasts them across **5 third-party platforms** in a single request using asynchronous HTTP (`HTTPX`).

---

## Key Features

- **Concurrent Multi-Platform Publishing:** Uses `asyncio.gather()` and `httpx.AsyncClient` to publish to all 5 platforms simultaneously rather than sequentially.
- **Fault Isolation:** If one platform fails (e.g., invalid credentials, rate limit, or network timeout), the remaining platforms continue publishing without interruption.
- **Strict Input Validation:** Enforces a 200-character limit, verifies that **exactly one** CTA link is included, and validates public domain formatting via Pydantic.
- **Extensible Adapter Architecture:** Each platform implements a shared `BasePlatform` interface, making it straightforward to add new channels without modifying core business logic.

---

## Integrated Platforms

| # | Platform | API Endpoint | Output |
|---|---|---|---|
| 1 | **GitHub Gist** | `POST https://api.github.com/gists` | Public Markdown Gist (`announcement.md`) |
| 2 | **Dev.to (Forem)** | `POST https://dev.to/api/articles` | Published public article |
| 3 | **Telegram Bot API** | `POST https://api.telegram.org/bot<TOKEN>/sendMessage` | Broadcast message to a public channel |
| 4 | **Discord Webhook** | `POST <WEBHOOK_URL>?wait=true` | Channel message with direct permalink |
| 5 | **Mastodon API** | `POST https://<instance>/api/v1/statuses` | Public status update |

---

## Project Structure

```text
automated-posting/
│
├── app/
│   ├── main.py                  # FastAPI application, routes, and validation handlers
│   ├── schemas.py               # Pydantic request/response models & URL validation
│   ├── config.py                # Environment configuration via pydantic-settings
│   ├── platforms/
│   │   ├── base.py              # Abstract BasePlatform contract & response helpers
│   │   ├── github_gist.py       # GitHub Gist integration
│   │   ├── devto.py             # Dev.to integration
│   │   ├── telegram.py          # Telegram Bot integration
│   │   ├── discord.py           # Discord Webhook integration
│   │   └── mastodon.py          # Mastodon integration
│   └── services/
│       └── posting_service.py   # Concurrent multi-platform orchestrator
│
├── tests/
│   └── test_posting.py          # Automated validation & fault-isolation tests
│
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore rules (excludes .env & cache)
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/automated-posting.git
cd automated-posting
```

### 2. Install Dependencies

Ensure **Python 3.10+** is installed, then run:

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` into a new `.env` file:

```bash
# Windows (CMD)
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

*(Never commit your `.env` file to GitHub.)*

---

## How to Obtain API Credentials (Step-by-Step)

Fill in the credentials inside your `.env` file using the guides below:

### 1. GitHub Gist (`GITHUB_GIST_TOKEN`)
1. Open **GitHub** → Profile Picture (top-right) → **Settings**.
2. Scroll down the left sidebar → **Developer settings** → **Personal access tokens** → **Tokens (classic)**.
3. Click **Generate new token** → **Generate new token (classic)**.
4. Enter a note (e.g., `automated-posting`) and **check ONLY the `gist` scope**.
5. Click **Generate token**, copy the `ghp_...` token, and paste it into `GITHUB_GIST_TOKEN`.

### 2. Discord (`DISCORD_WEBHOOK_URL` & `DISCORD_GUILD_ID`)
1. Open **Discord** and select or create a server.
2. Enable Developer Mode: **User Settings** (gear icon) → **Advanced** → toggle on **Developer Mode**.
3. **Get Guild ID:** Right-click your server icon on the left sidebar → **Copy Server ID** → paste into `DISCORD_GUILD_ID`.
4. **Create Webhook:** Hover over a text channel (e.g., `#general`) → **Edit Channel** (gear icon) → **Integrations** → **Webhooks** → **New Webhook** → **Copy Webhook URL** → paste into `DISCORD_WEBHOOK_URL`.

### 3. Telegram (`TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHANNEL_ID`)
1. **Create Bot:** Search for **`@BotFather`** on Telegram, send `/newbot`, and follow the prompts to copy your bot token into `TELEGRAM_BOT_TOKEN`.
2. **Create Public Channel:** Create a **New Channel** in Telegram, set its type to **Public**, and assign a username (e.g., `@your_public_channel`).
3. **Promote Bot to Admin:** Open Channel Info → **Administrators** → **Add Administrator** → search your bot's username and enable **Post Messages**.
4. Paste `@your_public_channel` into `TELEGRAM_CHANNEL_ID`.

### 4. Dev.to (`DEVTO_API_KEY`)
1. Log in to [dev.to](https://dev.to) (you can sign in via GitHub).
2. Click your profile picture → **Settings** → **Extensions** tab on the left menu.
3. Scroll to the bottom (**DEV Community API Keys**), enter a description, and click **Generate API Key**.
4. Copy the generated key into `DEVTO_API_KEY`.

### 5. Mastodon (`MASTODON_INSTANCE_URL` & `MASTODON_ACCESS_TOKEN`)
1. Sign up or log in to a Mastodon instance (e.g., `https://mastodon.social` or `https://mas.to`).
2. Go to **Preferences** → **Development** → **New application**.
3. Name the application, ensure the **`write:statuses`** scope is checked, and click **Submit**.
4. Open the created application, copy **Your access token** into `MASTODON_ACCESS_TOKEN`, and set `MASTODON_INSTANCE_URL` to your instance domain.

---

## Running the Application

Start the FastAPI server on port `4000`:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 4000
```

Open the interactive Swagger UI documentation in your browser:
- **Swagger UI:** `http://localhost:4000/docs`
- **Health Check:** `http://localhost:4000/health`

---

## API Reference

### `POST /posting`

Publishes a short message containing a single CTA URL to all configured platforms.

#### Validation Rules
- `message` must not be empty and must not exceed **200 characters**.
- `message` must contain **exactly 1** valid public URL (`http://` or `https://`).

#### Request Example

```json
{
  "message": "Check out our latest business platform and grow your online visibility. https://example.com"
}
```

#### Success Response Example (`200 OK`)

```json
{
  "success": true,
  "results": [
    {
      "platform": "GitHub Gist",
      "status": "success",
      "posted_url": "https://gist.github.com/username/9f8e7d6c5b4a",
      "public_access": true,
      "date": "2026-11-17",
      "time": "03:45:12",
      "error": null
    },
    {
      "platform": "Dev.to",
      "status": "success",
      "posted_url": "https://dev.to/username/check-out-our-latest-business-platform-034512",
      "public_access": true,
      "date": "2026-11-17",
      "time": "03:45:13",
      "error": null
    },
    {
      "platform": "Telegram",
      "status": "success",
      "posted_url": "https://t.me/your_public_channel/15",
      "public_access": true,
      "date": "2026-11-17",
      "time": "03:45:12",
      "error": null
    },
    {
      "platform": "Discord",
      "status": "success",
      "posted_url": "https://discord.com/channels/123456789/987654321/1122334455",
      "public_access": true,
      "date": "2026-11-17",
      "time": "03:45:12",
      "error": null
    },
    {
      "platform": "Mastodon",
      "status": "success",
      "posted_url": "https://mastodon.social/@username/1134987654321",
      "public_access": true,
      "date": "2026-11-17",
      "time": "03:45:13",
      "error": null
    }
  ]
}
```

#### Validation Error Example (`422 Unprocessable Entity`)

```json
{
  "success": false,
  "error": "Validation failed",
  "details": [
    {
      "field": "message",
      "message": "Message must include exactly one CTA link, but none was found."
    }
  ]
}
```

---

## Running Automated Tests

Run the test suite (covering input validation and partial failure isolation) with `pytest`:

```bash
python -m pytest -v
```