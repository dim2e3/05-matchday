# Architecture

```
 browser ──HTTPS──► Caddy ──► frontend (nginx, static Vite build)
                         └──► api (FastAPI) ──► Postgres
                                   │   ▲
                                   ▼   │ cache
                              ESPN scoreboard (or fake-espn)
                                   ▲
 Telegram ◄── sender ◄── outbox ◄─ worker (poll 30 s, detect transitions)
 Telegram ──webhook──► api /api/telegram/webhook

 api, worker ──OTLP──► otel-collector ──► Prometheus / Loki / Tempo ──► Grafana
                                                       Grafana alert ──► alert-bridge
                                                       alert-bridge ──► GitHub repository_dispatch
                                                       oncall.yml (Claude Code) ──► fix PR
```

## Components

| Component | Code | Notes |
|---|---|---|
| api | `backend/src/matchday/main.py`, `routers/` | Cookie identity middleware, REST API |
| worker | `backend/src/matchday/worker.py` | Poll loop, transition detection, outbox sender |
| ESPN client + normalizer | `espn_client.py`, `normalizer.py`, `scoreboard_service.py` | From ScoreFeed; TTL + stale cache |
| Telegram client | `telegram.py` | `sendMessage`, webhook parsing |
| fake-espn | `fake-espn/app.py` | Serves `backend/tests/fixtures/*.json`; `POST /_control` sets game state and `DRIFT` |
| frontend | `frontend/src` | Tabs: My Games, Teams, Notifications; Connect Telegram |
| alert-bridge | `alert-bridge/` | Adapted from module 04 incident responder |

## API contract

All endpoints are under `/api` and use the `md_uid` cookie for identity.

| Method | Path | Response |
|---|---|---|
| GET | `/health` | `{"status":"ok"}` |
| GET | `/ready` | 200 if DB reachable, else 503 |
| GET | `/version` | `{"sha": "<git sha>"}` |
| GET | `/me` | `{"telegram_connected": bool, "follows": int}` |
| GET | `/teams/{league}` | `[{"id","name","abbreviation","logo"}]` |
| GET | `/follows` | `[{"league","team_id","team_name","abbreviation","logo"}]` |
| POST | `/follows` | body `{"league","team_id"}` → follow (idempotent) |
| DELETE | `/follows/{league}/{team_id}` | 204 |
| GET | `/my-games` | `{"games":[Game], "stale": bool, "fetched_at": iso}` |
| GET | `/scoreboard/{league}` | ScoreFeed's scoreboard response (kept) |
| POST | `/telegram/link` | `{"url": "https://t.me/<bot>?start=<token>"}` |
| DELETE | `/telegram/link` | 204, unlink |
| POST | `/telegram/webhook` | Telegram update; header secret required |
| GET | `/notifications` | `[{"kind","text","status","created_at","sent_at"}]` |

`Game` is ScoreFeed's normalized schema: `id, league, start_time, status_state, status_detail,
period, clock, venue, competitors[{home_away, team{id,name,abbreviation,logo,score,winner,record}}]`.

## Data model

```
user(id uuid pk, created_at)
follow(id, user_id fk, league, team_id, team_name, abbreviation, logo, created_at,
       unique(user_id, league, team_id))
telegram_chat(user_id pk fk, chat_id bigint unique, linked_at)
telegram_link(token pk, user_id fk, expires_at, used_at)
game_snapshot(game_id pk, league, state, home_abbr, away_abbr, home_score, away_score,
              start_time, updated_at)
notification(id, user_id fk, game_id, kind 'kickoff'|'final', text, status, attempts,
             created_at, sent_at, unique(user_id, game_id, kind))
```

## Worker cycle

1. Leagues with ≥1 follow → fetch + normalize scoreboard (shared cache code).
2. For each game: load snapshot; if `old.state='pre' and new.state='in'` → kickoff; if
   `old.state='in' and new.state='post'` → final; no snapshot → store only (no notify).
3. Insert notification rows for connected followers (`ON CONFLICT`-free: catch unique
   violation per row) and upsert the snapshot, in one transaction.
4. Sender: claim `pending` rows (`FOR UPDATE SKIP LOCKED` on Postgres), send, mark
   `sent` or retry with backoff; `failed` after 3 attempts.
