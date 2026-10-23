from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models import FavoriteTeam
from ..schemas import FavoriteTeamIn, FavoriteTeamOut

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("", response_model=list[FavoriteTeamOut])
async def list_favorites(db: AsyncSession = Depends(get_db)) -> list[FavoriteTeam]:
    result = await db.execute(select(FavoriteTeam).order_by(FavoriteTeam.added_at))
    return list(result.scalars().all())


@router.post("", response_model=FavoriteTeamOut, status_code=201)
async def add_favorite(
    favorite: FavoriteTeamIn, db: AsyncSession = Depends(get_db)
) -> FavoriteTeam:
    """Idempotent add: relies on the (league, team_id) unique constraint, not a
    dialect-specific upsert, so this stays portable across database backends."""
    existing = await db.execute(
        select(FavoriteTeam).where(
            FavoriteTeam.league == favorite.league,
            FavoriteTeam.team_id == favorite.team_id,
        )
    )
    found = existing.scalar_one_or_none()
    if found is not None:
        return found

    row = FavoriteTeam(
        league=favorite.league,
        team_id=favorite.team_id,
        team_name=favorite.team_name,
        abbreviation=favorite.abbreviation,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@router.delete("/{league}/{team_id}", status_code=204)
async def remove_favorite(
    league: str, team_id: str, db: AsyncSession = Depends(get_db)
) -> Response:
    await db.execute(
        delete(FavoriteTeam).where(
            FavoriteTeam.league == league, FavoriteTeam.team_id == team_id
        )
    )
    await db.commit()
    return Response(status_code=204)
