import logging
from datetime import datetime

from .schemas import Competitor, Game, Team

logger = logging.getLogger(__name__)


def _normalize_team(raw_competitor: dict) -> Competitor:
    raw_team = raw_competitor["team"]
    records = raw_competitor.get("records") or []
    record_summary = records[0].get("summary") if records else None

    team = Team(
        id=str(raw_team["id"]),
        name=raw_team.get("displayName") or raw_team.get("name") or "Unknown",
        abbreviation=raw_team.get("abbreviation") or "",
        logo=raw_team.get("logo"),
        score=raw_competitor.get("score"),
        winner=raw_competitor.get("winner"),
        record=record_summary,
    )
    return Competitor(home_away=raw_competitor["homeAway"], team=team)


def _normalize_event(raw_event: dict, league: str) -> Game | None:
    try:
        competition = raw_event["competitions"][0]
        status = competition["status"]
        status_type = status["type"]

        competitors = [_normalize_team(c) for c in competition["competitors"]]

        venue = competition.get("venue", {}).get("fullName")

        return Game(
            id=str(raw_event["id"]),
            start_time=datetime.fromisoformat(raw_event["date"]),
            status_state=status_type["state"],
            status_detail=status_type.get("shortDetail") or status_type.get("detail") or "",
            period=status.get("period"),
            clock=status.get("displayClock"),
            competitors=competitors,
            venue=venue,
            league=league,
        )
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning(
            "Skipping malformed event for league=%s id=%s: %s",
            league,
            raw_event.get("id", "?"),
            exc,
        )
        return None


def normalize_scoreboard(raw: dict, league: str) -> list[Game]:
    events = raw.get("events", [])
    games: list[Game] = []
    for raw_event in events:
        game = _normalize_event(raw_event, league)
        if game is not None:
            games.append(game)
    return games
