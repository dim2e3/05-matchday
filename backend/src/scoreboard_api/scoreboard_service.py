from datetime import UTC, datetime

from . import config, espn_client
from .cache import TTLCache
from .normalizer import normalize_scoreboard
from .schemas import Game, ScoreboardResponse

_cache: TTLCache[ScoreboardResponse] = TTLCache(ttl_seconds=config.CACHE_TTL_SECONDS)


class UpstreamUnavailableError(Exception):
    def __init__(self, league: str) -> None:
        self.league = league
        super().__init__(f"Upstream unavailable for league: {league}")


async def get_scoreboard(league: str) -> ScoreboardResponse:
    cached = _cache.get(league)
    if cached is not None:
        return cached

    try:
        raw = await espn_client.fetch_raw_scoreboard(league)
        games = normalize_scoreboard(raw, league)
        response = ScoreboardResponse(
            league=league,
            fetched_at=datetime.now(UTC),
            stale=False,
            games=games,
        )
        _cache.set(league, response)
        return response
    except espn_client.EspnClientError:
        stale = _cache.get_stale(league)
        if stale is not None:
            return ScoreboardResponse(
                league=stale.league,
                fetched_at=stale.fetched_at,
                stale=True,
                games=stale.games,
            )
        raise UpstreamUnavailableError(league)


async def get_all_games() -> list[Game]:
    all_games: list[Game] = []
    for league in config.LEAGUES:
        try:
            response = await get_scoreboard(league)
            all_games.extend(response.games)
        except UpstreamUnavailableError:
            continue
    return all_games
