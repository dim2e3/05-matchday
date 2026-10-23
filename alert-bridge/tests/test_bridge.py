import json

import httpx
import pytest
from fastapi.testclient import TestClient

from bridge import collect, config, main

ALERT = {
    "status": "firing",
    "labels": {"alertname": "ESPN scoreboard schema drift", "deployment_environment": "dev",
               "league": "nhl"},
    "annotations": {"summary": "ESPN nhl games can't be parsed (dev)",
                    "endpoint": "ESPN scoreboard (nhl)"},
    "startsAt": "2026-10-23T11:00:00Z",
    "fingerprint": "abc",
}


@pytest.fixture(autouse=True)
def _config(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INCIDENTS_DIR", tmp_path)
    monkeypatch.setattr(config, "WEBHOOK_TOKEN", "t0ken")
    monkeypatch.setattr(config, "GITHUB_TOKEN", "")
    main.active_fingerprints.clear()


def fake_grafana() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "prometheus" in path:
            return httpx.Response(200, json={"data": {"result": [
                {"metric": {"league": "nhl", "outcome": "dropped"}, "value": [0, "42"]}]}})
        if "loki" in path:
            return httpx.Response(200, json={"data": {"result": [{
                "stream": {"service_name": "matchday-worker", "severity_text": "WARNING",
                           "trace_id": "t1"},
                "values": [["1761217200000000000",
                            "scoreboard parse dropped events league=nhl dropped=7 parsed=0"]]}]}})
        if path.endswith("/api/search"):
            return httpx.Response(200, json={"traces": []})
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler), base_url="http://grafana")


def test_rejects_missing_or_wrong_token():
    client = TestClient(main.app)
    assert client.post("/alerts", json={"alerts": [ALERT]}).status_code == 401
    bad = client.post("/alerts", json={"alerts": [ALERT]}, headers={"Authorization": "Bearer x"})
    assert bad.status_code == 401


def test_queues_firing_alert_once_and_skips_resolved(monkeypatch):
    monkeypatch.setattr(main.jobs, "put", lambda job: None)  # don't run the worker
    client = TestClient(main.app)
    headers = {"Authorization": "Bearer t0ken"}
    resolved = {**ALERT, "status": "resolved"}

    body = client.post("/alerts", json={"alerts": [ALERT, ALERT, resolved]}, headers=headers).json()

    assert [i["state"] for i in body["incidents"]] == ["queued", "duplicate", "resolved"]


def test_collect_writes_context(tmp_path):
    context = collect.collect(ALERT, tmp_path, collect.Collector(client=fake_grafana()))

    assert "# Alert: ESPN scoreboard schema drift" in context
    assert "- Environment: dev" in context
    assert "| nhl | dropped | 42.0 |" in context
    assert "scoreboard parse dropped events league=nhl" in context
    for name in ("alert", "metrics", "logs", "traces"):
        assert json.loads((tmp_path / f"{name}.json").read_text()) is not None


def test_dispatch_dry_run_without_token():
    assert main.dispatch("id", ALERT, "ctx") == "dry-run"


def test_dispatch_sends_repository_dispatch(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_TOKEN", "ghp_x")
    monkeypatch.setattr(config, "GITHUB_REPOSITORY", "me/matchday")
    sent = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["url"] = str(request.url)
        sent["auth"] = request.headers["authorization"]
        sent["body"] = json.loads(request.content)
        return httpx.Response(204)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = main.dispatch("inc-1", ALERT, "x" * 100_000, client=client)

    assert result == "dispatched"
    assert sent["url"] == "https://api.github.com/repos/me/matchday/dispatches"
    assert sent["auth"] == "Bearer ghp_x"
    payload = sent["body"]["client_payload"]
    assert sent["body"]["event_type"] == "incident"
    assert payload["environment"] == "dev"
    assert len(payload["context"]) == config.MAX_CONTEXT_CHARS
