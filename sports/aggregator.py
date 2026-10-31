from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from core.cache import cache_get, cache_set
from core.config import settings
from sports.api_football import ApiFootballProvider
from sports.base import Fixture, MatchBundle, OddsQuote
from sports.http import RateLimitedClient
from sports.mock import MockSportsProvider
from sports.odds import OddsApiClient
from sports.thesportsdb import TheSportsDbClient


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def fixture_from_dict(data: dict) -> Fixture:
    return Fixture(
        id=data["id"],
        league_id=data["league_id"],
        league_name=data["league_name"],
        home=data["home"],
        away=data["away"],
        kickoff=_dt(data["kickoff"]),
        status=data.get("status", "NS"),
    )


def fixture_to_dict(item: Fixture) -> dict:
    return {
        "id": item.id,
        "league_id": item.league_id,
        "league_name": item.league_name,
        "home": item.home,
        "away": item.away,
        "kickoff": item.kickoff.isoformat(),
        "status": item.status,
    }


class SportsHub:
    def __init__(self) -> None:
        self.http = RateLimitedClient(rps=settings.request_rps)
        self.mock = MockSportsProvider()
        self.api_football = (
            ApiFootballProvider(settings.api_football_key, self.http) if settings.has_api_football else None
        )
        self.odds = OddsApiClient(settings.odds_api_key, self.http) if settings.has_odds_api else None
        self.thesportsdb = TheSportsDbClient(settings.thesportsdb_key, self.http)

    async def upcoming(self, session: AsyncSession, league_id: str, days: int = 7) -> list[Fixture]:
        key = f"upcoming:{league_id}:{days}"
        cached = await cache_get(session, key)
        if isinstance(cached, list) and cached:
            return [fixture_from_dict(row) for row in cached]
        items: list[Fixture] = []
        if self.api_football:
            try:
                items = await self.api_football.upcoming(league_id, days)
            except Exception:
                items = []
        if not items:
            items = await self.mock.upcoming(league_id, days)
        await cache_set(session, key, [fixture_to_dict(x) for x in items], ttl_seconds=600)
        return items

    async def match_bundle(self, session: AsyncSession, fixture_id: str) -> MatchBundle:
        key = f"bundle:{fixture_id}"
        cached = await cache_get(session, key)
        if isinstance(cached, dict) and cached:
            return self._bundle_from_cache(cached)
        bundle: MatchBundle | None = None
        if self.api_football and not fixture_id.startswith("m"):
            try:
                bundle = await self.api_football.match_bundle(fixture_id)
            except Exception:
                bundle = None
        if bundle is None:
            bundle = await self.mock.match_bundle(fixture_id)
        if self.odds and bundle.fixture.league_id:
            try:
                quotes = await self._odds_for_fixture(session, bundle)
                if quotes:
                    bundle.odds = quotes
            except Exception:
                pass
        await cache_set(session, key, json.loads(json.dumps(bundle.as_prompt_dict(), default=str)), 1800)
        return bundle

    async def team_xg_series(self, session: AsyncSession, team: str) -> list[float]:
        key = f"xg:{team}"
        cached = await cache_get(session, key)
        if isinstance(cached, list) and cached:
            return [float(x) for x in cached]
        series = await self.mock.team_xg_series(team)
        await cache_set(session, key, series, 3600)
        return series

    async def team_card(self, name: str) -> dict | None:
        return await self.thesportsdb.lookup_team(name)

    async def _odds_for_fixture(self, session: AsyncSession, bundle: MatchBundle) -> list[OddsQuote]:
        if not self.odds:
            return []
        key = f"odds:{bundle.fixture.league_id}"
        cached = await cache_get(session, key)
        rows: list[tuple[str, str, list[dict]]]
        if isinstance(cached, list):
            rows = [(a, b, c) for a, b, c in cached]
        else:
            live = await self.odds.quotes(bundle.fixture.league_id)
            serial = [
                (home, away, [q.__dict__ for q in quotes])
                for home, away, quotes in live
            ]
            await cache_set(session, key, serial, 300)
            rows = serial
        home = bundle.fixture.home.lower()
        away = bundle.fixture.away.lower()
        for h, a, quotes in rows:
            if h.lower() in home or home in h.lower() or a.lower() in away or away in a.lower():
                return [OddsQuote(**q) if isinstance(q, dict) else q for q in quotes]
        return []

    def _bundle_from_cache(self, data: dict) -> MatchBundle:
        from sports.base import H2H, Injury, RefereeStats, TeamForm

        fx = data["fixture"]
        fixture = fixture_from_dict(fx)
        hf = data["home_form"]
        af = data["away_form"]
        h2h = data["h2h"]
        ref = data["referee"]
        return MatchBundle(
            fixture=fixture,
            home_form=TeamForm(**hf),
            away_form=TeamForm(**af),
            h2h=H2H(**h2h),
            referee=RefereeStats(**ref),
            injuries=[Injury(**i) for i in data.get("injuries") or []],
            odds=[OddsQuote(**o) for o in data.get("odds") or []],
            xg_home=[float(x) for x in data.get("xg_home") or []],
            xg_away=[float(x) for x in data.get("xg_away") or []],
            key_duel=data.get("key_duel") or "",
        )

    async def aclose(self) -> None:
        await self.http.aclose()
