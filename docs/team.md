# Agent Team

MatchDay is built by a team of coding agents (Claude Code subagents, defined in
`.claude/agents/`) coordinated by one human, the **owner**. Each agent has one
responsibility, a set of files it owns, and a hand-off artifact. How they work together is
in [`process.md`](process.md).

| Role | Agent file | Responsibilities | Owns | Hands off |
|---|---|---|---|---|
| Owner (human) | — | Picks priorities, approves specs, merges PRs, runs prod deploys | — | Approved issue, merge |
| Product owner | `product-owner.md` | Turns ideas into user stories with Given/When/Then acceptance criteria; keeps `docs/product/spec.md` and GitHub issues in sync | `docs/product/` | Issue labelled `ready` |
| Architect | `architect.md` | API contract, data model, ADRs, splits stories into tasks, plan comment on the issue | `docs/architecture.md`, `docs/decisions/` | Plan comment on issue |
| Backend dev | `backend-dev.md` | FastAPI API, worker, DB models and migrations, ESPN/Telegram clients, telemetry calls | `backend/`, `fake-espn/` | PR with tests |
| Frontend dev | `frontend-dev.md` | React UI, API client, frontend tests | `frontend/` | PR with tests |
| QA | `qa.md` | Writes tests from acceptance criteria first, integration and e2e suites, verifies ACs on the PR | `backend/tests/`, `frontend/src/**/*.test.tsx`, `e2e/` | AC checklist ticked on PR |
| DevOps | `devops.md` | Dockerfiles, compose, CI/CD workflows, EC2/Caddy, observability stack, alert rules | `deploy/`, `observability/`, `.github/workflows/`, `compose.yaml` | Green pipeline, deploy |
| Reviewer | `reviewer.md` | Reviews every PR against ACs, `AGENTS.md` rules and security/privacy; never edits code | — | Review comment: approve / changes |
| On-call | `.github/workflows/oncall.yml` + `docs/oncall-prompt.md` | Woken by an alert; investigates telemetry, reproduces, fixes, adds a regression test, opens PR | — | PR labelled `incident` + incident note |

## Rules for every agent

- Read `AGENTS.md` first, then only the docs it links that are relevant to the task.
- Work only on an issue that is labelled `ready` and stay inside the files your role owns;
  if a change is needed elsewhere, comment on the issue for the owning role.
- Every PR references its issue (`Closes #N`) and copies its AC checklist.
- Never commit secrets, never push to `main`, never deploy to production.
