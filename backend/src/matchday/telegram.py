"""Telegram Bot API client and update handling (S4)."""

import logging
import secrets
from datetime import UTC, datetime, timedelta

import httpx
from opentelemetry.trace import SpanKind, Status, StatusCode
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from . import config, telemetry
from .models import TelegramChat, TelegramLink

logger = logging.getLogger(__name__)


class TelegramError(Exception):
    pass


_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=10.0)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _method_url(method: str) -> str:
    return f"{config.TELEGRAM_API_BASE}/bot{config.TELEGRAM_BOT_TOKEN}/{method}"


async def call(method: str, payload: dict, timeout: float | None = None) -> dict:
    # Manual span: method name only. Never the URL (bot token) or payload (chat id).
    with telemetry.tracer.start_as_current_span(
        f"telegram {method}", kind=SpanKind.CLIENT, attributes={"telegram.method": method}
    ) as span:
        try:
            kwargs = {"timeout": timeout} if timeout is not None else {}
            response = await get_client().post(_method_url(method), json=payload, **kwargs)
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            # The URL contains the bot token; never include it in the error text.
            span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
            raise TelegramError(f"{method} failed: {type(exc).__name__}") from exc
        span.set_attribute("http.response.status_code", response.status_code)
        if not body.get("ok"):
            span.set_status(Status(StatusCode.ERROR, "rejected"))
            raise TelegramError(
                f"{method} rejected: {response.status_code} {body.get('description', '')}"
            )
        return body.get("result", {})


async def send_message(chat_id: int, text: str) -> None:
    await call("sendMessage", {"chat_id": chat_id, "text": text})


def link_url(token: str) -> str:
    return f"https://t.me/{config.TELEGRAM_BOT_USERNAME}?start={token}"


async def create_link(db: AsyncSession, user_id: str) -> str:
    token = secrets.token_urlsafe(24)
    db.add(
        TelegramLink(
            token=token,
            user_id=user_id,
            expires_at=datetime.now(UTC)
            + timedelta(seconds=config.TELEGRAM_LINK_TTL_SECONDS),
        )
    )
    await db.commit()
    return token


def _as_aware(value: datetime) -> datetime:
    # SQLite returns naive datetimes; Postgres returns aware ones.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def _link_chat(db: AsyncSession, chat_id: int, token: str) -> str:
    link = await db.get(TelegramLink, token)
    now = datetime.now(UTC)
    if link is None or link.used_at is not None or _as_aware(link.expires_at) < now:
        return "Link expired, press Connect Telegram again."
    link.used_at = now
    # One chat per user and one user per chat: replace both sides.
    await db.execute(
        delete(TelegramChat).where(
            (TelegramChat.chat_id == chat_id) | (TelegramChat.user_id == link.user_id)
        )
    )
    db.add(TelegramChat(user_id=link.user_id, chat_id=chat_id))
    await db.commit()
    return "Connected ✅ You'll get a message at kickoff and at the final score."


async def _unlink_chat(db: AsyncSession, chat_id: int) -> str:
    await db.execute(delete(TelegramChat).where(TelegramChat.chat_id == chat_id))
    await db.commit()
    return "Disconnected. Press Connect Telegram in MatchDay to start again."


async def handle_update(db: AsyncSession, update: dict) -> None:
    """Process one Telegram update: `/start <token>` links, `/stop` unlinks."""
    message = update.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    text = (message.get("text") or "").strip()
    if chat_id is None or not text.startswith("/"):
        return

    command, _, arg = text.partition(" ")
    if command == "/start" and arg:
        reply = await _link_chat(db, chat_id, arg.strip())
    elif command == "/start":
        reply = "Open MatchDay and press Connect Telegram to link this chat."
    elif command == "/stop":
        reply = await _unlink_chat(db, chat_id)
    else:
        return
    logger.info("telegram command handled: %s", command)
    try:
        await send_message(chat_id, reply)
    except TelegramError as exc:
        logger.warning("telegram reply failed: %s", exc)


async def is_connected(db: AsyncSession, user_id: str) -> bool:
    result = await db.execute(
        select(TelegramChat.user_id).where(TelegramChat.user_id == user_id)
    )
    return result.first() is not None
