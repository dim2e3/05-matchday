#!/usr/bin/env bash
# Deploy one environment on the EC2 host:   deploy.sh <dev|prod> <image-tag>
#
# Expects /opt/matchday/<env>/.env (written by the workflow) and compose.app.yaml next to it.
# Pulls the tagged images, starts them, waits for health, smoke-tests through Caddy-less
# localhost, and on failure rolls back to the last good tag automatically.
# Rollback by hand = run this script (or the deploy workflow) with an older tag.
set -euo pipefail

ENV_NAME=${1:?usage: deploy.sh <dev|prod> <tag>}
TAG=${2:?usage: deploy.sh <dev|prod> <tag>}
DIR=/opt/matchday/$ENV_NAME
PROJECT=matchday-$ENV_NAME
cd "$DIR"

compose() { TAG=$1 docker compose -p "$PROJECT" -f compose.app.yaml --env-file .env "${@:2}"; }

smoke() {
  # The api must be ready and report the deployed tag's sha.
  compose "$1" exec -T api python -c "
import json, sys, urllib.request
r = json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/version', timeout=5))
sys.exit(0 if r['sha'] == '$1'.removeprefix('sha-') else f'version {r} != $1')
"
}

up() {
  compose "$1" pull --quiet
  compose "$1" up -d --wait --wait-timeout 180 --remove-orphans
}

PREVIOUS=$(cat last_good_tag 2>/dev/null || true)
echo "==> $ENV_NAME: deploying $TAG (previous good: ${PREVIOUS:-none})"

if up "$TAG" && smoke "$TAG"; then
  [ -n "$PREVIOUS" ] && [ "$PREVIOUS" != "$TAG" ] && echo "$PREVIOUS" > previous_good_tag
  echo "$TAG" > last_good_tag
  echo "$(date -u +%FT%TZ) $TAG ok" >> deploy_history
  docker image prune -f --filter "until=168h" >/dev/null
  echo "==> $ENV_NAME: $TAG is live"
  exit 0
fi

echo "!!! $ENV_NAME: $TAG failed health/smoke check" >&2
echo "$(date -u +%FT%TZ) $TAG FAILED" >> deploy_history
compose "$TAG" logs --tail 50 api worker >&2 || true
if [ -n "$PREVIOUS" ] && [ "$PREVIOUS" != "$TAG" ]; then
  echo "==> rolling back to $PREVIOUS" >&2
  up "$PREVIOUS" && smoke "$PREVIOUS" && echo "==> rolled back to $PREVIOUS" >&2
fi
exit 1
