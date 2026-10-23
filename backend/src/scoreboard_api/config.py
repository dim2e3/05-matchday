import os

ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

LEAGUES: dict[str, tuple[str, str]] = {
    "nfl": ("football", "nfl"),
    "nba": ("basketball", "nba"),
    "nhl": ("hockey", "nhl"),
    "mlb": ("baseball", "mlb"),
}

CACHE_TTL_SECONDS = 15
ESPN_TIMEOUT_SECONDS = 5.0
ESPN_USER_AGENT = "scorefeed-homework/0.1 (+https://github.com/)"

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "sqlite+aiosqlite:///./scorefeed.db"
)

CORS_ORIGINS = ["http://localhost:5173"]
