from __future__ import annotations

from sports.http import RateLimitedClient


class TheSportsDbClient:
    BASE = "https://www.thesportsdb.com/api/v1/json"

    def __init__(self, api_key: str, client: RateLimitedClient) -> None:
        self._key = api_key or "123"
        self._client = client

    async def lookup_team(self, name: str) -> dict | None:
        try:
            payload = await self._client.get_json(
                f"{self.BASE}/{self._key}/searchteams.php",
                params={"t": name},
            )
        except Exception:
            return None
        teams = payload.get("teams") if isinstance(payload, dict) else None
        if not teams:
            return None
        team = teams[0]
        return {
            "name": team.get("strTeam"),
            "badge": team.get("strBadge") or team.get("strTeamBadge"),
            "stadium": team.get("strStadium"),
            "league": team.get("strLeague"),
        }
