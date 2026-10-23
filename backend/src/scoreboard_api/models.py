from datetime import UTC, datetime

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class FavoriteTeam(Base):
    __tablename__ = "favorite_teams"
    __table_args__ = (UniqueConstraint("league", "team_id", name="uq_league_team"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    league: Mapped[str] = mapped_column(String(16))
    team_id: Mapped[str] = mapped_column(String(32))
    team_name: Mapped[str] = mapped_column(String(128))
    abbreviation: Mapped[str] = mapped_column(String(16))
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
