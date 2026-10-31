from sports.base import LEAGUES
from sports.mock import MockSportsProvider


async def test_upcoming_rpl():
    provider = MockSportsProvider()
    items = await provider.upcoming("RL")
    assert items
    assert items[0].home == "Зенит"


async def test_bundle_has_odds_and_h2h():
    provider = MockSportsProvider()
    bundle = await provider.match_bundle("m1")
    assert bundle.h2h.last_scores
    assert bundle.odds
    assert bundle.home_form.late_goals_conceded >= 1


def test_leagues_include_pl():
    assert any(item.id == "PL" for item in LEAGUES)
