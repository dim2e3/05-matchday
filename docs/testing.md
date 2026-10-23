# Testing

| Level | Where | What | Runs against |
|---|---|---|---|
| Unit | `backend/tests/unit/` | normalizer (recorded + drift fixtures), transition detector, message text, cache | pure Python |
| Integration | `backend/tests/integration/` | API routes + DB, worker cycle with fake ESPN (respx) and mocked Telegram, exactly-once delivery | Postgres (`TEST_DATABASE_URL`), SQLite fallback locally |
| Frontend | `frontend/src/**/*.test.tsx` | components, hooks, API client | Vitest + jsdom |
| E2E | `e2e/` | follow a team → My Games shows its live score | Playwright against `make up` |

Name tests after the AC they prove: `test_s3_ac2_no_follows_returns_empty`.

```sh
make test            # unit + integration + frontend
make test-backend    # backend only
make e2e             # needs `make up`
```

Fixtures: `backend/tests/fixtures/*_scoreboard.json` are real recorded ESPN responses
(from ScoreFeed). `fake-espn` serves the same files. Drift fixtures live in
`backend/tests/fixtures/drift/`.
