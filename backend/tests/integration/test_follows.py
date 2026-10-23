"""S1 identity, S2 follows, S3 My Games — API + DB + fake-espn."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

STL = {"league": "nhl", "team_id": "19"}  # St. Louis, home in game 401886427
GAME_ID = "401886427"


async def test_s1_first_call_sets_httponly_cookie(client: AsyncClient, fake_espn) -> None:
    res = await client.get("/api/me")

    assert res.status_code == 200
    cookie = res.headers["set-cookie"]
    assert cookie.startswith("md_uid=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


async def test_s1_same_cookie_reuses_user(client: AsyncClient, fake_espn) -> None:
    await client.post("/api/follows", json=STL)

    res = await client.get("/api/me")

    assert "set-cookie" not in res.headers
    assert res.json() == {"telegram_connected": False, "follows": 1}


async def test_s1_unknown_cookie_creates_new_user(client: AsyncClient, fake_espn) -> None:
    client.cookies.set("md_uid", "00000000-0000-0000-0000-000000000000")

    res = await client.get("/api/me")

    assert res.headers["set-cookie"].startswith("md_uid=")
    assert res.json()["follows"] == 0


async def test_s2_list_teams(client: AsyncClient, fake_espn) -> None:
    res = await client.get("/api/teams/nhl")

    assert res.status_code == 200
    abbreviations = {t["abbreviation"] for t in res.json()}
    assert {"TOR", "MTL", "STL", "DAL"} <= abbreviations


async def test_s2_unknown_league_422(client: AsyncClient) -> None:
    assert (await client.get("/api/teams/xyz")).status_code == 422


async def test_s2_follow_is_idempotent(client: AsyncClient, fake_espn) -> None:
    first = await client.post("/api/follows", json=STL)
    second = await client.post("/api/follows", json=STL)

    assert first.status_code == second.status_code == 200
    assert first.json()["team_name"] == "St. Louis Blues"
    follows = (await client.get("/api/follows")).json()
    assert len(follows) == 1


async def test_s2_follow_unknown_team_404(client: AsyncClient, fake_espn) -> None:
    res = await client.post("/api/follows", json={"league": "nhl", "team_id": "999"})

    assert res.status_code == 404


async def test_s2_unfollow_returns_204_always(client: AsyncClient, fake_espn) -> None:
    await client.post("/api/follows", json=STL)

    assert (await client.delete("/api/follows/nhl/19")).status_code == 204
    assert (await client.delete("/api/follows/nhl/19")).status_code == 204
    assert (await client.get("/api/follows")).json() == []


async def test_s2_follows_are_per_user(client: AsyncClient, fake_espn) -> None:
    await client.post("/api/follows", json=STL)
    client.cookies.clear()

    assert (await client.get("/api/follows")).json() == []


async def test_s3_no_follows_returns_empty(client: AsyncClient, fake_espn) -> None:
    res = await client.get("/api/my-games")

    assert res.status_code == 200
    assert res.json()["games"] == []
    assert res.json()["stale"] is False


async def test_s3_returns_only_followed_games(client: AsyncClient, fake_espn) -> None:
    await client.post("/api/follows", json=STL)

    games = (await client.get("/api/my-games")).json()["games"]

    assert [g["id"] for g in games] == [GAME_ID]
    assert games[0]["league"] == "nhl"


async def test_s3_live_score_is_shown(client: AsyncClient, fake_espn) -> None:
    await client.post("/api/follows", json=STL)
    await fake_espn.post(
        "/_control/game",
        json={"game_id": GAME_ID, "state": "in", "home_score": 2, "away_score": 1},
    )

    game = (await client.get("/api/my-games")).json()["games"][0]

    assert game["status_state"] == "in"
    scores = {c["team"]["abbreviation"]: c["team"]["score"] for c in game["competitors"]}
    assert scores == {"STL": "2", "DAL": "1"}


async def test_s3_outage_with_cache_serves_stale(client: AsyncClient, fake_espn) -> None:
    from matchday import scoreboard_service

    await client.post("/api/follows", json=STL)
    await client.get("/api/my-games")  # warm the cache
    scoreboard_service._cache._store["nhl"] = (0.0, scoreboard_service._cache._store["nhl"][1])
    await fake_espn.post("/_control/drift", json={"mode": "http_500"})

    res = await client.get("/api/my-games")

    assert res.status_code == 200
    assert res.json()["stale"] is True
    assert len(res.json()["games"]) == 1


async def test_s3_outage_without_cache_502(client: AsyncClient, fake_espn) -> None:
    await client.post("/api/follows", json=STL)
    await fake_espn.post("/_control/drift", json={"mode": "http_500"})

    res = await client.get("/api/my-games")

    assert res.status_code == 502
    assert res.json()["detail"]["error"] == "upstream_unavailable"


async def test_s3_unparseable_upstream_without_cache_502(
    client: AsyncClient, fake_espn
) -> None:
    await client.post("/api/follows", json=STL)
    await fake_espn.post("/_control/drift", json={"mode": "renamed_competitors"})

    res = await client.get("/api/my-games")

    assert res.status_code == 502
