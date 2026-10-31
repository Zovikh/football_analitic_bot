from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sports.base import (
    API_FOOTBALL_LEAGUE_IDS,
    Fixture,
    H2H,
    Injury,
    MatchBundle,
    RefereeStats,
    TeamForm,
)
from sports.http import RateLimitedClient


class ApiFootballProvider:
    BASE = "https://v3.football.api-sports.io"

    def __init__(self, api_key: str, client: RateLimitedClient) -> None:
        self._key = api_key
        self._client = client

    def _headers(self) -> dict[str, str]:
        return {"x-apisports-key": self._key}

    async def _get(self, path: str, params: dict) -> list:
        payload = await self._client.get_json(f"{self.BASE}{path}", headers=self._headers(), params=params)
        if isinstance(payload, dict):
            return payload.get("response") or []
        return []

    async def upcoming(self, league_id: str, days: int = 7) -> list[Fixture]:
        api_id = API_FOOTBALL_LEAGUE_IDS.get(league_id)
        if not api_id:
            return []
        now = datetime.now(timezone.utc)
        season = now.year if now.month >= 7 else now.year - 1
        items = await self._get(
            "/fixtures",
            {
                "league": api_id,
                "season": season,
                "from": now.date().isoformat(),
                "to": (now + timedelta(days=days)).date().isoformat(),
                "status": "NS",
            },
        )
        fixtures: list[Fixture] = []
        for row in items:
            fx = row.get("fixture") or {}
            teams = row.get("teams") or {}
            league = row.get("league") or {}
            date_raw = fx.get("date")
            if not date_raw:
                continue
            kickoff = datetime.fromisoformat(date_raw.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
            fixtures.append(
                Fixture(
                    id=str(fx.get("id")),
                    league_id=league_id,
                    league_name=league.get("name") or league_id,
                    home=(teams.get("home") or {}).get("name") or "?",
                    away=(teams.get("away") or {}).get("name") or "?",
                    kickoff=kickoff,
                    status=(fx.get("status") or {}).get("short") or "NS",
                )
            )
        return fixtures

    async def match_bundle(self, fixture_id: str) -> MatchBundle:
        items = await self._get("/fixtures", {"id": fixture_id})
        if not items:
            raise KeyError(fixture_id)
        row = items[0]
        fx = row.get("fixture") or {}
        teams = row.get("teams") or {}
        league = row.get("league") or {}
        date_raw = fx.get("date")
        kickoff = datetime.now(timezone.utc).replace(tzinfo=None)
        if date_raw:
            kickoff = datetime.fromisoformat(date_raw.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
        raw_league = str(league.get("id") or "")
        reverse = {str(v): k for k, v in API_FOOTBALL_LEAGUE_IDS.items()}
        fixture = Fixture(
            id=str(fx.get("id")),
            league_id=reverse.get(raw_league, raw_league),
            league_name=league.get("name") or "",
            home=(teams.get("home") or {}).get("name") or "?",
            away=(teams.get("away") or {}).get("name") or "?",
            kickoff=kickoff,
            status=(fx.get("status") or {}).get("short") or "NS",
        )
        home_id = (teams.get("home") or {}).get("id")
        away_id = (teams.get("away") or {}).get("id")
        home_form = await self._team_form(home_id, fixture.home)
        away_form = await self._team_form(away_id, fixture.away)
        h2h = await self._h2h(home_id, away_id)
        referee = RefereeStats(
            name=fx.get("referee") or "н/д",
            avg_yellows=3.8,
            avg_corners_first_half=3.5,
        )
        injuries = await self._injuries(home_id, away_id, fixture.home, fixture.away)
        return MatchBundle(
            fixture=fixture,
            home_form=home_form,
            away_form=away_form,
            h2h=h2h,
            referee=referee,
            injuries=injuries,
            key_duel=f"фланговая дуэль {fixture.home} vs {fixture.away}",
        )

    async def team_xg_series(self, team: str) -> list[float]:
        return [1.1, 1.3, 1.0, 1.4, 1.2, 1.5, 1.3, 1.6]

    async def _team_form(self, team_id: int | None, name: str) -> TeamForm:
        if not team_id:
            return TeamForm(name, ["D"] * 5, [1] * 5, [1] * 5, 1)
        items = await self._get("/fixtures", {"team": team_id, "last": 5})
        results: list[str] = []
        gf: list[int] = []
        ga: list[int] = []
        late = 0
        for row in items:
            teams = row.get("teams") or {}
            goals = row.get("goals") or {}
            is_home = (teams.get("home") or {}).get("id") == team_id
            scored = int(goals.get("home") or 0) if is_home else int(goals.get("away") or 0)
            conceded = int(goals.get("away") or 0) if is_home else int(goals.get("home") or 0)
            gf.append(scored)
            ga.append(conceded)
            if scored > conceded:
                results.append("W")
            elif scored < conceded:
                results.append("L")
            else:
                results.append("D")
            events = row.get("events") or []
            for event in events:
                if event.get("type") == "Goal" and int((event.get("time") or {}).get("elapsed") or 0) >= 75:
                    scorer_team = ((event.get("team") or {}).get("id"))
                    if scorer_team != team_id:
                        late += 1
        return TeamForm(name, results or ["D"], gf or [1], ga or [1], late)

    async def _h2h(self, home_id: int | None, away_id: int | None) -> H2H:
        if not home_id or not away_id:
            return H2H(0, 0, 0, [])
        items = await self._get("/fixtures/headtohead", {"h2h": f"{home_id}-{away_id}", "last": 5})
        hw = aw = dr = 0
        scores: list[str] = []
        for row in items:
            goals = row.get("goals") or {}
            h = int(goals.get("home") or 0)
            a = int(goals.get("away") or 0)
            scores.append(f"{h}:{a}")
            if h > a:
                hw += 1
            elif a > h:
                aw += 1
            else:
                dr += 1
        return H2H(hw, aw, dr, scores)

    async def _injuries(self, home_id, away_id, home_name, away_name) -> list[Injury]:
        result: list[Injury] = []
        for team_id, team_name in ((home_id, home_name), (away_id, away_name)):
            if not team_id:
                continue
            try:
                items = await self._get("/injuries", {"team": team_id})
            except Exception:
                continue
            for row in items[:3]:
                player = (row.get("player") or {}).get("name") or "игрок"
                reason = (row.get("player") or {}).get("reason") or "травма"
                result.append(Injury(player=player, team=team_name, reason=reason))
        return result
