from __future__ import annotations

import json
import re

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from pydantic import BaseModel, Field, field_validator

from analytics.llm import get_llm
from analytics.stats import heuristic_probs, template_report
from sports.base import MatchBundle


class PrematchReport(BaseModel):
    headline: str
    form_summary: str
    h2h_summary: str
    referee_note: str
    key_duel: str
    prob_over_15: float = Field(ge=0, le=1)
    prob_over_25: float = Field(ge=0, le=1)
    prob_btts: float = Field(ge=0, le=1)
    value_hint: str = ""

    @field_validator("prob_over_15", "prob_over_25", "prob_btts", mode="before")
    @classmethod
    def clamp_prob(cls, value):
        return float(value)


parser = PydanticOutputParser(pydantic_object=PrematchReport)

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Ты футбольный аналитик. Ответь СТРОГО JSON по схеме. "
            "Не выдумывай игроков, которых нет во входных данных. Вероятности — числа 0..1.\n{format}",
        ),
        (
            "human",
            "Матч: {home} — {away}, лига {league}.\n"
            "Статистика JSON:\n{stats}\n"
            "Эвристические вероятности: {heuristics}\n"
            "Собери краткий предматчевый отчёт.",
        ),
    ]
).partial(format=parser.get_format_instructions())


def _extract_json(text: str) -> str:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.S)
    return match.group(0) if match else text


def _clean(bundle: MatchBundle) -> dict:
    data = bundle.as_prompt_dict()
    data["heuristics"] = heuristic_probs(bundle)
    return data


async def build_prematch_report(bundle: MatchBundle) -> PrematchReport:
    fallback = PrematchReport.model_validate(template_report(bundle))
    llm = get_llm("prematch")

    def parse_or_fallback(message) -> PrematchReport:
        content = message.content if hasattr(message, "content") else str(message)
        try:
            return PrematchReport.model_validate(json.loads(_extract_json(content)))
        except Exception:
            return fallback

    chain = (
        RunnableLambda(lambda _: _clean(bundle))
        | RunnablePassthrough.assign(
            home=lambda d: bundle.fixture.home,
            away=lambda d: bundle.fixture.away,
            league=lambda d: bundle.fixture.league_name,
            stats=lambda d: json.dumps(d, ensure_ascii=False),
            heuristics=lambda d: json.dumps(d["heuristics"], ensure_ascii=False),
        )
        | PROMPT
        | llm
        | RunnableLambda(parse_or_fallback)
    )
    try:
        return await chain.ainvoke({})
    except Exception:
        return fallback


def format_report(bundle: MatchBundle, report: PrematchReport) -> str:
    kickoff = bundle.fixture.kickoff.strftime("%d.%m %H:%M UTC")
    return (
        f"<b>{bundle.fixture.title()}</b>\n"
        f"{bundle.fixture.league_name} · {kickoff}\n\n"
        f"{report.headline}\n\n"
        f"<b>Форма:</b> {report.form_summary}\n"
        f"<b>H2H:</b> {report.h2h_summary}\n"
        f"<b>Судья:</b> {report.referee_note}\n"
        f"<b>Ключевая дуэль:</b> {report.key_duel}\n\n"
        f"Вероятность ТБ(1.5): <b>{report.prob_over_15:.0%}</b>\n"
        f"ТБ(2.5): {report.prob_over_25:.0%} · обе забьют: {report.prob_btts:.0%}\n"
        f"{report.value_hint}\n\n"
        f"<i>Это аналитика, а не рекомендация ставить.</i>"
    )
