from analytics.prematch import PrematchReport, build_prematch_report, format_report
from analytics.stats import heuristic_probs
from sports.mock import MockSportsProvider


async def test_prematch_report_valid():
    bundle = await MockSportsProvider().match_bundle("m1")
    report = await build_prematch_report(bundle)
    assert isinstance(report, PrematchReport)
    assert 0 <= report.prob_over_15 <= 1
    text = format_report(bundle, report)
    assert "Зенит" in text
    assert "ТБ(1.5)" in text


async def test_heuristic_bounds():
    bundle = await MockSportsProvider().match_bundle("m2")
    probs = heuristic_probs(bundle)
    assert 0 <= probs["over_15"] <= 1
    assert probs["over_15"] >= probs["over_25"]
