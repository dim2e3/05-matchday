import httpx
import pytest
import respx
from httpx import AsyncClient

from scoreboard_api import config

pytestmark = pytest.mark.asyncio

RAW_NFL_EVENT = {
    "events": [
        {
            "id": "1",
            "date": "2026-09-12T18:00Z",
            "competitions": [
                {
                    "venue": {"fullName": "Test Stadium"},
                    "status": {
                        "type": {"state": "in", "shortDetail": "Q3 4:12"},
                        "period": 3,
                        "displayClock": "4:12",
                    },
                    "competitors": [
                        {
                            "id": "1",
                            "homeAway": "home",
                            "score": "14",
                            "winner": None,
                            "records": [{"summary": "1-0"}],
                            "team": {
                                "id": "26",
                                "displayName": "Seattle Seahawks",
                                "abbreviation": "SEA",
                                "logo": "logo.png",
                            },
                        },
                        {
                            "id": "2",
                            "homeAway": "away",
                            "score": "7",
                            "winner": None,
                            "records": [{"summary": "0-1"}],
                            "team": {
                                "id": "17",
                                "displayName": "New England Patriots",
                                "abbreviation": "NE",
                                "logo": "logo2.png",
                            },
                        },
                    ],
                }
            ],
        }
    ]
}


def _espn_url(league: str) -> str:
    sport, league_slug = config.LEAGUES[league]
    return f"{config.ESPN_BASE_URL}/{sport}/{league_slug}/scoreboard"


@respx.mock
async def test_get_league_scoreboard_success(client: AsyncClient) -> None:
    respx.get(_espn_url("nfl")).mock(
        return_value=httpx.Response(200, json=RAW_NFL_EVENT)
    )

    res = await client.get("/api/scoreboard/nfl")

    assert res.status_code == 200
    body = res.json()
    assert body["league"] == "nfl"
    assert body["stale"] is False
    assert len(body["games"]) == 1


async def test_get_scoreboard_invalid_league(client: AsyncClient) -> None:
    res = await client.get("/api/scoreboard/xyz")
    assert res.status_code == 422


@respx.mock
async def test_get_league_scoreboard_upstream_failure(client: AsyncClient) -> None:
    for league in config.LEAGUES:
        respx.get(_espn_url(league)).mock(side_effect=httpx.ConnectError("boom"))

    res = await client.get("/api/scoreboard/nfl")

    assert res.status_code == 502
    assert res.json()["detail"]["error"] == "upstream_unavailable"


@respx.mock
async def test_favorites_scoreboard_filters_by_favorite_team(
    client: AsyncClient,
) -> None:
    respx.get(_espn_url("nfl")).mock(
        return_value=httpx.Response(200, json=RAW_NFL_EVENT)
    )
    for league in ("nba", "nhl", "mlb"):
        respx.get(_espn_url(league)).mock(
            return_value=httpx.Response(200, json={"events": []})
        )

    await client.post(
        "/api/favorites",
        json={
            "league": "nfl",
            "team_id": "26",
            "team_name": "Seattle Seahawks",
            "abbreviation": "SEA",
        },
    )

    res = await client.get("/api/scoreboard/favorites")

    assert res.status_code == 200
    body = res.json()
    assert len(body["games"]) == 1
    assert body["games"][0]["league"] == "nfl"


@respx.mock
async def test_favorites_scoreboard_empty_when_no_favorites(
    client: AsyncClient,
) -> None:
    for league in config.LEAGUES:
        respx.get(_espn_url(league)).mock(
            return_value=httpx.Response(200, json={"events": []})
        )

    res = await client.get("/api/scoreboard/favorites")

    assert res.status_code == 200
    assert res.json()["games"] == []
