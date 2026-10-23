import httpx

from . import config


class EspnClientError(Exception):
    pass


_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=config.ESPN_TIMEOUT_SECONDS,
            headers={"User-Agent": config.ESPN_USER_AGENT},
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def fetch_raw_scoreboard(league: str) -> dict:
    if league not in config.LEAGUES:
        raise ValueError(f"Unknown league: {league}")
    sport, league_slug = config.LEAGUES[league]
    url = f"{config.ESPN_BASE_URL}/{sport}/{league_slug}/scoreboard"
    client = get_client()
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException as exc:
        raise EspnClientError(f"Timed out fetching {league} scoreboard") from exc
    except httpx.HTTPStatusError as exc:
        raise EspnClientError(
            f"ESPN returned {exc.response.status_code} for {league} scoreboard"
        ) from exc
    except httpx.HTTPError as exc:
        raise EspnClientError(f"Error fetching {league} scoreboard: {exc}") from exc
    except ValueError as exc:
        raise EspnClientError(f"Malformed JSON for {league} scoreboard") from exc
