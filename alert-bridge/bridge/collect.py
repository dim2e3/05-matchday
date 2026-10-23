"""Collect the telemetry around a MatchDay alert (adapted from the module 04 responder)."""

import json
from datetime import UTC, datetime, timedelta

import httpx

from bridge import config

METRIC_QUERIES = {
    "My Games requests by status": (
        "sum by (http_response_status_code) (increase(http_server_request_duration_seconds_count"
        '{{deployment_environment="{env}", http_route="/api/my-games"}}[{m}m]))'
    ),
    "Scoreboard events by league and outcome": (
        "sum by (league, outcome) (increase(matchday_scoreboard_events_total"
        '{{deployment_environment="{env}"}}[{m}m]))'
    ),
    "ESPN calls by league and outcome": (
        "sum by (league, outcome) (increase(matchday_espn_requests_total"
        '{{deployment_environment="{env}"}}[{m}m]))'
    ),
    "Notifications by kind and outcome": (
        "sum by (kind, outcome) (increase(matchday_notifications_total"
        '{{deployment_environment="{env}"}}[{m}m]))'
    ),
}


def parse_time(value):
    if not value or value.startswith("0001-"):
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def time_window(alert, now=None):
    now = now or datetime.now(UTC)
    lookback = timedelta(minutes=config.LOOKBACK_MINUTES)
    started = parse_time(alert.get("startsAt"))
    start = min(started - lookback, now - lookback) if started else now - lookback
    return start, now


class Collector:
    def __init__(self, client=None):
        auth = (config.GRAFANA_USER, config.GRAFANA_PASSWORD) if config.GRAFANA_PASSWORD else None
        self.client = client or httpx.Client(base_url=config.GRAFANA_URL, timeout=15, auth=auth)
        self.errors = []

    def _get(self, source, path, params):
        try:
            response = self.client.get(
                f"/api/datasources/proxy/uid/{source}{path}",
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            self.errors.append(f"{source} {path}: {exc}")
            return None

    def metrics(self, env, start, end):
        minutes = max(1, int((end - start).total_seconds() // 60))
        tables = {}
        for title, template in METRIC_QUERIES.items():
            query = template.format(env=env, m=minutes)
            data = self._get("prometheus", "/api/v1/query", {"query": query, "time": end.timestamp()})
            tables[title] = [
                {**item["metric"], "count": round(float(item["value"][1]), 1)}
                for item in (data or {}).get("data", {}).get("result", [])
            ]
        return {"window_minutes": minutes, "tables": tables}

    def logs(self, env, start, end, limit=200):
        data = self._get("loki", "/loki/api/v1/query_range", {
            "query": f'{{service_name=~"matchday-.*", deployment_environment="{env}"}}',
            "start": int(start.timestamp() * 1e9),
            "end": int(end.timestamp() * 1e9),
            "limit": limit,
            "direction": "backward",
        })
        entries = []
        for stream in (data or {}).get("data", {}).get("result", []):
            labels = stream.get("stream", {})
            for ts, line in stream.get("values", []):
                entries.append({
                    "time": datetime.fromtimestamp(int(ts) / 1e9, UTC).isoformat(),
                    "service": labels.get("service_name"),
                    "level": labels.get("severity_text") or labels.get("detected_level"),
                    "message": line,
                    "trace_id": labels.get("trace_id"),
                })
        entries.sort(key=lambda e: e["time"], reverse=True)
        return entries

    def traces(self, env, start, end, limit=5):
        query = (
            '{resource.service.name=~"matchday-.*" && '
            f'resource.deployment.environment="{env}" && '
            "(status=error || span.http.response.status_code>=500)}"
        )
        found = self._get("tempo", "/api/search", {
            "q": query, "start": int(start.timestamp()), "end": int(end.timestamp()), "limit": limit,
        })
        traces = []
        for item in (found or {}).get("traces", [])[:limit]:
            detail = self._get("tempo", f"/api/traces/{item['traceID']}", {})
            traces.append({"trace_id": item["traceID"], "root": item.get("rootTraceName"),
                           "spans": summarize_spans(detail or {})})
        return {"query": query, "traces": traces}


def _attr_value(value):
    return next(iter(value.values()), None) if isinstance(value, dict) else value


def summarize_spans(trace):
    spans = []
    for batch in trace.get("batches") or trace.get("resourceSpans") or []:
        for scope in batch.get("scopeSpans") or []:
            for span in scope.get("spans", []):
                start, end = int(span.get("startTimeUnixNano", 0)), int(span.get("endTimeUnixNano", 0))
                spans.append({
                    "name": span.get("name"),
                    "status": span.get("status", {}),
                    "duration_ms": round((end - start) / 1e6, 2),
                    "attributes": {a["key"]: _attr_value(a.get("value"))
                                   for a in span.get("attributes", [])},
                })
    return spans


def collect(alert, incident_dir, collector=None):
    """Write alert/metrics/logs/traces JSON and context.md into incident_dir; return context."""
    collector = collector or Collector()
    env = alert.get("labels", {}).get("deployment_environment", "dev")
    start, end = time_window(alert)
    metrics = collector.metrics(env, start, end)
    logs = collector.logs(env, start, end)
    traces = collector.traces(env, start, end)
    for name, data in (("alert", alert), ("metrics", metrics), ("logs", logs), ("traces", traces)):
        (incident_dir / f"{name}.json").write_text(json.dumps(data, indent=2, default=str))
    context = render_context(alert, env, start, end, metrics, logs, traces, collector.errors)
    (incident_dir / "context.md").write_text(context)
    return context


def render_context(alert, env, start, end, metrics, logs, traces, errors):
    labels, annotations = alert.get("labels", {}), alert.get("annotations", {})
    out = [
        f"# Alert: {labels.get('alertname', 'unknown')}",
        "",
        f"- Environment: {env}",
        f"- Status: {alert.get('status', 'unknown')}",
        f"- Started: {alert.get('startsAt') or 'unknown'}",
        f"- Endpoint: {annotations.get('endpoint', 'not specified')}",
        f"- Window collected: {start.isoformat()} to {end.isoformat()}",
        f"- Summary: {annotations.get('summary', '')}",
        f"- Description: {annotations.get('description', '')}",
        f"- Runbook: {annotations.get('runbook', 'docs/runbook.md')}",
        f"- Labels: {json.dumps(labels)}",
        "",
        f"## Metrics (last {metrics['window_minutes']} minutes)",
    ]
    for title, rows in metrics["tables"].items():
        out += ["", f"### {title}", ""]
        if not rows:
            out.append("No data.")
            continue
        keys = [k for k in rows[0] if k != "count"]
        out += ["| " + " | ".join(keys + ["count"]) + " |", "|" + " --- |" * (len(keys) + 1)]
        out += ["| " + " | ".join(str(r.get(k, "")) for k in keys + ["count"]) + " |" for r in rows]

    problems = [e for e in logs if (e.get("level") or "").upper() in {"WARN", "WARNING", "ERROR"}]
    out += ["", f"## Warning and error logs ({len(problems)})", ""]
    out += [f"- {e['time']} {e['service']} [{e['level']}] {e['message']} "
            f"(trace_id={e.get('trace_id') or '-'})" for e in problems[:25]] or ["None."]

    out += ["", "## Recent logs", ""]
    out += [f"- {e['time']} {e['service']} [{e.get('level') or '-'}] {e['message']}"
            for e in logs[:20]] or ["None."]

    out += ["", f"## Failing traces ({len(traces['traces'])})", "", f"TraceQL: `{traces['query']}`", ""]
    for trace in traces["traces"]:
        out.append(f"### {trace['trace_id']} {trace['root'] or ''}")
        out += [f"- span `{s['name']}` {s['duration_ms']} ms, status={s['status']}, "
                f"attributes={json.dumps(s['attributes'])}" for s in trace["spans"]]
    if not traces["traces"]:
        out.append("None.")
    if errors:
        out += ["", "## Collection errors", ""] + [f"- {e}" for e in errors]
    return "\n".join(out) + "\n"
