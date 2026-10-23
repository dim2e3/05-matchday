#!/usr/bin/env bash
# Create the public tracker from docs/product/spec.md: labels, milestones, one issue per
# story (S1..S8) with its acceptance criteria, ops issues, and a project board.
# Run once after creating the repo:   gh auth login && scripts/bootstrap-github.sh
# Needs: gh (with the "project" scope: gh auth refresh -s project), python3.
set -euo pipefail
cd "$(dirname "$0")/.."

repo=$(gh repo view --json nameWithOwner -q .nameWithOwner)
owner=${repo%%/*}
echo "==> $repo"

label() { gh label create "$1" --color "$2" --description "$3" --force >/dev/null; }
label story 0E8A16 "User story with acceptance criteria"
label ready 1D76DB "Definition of Ready met; an agent may start"
label ops 5319E7 "Delivery and operations"
label incident B60205 "Opened by the on-call agent"
for role in backend-dev frontend-dev devops qa; do label "role:$role" C5DEF5 "Owning agent role"; done

milestone() {
  gh api "repos/$repo/milestones" -f title="$1" -f description="$2" >/dev/null 2>&1 || true
}
milestone "M1 App" "Stories S1-S6"
milestone "M3 Deploy" "Containers, CI/CD, EC2"
milestone "M4 Observability" "Telemetry and alerts"
milestone "M5 On-call" "Alert-driven agent"

# Split spec.md into "### S<n> Title" sections -> one issue each.
python3 - <<'PY' > /tmp/matchday-stories.tsv
import re, pathlib
spec = pathlib.Path("docs/product/spec.md").read_text()
roles = {"S1": "backend-dev", "S2": "backend-dev", "S3": "backend-dev", "S4": "backend-dev",
         "S5": "backend-dev", "S6": "frontend-dev", "S7": "devops", "S8": "backend-dev"}
for m in re.finditer(r"^### (S\d+) (.+?)\n(.*?)(?=^### |^## |\Z)", spec, re.S | re.M):
    sid, title, body = m.group(1), m.group(2).strip(), m.group(3).strip()
    body = (f"**Story {sid}** — from [`docs/product/spec.md`](../blob/main/docs/product/spec.md)\n\n"
            f"{body}\n\n_Definition of Done: see docs/process.md._")
    print("\t".join([sid, title, roles.get(sid, "backend-dev"), body.replace("\n", "\\n")]))
PY

while IFS=$'\t' read -r sid title role body; do
  milestone_name="M1 App"; [ "$sid" = "S7" ] && milestone_name="M4 Observability"
  labels="story,role:$role"; [ "$sid" != "S8" ] && labels="$labels,ready"
  printf '%b' "$body" | gh issue create --title "$sid: $title" --label "$labels" \
    --milestone "$milestone_name" --body-file - >/dev/null
  echo "    issue $sid: $title"
done < /tmp/matchday-stories.tsv

ops_issue() {
  gh issue create --title "$1" --label "ops,ready,role:devops" --milestone "$2" --body "$3" >/dev/null
  echo "    issue: $1"
}
ops_issue "CI: lint, unit, integration (Postgres), frontend, e2e on every PR" "M3 Deploy" \
"- [ ] ruff + pytest against Postgres service, alembic check
- [ ] frontend lint, vitest, build
- [ ] compose + Playwright e2e
- [ ] required status checks on main"
ops_issue "CD to dev on main, manual production deploy with rollback" "M3 Deploy" \
"- [ ] images tagged sha-<short> in GHCR
- [ ] dev deploys automatically after green CI
- [ ] production via workflow_dispatch + environment approval
- [ ] failed deploy rolls back to last good tag; manual rollback = redeploy previous tag
- [ ] public HTTPS URLs via Caddy + sslip.io"
ops_issue "Telemetry on the key journey + user-impact alerts" "M4 Observability" \
"- [ ] traces, metrics, JSON logs share trace ids for GET /api/my-games and the worker path
- [ ] no customer data or secrets in telemetry (test)
- [ ] Grafana dashboard; alerts: my-games 5xx, schema drift, notifications failing"
ops_issue "On-call agent: alert -> context -> Claude Code fix PR" "M5 On-call" \
"- [ ] Grafana webhook -> alert-bridge collects context -> repository_dispatch
- [ ] oncall.yml reproduces in a test, fixes, opens PR labelled incident
- [ ] demo: DRIFT on dev -> alert -> PR -> merge -> alert resolves"

# Project board with all issues.
project=$(gh project create --owner "$owner" --title "MatchDay Alerts" --format json -q .number)
gh project link "$project" --owner "$owner" --repo "$repo" >/dev/null || true
for url in $(gh issue list --state all --limit 100 --json url -q '.[].url'); do
  gh project item-add "$project" --owner "$owner" --url "$url" >/dev/null
done
echo "==> project board #$project with $(gh issue list --state all --limit 100 --json number -q length) issues"
