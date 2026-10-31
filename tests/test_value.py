from analytics.value import find_value_bets, implied
from sports.mock import MockSportsProvider


def test_implied_probability():
    assert abs(implied(2.0) - 0.5) < 1e-9
    assert implied(1.0) == 1.0


async def test_mock_value_bets_detect_over_15():
    provider = MockSportsProvider()
    bundle = await provider.match_bundle("m1")
    bets = find_value_bets(bundle, threshold=0.01)
    markets = {f"{b.market}:{b.selection}" for b in bets}
    assert any("1.5" in m or "Over 1.5" in m for m in markets)
    assert all(b.edge >= 0.01 for b in bets)
