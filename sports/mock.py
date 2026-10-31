from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sports.base import Fixture, H2H, Injury, MatchBundle, OddsQuote, RefereeStats, TeamForm


def _utc(hours: int) -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=hours)


class MockSportsProvider:
    def __init__(self) -> None:
        self._fixtures = [
            Fixture("m1", "RL", "РПЛ", "Зенит", "Спартак", _utc(2)),
            Fixture("m2", "PL", "АПЛ", "Арсенал", "Челси", _utc(5)),
            Fixture("m3", "PD", "Ла Лига", "Барселона", "Реал Мадрид", _utc(8)),
            Fixture("m4", "BL1", "Бундеслига", "Бавария", "Боруссия Д", _utc(26)),
            Fixture("m5", "SA", "Серия А", "Интер", "Милан", _utc(30)),
        ]
        self._bundles = {item.id: self._build_bundle(item) for item in self._fixtures}

    def _build_bundle(self, fixture: Fixture) -> MatchBundle:
        home_form = TeamForm(
            team=fixture.home,
            last_results=["W", "D", "W", "L", "W"],
            goals_for=[2, 1, 3, 0, 2],
            goals_against=[1, 1, 1, 2, 1],
            late_goals_conceded=3,
        )
        away_form = TeamForm(
            team=fixture.away,
            last_results=["L", "W", "W", "D", "W"],
            goals_for=[0, 2, 1, 1, 3],
            goals_against=[1, 1, 0, 1, 2],
            late_goals_conceded=4,
        )
        return MatchBundle(
            fixture=fixture,
            home_form=home_form,
            away_form=away_form,
            h2h=H2H(home_wins=3, away_wins=2, draws=2, last_scores=["2:1", "1:1", "0:2", "3:1", "1:0"]),
            referee=RefereeStats(name="Сергей Карасев", avg_yellows=4.2, avg_corners_first_half=4.0),
            injuries=[
                Injury(player="Основной ЦЗ", team=fixture.home, reason="мышца"),
                Injury(player="Правый вингер", team=fixture.away, reason="ankle"),
            ],
            odds=[
                OddsQuote("Pinnacle", "1X2", "1", 2.10),
                OddsQuote("Pinnacle", "1X2", "X", 3.40),
                OddsQuote("Pinnacle", "1X2", "2", 3.55),
                OddsQuote("Pinnacle", "OU", "Over 1.5", 1.28),
                OddsQuote("Pinnacle", "OU", "Over 2.5", 1.85),
                OddsQuote("Pinnacle", "BTTS", "Yes", 1.72),
            ],
            xg_home=[1.4, 1.8, 2.1, 0.9, 1.6, 1.7, 2.0],
            xg_away=[1.1, 1.5, 1.2, 1.9, 1.3, 1.6, 1.8],
            key_duel=f"левый фланг {fixture.home} против скоростного вингера {fixture.away}",
        )

    async def upcoming(self, league_id: str, days: int = 7) -> list[Fixture]:
        until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=days)
        return [f for f in self._fixtures if f.league_id == league_id and f.kickoff <= until]

    async def match_bundle(self, fixture_id: str) -> MatchBundle:
        if fixture_id not in self._bundles:
            raise KeyError(fixture_id)
        return self._bundles[fixture_id]

    async def team_xg_series(self, team: str) -> list[float]:
        mapping = {
            "Зенит": [1.6, 1.8, 2.2, 1.1, 1.9, 1.4, 2.0, 1.7],
            "Спартак": [1.2, 1.5, 1.0, 1.8, 1.3, 1.6, 1.1, 1.4],
            "Арсенал": [1.9, 2.1, 1.7, 2.4, 1.8, 2.0, 2.2, 1.6],
        }
        return mapping.get(team, [1.2, 1.3, 1.1, 1.5, 1.4, 1.6, 1.3, 1.7])

    def all_upcoming(self) -> list[Fixture]:
        return list(self._fixtures)
