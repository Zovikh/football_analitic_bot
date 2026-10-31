from __future__ import annotations

from sports.base import MatchBundle, TeamForm


def late_goal_share(form: TeamForm) -> float:
    matches = max(len(form.last_results), 1)
    return form.late_goals_conceded / matches


def avg(values: list[int] | list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def heuristic_probs(bundle: MatchBundle) -> dict[str, float]:
    gf = avg(bundle.home_form.goals_for) + avg(bundle.away_form.goals_for)
    ga = avg(bundle.home_form.goals_against) + avg(bundle.away_form.goals_against)
    expected = (gf + ga) / 2
    late = (bundle.home_form.late_goals_conceded + bundle.away_form.late_goals_conceded) / 10
    over15 = min(0.92, max(0.45, 0.55 + expected * 0.08 + late * 0.1))
    over25 = min(0.85, max(0.28, 0.30 + expected * 0.09 + late * 0.08))
    btts = min(0.80, max(0.30, 0.35 + (avg(bundle.home_form.goals_for) + avg(bundle.away_form.goals_for)) * 0.08))
    return {"over_15": round(over15, 3), "over_25": round(over25, 3), "btts": round(btts, 3)}


def template_report(bundle: MatchBundle) -> dict:
    probs = heuristic_probs(bundle)
    inj = ", ".join(f"{i.player} ({i.team})" for i in bundle.injuries) or "нет данных"
    return {
        "headline": (
            f"В последних 5 матчах обе команды пропускают после 75-й минуты "
            f"({bundle.home_form.late_goals_conceded} и {bundle.away_form.late_goals_conceded} эпизода)."
        ),
        "form_summary": (
            f"{bundle.home_form.team}: {''.join(bundle.home_form.last_results)}. "
            f"{bundle.away_form.team}: {''.join(bundle.away_form.last_results)}."
        ),
        "h2h_summary": (
            f"H2H: {bundle.h2h.home_wins}-{bundle.h2h.draws}-{bundle.h2h.away_wins}. "
            f"Счета: {', '.join(bundle.h2h.last_scores) or 'н/д'}."
        ),
        "referee_note": (
            f"{bundle.referee.name}: в среднем {bundle.referee.avg_corners_first_half:.1f} угловых в первом тайме, "
            f"{bundle.referee.avg_yellows:.1f} жёлтых."
        ),
        "key_duel": bundle.key_duel or "фланговая скорость против опорной зоны",
        "prob_over_15": probs["over_15"],
        "prob_over_25": probs["over_25"],
        "prob_btts": probs["btts"],
        "value_hint": f"Травмы/потери: {inj}.",
    }
