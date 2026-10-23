# Working Process

```
idea ─► product-owner ─► issue (ACs, label: ready)
            │
            ▼
        architect ─► plan comment on the issue (files, API, data, tests)
            │
            ▼
   qa writes failing tests from ACs ─► backend-dev / frontend-dev implement
            │
            ▼
        branch  feat/<issue>-<slug>  ─► PR "Closes #N" + AC checklist
            │
            ▼
   CI (lint, unit, integration, frontend, e2e) ─► reviewer agent comment
            │
            ▼
   owner merges ─► CD deploys to dev ─► owner runs "Deploy production" with the tag
```

## Definition of Ready (issue)

- User story, Given/When/Then ACs, out-of-scope notes, label `ready`, milestone set.

## Definition of Done (PR)

- All ACs ticked with evidence (test name, screenshot, or curl output).
- `make test` passes locally and in CI.
- New behavior on the key journey emits telemetry per `observability.md`; nothing sensitive
  logged.
- Docs updated when behavior, commands or config change.
- Reviewer agent approved; owner merged.

## Branches and commits

- `main` is protected: PR + green CI required.
- Branches: `feat/`, `fix/`, `chore/`, `incident/` + issue number.
- Conventional commit subjects (`feat: follow teams (#3)`).

## Incidents

Alert → on-call agent (see [`runbook.md`](runbook.md)) → PR labelled `incident` → normal
review and merge → CD to dev → owner promotes to prod. A short note is added to
`docs/incidents/YYYY-MM-DD-<slug>.md`.

## How to run an agent

```sh
claude                                  # interactive, AGENTS.md is loaded automatically
> Use the architect agent to plan issue #5
> Use the qa agent to write tests for the ACs of #5
> Use the backend-dev agent to implement #5
> Use the reviewer agent to review PR #12
```
