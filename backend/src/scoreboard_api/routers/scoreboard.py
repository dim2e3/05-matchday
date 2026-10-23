from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import scoreboard_service
from ..db import get_db
from ..models import FavoriteTeam
from ..schemas import FavoritesScoreboardResponse, ScoreboardResponse

router = APIRouter(prefix="/api/scoreboard", tags=["scoreboard"])

League = Literal["nfl", "nba", "nhl", "mlb"]


@router.get("/favorites", response_model=FavoritesScoreboardResponse)
async def get_favorites_scoreboard(
    db: AsyncSession = Depends(get_db),
) -> FavoritesScoreboardResponse:
    result = await db.execute(select(FavoriteTeam))
    favorites = result.scalars().all()
    favorite_keys = {(f.league, f.team_id) for f in favorites}

    all_games = await scoreboard_service.get_all_games()

    matching_games = [
        game
        for game in all_games
        if any((game.league, c.team.id) in favorite_keys for c in game.competitors)
    ]
    matching_games.sort(key=lambda g: g.start_time)

    return FavoritesScoreboardResponse(
        fetched_at=datetime.now(UTC), games=matching_games
    )


@router.get("/{league}", response_model=ScoreboardResponse)
async def get_league_scoreboard(league: League) -> ScoreboardResponse:
    try:
        return await scoreboard_service.get_scoreboard(league)
    except scoreboard_service.UpstreamUnavailableError:
        raise HTTPException(
            status_code=502,
            detail={"error": "upstream_unavailable", "league": league},
        )
