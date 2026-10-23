from fastapi import APIRouter, HTTPException

from .. import scoreboard_service
from ..schemas import League, ScoreboardResponse

router = APIRouter(prefix="/api/scoreboard", tags=["scoreboard"])


@router.get("/{league}", response_model=ScoreboardResponse)
async def get_league_scoreboard(league: League) -> ScoreboardResponse:
    try:
        return await scoreboard_service.get_scoreboard(league)
    except scoreboard_service.UpstreamUnavailableError:
        raise HTTPException(
            status_code=502,
            detail={"error": "upstream_unavailable", "league": league},
        ) from None
