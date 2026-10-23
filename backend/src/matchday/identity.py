"""Anonymous cookie identity (S1): every visitor gets a random user id cookie."""

import uuid

from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from . import config
from .db import get_db
from .models import User


def _valid_uuid(value: str | None) -> bool:
    if not value:
        return False
    try:
        uuid.UUID(value)
    except ValueError:
        return False
    return True


async def current_user(
    request: Request, response: Response, db: AsyncSession = Depends(get_db)
) -> User:
    uid = request.cookies.get(config.COOKIE_NAME)
    if _valid_uuid(uid):
        user = await db.get(User, uid)
        if user is not None:
            return user

    user = User()
    db.add(user)
    await db.commit()
    response.set_cookie(
        config.COOKIE_NAME,
        user.id,
        max_age=config.COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=config.COOKIE_SECURE,
    )
    return user
