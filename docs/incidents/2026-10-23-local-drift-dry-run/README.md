# 2026-10-23 · ESPN scoreboard schema drift (local, dry run)

First end-to-end check of the alert path on the local stack, before GitHub/EC2 existed.

| Step | Result |
|---|---|
| Trigger | `make demo-drift` → fake-espn renames `competitions[].competitors` → `teams`, `score` → `{"value": …}` |
| User impact | NHL games disappear from My Games after the cache expires; no kickoff/final notifications |
| Alert | **ESPN scoreboard schema drift** fired (`league=nhl`, `deployment_environment=local`): "40.68% of nhl scoreboard events were dropped…" |
| alert-bridge | received the webhook (Bearer token), collected 15 min of telemetry → [`context.md`](context.md); dispatch **dry-run** (no GitHub token yet) |
| On-call agent | not run yet — needs the repo, `ANTHROPIC_API_KEY` and `ONCALL_GH_TOKEN` |

The context shows the evidence the agent works from: the parsed/dropped table, and log lines
`Skipping malformed event for league=nhl id=…: 'competitors'` with trace ids.
