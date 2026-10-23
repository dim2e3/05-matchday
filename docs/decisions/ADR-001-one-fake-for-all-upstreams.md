# ADR-001: One fake service for ESPN and Telegram

**Status:** accepted · 2026-10-23

## Context
ESPN's scoreboard API is unofficial and only has live games at certain hours; Telegram
needs a real bot and a public webhook. Tests, e2e, local demos and the incident demo all need
deterministic upstreams, including a way to break them on purpose.

## Decision
`fake-espn/app.py` serves recorded ESPN fixtures and a Telegram Bot API sink, with a control
API (`/_control/game`, `/_control/drift`, `/_control/telegram/*`). The same file runs
in-process in backend tests (httpx `ASGITransport`), as a compose service locally and in CI
e2e, and in the dev environment on EC2. Production uses the real services.

## Consequences
- Every test level exercises the same upstream behavior; no `respx` route tables to keep in sync.
- The incident demo (`DRIFT=renamed_competitors`) is reproducible on dev without touching prod.
- dev does not show real games; prod is the place to see real ESPN data.
- The fake must behave like the real thing where we depend on it (e.g. monotonically
  increasing Telegram `update_id`s — a bug found by e2e).
