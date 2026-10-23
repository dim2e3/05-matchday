from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .db import init_db
from .espn_client import close_client
from .routers import favorites, scoreboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_client()


app = FastAPI(title="ScoreFeed API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scoreboard.router)
app.include_router(favorites.router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
