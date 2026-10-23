# Deployment

## Environments

| | Local | dev | prod |
|---|---|---|---|
| How | `make up` | automatic on every green `main` | manual `Deploy production` workflow + approval |
| URL | http://localhost:8080 | `https://dev.<ip>.sslip.io` | `https://matchday.<ip>.sslip.io` |
| ESPN | fake-espn | fake-espn (incident demo) | real ESPN |
| Telegram | fake-espn sink, polling | fake-espn sink, polling | real bot, webhook |
| Poll / cache | 3 s / 2 s | 5 s / 3 s | 30 s / 15 s |

All environments share one EC2 host:

```
                  :443 Caddy (matchday-edge, auto HTTPS via sslip.io)
                  ├── matchday.<ip>.sslip.io → matchday-prod  (postgres, api, worker, frontend)
                  ├── dev.<ip>.sslip.io      → matchday-dev   (… + fake-espn)
                  └── grafana.<ip>.sslip.io  → matchday-ops   (collector, prometheus, loki, tempo, grafana)
docker networks:  edge (Caddy ↔ frontends, grafana)   ops (apps → otel-collector)
/opt/matchday/{edge,dev,prod,ops}/   .env + compose file + last_good_tag + deploy_history
```

## Pipeline

```
PR ──► CI: backend (ruff, pytest on Postgres, alembic check) · frontend (lint, test, build)
           · e2e (compose + Playwright)
merge to main ──► CI ──► CD (dev): build backend/frontend/fake-espn images → ghcr.io/<owner>/matchday/*:sha-<short>
                         → ssh: Caddy up to date → deploy.sh dev sha-<short> → public smoke test
owner ──► Deploy production (tag=sha-<short>) ──► approval ──► deploy.sh prod … → setWebhook → smoke
```

`deploy/deploy.sh <env> <tag>` pulls the tag, `docker compose up --wait`, checks that
`/api/version` reports the tag's sha, records `last_good_tag`, and **rolls back
automatically** to the previous good tag if health or smoke fails.

### Rollback

- Automatic: a failed deploy restores `last_good_tag` (see job log).
- Manual: run **Deploy production** with the previous tag. The tag is in
  `/opt/matchday/prod/previous_good_tag` and `deploy_history` on the host, and in the
  Actions history.
- Migrations are expand-only (add columns/tables, never drop or rename in the same
  release), so the previous image always runs against the newer schema.

## One-time setup

1. **EC2**: security group allows 22 (your IP), 80, 443. Then:
   ```sh
   scp -r deploy <user>@<ip>:/tmp/ && ssh <user>@<ip> 'bash /tmp/deploy/bootstrap.sh'
   ```
   Installs Docker + compose plugin, 2 GB swap, `/opt/matchday/*`, networks `edge` and `ops`.
   At least a t3.small (2 GB) works with swap; t3.medium is comfortable.
2. **Deploy key**: `ssh-keygen -t ed25519 -f matchday_deploy -N ''`, append the `.pub` to
   `~/.ssh/authorized_keys` on the host.
3. **GitHub repo settings**
   - Secrets (repo): `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` (private key);
     `GRAFANA_ADMIN_PASSWORD`; `ALERT_WEBHOOK_TOKEN` (`openssl rand -hex 32`, Grafana → bridge);
     `ANTHROPIC_API_KEY` (on-call agent); `ONCALL_GH_TOKEN` — fine-grained PAT for this repo
     with *Contents*, *Pull requests*, *Issues*: read/write (bridge dispatch + agent PR; a PAT so
     the PR triggers CI).
   - Variables (repo): `PROD_HOST=matchday.<ip>.sslip.io`, `DEV_HOST=dev.<ip>.sslip.io`,
     `GRAFANA_HOST=grafana.<ip>.sslip.io`, `ACME_EMAIL`.
   - Environment `dev`: variable `PUBLIC_HOST=dev.<ip>.sslip.io`; secret `POSTGRES_PASSWORD`.
   - Environment `production`: **required reviewer = you**; variable
     `PUBLIC_HOST=matchday.<ip>.sslip.io`, `TELEGRAM_BOT_USERNAME`; secrets
     `POSTGRES_PASSWORD`, `TELEGRAM_BOT_TOKEN` (from @BotFather),
     `TELEGRAM_WEBHOOK_SECRET` (`openssl rand -hex 32`).
   - Branch protection on `main`: require PR + CI checks.
4. First push to `main` → CD publishes the images. Make the three GHCR packages
   **public** (Package settings → Change visibility) so the host can pull without a token.

## Incident demo on dev

```sh
ssh <user>@<ip> 'docker exec matchday-dev-fake-espn-1 python -c "import urllib.request,json; \
  urllib.request.urlopen(urllib.request.Request(\"http://127.0.0.1:8000/_control/drift\", \
  data=json.dumps({\"mode\":\"renamed_competitors\"}).encode(), headers={\"content-type\":\"application/json\"}))"'
```

See [`runbook.md`](runbook.md) for what happens next.
