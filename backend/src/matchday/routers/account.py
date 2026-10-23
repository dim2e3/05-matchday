"""Me, Telegram linking and notification history (S4, S6)."""

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import config, telegram
from ..db import get_db
from ..identity import current_user
from ..models import Follow, Notification, TelegramChat, User
from ..schemas import MeOut, NotificationOut, TelegramLinkOut

router = APIRouter(prefix="/api", tags=["account"])


@router.get("/me", response_model=MeOut)
async def me(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> MeOut:
    follows = await db.scalar(
        select(func.count()).select_from(Follow).where(Follow.user_id == user.id)
    )
    return MeOut(
        telegram_connected=await telegram.is_connected(db, user.id),
        follows=follows or 0,
    )


@router.post("/telegram/link", response_model=TelegramLinkOut)
async def create_telegram_link(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> TelegramLinkOut:
    token = await telegram.create_link(db, user.id)
    return TelegramLinkOut(url=telegram.link_url(token))


@router.delete("/telegram/link", status_code=204)
async def delete_telegram_link(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> Response:
    await db.execute(delete(TelegramChat).where(TelegramChat.user_id == user.id))
    await db.commit()
    return Response(status_code=204)


@router.post("/telegram/webhook")
async def telegram_webhook(
    update: dict,
    db: AsyncSession = Depends(get_db),
    secret: str | None = Header(default=None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> dict:
    expected = config.TELEGRAM_WEBHOOK_SECRET
    if not expected or not secret or not hmac.compare_digest(secret, expected):
        raise HTTPException(status_code=401, detail={"error": "bad_secret"})
    await telegram.handle_update(db, update)
    return {"ok": True}


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(
    user: User = Depends(current_user), db: AsyncSession = Depends(get_db)
) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(50)
    )
    return list(result.scalars().all())
