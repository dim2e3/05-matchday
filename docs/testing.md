# Testing

| Level | Where | What | Runs against |
|---|---|---|---|
| Unit | `backend/tests/unit/` | normalizer (recorded fixtures, malformed events, teams), transition rules, message text | pure Python |
| Integration | `backend/tests/integration/` | API + DB (identity, follows, My Games, stale/502), Telegram linking and webhook auth, worker cycle: transitions, exactly-once outbox, retries, history | Postgres (`TEST_DATABASE_URL`, CI) or temp SQLite (local default); fake-espn in-process via `httpx.ASGITransport` |
| Frontend | `frontend/src/**/*.test.tsx` | components, follows context, polling hook; API mocked | Vitest + RTL + jsdom |
| E2E | `e2e/tests/` | follow → live score updates on the page; connect Telegram → kickoff + final delivered exactly once → visible in history | Playwright (Pixel 7) against `make up` |

Test names point at the story they prove (`test_s3_outage_without_cache_502`,
`"S4+S5+S6: connected fan gets kickoff and final on Telegram"`).

```sh
make test              # backend (SQLite) + frontend — fast, no Docker
make test-backend-pg   # backend against a throwaway Postgres container
make up && make e2e    # e2e; first time: npm --prefix e2e ci && npm --prefix e2e run install-browsers
```

## How the upstreams are faked

`fake-espn/app.py` is the single fake for both ESPN and Telegram, used three ways:
in-process by backend tests, as a compose service for `make up`/e2e, and on the dev
server for the incident demo. It serves the recorded `backend/tests/fixtures/*_scoreboard.json`
and has a control API:

| Call | Effect |
|---|---|
| `POST /_control/game {game_id, state, home_score, away_score}` | override one game |
| `POST /_control/drift {mode: none\|renamed_competitors\|http_500}` | simulate schema change / outage |
| `POST /_control/telegram/updates {chat_id, text}` | a user sends the bot a message |
| `GET /_control/telegram/messages` | what the bot sent |
| `POST /_control/reset` | back to fixtures |

Compose runs the worker with a 3 s poll and 2 s cache so e2e reacts quickly; production
uses 30 s / 15 s.
