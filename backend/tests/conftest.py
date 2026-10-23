import os
import tempfile

_tmp_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp_dir}/test.db"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from scoreboard_api.db import Base, engine
from scoreboard_api.main import app
from scoreboard_api.scoreboard_service import _cache


@pytest_asyncio.fixture(autouse=True)
async def _reset_state():
    _cache._store.clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
