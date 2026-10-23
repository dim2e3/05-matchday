import logging
from datetime import UTC, datetime

from . import config, espn_client
from .cache import TTLCache
from .normalizer import normalize_teams, parse_scoreboard
from .schemas import ScoreboardResponse, TeamInfo

logger = logging.getLogger(__name__)

_cache: TTLCache[ScoreboardResponse] = TTLCache(ttl_seconds=config.CACHE_TTL_SECONDS)
_teams_cache: TTLCache[list[TeamInfo]] = TTLCache(
    ttl_seconds=config.TEAMS_CACHE_TTL_SECONDS
)


class UpstreamUnavailableError(Exception):
    def __init__(self, league: str) -> None:
        self.league = league
        super().__init__(f"Upstream unavailable for league: {league}")


class UpstreamSchemaError(espn_client.EspnClientError):
    """ESPN answered, but none of its events could be parsed — most likely a
    schema change. Handled like an outage: stale cache, else 502."""


async def get_scoreboard(league: str) -> ScoreboardResponse:
    cached = _cache.get(league)
    if cached is not None:
        return cached

    try:
        raw = await espn_client.fetch_raw_scoreboard(league)
        result = parse_scoreboard(raw, league)
        if result.dropped and not result.games:
            raise UpstreamSchemaError(
                f"All {result.dropped} {league} events failed to parse"
            )
        response = ScoreboardResponse(
            league=league,
            fetched_at=datetime.now(UTC),
            stale=False,
            games=result.games,
        )
        _cache.set(league, response)
        return response
    except espn_client.EspnClientError as exc:
        logger.warning("ESPN scoreboard failed for league=%s: %s", league, exc)
        stale = _cache.get_stale(league)
        if stale is not None:
            return ScoreboardResponse(
                league=stale.league,
                fetched_at=stale.fetched_at,
                stale=True,
                games=stale.games,
            )
        raise UpstreamUnavailableError(league) from exc


async def get_teams(league: str) -> list[TeamInfo]:
    cached = _teams_cache.get(league)
    if cached is not None:
        return cached
    try:
        teams = normalize_teams(await espn_client.fetch_raw_teams(league))
    except espn_client.EspnClientError as exc:
        stale = _teams_cache.get_stale(league)
        if stale is not None:
            return stale
        raise UpstreamUnavailableError(league) from exc
    if not teams:
        raise UpstreamUnavailableError(league)
    _teams_cache.set(league, teams)
    return teams


def clear_caches() -> None:
    _cache._store.clear()
    _teams_cache._store.clear()
