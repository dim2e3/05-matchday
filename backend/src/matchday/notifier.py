"""Pure notification logic (S5): which transition notifies, and the message text."""

from typing import Literal

from .schemas import Game

Kind = Literal["kickoff", "final"]

LEAGUE_LABELS = {"nfl": "NFL", "nba": "NBA", "nhl": "NHL", "mlb": "MLB"}


def detect_transition(old_state: str | None, new_state: str) -> Kind | None:
    """A game first seen (no previous state) never notifies: no back-fill."""
    if old_state == "pre" and new_state == "in":
        return "kickoff"
    if old_state == "in" and new_state == "post":
        return "final"
    if old_state == "pre" and new_state == "post":
        # Missed the live phase between two polls; the final is still news.
        return "final"
    return None


def _sides(game: Game):
    home = next(c.team for c in game.competitors if c.home_away == "home")
    away = next(c.team for c in game.competitors if c.home_away == "away")
    return home, away


def format_message(game: Game, kind: Kind) -> str:
    home, away = _sides(game)
    league = LEAGUE_LABELS.get(game.league or "", (game.league or "").upper())
    if kind == "kickoff":
        return f"🟢 Kickoff: {away.abbreviation} @ {home.abbreviation} ({league})"
    return (
        f"🏁 Final: {away.abbreviation} {away.score or 0} – "
        f"{home.score or 0} {home.abbreviation} ({league})"
    )
