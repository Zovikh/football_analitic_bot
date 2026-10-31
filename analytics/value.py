from __future__ import annotations

from dataclasses import dataclass

from analytics.stats import heuristic_probs
from core.config import settings
from sports.base import MatchBundle, OddsQuote


@dataclass
class ValueBet:
    market: str
    selection: str
    bookmaker: str
    price: float
    model_prob: float
    implied_prob: float
    edge: float

    def as_text(self) -> str:
        return (
            f"{self.market} · {self.selection} @ {self.price:.2f} ({self.bookmaker})\n"
            f"модель {self.model_prob:.0%} vs рынок {self.implied_prob:.0%} · edge {self.edge:.1%}"
        )


def implied(price: float) -> float:
    if price <= 1:
        return 1.0
    return 1.0 / price


def _map_quote_to_prob(quote: OddsQuote, probs: dict[str, float]) -> float | None:
    sel = quote.selection.lower()
    market = quote.market.lower()
    if "over 1.5" in sel or (market == "ou" and "1.5" in sel and "over" in sel):
        return probs["over_15"]
    if "over 2.5" in sel or (market == "ou" and "2.5" in sel and "over" in sel):
        return probs["over_25"]
    if market in {"btts", "ou"} and sel in {"yes", "btts yes"}:
        return probs["btts"]
    if quote.market == "BTTS" and sel.lower() in {"yes", "да"}:
        return probs["btts"]
    return None


def find_value_bets(bundle: MatchBundle, threshold: float | None = None) -> list[ValueBet]:
    edge_min = threshold if threshold is not None else settings.value_edge_threshold
    probs = heuristic_probs(bundle)
    found: list[ValueBet] = []
    for quote in bundle.odds:
        model_p = _map_quote_to_prob(quote, probs)
        if model_p is None or quote.price <= 1:
            continue
        imp = implied(quote.price)
        edge = model_p - imp
        if edge >= edge_min:
            found.append(
                ValueBet(
                    market=quote.market,
                    selection=quote.selection,
                    bookmaker=quote.bookmaker,
                    price=quote.price,
                    model_prob=model_p,
                    implied_prob=imp,
                    edge=edge,
                )
            )
    found.sort(key=lambda x: x.edge, reverse=True)
    return found
