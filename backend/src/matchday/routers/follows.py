"""Teams, follows and My Games (S2, S3)."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .. import scoreboard_service
from ..db import get_db
from ..identity import current_user
from ..models import Follow, User
from ..schemas import FollowIn, FollowOut, League, MyGamesResponse, TeamInfo

router = APIRouter(prefix="/api", tags=["follows"])


def _upstream_unavailable(league: str) -> HTTPException:
    return HTTPException(
        status_code=502, detail={"error": "upstream_unavailable", "league": league}
    )


@router.get("/teams/{league}", response_model=list[TeamInfo])
async def list_teams(league: League) -> list[TeamInfo]:
    try:
        return await scoreboard_service.get_teams(league)
    except scoreboard_service.UpstreamUnavailableError:
        raise _upstream_unavailable(league) from None


async def _user_follows(db: AsyncSession, user: User) -> list[Follow]:
    result = await db.execute(
        select(Follow).where(Follow.user_id == user.id).order_by(Follow.created_at)
    )
    return list(result.scalars().all())


@router.get("/follows", response_model=list[FollowOut])
async def list_follows(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> list[Follow]:
    return await _user_follows(db, user)


@router.post("/follows", response_model=FollowOut)
async def follow_team(
    body: FollowIn,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Follow:
    """Idempotent: following an already-followed team returns the existing row."""
    query = select(Follow).where(
        Follow.user_id == user.id,
        Follow.league == body.league,
        Follow.team_id == body.team_id,
    )
    existing = (await db.execute(query)).scalar_one_or_none()
    if existing is not None:
        return existing

    try:
        teams = await scoreboard_service.get_teams(body.league)
    except scoreboard_service.UpstreamUnavailableError:
        raise _upstream_unavailable(body.league) from None
    team = next((t for t in teams if t.id == body.team_id), None)
    if team is None:
        raise HTTPException(status_code=404, detail={"error": "unknown_team"})

    row = Follow(
        user_id=user.id,
        league=body.league,
        team_id=team.id,
        team_name=team.name,
        abbreviation=team.abbreviation,
        logo=team.logo,
    )
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        # A concurrent duplicate request won the race; return its row.
        await db.rollback()
        return (await db.execute(query)).scalar_one()
    return row


@router.delete("/follows/{league}/{team_id}", status_code=204)
async def unfollow_team(
    league: League,
    team_id: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await db.execute(
        delete(Follow).where(
            Follow.user_id == user.id, Follow.league == league, Follow.team_id == team_id
        )
    )
    await db.commit()
    return Response(status_code=204)


@router.get("/my-games", response_model=MyGamesResponse)
async def my_games(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> MyGamesResponse:
    follows = await _user_follows(db, user)
    followed = {(f.league, f.team_id) for f in follows}
    leagues = sorted({f.league for f in follows})

    games = []
    stale = False
    for league in leagues:
        try:
            scoreboard = await scoreboard_service.get_scoreboard(league)
        except scoreboard_service.UpstreamUnavailableError:
            raise _upstream_unavailable(league) from None
        stale = stale or scoreboard.stale
        games.extend(
            g for g in scoreboard.games
            if any((league, c.team.id) in followed for c in g.competitors)
        )
    games.sort(key=lambda g: g.start_time)
    return MyGamesResponse(fetched_at=datetime.now(UTC), stale=stale, games=games)
