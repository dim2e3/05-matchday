# MatchDay Alerts

Follow your teams across the NFL, NBA, NHL and MLB, see their games live on one page, and
get a Telegram message at kickoff and at the final score. No sign-up.

**Live:** prod `https://matchday.<EC2-IP>.sslip.io` · dev `https://dev.<EC2-IP>.sslip.io`
· Grafana `https://grafana.<EC2-IP>.sslip.io` *(filled in after first deploy)*

Final project for [AI Dev Tools Zoomcamp 2026](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/tree/main/project).

## The problem

Fans who follow a few teams across leagues must open a sports app and dig through every
league's scoreboard to learn whether their team plays today, whether the game has started,
and how it ended. Generic apps need an account, push far too much, and bury the one score
that matters.

## What it does

1. **Follow teams.** Pick teams from any of the four leagues; no account, an anonymous
   cookie identifies you.
2. **My Games.** One page shows today's games of the teams you follow, with live score,
   period and clock, refreshed every 15 s. If ESPN is down you see the last known scores
   with an "out of date" banner.
3. **Telegram alerts.** Press *Connect Telegram*, tap *Start* in the bot, and you get
   "🟢 Kickoff: BOS @ NYR" when a followed game starts and "🏁 Final: BOS 3 – 2 NYR" when it
   ends — exactly once per game.
4. **Notification history** shows what was sent and whether delivery succeeded.

Expected behavior in detail, with acceptance criteria: [`docs/product/spec.md`](docs/product/spec.md).

## Run locally

```sh
cp .env.example .env      # optional: TELEGRAM_BOT_TOKEN for real messages
make up                   # app, worker, postgres, fake-espn, telemetry stack
make test                 # all test suites
```

Open http://localhost:8080 (app) and http://localhost:3000 (Grafana).

## Rubric map

| # | Criterion | Where |
|---|---|---|
| 1 | Problem description | This README, [`docs/product/spec.md`](docs/product/spec.md) |
| 2 | Product specification | [`docs/product/spec.md`](docs/product/spec.md), [GitHub Issues](../../issues), [Project board](../../projects) |
| 3 | Agent team | [`docs/team.md`](docs/team.md), [`docs/process.md`](docs/process.md), [`.claude/agents/`](.claude/agents/) |
| 4 | Context management | [`AGENTS.md`](AGENTS.md) → modular [`docs/`](docs/) |
| 5 | Application | `make up`; [`docs/architecture.md`](docs/architecture.md) |
| 6 | Testing | `make test`; [`docs/testing.md`](docs/testing.md) |
| 7 | Containerization | [`compose.yaml`](compose.yaml), Dockerfiles |
| 8 | Deployment | Live URLs above; [`docs/deployment.md`](docs/deployment.md) |
| 9 | CI/CD | [`.github/workflows/`](.github/workflows/): CI on PR, CD to dev, manual prod + rollback |
| 10 | Observability | [`docs/observability.md`](docs/observability.md) |
| 11 | Alerting | [`docs/runbook.md`](docs/runbook.md), `observability/grafana/provisioning/alerting/` |
| 12 | On-call agent | [`docs/runbook.md`](docs/runbook.md), [`.github/workflows/oncall.yml`](.github/workflows/oncall.yml), [`docs/incidents/`](docs/incidents/) |
