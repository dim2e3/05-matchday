"""S7: the key journey is traced, and no customer data or secrets reach telemetry."""

import logging

import pytest
from httpx import AsyncClient
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from matchday import scoreboard_service, worker

pytestmark = pytest.mark.asyncio

exporter = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(exporter))
trace.set_tracer_provider(_provider)

CHAT_ID = 987654321
SECRET = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}


def _is_fake_upstream_server_span(span) -> bool:
    """In tests fake-espn runs in-process and its FastAPI server spans get recorded too.
    They stand in for Telegram's/ESPN's own servers, which never report to our telemetry."""
    route = (span.attributes or {}).get("http.route", "")
    return not route.startswith("/api") and route != ""


async def _journey(client: AsyncClient, fake_espn) -> dict[str, str]:
    """Follow → My Games → connect Telegram → kickoff delivered. Returns the secrets used."""
    await client.post("/api/follows", json={"league": "nhl", "team_id": "19"})
    await client.get("/api/my-games")
    token = (await client.post("/api/telegram/link")).json()["url"].split("?start=")[1]
    update = {"update_id": 1, "message": {"chat": {"id": CHAT_ID}, "text": f"/start {token}"}}
    await client.post("/api/telegram/webhook", json=update, headers=SECRET)
    await worker.run_cycle()
    await fake_espn.post("/_control/game", json={"game_id": "401886427", "state": "in"})
    scoreboard_service.clear_caches()
    await worker.run_cycle()
    return {
        "cookie": client.cookies.get("md_uid"),
        "link token": token,
        "chat id": str(CHAT_ID),
        "bot token": "test-token",
        "webhook secret": "test-secret",
    }


async def test_s7_key_journey_is_traced(client: AsyncClient, fake_espn) -> None:
    exporter.clear()
    await _journey(client, fake_espn)

    names = {s.name for s in exporter.get_finished_spans()}
    assert "GET /api/my-games" in names
    assert "worker cycle" in names
    assert "game transition" in names
    assert "notification send" in names
    assert "telegram sendMessage" in names
    # DB spans (the SQLAlchemy instrumentation silently no-ops on unsupported versions).
    assert any(n.startswith("SELECT") for n in names), names
    my_games = next(s for s in exporter.get_finished_spans() if s.name == "GET /api/my-games")
    assert my_games.attributes["matchday.games"] == 1


async def test_s7_no_customer_data_or_secrets_in_telemetry(
    client: AsyncClient, fake_espn, caplog
) -> None:
    exporter.clear()
    caplog.set_level(logging.INFO)  # production level (telemetry.setup)
    secrets = await _journey(client, fake_espn)
    assert all(secrets.values())

    span_text = "\n".join(
        f"{s.name} {dict(s.attributes or {})} "
        + " ".join(f"{e.name} {dict(e.attributes or {})}" for e in s.events)
        for s in exporter.get_finished_spans()
        if not _is_fake_upstream_server_span(s)
    )
    log_text = "\n".join(r.getMessage() for r in caplog.records)
    for label, value in secrets.items():
        assert value not in span_text, f"{label} leaked into a span"
        assert value not in log_text, f"{label} leaked into a log line"
