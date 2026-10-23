"""fake-espn: a local stand-in for ESPN's scoreboard API and Telegram's Bot API.

- Replays recorded scoreboards from FIXTURES_DIR with per-game overrides.
- `DRIFT` simulates upstream breakage: `renamed_competitors` (schema change) or
  `http_500` (outage). Set it with the env var or at runtime via /_control/drift.
- `/telegram/bot<token>/<method>` records sendMessage calls and serves queued
  updates to getUpdates, so linking and notifications work without real Telegram.

Dev and tests only — never deployed to production.
"""

import asyncio
import copy
import json
import os
import time
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

FIXTURES_DIR = Path(os.environ.get("FIXTURES_DIR", "/fixtures"))
SPORTS = {"football": "nfl", "basketball": "nba", "hockey": "nhl", "baseball": "mlb"}
DriftMode = Literal["none", "renamed_competitors", "http_500"]

app = FastAPI(title="fake-espn")


class State:
    def __init__(self) -> None:
        # Never reset, and seeded from the clock: a running worker keeps its getUpdates
        # offset across resets and fake-espn restarts, so ids must only ever increase,
        # like Telegram's do.
        self.next_update_id = int(time.time() * 1000)
        self.reset()

    def reset(self) -> None:
        self.drift: str = os.environ.get("DRIFT", "none")
        self.overrides: dict[str, dict] = {}  # game_id -> {state, home_score, away_score}
        self.messages: list[dict] = []
        self.updates: list[dict] = []


state = State()


def _load(league: str) -> dict:
    path = FIXTURES_DIR / f"{league}_scoreboard.json"
    if not path.exists():
        return {"events": []}
    return json.loads(path.read_text())


def _apply_override(event: dict) -> None:
    override = state.overrides.get(str(event["id"]))
    if not override:
        return
    competition = event["competitions"][0]
    status_type = competition["status"]["type"]
    new_state = override["state"]
    status_type["state"] = new_state
    status_type["completed"] = new_state == "post"
    status_type["shortDetail"] = {"pre": "Scheduled", "in": "Live", "post": "Final"}[new_state]
    for competitor in competition["competitors"]:
        key = f"{competitor['homeAway']}_score"
        if override.get(key) is not None:
            competitor["score"] = str(override[key])


def _drift(raw: dict) -> dict:
    """renamed_competitors: competitors → teams, score → {"value": score}."""
    for event in raw.get("events", []):
        for competition in event.get("competitions", []):
            teams = competition.pop("competitors", [])
            for team in teams:
                team["score"] = {"value": team.get("score")}
            competition["teams"] = teams
    return raw


@app.get("/apis/site/v2/sports/{sport}/{league}/scoreboard")
async def scoreboard(sport: str, league: str) -> dict:
    if SPORTS.get(sport) != league:
        raise HTTPException(404)
    if state.drift == "http_500":
        raise HTTPException(500, "fake outage")
    raw = copy.deepcopy(_load(league))
    for event in raw.get("events", []):
        _apply_override(event)
    if state.drift == "renamed_competitors":
        raw = _drift(raw)
    return raw


@app.get("/apis/site/v2/sports/{sport}/{league}/teams")
async def teams(sport: str, league: str) -> dict:
    if SPORTS.get(sport) != league:
        raise HTTPException(404)
    seen: dict[str, dict] = {}
    for event in _load(league).get("events", []):
        for competitor in event["competitions"][0]["competitors"]:
            team = competitor["team"]
            seen[str(team["id"])] = {
                "team": {
                    "id": str(team["id"]),
                    "displayName": team.get("displayName"),
                    "abbreviation": team.get("abbreviation"),
                    "logos": [{"href": team["logo"]}] if team.get("logo") else [],
                }
            }
    return {"sports": [{"leagues": [{"teams": list(seen.values())}]}]}


# ---- control API (used by tests, e2e and the incident demo) ----


class GameOverride(BaseModel):
    game_id: str
    state: Literal["pre", "in", "post"]
    home_score: int | None = None
    away_score: int | None = None


class Drift(BaseModel):
    mode: DriftMode


class TelegramUpdateIn(BaseModel):
    chat_id: int
    text: str


@app.get("/_control")
async def control_state() -> dict:
    return {"drift": state.drift, "overrides": state.overrides}


@app.post("/_control/game")
async def set_game(override: GameOverride) -> dict:
    state.overrides[override.game_id] = override.model_dump()
    return {"ok": True}


@app.post("/_control/drift")
async def set_drift(drift: Drift) -> dict:
    state.drift = drift.mode
    return {"ok": True, "drift": state.drift}


@app.post("/_control/reset")
async def reset() -> dict:
    state.reset()
    return {"ok": True}


@app.post("/_control/telegram/updates")
async def queue_update(update: TelegramUpdateIn) -> dict:
    state.updates.append(
        {
            "update_id": state.next_update_id,
            "message": {"chat": {"id": update.chat_id}, "text": update.text},
        }
    )
    state.next_update_id += 1
    return {"ok": True}


@app.get("/_control/telegram/messages")
async def sent_messages() -> list[dict]:
    return state.messages


# ---- Telegram Bot API sink ----


@app.post("/telegram/bot{token}/{method}")
async def telegram(token: str, method: str, payload: dict) -> dict:
    if method == "sendMessage":
        state.messages.append({"chat_id": payload.get("chat_id"), "text": payload.get("text")})
        return {"ok": True, "result": {"message_id": len(state.messages)}}
    if method == "getUpdates":
        offset = payload.get("offset", 0)
        for _ in range(10):  # short long-poll so the worker loop doesn't spin
            pending = [u for u in state.updates if u["update_id"] >= offset]
            if pending:
                return {"ok": True, "result": pending}
            await asyncio.sleep(0.5)
        return {"ok": True, "result": []}
    if method in ("deleteWebhook", "setWebhook"):
        return {"ok": True, "result": True}
    return {"ok": False, "description": f"fake-espn: unsupported method {method}"}


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}
