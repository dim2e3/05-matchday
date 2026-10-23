"""S4 Connect Telegram."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from matchday.db import async_session_factory
from matchday.models import TelegramLink

pytestmark = pytest.mark.asyncio

SECRET = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
CHAT_ID = 4242


def _update(text: str, chat_id: int = CHAT_ID) -> dict:
    return {"update_id": 1, "message": {"chat": {"id": chat_id}, "text": text}}


async def _link_token(client: AsyncClient) -> str:
    res = await client.post("/api/telegram/link")
    assert res.status_code == 200
    url = res.json()["url"]
    assert url.startswith("https://t.me/")
    return url.split("?start=")[1]


async def test_s4_link_url_and_start_connects(client: AsyncClient, fake_espn) -> None:
    token = await _link_token(client)

    res = await client.post(
        "/api/telegram/webhook", json=_update(f"/start {token}"), headers=SECRET
    )

    assert res.status_code == 200
    assert (await client.get("/api/me")).json()["telegram_connected"] is True
    messages = (await fake_espn.get("/_control/telegram/messages")).json()
    assert messages[-1]["chat_id"] == CHAT_ID
    assert messages[-1]["text"].startswith("Connected")


async def test_s4_webhook_rejects_missing_or_wrong_secret(client: AsyncClient) -> None:
    no_header = await client.post("/api/telegram/webhook", json=_update("/stop"))
    wrong = await client.post(
        "/api/telegram/webhook",
        json=_update("/stop"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "nope"},
    )

    assert no_header.status_code == 401
    assert wrong.status_code == 401


async def test_s4_token_is_single_use(client: AsyncClient, fake_espn) -> None:
    token = await _link_token(client)
    await client.post("/api/telegram/webhook", json=_update(f"/start {token}"), headers=SECRET)

    await client.post(
        "/api/telegram/webhook", json=_update(f"/start {token}", chat_id=999), headers=SECRET
    )

    messages = (await fake_espn.get("/_control/telegram/messages")).json()
    assert messages[-1] == {"chat_id": 999, "text": "Link expired, press Connect Telegram again."}


async def test_s4_expired_token_is_rejected(client: AsyncClient, fake_espn) -> None:
    token = await _link_token(client)
    async with async_session_factory() as db:
        link = await db.get(TelegramLink, token)
        link.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        await db.commit()

    await client.post("/api/telegram/webhook", json=_update(f"/start {token}"), headers=SECRET)

    assert (await client.get("/api/me")).json()["telegram_connected"] is False


async def test_s4_stop_unlinks(client: AsyncClient, fake_espn) -> None:
    token = await _link_token(client)
    await client.post("/api/telegram/webhook", json=_update(f"/start {token}"), headers=SECRET)

    await client.post("/api/telegram/webhook", json=_update("/stop"), headers=SECRET)

    assert (await client.get("/api/me")).json()["telegram_connected"] is False


async def test_s4_disconnect_from_ui(client: AsyncClient, fake_espn) -> None:
    token = await _link_token(client)
    await client.post("/api/telegram/webhook", json=_update(f"/start {token}"), headers=SECRET)

    assert (await client.delete("/api/telegram/link")).status_code == 204
    assert (await client.get("/api/me")).json()["telegram_connected"] is False
