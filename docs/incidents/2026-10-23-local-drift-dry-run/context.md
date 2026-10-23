# Alert: ESPN scoreboard schema drift

- Environment: local
- Status: firing
- Started: 2026-10-23T11:47:10Z
- Endpoint: ESPN scoreboard (nhl) → GET /api/my-games, worker
- Window collected: 2026-10-23T11:32:10+00:00 to 2026-10-23T11:47:26.753628+00:00
- Summary: ESPN nhl games can't be parsed (local)
- Description: 40.68% of nhl scoreboard events were dropped by the normalizer in the last 5 minutes. Fans following nhl teams see stale or missing scores and get no notifications. Likely an ESPN response schema change: see backend/src/matchday/normalizer.py.
- Runbook: docs/runbook.md#espn-scoreboard-schema-drift
- Labels: {"alertname": "ESPN scoreboard schema drift", "deployment_environment": "local", "grafana_folder": "MatchDay", "journey": "my-games", "league": "nhl", "service": "matchday", "severity": "critical"}

## Metrics (last 15 minutes)

### My Games requests by status

| http_response_status_code | count |
| --- | --- |
| 200 | 60.3 |

### Scoreboard events by league and outcome

| league | outcome | count |
| --- | --- | --- |
| nhl | parsed | 2124.0 |
| nhl | dropped | 379.8 |

### ESPN calls by league and outcome

| league | outcome | count |
| --- | --- | --- |
| nhl | ok | 357.7 |

### Notifications by kind and outcome

No data.

## Warning and error logs (197)

- 2026-10-23T11:47:25.610391+00:00 matchday-worker [WARN] ESPN scoreboard failed for league=nhl: All 7 nhl events failed to parse (trace_id=992e312eee06eadd1ae39ef022b1dd6b)
- 2026-10-23T11:47:25.610267+00:00 matchday-worker [WARN] scoreboard parse dropped events league=nhl dropped=7 parsed=0 (trace_id=992e312eee06eadd1ae39ef022b1dd6b)
- 2026-10-23T11:47:25.610060+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401879652: 'competitors' (trace_id=992e312eee06eadd1ae39ef022b1dd6b)
- 2026-10-23T11:47:25.609963+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401879412: 'competitors' (trace_id=992e312eee06eadd1ae39ef022b1dd6b)
- 2026-10-23T11:47:25.609874+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401886258: 'competitors' (trace_id=992e312eee06eadd1ae39ef022b1dd6b)
- 2026-10-23T11:47:25.609758+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401878099: 'competitors' (trace_id=992e312eee06eadd1ae39ef022b1dd6b)
- 2026-10-23T11:47:25.609649+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401886427: 'competitors' (trace_id=992e312eee06eadd1ae39ef022b1dd6b)
- 2026-10-23T11:47:25.609540+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401881923: 'competitors' (trace_id=992e312eee06eadd1ae39ef022b1dd6b)
- 2026-10-23T11:47:25.609341+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401881922: 'competitors' (trace_id=992e312eee06eadd1ae39ef022b1dd6b)
- 2026-10-23T11:47:22.590783+00:00 matchday-worker [WARN] ESPN scoreboard failed for league=nhl: All 7 nhl events failed to parse (trace_id=7ce1e9d48fcec18ff85dca9350a0944b)
- 2026-10-23T11:47:22.590699+00:00 matchday-worker [WARN] scoreboard parse dropped events league=nhl dropped=7 parsed=0 (trace_id=7ce1e9d48fcec18ff85dca9350a0944b)
- 2026-10-23T11:47:22.590571+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401879652: 'competitors' (trace_id=7ce1e9d48fcec18ff85dca9350a0944b)
- 2026-10-23T11:47:22.590489+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401879412: 'competitors' (trace_id=7ce1e9d48fcec18ff85dca9350a0944b)
- 2026-10-23T11:47:22.590407+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401886258: 'competitors' (trace_id=7ce1e9d48fcec18ff85dca9350a0944b)
- 2026-10-23T11:47:22.590319+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401878099: 'competitors' (trace_id=7ce1e9d48fcec18ff85dca9350a0944b)
- 2026-10-23T11:47:22.590227+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401886427: 'competitors' (trace_id=7ce1e9d48fcec18ff85dca9350a0944b)
- 2026-10-23T11:47:22.590122+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401881923: 'competitors' (trace_id=7ce1e9d48fcec18ff85dca9350a0944b)
- 2026-10-23T11:47:22.589949+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401881922: 'competitors' (trace_id=7ce1e9d48fcec18ff85dca9350a0944b)
- 2026-10-23T11:47:19.577920+00:00 matchday-worker [WARN] ESPN scoreboard failed for league=nhl: All 7 nhl events failed to parse (trace_id=da931eecf57b2862558f089968d85944)
- 2026-10-23T11:47:19.577797+00:00 matchday-worker [WARN] scoreboard parse dropped events league=nhl dropped=7 parsed=0 (trace_id=da931eecf57b2862558f089968d85944)
- 2026-10-23T11:47:19.577664+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401879652: 'competitors' (trace_id=da931eecf57b2862558f089968d85944)
- 2026-10-23T11:47:19.577586+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401879412: 'competitors' (trace_id=da931eecf57b2862558f089968d85944)
- 2026-10-23T11:47:19.577505+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401886258: 'competitors' (trace_id=da931eecf57b2862558f089968d85944)
- 2026-10-23T11:47:19.577380+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401878099: 'competitors' (trace_id=da931eecf57b2862558f089968d85944)
- 2026-10-23T11:47:19.577287+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401886427: 'competitors' (trace_id=da931eecf57b2862558f089968d85944)

## Recent logs

- 2026-10-23T11:47:25.610391+00:00 matchday-worker [WARN] ESPN scoreboard failed for league=nhl: All 7 nhl events failed to parse
- 2026-10-23T11:47:25.610267+00:00 matchday-worker [WARN] scoreboard parse dropped events league=nhl dropped=7 parsed=0
- 2026-10-23T11:47:25.610060+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401879652: 'competitors'
- 2026-10-23T11:47:25.609963+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401879412: 'competitors'
- 2026-10-23T11:47:25.609874+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401886258: 'competitors'
- 2026-10-23T11:47:25.609758+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401878099: 'competitors'
- 2026-10-23T11:47:25.609649+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401886427: 'competitors'
- 2026-10-23T11:47:25.609540+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401881923: 'competitors'
- 2026-10-23T11:47:25.609341+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401881922: 'competitors'
- 2026-10-23T11:47:22.590783+00:00 matchday-worker [WARN] ESPN scoreboard failed for league=nhl: All 7 nhl events failed to parse
- 2026-10-23T11:47:22.590699+00:00 matchday-worker [WARN] scoreboard parse dropped events league=nhl dropped=7 parsed=0
- 2026-10-23T11:47:22.590571+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401879652: 'competitors'
- 2026-10-23T11:47:22.590489+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401879412: 'competitors'
- 2026-10-23T11:47:22.590407+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401886258: 'competitors'
- 2026-10-23T11:47:22.590319+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401878099: 'competitors'
- 2026-10-23T11:47:22.590227+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401886427: 'competitors'
- 2026-10-23T11:47:22.590122+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401881923: 'competitors'
- 2026-10-23T11:47:22.589949+00:00 matchday-worker [WARN] Skipping malformed event for league=nhl id=401881922: 'competitors'
- 2026-10-23T11:47:19.577920+00:00 matchday-worker [WARN] ESPN scoreboard failed for league=nhl: All 7 nhl events failed to parse
- 2026-10-23T11:47:19.577797+00:00 matchday-worker [WARN] scoreboard parse dropped events league=nhl dropped=7 parsed=0

## Failing traces (0)

TraceQL: `{resource.service.name=~"matchday-.*" && resource.deployment.environment="local" && (status=error || span.http.response.status_code>=500)}`

None.

