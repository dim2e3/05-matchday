import os

ESPN_BASE_URL = os.environ.get(
    "ESPN_BASE_URL", "https://site.api.espn.com/apis/site/v2/sports"
)

LEAGUES: dict[str, tuple[str, str]] = {
    "nfl": ("football", "nfl"),
    "nba": ("basketball", "nba"),
    "nhl": ("hockey", "nhl"),
    "mlb": ("baseball", "mlb"),
}

CACHE_TTL_SECONDS = 15
TEAMS_CACHE_TTL_SECONDS = 24 * 3600
ESPN_TIMEOUT_SECONDS = 5.0
ESPN_USER_AGENT = "matchday-alerts/0.1 (+https://github.com/)"

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./matchday.db")

CORS_ORIGINS = ["http://localhost:5173"]

# Identity cookie. Secure only behind HTTPS (prod/dev on EC2).
COOKIE_NAME = "md_uid"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
COOKIE_MAX_AGE_SECONDS = 365 * 24 * 3600

GIT_SHA = os.environ.get("GIT_SHA", "dev")

# Telegram. TELEGRAM_API_BASE points at fake-espn's sink locally.
TELEGRAM_API_BASE = os.environ.get("TELEGRAM_API_BASE", "https://api.telegram.org")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "matchday_alerts_bot")
TELEGRAM_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
# "webhook" (prod: Telegram calls /api/telegram/webhook) or "polling" (worker calls getUpdates).
TELEGRAM_MODE = os.environ.get("TELEGRAM_MODE", "webhook")
TELEGRAM_LINK_TTL_SECONDS = 15 * 60

# Worker.
POLL_INTERVAL_SECONDS = float(os.environ.get("POLL_INTERVAL_SECONDS", "30"))
SEND_MAX_ATTEMPTS = 3
SEND_BACKOFF_SECONDS = (10, 60)  # delay before attempt 2 and 3
# A snapshot older than this is not trusted to detect transitions (no back-fill).
SNAPSHOT_MAX_AGE_SECONDS = 6 * 3600
