# MatchDay backend

FastAPI api + background worker (package `matchday`). Overview, API and configuration:
[root README](../README.md) §7–9; design: [`docs/architecture.md`](../docs/architecture.md).

```sh
uv sync
uv run pytest -q                                   # unit + integration (SQLite)
uv run ruff check .
uv run uvicorn matchday.main:app --reload --port 8001   # api, SQLite, real ESPN
uv run python -m matchday.worker                   # worker
DATABASE_URL=postgresql+asyncpg://… uv run alembic upgrade head
```
