from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass
class League:
    id: str
    name: str
    country: str


@dataclass
class Fixture:
    id: str
    league_id: str
    league_name: str
    home: str
    away: str
    kickoff: datetime
    status: str = "NS"

    def title(self) -> str:
        return f"{self.home} — {self.away}"


@dataclass
class TeamForm:
    team: str
    last_results: list[str]
    goals_for: list[int]
    goals_against: list[int]
    late_goals_conceded: int = 0


@dataclass
class H2H:
    home_wins: int
    away_wins: int
    draws: int
    last_scores: list[str]


@dataclass
class RefereeStats:
    name: str
    avg_yellows: float
    avg_corners_first_half: float


@dataclass
class Injury:
    player: str
    team: str
    reason: str


@dataclass
class OddsQuote:
    bookmaker: str
    market: str
    selection: str
    price: float


@dataclass
class MatchBundle:
    fixture: Fixture
    home_form: TeamForm
    away_form: TeamForm
    h2h: H2H
    referee: RefereeStats
    injuries: list[Injury] = field(default_factory=list)
    odds: list[OddsQuote] = field(default_factory=list)
    xg_home: list[float] = field(default_factory=list)
    xg_away: list[float] = field(default_factory=list)
    key_duel: str = ""

    def as_prompt_dict(self) -> dict:
        data = asdict(self)
        data["fixture"]["kickoff"] = self.fixture.kickoff.isoformat()
        return data


LEAGUES: list[League] = [
    League("PL", "АПЛ", "England"),
    League("RL", "РПЛ", "Russia"),
    League("PD", "Ла Лига", "Spain"),
    League("BL1", "Бундеслига", "Germany"),
    League("SA", "Серия А", "Italy"),
    League("FL1", "Лига 1", "France"),
]

LEAGUE_BY_ID = {item.id: item for item in LEAGUES}

API_FOOTBALL_LEAGUE_IDS = {
    "PL": 39,
    "PD": 140,
    "BL1": 78,
    "SA": 135,
    "FL1": 61,
    "RL": 235,
}


class SportsProvider(Protocol):
    async def upcoming(self, league_id: str, days: int = 7) -> list[Fixture]: ...

    async def match_bundle(self, fixture_id: str) -> MatchBundle: ...

    async def team_xg_series(self, team: str) -> list[float]: ...
