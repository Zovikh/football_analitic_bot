from __future__ import annotations

from sports.base import OddsQuote
from sports.http import RateLimitedClient

SPORT_KEYS = {
    "PL": "soccer_epl",
    "PD": "soccer_spain_la_liga",
    "BL1": "soccer_germany_bundesliga",
    "SA": "soccer_italy_serie_a",
    "FL1": "soccer_france_ligue_one",
}


class OddsApiClient:
    BASE = "https://api.the-odds-api.com/v4"

    def __init__(self, api_key: str, client: RateLimitedClient) -> None:
        self._key = api_key
        self._client = client

    async def quotes(self, league_id: str) -> list[tuple[str, str, list[OddsQuote]]]:
        sport = SPORT_KEYS.get(league_id)
        if not sport:
            return []
        payload = await self._client.get_json(
            f"{self.BASE}/sports/{sport}/odds",
            params={
                "apiKey": self._key,
                "regions": "eu",
                "markets": "h2h,totals",
                "oddsFormat": "decimal",
            },
        )
        if not isinstance(payload, list):
            return []
        result: list[tuple[str, str, list[OddsQuote]]] = []
        for event in payload:
            home = event.get("home_team") or ""
            away = event.get("away_team") or ""
            quotes: list[OddsQuote] = []
            for book in event.get("bookmakers") or []:
                book_name = book.get("title") or "book"
                for market in book.get("markets") or []:
                    key = market.get("key")
                    label = "1X2" if key == "h2h" else "OU"
                    for outcome in market.get("outcomes") or []:
                        quotes.append(
                            OddsQuote(
                                bookmaker=book_name,
                                market=label,
                                selection=str(outcome.get("name")),
                                price=float(outcome.get("price") or 0),
                            )
                        )
                if quotes:
                    break
            result.append((home, away, quotes))
        return result
