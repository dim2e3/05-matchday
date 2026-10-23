from datetime import datetime
from typing import Literal

from pydantic import BaseModel

StatusState = Literal["pre", "in", "post"]
HomeAway = Literal["home", "away"]


class Team(BaseModel):
    id: str
    name: str
    abbreviation: str
    logo: str | None = None
    score: str | None = None
    winner: bool | None = None
    record: str | None = None


class Competitor(BaseModel):
    home_away: HomeAway
    team: Team


class Game(BaseModel):
    id: str
    start_time: datetime
    status_state: StatusState
    status_detail: str
    period: int | None = None
    clock: str | None = None
    competitors: list[Competitor]
    venue: str | None = None
    league: str | None = None


class ScoreboardResponse(BaseModel):
    league: str
    fetched_at: datetime
    stale: bool = False
    games: list[Game]


class MyGamesResponse(BaseModel):
    fetched_at: datetime
    stale: bool = False
    games: list[Game]


class TeamInfo(BaseModel):
    id: str
    name: str
    abbreviation: str
    logo: str | None = None


League = Literal["nfl", "nba", "nhl", "mlb"]


class FollowIn(BaseModel):
    league: League
    team_id: str


class FollowOut(BaseModel):
    league: str
    team_id: str
    team_name: str
    abbreviation: str
    logo: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MeOut(BaseModel):
    telegram_connected: bool
    follows: int


class TelegramLinkOut(BaseModel):
    url: str


class NotificationOut(BaseModel):
    kind: str
    league: str
    text: str
    status: str
    created_at: datetime
    sent_at: datetime | None = None

    model_config = {"from_attributes": True}
