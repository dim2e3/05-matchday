"""S5 notifications and S6 history — worker cycle against fake-espn + DB."""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from matchday import scoreboard_service, worker
from matchday.db import async_session_factory
from matchday.models import GameSnapshot, Notification

pytestmark = pytest.mark.asyncio

GAME_ID = "401886427"  # DAL @ STL
SECRET = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}


async def _connected_fan(client: AsyncClient, chat_id: int = 777, team_id: str = "19") -> None:
    await client.post("/api/follows", json={"league": "nhl", "team_id": team_id})
    token = (await client.post("/api/telegram/link")).json()["url"].split("?start=")[1]
    update_ = {"update_id": 1, "message": {"chat": {"id": chat_id}, "text": f"/start {token}"}}
    await client.post("/api/telegram/webhook", json=update_, headers=SECRET)


async def _set_game(fake_espn, state: str, home: int = 0, away: int = 0) -> None:
    await fake_espn.post(
        "/_control/game",
        json={"game_id": GAME_ID, "state": state, "home_score": home, "away_score": away},
    )
    scoreboard_service.clear_caches()


async def _cycle() -> int:
    enqueued = await worker.poll_once()
    await worker.send_pending()
    return enqueued


async def _game_messages(fake_espn) -> list[str]:
    messages = (await fake_espn.get("/_control/telegram/messages")).json()
    return [m["text"] for m in messages if not m["text"].startswith("Connected")]


async def test_s5_kickoff_and_final_are_sent_once(client: AsyncClient, fake_espn) -> None:
    await _connected_fan(client)

    await _cycle()  # first sight: pre, no notification
    await _set_game(fake_espn, "in", 1, 0)
    await _cycle()
    await _cycle()  # still live: nothing new
    await _set_game(fake_espn, "post", 3, 2)
    await _cycle()
    await _cycle()

    assert await _game_messages(fake_espn) == [
        "🟢 Kickoff: DAL @ STL (NHL)",
        "🏁 Final: DAL 2 – 3 STL (NHL)",
    ]


async def test_s5_game_first_seen_final_does_not_notify(client: AsyncClient, fake_espn) -> None:
    await _connected_fan(client)
    await _set_game(fake_espn, "post", 3, 2)

    assert await _cycle() == 0
    assert await _game_messages(fake_espn) == []


async def test_s5_old_snapshot_does_not_backfill(client: AsyncClient, fake_espn) -> None:
    await _connected_fan(client)
    await _cycle()
    async with async_session_factory() as db:
        await db.execute(
            update(GameSnapshot).values(updated_at=datetime.now(UTC) - timedelta(hours=7))
        )
        await db.commit()
    await _set_game(fake_espn, "post", 3, 2)

    assert await _cycle() == 0


async def test_s5_only_connected_followers_are_notified(client: AsyncClient, fake_espn) -> None:
    await client.post("/api/follows", json={"league": "nhl", "team_id": "19"})  # not connected
    client.cookies.clear()
    await _connected_fan(client, chat_id=1, team_id="9")  # follows the away team (DAL)
    client.cookies.clear()
    await _connected_fan(client, chat_id=2, team_id="21")  # TOR, not in this game

    await _cycle()
    await _set_game(fake_espn, "in")
    await _cycle()

    messages = (await fake_espn.get("/_control/telegram/messages")).json()
    kickoffs = [m["chat_id"] for m in messages if m["text"].startswith("🟢")]
    assert kickoffs == [1]


async def test_s5_enqueue_is_idempotent_across_restarts(client: AsyncClient, fake_espn) -> None:
    await _connected_fan(client)
    await _cycle()
    await _set_game(fake_espn, "in")
    await worker.poll_once()
    # Simulate a restart that lost the snapshot update: same transition seen again.
    async with async_session_factory() as db:
        await db.execute(update(GameSnapshot).values(state="pre"))
        await db.commit()
    scoreboard_service.clear_caches()
    await worker.poll_once()

    async with async_session_factory() as db:
        rows = (await db.execute(select(Notification))).scalars().all()
    assert [(r.kind, r.game_id) for r in rows] == [("kickoff", GAME_ID)]


async def test_s5_delivery_retries_then_fails(client: AsyncClient, fake_espn, monkeypatch) -> None:
    await _connected_fan(client)
    await _cycle()
    await _set_game(fake_espn, "in")
    await worker.poll_once()

    async def broken(chat_id: int, text: str) -> None:
        raise worker.telegram.TelegramError("sendMessage rejected: 500")

    monkeypatch.setattr(worker.telegram, "send_message", broken)
    for _ in range(3):
        await worker.send_pending()
        async with async_session_factory() as db:  # make the retry due now
            await db.execute(update(Notification).values(next_attempt_at=datetime.now(UTC)))
            await db.commit()

    async with async_session_factory() as db:
        row = (await db.execute(select(Notification))).scalar_one()
    assert (row.status, row.attempts) == ("failed", 3)


async def test_s6_notification_history(client: AsyncClient, fake_espn) -> None:
    await _connected_fan(client)
    await _cycle()
    await _set_game(fake_espn, "in")
    await _cycle()

    history = (await client.get("/api/notifications")).json()

    assert len(history) == 1
    assert history[0]["kind"] == "kickoff"
    assert history[0]["status"] == "sent"
    assert history[0]["sent_at"] is not None


async def test_s5_worker_polls_only_followed_leagues(
    client: AsyncClient, fake_espn, monkeypatch
) -> None:
    await client.post("/api/follows", json={"league": "nhl", "team_id": "19"})
    polled: list[str] = []
    original = scoreboard_service.get_scoreboard

    async def spy(league: str):
        polled.append(league)
        return await original(league)

    monkeypatch.setattr(worker.scoreboard_service, "get_scoreboard", spy)
    await worker.poll_once()

    assert polled == ["nhl"]
