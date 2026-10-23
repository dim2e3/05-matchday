# ADR-003: On-call agent runs in GitHub Actions, fixes land as PRs

**Status:** accepted · 2026-10-23

## Context
Module 04's responder ran `claude -p` on the developer's machine against the local stack.
MatchDay runs on EC2; the agent must work when nobody's laptop is on, must not get shell
access to production, and its fix must pass the same checks as any human change.

## Decision
Grafana → `alert-bridge` (on the EC2 ops stack) collects telemetry context through Grafana's
datasource proxy and sends a `repository_dispatch`. `.github/workflows/oncall.yml` runs Claude
Code headless on a fresh checkout with a restricted toolset (read/edit, pytest, ruff; no git
push, curl or gh), then the workflow — not the agent — runs the tests, enforces a path guard
rail (`backend/`, `docs/incidents/` only) and opens a PR labelled `incident` (or an issue when
the agent cannot fix it in code).

## Consequences
- The agent never touches production; the fix ships through CI → dev → manual prod.
- Time to mitigation includes review + CI (~10 min). Acceptable for this app; a stale cache
  keeps most fans served meanwhile.
- Needs `ANTHROPIC_API_KEY` and a fine-grained PAT (`ONCALL_GH_TOKEN`) so the PR triggers CI.
- The alert context is passed in the dispatch payload (≤ 40 KB), so the runner needs no
  network access to Grafana.
