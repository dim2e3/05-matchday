"""Background worker (S5): poll ESPN, detect game transitions, deliver the outbox.

Run with `python -m matchday.worker`.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from opentelemetry.trace import Status, StatusCode
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from . import config, espn_client, scoreboard_service, telegram, telemetry
from .db import async_session_factory, engine
from .models import Follow, GameSnapshot, Notification, TelegramChat
from .notifier import detect_transition, format_message
from .schemas import Game

logger = logging.getLogger("matchday.worker")


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _side(game: Game, home_away: str):
    return next(c.team for c in game.competitors if c.home_away == home_away)


async def _followed_leagues(db: AsyncSession) -> list[str]:
    result = await db.execute(select(Follow.league).distinct())
    return sorted(result.scalars().all())


async def _recipients(db: AsyncSession, game: Game) -> list[str]:
    """Connected users following either team of the game."""
    team_ids = [c.team.id for c in game.competitors]
    result = await db.execute(
        select(Follow.user_id)
        .join(TelegramChat, TelegramChat.user_id == Follow.user_id)
        .where(Follow.league == game.league, Follow.team_id.in_(team_ids))
        .distinct()
    )
    return list(result.scalars().all())


async def _enqueue(db: AsyncSession, game: Game, kind: str, user_ids: list[str]) -> int:
    text = format_message(game, kind)
    created = 0
    for user_id in user_ids:
        try:
            async with db.begin_nested():
                db.add(
                    Notification(
                        user_id=user_id,
                        game_id=game.id,
                        league=game.league,
                        kind=kind,
                        text=text,
                    )
                )
            created += 1
        except IntegrityError:
            pass  # already enqueued: (user, game, kind) is delivered at most once
    return created


async def process_game(db: AsyncSession, game: Game, now: datetime) -> int:
    """Update the game's snapshot; enqueue notifications on a transition."""
    snapshot = await db.get(GameSnapshot, game.id)
    home, away = _side(game, "home"), _side(game, "away")

    kind = None
    if snapshot is not None:
        fresh = now - _as_aware(snapshot.updated_at) <= timedelta(
            seconds=config.SNAPSHOT_MAX_AGE_SECONDS
        )
        if fresh:
            kind = detect_transition(snapshot.state, game.status_state)
    else:
        snapshot = GameSnapshot(game_id=game.id, league=game.league)
        db.add(snapshot)

    snapshot.state = game.status_state
    snapshot.home_abbr, snapshot.away_abbr = home.abbreviation, away.abbreviation
    snapshot.home_score, snapshot.away_score = home.score, away.score
    snapshot.start_time = game.start_time
    snapshot.updated_at = now

    if kind is None:
        return 0
    with telemetry.tracer.start_as_current_span(
        "game transition",
        attributes={"matchday.league": game.league, "matchday.game_id": game.id,
                    "matchday.kind": kind},
    ) as span:
        created = await _enqueue(db, game, kind, await _recipients(db, game))
        span.set_attribute("matchday.enqueued", created)
        telemetry.notifications.add(created, {"kind": kind, "outcome": "enqueued"})
        logger.info(
            "game transition league=%s game=%s kind=%s enqueued=%d",
            game.league, game.id, kind, created,
        )
    return created


async def poll_once() -> int:
    """One poll cycle over all followed leagues. Returns notifications enqueued."""
    now = datetime.now(UTC)
    enqueued = 0
    async with async_session_factory() as db:
        for league in await _followed_leagues(db):
            try:
                scoreboard = await scoreboard_service.get_scoreboard(league)
            except scoreboard_service.UpstreamUnavailableError:
                logger.warning("skipping league=%s: upstream unavailable", league)
                continue
            if scoreboard.stale:
                continue  # stale data cannot show a new transition
            for game in scoreboard.games:
                enqueued += await process_game(db, game, now)
            await db.commit()
    return enqueued


async def send_pending(limit: int = 50) -> int:
    """Deliver due notifications. Returns how many were sent."""
    now = datetime.now(UTC)
    sent = 0
    async with async_session_factory() as db:
        result = await db.execute(
            select(Notification, TelegramChat.chat_id)
            .outerjoin(TelegramChat, TelegramChat.user_id == Notification.user_id)
            .where(Notification.status == "pending", Notification.next_attempt_at <= now)
            .order_by(Notification.id)
            .limit(limit)
            .with_for_update(of=Notification, skip_locked=True)
        )
        for notification, chat_id in result.all():
            kind = notification.kind
            if chat_id is None:
                notification.status = "failed"  # user disconnected before delivery
                telemetry.notifications.add(1, {"kind": kind, "outcome": "failed"})
                continue
            notification.attempts += 1
            with telemetry.tracer.start_as_current_span(
                "notification send",
                attributes={"matchday.notification_id": notification.id, "matchday.kind": kind,
                            "matchday.attempt": notification.attempts},
            ):
                try:
                    await telegram.send_message(chat_id, notification.text)
                except telegram.TelegramError as exc:
                    logger.warning(
                        "notification delivery failed id=%s attempt=%d: %s",
                        notification.id, notification.attempts, exc,
                    )
                    if notification.attempts >= config.SEND_MAX_ATTEMPTS:
                        notification.status = "failed"
                        telemetry.notifications.add(1, {"kind": kind, "outcome": "failed"})
                    else:
                        delay = config.SEND_BACKOFF_SECONDS[notification.attempts - 1]
                        notification.next_attempt_at = now + timedelta(seconds=delay)
                        telemetry.notifications.add(1, {"kind": kind, "outcome": "retry"})
                    continue
                notification.status = "sent"
                notification.sent_at = datetime.now(UTC)
                telemetry.notifications.add(1, {"kind": kind, "outcome": "sent"})
                telemetry.notification_latency.record(
                    (notification.sent_at - _as_aware(notification.created_at)).total_seconds(),
                    {"kind": kind},
                )
                logger.info("notification sent id=%s kind=%s", notification.id, kind)
                sent += 1
        await db.commit()
    return sent


async def poll_telegram_updates(offset: int) -> int:
    """Long-poll getUpdates (TELEGRAM_MODE=polling, for local runs without a
    public webhook URL). Returns the next offset."""
    updates = await telegram.call(
        "getUpdates", {"offset": offset, "timeout": 20}, timeout=30.0
    )
    for update in updates:
        async with async_session_factory() as db:
            await telegram.handle_update(db, update)
        offset = update["update_id"] + 1
    return offset


async def _telegram_loop() -> None:
    offset = 0
    while True:
        try:
            offset = await poll_telegram_updates(offset)
        except telegram.TelegramError as exc:
            logger.warning("getUpdates failed: %s", exc)
            await asyncio.sleep(5)


async def run_cycle() -> None:
    """One traced worker cycle: poll ESPN, then deliver due notifications."""
    with telemetry.tracer.start_as_current_span("worker cycle") as span:
        try:
            enqueued = await poll_once()
            sent = await send_pending()
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
            telemetry.worker_cycles.add(1, {"outcome": "error"})
            logger.exception("worker cycle failed")
            return
        span.set_attributes({"matchday.enqueued": enqueued, "matchday.sent": sent})
        telemetry.worker_cycles.add(1, {"outcome": "ok"})


async def _main_loop() -> None:
    while True:
        await run_cycle()
        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)


async def main() -> None:
    telemetry.setup("matchday-worker")
    telemetry.instrument_db(engine)
    logger.info("worker started poll_interval=%ss", config.POLL_INTERVAL_SECONDS)
    tasks = [_main_loop()]
    if config.TELEGRAM_MODE == "polling" and config.TELEGRAM_BOT_TOKEN:
        await telegram.call("deleteWebhook", {})
        tasks.append(_telegram_loop())
    try:
        await asyncio.gather(*tasks)
    finally:
        await espn_client.close_client()
        await telegram.close_client()


if __name__ == "__main__":
    asyncio.run(main())
