# Runbook

## How an incident flows

```
Grafana alert (user impact, per environment)
  └─► contact point "oncall-agent" ─ webhook + Bearer token ─► alert-bridge (matchday-ops)
        collects 15 min of metrics, warn/error logs with trace ids, failing traces → context.md
        └─► GitHub repository_dispatch "incident" (fine-grained PAT, contents: write)
              └─► .github/workflows/oncall.yml
                    claude -p docs/oncall-prompt.md (restricted tools: read/edit, pytest, ruff)
                    reproduce in a test → fix → tests + ruff → guard rail (backend/, docs/incidents/ only)
                    ├─ STATUS: FIXED            → PR "fix(incident): …" labelled incident
                    └─ ROOT_CAUSE_FOUND/ESCALATE → issue labelled incident
PR → CI → review → merge → CD to dev (alert resolves) → owner runs Deploy production
```

The agent never commits to main, deploys or restarts anything. Incident records live in
`docs/incidents/<id>/` (context.md, response.md) on the incident branch.

Bridge state: `curl localhost:8095/incidents` locally, or
`docker exec matchday-ops-alert-bridge-1 …` on the host. Without `GITHUB_DISPATCH_TOKEN` the
bridge runs in dry-run mode (collects context, no dispatch).

## Fans can't load live scores

5xx on `GET /api/my-games`. The API returns 502 when ESPN fails or cannot be parsed for a
followed league and no cached scoreboard exists.
1. Dashboard → *My Games requests by status*, *ESPN calls by outcome*.
2. ESPN errors (`outcome="error"`) → outage upstream: nothing to fix in code; stale cache keeps
   most fans served. If prolonged, ESCALATE.
3. ESPN ok but events dropped → see schema drift below.
4. Other 5xx (exceptions in logs, red spans) → code bug: reproduce with an API test.

## ESPN scoreboard schema drift

More than 20 % of a league's events failed to parse. Logs: `Skipping malformed event … '<key>'`,
`scoreboard parse dropped events`.
1. The missing key in the log tells what changed. Compare with the recorded fixture.
2. Fix `backend/src/matchday/normalizer.py` to accept old **and** new shapes; add a drift
   fixture and a unit test.
3. After deploy, *Scoreboard events parsed vs dropped* returns to 0 dropped and the alert
   resolves.

Demo trigger (dev or local): `make demo-drift` locally; on the host see `docs/deployment.md`.

## Telegram notifications failing

Failed/retried deliveries. Logs: `notification delivery failed id=… : sendMessage rejected: <code>`.
- 401/404 → bot token wrong or revoked: rotate `TELEGRAM_BOT_TOKEN` (no code change; ESCALATE).
- 403 → user blocked the bot: expected occasionally; persistent rise means a bug in unlinking.
- 429 → rate limit: back off / batch (code change).
- Network errors → Telegram outage: ESCALATE.

## Rollback

Run **Deploy production** with the previous tag (`/opt/matchday/prod/previous_good_tag`).
See [`deployment.md`](deployment.md#rollback).
