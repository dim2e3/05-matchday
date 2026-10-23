"""Shared fixtures.

DB: Postgres when TEST_DATABASE_URL is set (CI, compose), otherwise a temp SQLite file.
Upstreams: the real fake-espn app (../../fake-espn/app.py) served in-process through
httpx's ASGITransport, so tests hit exactly what `make up` runs.
"""

import importlib.util
import os
import sys
import tempfile
from pathlib import Path

_tmp_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", f"sqlite+aiosqlite:///{_tmp_dir}/test.db"
)
os.environ["ESPN_BASE_URL"] = "http://fake-espn/apis/site/v2/sports"
os.environ["TELEGRAM_API_BASE"] = "http://fake-espn/telegram"
os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
os.environ["TELEGRAM_WEBHOOK_SECRET"] = "test-secret"

FIXTURES_DIR = Path(__file__).parent / "fixtures"
os.environ["FIXTURES_DIR"] = str(FIXTURES_DIR)

import httpx  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from matchday import espn_client, scoreboard_service, telegram  # noqa: E402
from matchday.db import Base, engine  # noqa: E402
from matchday.main import app  # noqa: E402


def _load_fake_espn():
    path = Path(__file__).resolve().parents[2] / "fake-espn" / "app.py"
    spec = importlib.util.spec_from_file_location("fake_espn_app", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["fake_espn_app"] = module
    spec.loader.exec_module(module)
    return module


fake_espn_module = _load_fake_espn()


@pytest_asyncio.fixture(autouse=True)
async def _reset_state():
    scoreboard_service.clear_caches()
    fake_espn_module.state.reset()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await espn_client.close_client()
    await telegram.close_client()


@pytest_asyncio.fixture
async def fake_espn():
    """Route the app's ESPN and Telegram clients to the in-process fake-espn."""
    transport = ASGITransport(app=fake_espn_module.app)
    espn_client._client = httpx.AsyncClient(transport=transport, timeout=5.0)
    telegram._client = httpx.AsyncClient(transport=transport, timeout=5.0)
    async with AsyncClient(transport=transport, base_url="http://fake-espn") as control:
        yield control


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
