# Observability

```
api (matchday-api) ─┐            ┌─► Prometheus  (metrics)  ─┐
                    ├─OTLP/HTTP─► otel-collector ─► Loki (logs) ├─► Grafana ─► alerts ─► alert-bridge
worker (matchday-worker) ┘   (redact)    └─► Tempo (traces)  ─┘
```

Setup: `backend/src/matchday/telemetry.py` (`setup(service)`), enabled when
`OTEL_EXPORTER_OTLP_ENDPOINT` is set. Stack config: `observability/` (local via
`compose.yaml` include; EC2 via `deploy/compose.ops.override.yaml`). Every signal carries
`service_name` and `deployment_environment` (local | dev | prod).

## Key journey: follow team → see live score

| Signal | What |
|---|---|
| Trace | `GET /api/my-games` (FastAPI) → `SELECT …` (SQLAlchemy) → `GET` ESPN scoreboard (httpx, on cache miss). Attributes `matchday.follows/leagues/games/stale`. |
| Metrics | `http_server_request_duration_seconds{http_route="/api/my-games", http_response_status_code}` (rate, errors, p95); `matchday_espn_requests_total{league,resource,outcome}`; `matchday_scoreboard_events_total{league,outcome=parsed\|dropped}` |
| Logs | JSON, `trace_id`/`span_id` on every line: `my-games served follows=1 leagues=nhl games=1 stale=False`, `scoreboard parse dropped events league=… dropped=…`, `my-games failed: upstream unavailable` |

Background journey (ESPN poll → transition → Telegram): trace `worker cycle` → `game transition`
→ `notification send` → `telegram sendMessage`; metrics `matchday_notifications_total{kind,outcome}`,
`matchday_notification_latency_seconds` (transition → delivered), `matchday_worker_cycles_total`.

## Correlation in Grafana

Dashboard **MatchDay** (home dashboard, `$env` selector). Logs panel → click a line → **View
trace** (Loki derived field → Tempo). In a trace → **Logs for this span** (Tempo → Loki by
`trace_id`) and **Requests by route and status** (Tempo → Prometheus).

## Privacy

Never in telemetry: `md_uid` cookie, Telegram chat ids/usernames, link tokens, bot token,
webhook secret.
- Telegram client is not auto-instrumented (URL contains the token); its manual span has only
  `telegram.method`.
- No request headers/bodies are captured; httpx and DB driver loggers are capped at WARNING.
- The collector's `transform/redact` scrubs `/bot<token>/` and cookie/secret headers anyway.
- Enforced by `backend/tests/integration/test_telemetry.py`, which runs the whole journey and
  searches every span and INFO log line for each secret.

## Alerts (user impact)

`observability/grafana/provisioning/alerting/alerts.yaml`, all routed to the `oncall-agent`
contact point (see [`runbook.md`](runbook.md)):

| Alert | Condition | Impact |
|---|---|---|
| Fans can't load live scores | any 5xx on `/api/my-games` in 5 m | fans see an error instead of scores |
| ESPN scoreboard schema drift | > 20 % of a league's events dropped in 5 m, for 1 m | stale/missing scores, no notifications |
| Telegram notifications failing | any failed/retried delivery in 10 m | fans miss kickoff/final |

Local: http://localhost:3000 (anonymous admin). EC2: `https://grafana.<ip>.sslip.io` (login).
