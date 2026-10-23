import json
from pathlib import Path

import pytest

from scoreboard_api.normalizer import normalize_scoreboard

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("league", ["nfl", "nba", "nhl", "mlb"])
def test_normalize_scoreboard_produces_valid_games(league: str) -> None:
    raw = json.loads((FIXTURES_DIR / f"{league}_scoreboard.json").read_text())

    games = normalize_scoreboard(raw, league)

    assert len(games) == len(raw.get("events", []))
    for game in games:
        assert game.league == league
        assert game.status_state in ("pre", "in", "post")
        assert len(game.competitors) == 2
        home_away = {c.home_away for c in game.competitors}
        assert home_away == {"home", "away"}
        for competitor in game.competitors:
            assert competitor.team.id
            assert competitor.team.name


def test_normalize_scoreboard_skips_malformed_event() -> None:
    raw = {
        "events": [
            {"id": "1", "date": "2026-09-12T18:00Z", "competitions": []},
        ]
    }

    games = normalize_scoreboard(raw, "nfl")

    assert games == []


def test_normalize_scoreboard_empty_events() -> None:
    assert normalize_scoreboard({"events": []}, "nfl") == []
