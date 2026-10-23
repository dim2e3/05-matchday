# AGENTS.md — MatchDay Alerts

Follow teams across NFL/NBA/NHL/MLB, see their games live, get a Telegram message at kickoff
and at the final score. Built from the ScoreFeed homework (module 02).

## Read next (only what your task needs)

| Doc | When |
|---|---|
| [`docs/product/spec.md`](docs/product/spec.md) | What to build: stories and acceptance criteria |
| [`docs/team.md`](docs/team.md) | Which agent role you are and which files you own |
| [`docs/process.md`](docs/process.md) | Issue → plan → tests → PR → review → deploy |
| [`docs/architecture.md`](docs/architecture.md) | Components, API contract, data model |
| [`docs/testing.md`](docs/testing.md) | Test levels, fixtures, how to run |
| [`docs/deployment.md`](docs/deployment.md) | Compose, EC2, CI/CD, rollback |
| [`docs/observability.md`](docs/observability.md) | What telemetry to emit and where to see it |
| [`docs/runbook.md`](docs/runbook.md) | Alerts, on-call agent, incident handling |
| [`docs/decisions/`](docs/decisions/) | ADRs |

## Stack

- Backend `backend/`: Python 3.12, FastAPI, SQLAlchemy 2 async, Alembic, httpx, managed with `uv`.
  Package `matchday`. Two processes from one image: `api` and `worker`.
- Frontend `frontend/`: React 19 + TypeScript + Vite, plain CSS, Vitest + RTL.
- DB: PostgreSQL 16 (compose and prod); SQLite only in fast unit tests.
- Upstream: ESPN's unofficial `site.api.espn.com` scoreboard; `fake-espn/` replays recorded
  fixtures locally and in tests, with a `DRIFT` switch to simulate schema changes.
- Notifications: Telegram Bot API.
- Telemetry: OpenTelemetry → Collector → Prometheus / Loki / Tempo → Grafana.

## Commands

```sh
make up            # full system: app, worker, postgres, fake-espn, telemetry stack
make test          # backend unit + integration, frontend tests
make e2e           # Playwright against the running compose stack
make down
```

UI http://localhost:8080 · API http://localhost:8080/api · Grafana http://localhost:3000

## Rules

- ESPN is unreliable: 5 s timeout, serve stale cache when it fails, one malformed event never
  breaks a response. Treat ESPN 5xx/timeouts as expected, not bugs.
- `status_state` (`pre|in|post`) is the only field the UI and the worker branch on.
- Writes are idempotent (select-then-insert or unique constraint + catch), dialect-neutral.
- **Never** put cookie ids, Telegram chat ids/usernames, link tokens or secrets in logs,
  span attributes or metric labels. Use `user.hash` (sha256 prefix) if you must correlate.
- Migrations must be backward compatible with the previous release (rollback safety).
- Never push to `main`, never deploy to production, never commit `.env`.
