import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_list_favorites_starts_empty(client: AsyncClient) -> None:
    res = await client.get("/api/favorites")
    assert res.status_code == 200
    assert res.json() == []


async def test_add_and_list_favorite(client: AsyncClient) -> None:
    payload = {
        "league": "nfl",
        "team_id": "26",
        "team_name": "Seattle Seahawks",
        "abbreviation": "SEA",
    }
    res = await client.post("/api/favorites", json=payload)
    assert res.status_code == 201
    body = res.json()
    assert body["league"] == "nfl"
    assert body["team_id"] == "26"

    res = await client.get("/api/favorites")
    assert res.status_code == 200
    assert len(res.json()) == 1


async def test_add_favorite_is_idempotent(client: AsyncClient) -> None:
    payload = {
        "league": "nfl",
        "team_id": "26",
        "team_name": "Seattle Seahawks",
        "abbreviation": "SEA",
    }
    await client.post("/api/favorites", json=payload)
    await client.post("/api/favorites", json=payload)

    res = await client.get("/api/favorites")
    assert len(res.json()) == 1


async def test_remove_favorite_is_idempotent(client: AsyncClient) -> None:
    payload = {
        "league": "nfl",
        "team_id": "26",
        "team_name": "Seattle Seahawks",
        "abbreviation": "SEA",
    }
    await client.post("/api/favorites", json=payload)

    res = await client.delete("/api/favorites/nfl/26")
    assert res.status_code == 204

    res = await client.get("/api/favorites")
    assert res.json() == []

    res = await client.delete("/api/favorites/nfl/26")
    assert res.status_code == 204
