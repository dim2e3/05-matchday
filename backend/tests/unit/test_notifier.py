from datetime import UTC, datetime

import pytest

from matchday.notifier import detect_transition, format_message
from matchday.schemas import Competitor, Game, Team


def _game(home_score: str = "3", away_score: str = "2") -> Game:
    return Game(
        id="1",
        league="nhl",
        start_time=datetime(2026, 10, 23, 23, 0, tzinfo=UTC),
        status_state="post",
        status_detail="Final",
        competitors=[
            Competitor(
                home_away="home",
                team=Team(id="21", name="Toronto", abbreviation="TOR", score=home_score),
            ),
            Competitor(
                home_away="away",
                team=Team(id="10", name="Montreal", abbreviation="MTL", score=away_score),
            ),
        ],
    )


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("pre", "in", "kickoff"),
        ("in", "post", "final"),
        ("pre", "post", "final"),
        (None, "in", None),
        (None, "post", None),
        ("in", "in", None),
        ("post", "post", None),
        ("pre", "pre", None),
    ],
)
def test_s5_detect_transition(old, new, expected) -> None:
    assert detect_transition(old, new) == expected


def test_s5_kickoff_message() -> None:
    assert format_message(_game(), "kickoff") == "🟢 Kickoff: MTL @ TOR (NHL)"


def test_s5_final_message_has_score_away_first() -> None:
    assert format_message(_game("3", "2"), "final") == "🏁 Final: MTL 2 – 3 TOR (NHL)"


def test_s5_final_message_missing_score_shows_zero() -> None:
    assert format_message(_game(None, None), "final") == "🏁 Final: MTL 0 – 0 TOR (NHL)"
