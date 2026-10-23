from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from . import config, espn_client, telegram
from .db import async_session_factory, create_all
from .routers import account, follows, scoreboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    if config.DATABASE_URL.startswith("sqlite"):
        await create_all()  # local convenience; Postgres uses Alembic migrations
    yield
    await espn_client.close_client()
    await telegram.close_client()


app = FastAPI(title="MatchDay Alerts API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scoreboard.router)
app.include_router(follows.router)
app.include_router(account.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/ready")
async def ready() -> JSONResponse:
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse({"status": "unavailable"}, status_code=503)
    return JSONResponse({"status": "ok"})


@app.get("/api/version")
async def version() -> dict[str, str]:
    return {"sha": config.GIT_SHA}
