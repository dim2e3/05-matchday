import uuid
from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("user_id", "league", "team_id", name="uq_follow_user_team"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    league: Mapped[str] = mapped_column(String(16))
    team_id: Mapped[str] = mapped_column(String(32))
    team_name: Mapped[str] = mapped_column(String(128))
    abbreviation: Mapped[str] = mapped_column(String(16))
    logo: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class TelegramChat(Base):
    __tablename__ = "telegram_chats"

    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class TelegramLink(Base):
    __tablename__ = "telegram_links"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GameSnapshot(Base):
    __tablename__ = "game_snapshots"

    game_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    league: Mapped[str] = mapped_column(String(16))
    state: Mapped[str] = mapped_column(String(8))
    home_abbr: Mapped[str] = mapped_column(String(16))
    away_abbr: Mapped[str] = mapped_column(String(16))
    home_score: Mapped[str | None] = mapped_column(String(8), nullable=True)
    away_score: Mapped[str | None] = mapped_column(String(8), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("user_id", "game_id", "kind", name="uq_notification_once"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    game_id: Mapped[str] = mapped_column(String(32))
    league: Mapped[str] = mapped_column(String(16))
    kind: Mapped[str] = mapped_column(String(16))  # kickoff | final
    text: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
