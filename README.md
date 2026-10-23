# MatchDay Alerts

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

Follow your teams across the NFL, NBA, NHL and MLB, see their games live on one page, and
get a Telegram message at kickoff and at the final score. No sign-up.

| | |
|---|---|
| **Production** | `https://matchday.<EC2-IP>.sslip.io` *(after first deploy)* |
| **Dev** (fake upstreams, incident demo) | `https://dev.<EC2-IP>.sslip.io` |
| **Grafana** | `https://grafana.<EC2-IP>.sslip.io` |

Final project for [AI Dev Tools Zoomcamp 2026](https://github.com/DataTalksClub/ai-dev-tools-zoomcamp/tree/main/project),
grown from the module 02 ScoreFeed homework, with the module 03 deployment and module 04
observability/incident-response patterns.

<p>
  <img src="docs/img/my-games.png" alt="My Games on a phone" width="260">
  <img src="docs/img/teams.png" alt="Team picker" width="260">
</p>

## The problem

Fans who follow a few teams across leagues must open a sports app and dig through every
league's scoreboard to learn whether their team plays today, whether the game has started,
and how it ended. Generic apps need an account, push far too much, and bury the one score
that matters.

## What it does

1. **Follow teams.** Pick teams from any of the four leagues. No account: an anonymous
   HttpOnly cookie identifies you.
2. **My Games.** One page shows today's games of the teams you follow, with live score,
   period and clock, refreshed every 15 s. If ESPN is down you see the last known scores with
   an "out of date" banner instead of an error.
3. **Telegram alerts.** Press *Connect Telegram*, tap *Start* in the bot, and you get
   "🟢 Kickoff: DAL @ STL (NHL)" when a followed game starts and "🏁 Final: DAL 2 – 3 STL (NHL)"
   when it ends — exactly once per game. `/stop` in the bot unlinks.
4. **Notification history** shows what was sent and whether delivery succeeded.

Stories and acceptance criteria: [`docs/product/spec.md`](docs/product/spec.md).

## Architecture

```
browser ─► Caddy (HTTPS) ─► frontend (nginx + React) ─► api (FastAPI) ─► Postgres
                                                          │        ▲
                                     ESPN scoreboard ◄────┴─ worker (poll → transitions → outbox → Telegram)
api, worker ─OTLP─► collector ─► Prometheus · Loki · Tempo ─► Grafana ─alert─► alert-bridge
                                         alert-bridge ─repository_dispatch─► on-call agent (Claude Code, GitHub Actions) ─► fix PR
```

Details: [`docs/architecture.md`](docs/architecture.md) · decisions: [`docs/decisions/`](docs/decisions/).

## Run locally

Requirements: Docker with compose v2. For tests also `uv` and Node 22.

```sh
make up        # app, worker, postgres, fake-espn, OTel collector, Prometheus, Loki, Tempo, Grafana, alert-bridge
```

| URL | |
|---|---|
| http://localhost:8080 | MatchDay |
| http://localhost:3000 | Grafana (dashboard **MatchDay**) |
| http://localhost:8090/_control | fake ESPN + Telegram state |
| http://localhost:8095/incidents | alert-bridge incidents |

Locally ESPN and Telegram are replaced by `fake-espn`. Drive a game by hand:
`make demo-live`, `make demo-final` (game DAL @ STL — follow St. Louis Blues first),
`make demo-drift` (break the ESPN schema → alert → incident), `make demo-reset`.
To use the real ESPN API: `ESPN_BASE_URL=https://site.api.espn.com/apis/site/v2/sports make up`.

## Tests

```sh
make test              # backend unit + integration (53), alert-bridge (5), frontend (33)
make test-backend-pg   # backend suite against a real Postgres container
make up && make e2e    # Playwright: follow → live score; Telegram → kickoff + final exactly once
```

See [`docs/testing.md`](docs/testing.md).

## How it was built: agent team

The project is built by a team of Claude Code subagents — product owner, architect, backend
and frontend developers, QA, DevOps, reviewer — plus an on-call agent woken by alerts. Roles,
file ownership and hand-offs: [`docs/team.md`](docs/team.md); workflow from issue to production:
[`docs/process.md`](docs/process.md). Every agent starts from [`AGENTS.md`](AGENTS.md).

![Grafana dashboard during the schema-drift demo](docs/img/grafana-dashboard.png)

## Rubric map

| # | Criterion | Evidence |
|---|---|---|
| 1 | Problem description | This README · [`docs/product/spec.md`](docs/product/spec.md) |
| 2 | Product specification | [`spec.md`](docs/product/spec.md) (8 stories, Given/When/Then ACs) · [Issues](../../issues) and [project board](../../projects), created from the spec by [`scripts/bootstrap-github.sh`](scripts/bootstrap-github.sh) · tests named after ACs (`test_s3_…`) |
| 3 | Agent team | [`docs/team.md`](docs/team.md) · [`docs/process.md`](docs/process.md) · [`.claude/agents/`](.claude/agents/) (7 roles) · on-call agent [`oncall.yml`](.github/workflows/oncall.yml) |
| 4 | Context management | [`AGENTS.md`](AGENTS.md) (= `CLAUDE.md`) → modular [`docs/`](docs/): spec, team, process, architecture, testing, deployment, observability, runbook, ADRs |
| 5 | Application | React frontend + FastAPI api + worker + Postgres (Alembic); `make up` |
| 6 | Testing | unit + integration (Postgres in CI) + frontend + Playwright e2e; `make test` · [`docs/testing.md`](docs/testing.md) |
| 7 | Containerization | Dockerfiles for backend, frontend, fake-espn, alert-bridge; [`compose.yaml`](compose.yaml) starts everything incl. DB and telemetry with one command |
| 8 | Deployment | EC2 + Caddy HTTPS, URLs above · [`docs/deployment.md`](docs/deployment.md) |
| 9 | CI/CD | [`ci.yml`](.github/workflows/ci.yml) on every PR · [`cd-dev.yml`](.github/workflows/cd-dev.yml) auto-deploys dev · [`deploy-prod.yml`](.github/workflows/deploy-prod.yml) manual + approval · automatic and manual **rollback** ([`deploy/deploy.sh`](deploy/deploy.sh)) |
| 10 | Observability | key journey traced api → DB → ESPN, metrics, JSON logs sharing trace ids, in Grafana · privacy test · [`docs/observability.md`](docs/observability.md) |
| 11 | Alerting on user impact | 3 rules: fans can't load scores, ESPN schema drift, notifications failing · [`alerts.yaml`](observability/grafana/provisioning/alerting/alerts.yaml) |
| 12 | On-call agent | Grafana → [`alert-bridge`](alert-bridge/) → [`oncall.yml`](.github/workflows/oncall.yml) (Claude Code fixes + PR) · [`docs/runbook.md`](docs/runbook.md) · [`docs/incidents/`](docs/incidents/) |
