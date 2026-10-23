import os
from pathlib import Path

# Telemetry is read through Grafana's datasource proxy, so only Grafana must be reachable.
GRAFANA_URL = os.getenv("GRAFANA_URL", "http://grafana:3000").rstrip("/")
GRAFANA_USER = os.getenv("GRAFANA_USER", "admin")
GRAFANA_PASSWORD = os.getenv("GRAFANA_PASSWORD", "")  # empty: anonymous (local stack)
LOOKBACK_MINUTES = int(os.getenv("BRIDGE_LOOKBACK_MINUTES", "15"))

# Grafana's contact point sends "Authorization: Bearer <token>".
WEBHOOK_TOKEN = os.getenv("ALERT_WEBHOOK_TOKEN", "")

# repository_dispatch target. Without a token the bridge runs dry: it only writes incidents.
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "")
GITHUB_TOKEN = os.getenv("GITHUB_DISPATCH_TOKEN", "")
GITHUB_API = os.getenv("GITHUB_API", "https://api.github.com")
# Environments whose alerts wake the agent; prod alerts are investigated on dev's code too,
# but a fix still goes through PR → CI → dev → manual prod.
DISPATCH_ENVIRONMENTS = set(os.getenv("BRIDGE_DISPATCH_ENVS", "dev,prod,local").split(","))

INCIDENTS_DIR = Path(os.getenv("BRIDGE_INCIDENTS_DIR", "/data/incidents"))
# client_payload is limited (~64 KB); keep the context well under it.
MAX_CONTEXT_CHARS = 40_000
