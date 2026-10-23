"""alert-bridge: Grafana alert webhook in, on-call agent wake-up out.

POST /alerts (Bearer token) accepts Grafana's webhook payload. Each firing alert becomes an
incident folder with the collected telemetry; then the bridge sends a GitHub
repository_dispatch (event_type "incident") that starts .github/workflows/oncall.yml.
Adapted from the module 04 incident responder, which ran `claude -p` on the host instead.
"""

import hmac
import json
import logging
import queue
import re
import threading
from datetime import UTC, datetime
from uuid import uuid4

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from bridge import config
from bridge.collect import collect

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("alert-bridge")


class Alert(BaseModel, extra="allow"):
    status: str = "firing"
    labels: dict[str, str] = Field(default_factory=dict)
    annotations: dict[str, str] = Field(default_factory=dict)
    startsAt: str | None = None
    fingerprint: str | None = None


class WebhookPayload(BaseModel, extra="allow"):
    alerts: list[Alert]


jobs: queue.Queue = queue.Queue()
active_fingerprints: set[str] = set()
lock = threading.Lock()


def now():
    return datetime.now(UTC)


def write_status(incident_dir, **fields):
    path = incident_dir / "status.json"
    status = json.loads(path.read_text()) if path.exists() else {}
    status.update(fields, updated_at=now().isoformat())
    path.write_text(json.dumps(status, indent=2))
    return status


def new_incident(alert):
    name = re.sub(r"[^A-Za-z0-9_-]+", "-", alert.get("labels", {}).get("alertname", "alert"))[:40]
    incident_id = f"{now():%Y%m%d-%H%M%S}-{name.strip('-')}-{uuid4().hex[:6]}"
    incident_dir = config.INCIDENTS_DIR / incident_id
    incident_dir.mkdir(parents=True)
    return incident_id, incident_dir


def dispatch(incident_id, alert, context, client=None):
    """Wake the on-call agent. Returns 'dispatched' or 'dry-run'."""
    if not (config.GITHUB_TOKEN and config.GITHUB_REPOSITORY):
        return "dry-run"
    labels = alert.get("labels", {})
    payload = {
        "event_type": "incident",
        "client_payload": {
            "incident_id": incident_id,
            "alertname": labels.get("alertname", ""),
            "environment": labels.get("deployment_environment", ""),
            "summary": alert.get("annotations", {}).get("summary", ""),
            "context": context[: config.MAX_CONTEXT_CHARS],
        },
    }
    client = client or httpx.Client(timeout=15)
    response = client.post(
        f"{config.GITHUB_API}/repos/{config.GITHUB_REPOSITORY}/dispatches",
        json=payload,
        headers={
            "Authorization": f"Bearer {config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    response.raise_for_status()
    return "dispatched"


def handle(incident_id, incident_dir, alert, fingerprint):
    try:
        write_status(incident_dir, state="collecting")
        context = collect(alert, incident_dir)
        result = dispatch(incident_id, alert, context)
        write_status(incident_dir, state=result)
        log.info("Incident %s: %s", incident_id, result)
    except Exception as exc:
        log.exception("Incident %s failed", incident_id)
        write_status(incident_dir, state="failed", error=str(exc))
    finally:
        with lock:
            active_fingerprints.discard(fingerprint)


def worker():
    while True:
        handle(*jobs.get())
        jobs.task_done()


app = FastAPI(title="alert-bridge")
threading.Thread(target=worker, daemon=True, name="dispatcher").start()


@app.get("/healthz")
def health():
    return {"status": "ok", "queued": jobs.qsize(),
            "mode": "dispatch" if config.GITHUB_TOKEN else "dry-run"}


@app.post("/alerts", status_code=202)
def receive_alerts(payload: WebhookPayload, authorization: str | None = Header(default=None)):
    expected = f"Bearer {config.WEBHOOK_TOKEN}"
    if not config.WEBHOOK_TOKEN or not hmac.compare_digest(authorization or "", expected):
        raise HTTPException(401, "bad token")
    incidents = []
    for alert_model in payload.alerts:
        alert = alert_model.model_dump()
        labels = alert["labels"]
        fingerprint = alert.get("fingerprint") or json.dumps(labels, sort_keys=True)
        env = labels.get("deployment_environment", "")
        if alert["status"] != "firing":
            log.info("Alert %s resolved (%s)", labels.get("alertname"), env)
            incidents.append({"alert": labels.get("alertname"), "state": "resolved"})
            continue
        if env not in config.DISPATCH_ENVIRONMENTS:
            incidents.append({"alert": labels.get("alertname"), "state": "ignored-env"})
            continue
        with lock:
            duplicate = fingerprint in active_fingerprints
            active_fingerprints.add(fingerprint)
        if duplicate:
            incidents.append({"alert": labels.get("alertname"), "state": "duplicate"})
            continue
        incident_id, incident_dir = new_incident(alert)
        write_status(incident_dir, state="queued", alert=labels.get("alertname"),
                     environment=env, received_at=now().isoformat())
        jobs.put((incident_id, incident_dir, alert, fingerprint))
        log.info("Alert %s (%s) -> incident %s", labels.get("alertname"), env, incident_id)
        incidents.append({"id": incident_id, "state": "queued"})
    return {"incidents": incidents}


@app.get("/incidents")
def list_incidents():
    if not config.INCIDENTS_DIR.exists():
        return []
    result = []
    for incident_dir in sorted(config.INCIDENTS_DIR.iterdir(), reverse=True):
        status_file = incident_dir / "status.json"
        if status_file.exists():
            result.append({"id": incident_dir.name, **json.loads(status_file.read_text())})
    return result


@app.get("/incidents/{incident_id}/context")
def get_context(incident_id: str):
    incident_dir = config.INCIDENTS_DIR / incident_id
    context = incident_dir / "context.md"
    if not re.fullmatch(r"[A-Za-z0-9_-]+", incident_id) or not context.exists():
        raise HTTPException(404, "Incident not found")
    return {"id": incident_id, "context": context.read_text()}
