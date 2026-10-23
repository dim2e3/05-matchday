"""OpenTelemetry setup: traces, metrics and logs over OTLP, plus JSON logs on stdout.

Adapted from the module 04 order-tracker. Each process calls `setup(<service name>)` once.
Without OTEL_EXPORTER_OTLP_ENDPOINT (tests, plain local runs) no exporters are installed;
instruments stay no-ops and logs still go to stdout as JSON with trace ids.

Privacy rules (AGENTS.md): no cookie ids, chat ids, link tokens or bot token in any span,
metric label or log. The Telegram client is deliberately NOT auto-instrumented because its
URLs contain the bot token; it records a manual span with only the API method name.
"""

import json
import logging
import os
import sys
from datetime import UTC, datetime

# Stable HTTP semantic conventions: http.server.request.duration with http.route and
# http.response.status_code (the alert rules depend on these names). Must be set before
# the instrumentations are imported.
os.environ.setdefault("OTEL_SEMCONV_STABILITY_OPT_IN", "http")

from opentelemetry import metrics, trace  # noqa: E402

logger = logging.getLogger(__name__)

meter = metrics.get_meter("matchday")
tracer = trace.get_tracer("matchday")

espn_requests = meter.create_counter(
    "matchday.espn.requests",
    unit="{request}",
    description="ESPN API calls by league, resource and outcome (ok|error)",
)
scoreboard_events = meter.create_counter(
    "matchday.scoreboard.events",
    unit="{event}",
    description="ESPN scoreboard events by league and outcome (parsed|dropped); "
    "dropped events signal an upstream schema change",
)
notifications = meter.create_counter(
    "matchday.notifications",
    unit="{notification}",
    description="Notifications by kind and outcome (enqueued|sent|retry|failed)",
)
notification_latency = meter.create_histogram(
    "matchday.notification.latency",
    unit="s",
    description="Time from detecting a game transition to delivering its Telegram message",
)
worker_cycles = meter.create_counter(
    "matchday.worker.cycles",
    unit="{cycle}",
    description="Worker poll cycles by outcome (ok|error)",
)


class JsonFormatter(logging.Formatter):
    """One JSON object per line, with the active trace and span ids."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        ctx = trace.get_current_span().get_span_context()
        if ctx.is_valid:
            entry["trace_id"] = format(ctx.trace_id, "032x")
            entry["span_id"] = format(ctx.span_id, "016x")
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def _configure_logging(otlp_handler: logging.Handler | None) -> None:
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(JsonFormatter())
    root.handlers = [stdout]
    if otlp_handler is not None:
        logging.getLogger("matchday").addHandler(otlp_handler)
    # httpx logs full request URLs at INFO (the Telegram URL contains the bot token);
    # DB drivers log SQL parameters (user ids, chat ids) at DEBUG.
    for noisy in ("httpx", "httpcore", "aiosqlite", "asyncpg", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def setup(service_name: str) -> None:
    if os.getenv("OTEL_SDK_DISABLED", "").lower() == "true" or not os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT"
    ):
        _configure_logging(None)
        return

    from opentelemetry._logs import set_logger_provider
    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    # OTEL_RESOURCE_ATTRIBUTES (e.g. deployment.environment=dev) is merged in by Resource.
    resource = Resource.create({"service.name": service_name})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    interval = int(os.getenv("OTEL_METRIC_EXPORT_INTERVAL", "10000"))
    reader = PeriodicExportingMetricReader(OTLPMetricExporter(), export_interval_millis=interval)
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    set_logger_provider(logger_provider)
    _configure_logging(LoggingHandler(logger_provider=logger_provider))
    logger.info("telemetry enabled service=%s", service_name)


def instrument_app(app) -> None:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app, excluded_urls="api/health,api/ready")


def instrument_db(engine) -> None:
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


def instrument_http_client(client) -> None:
    """Instrument one httpx client (ESPN only; never the Telegram client)."""
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

    HTTPXClientInstrumentor.instrument_client(client)
