from __future__ import annotations

import json
import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

from analytics.llm import get_llm


class TextInsight(BaseModel):
    impact: str
    confidence: float = Field(ge=0, le=1)
    historical_note: str
    advice: str


PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Ты аналитик футбольных новостей. Ответь JSON с полями "
            "impact, confidence (0..1), historical_note, advice. "
            "Оцени, как похожие новости исторически влияли на результат.",
        ),
        (
            "human",
            "Текст пользователя:\n{text}\nКонтекст матчей (если есть):\n{context}",
        ),
    ]
)


def _extract_json(text: str) -> str:
    match = re.search(r"\{.*\}", text, re.S)
    return match.group(0) if match else text


FALLBACK = TextInsight(
    impact="неоднозначно",
    confidence=0.45,
    historical_note="Ротация и травмы лидеров чаще снижают остроту атаки фаворита, но не всегда меняют исход.",
    advice="Смотреть тоталы и обе забьют, а не только исход 1X2.",
)


async def analyze_text(text: str, context: str = "") -> TextInsight:
    llm = get_llm("insight")
    chain = PROMPT | llm | RunnableLambda(_parse)
    try:
        return await chain.ainvoke({"text": text, "context": context or "нет"})
    except Exception:
        return FALLBACK


def _parse(message) -> TextInsight:
    content = message.content if hasattr(message, "content") else str(message)
    try:
        return TextInsight.model_validate(json.loads(_extract_json(content)))
    except Exception:
        return FALLBACK


def format_insight(item: TextInsight, source: str) -> str:
    return (
        f"<b>Разбор новости/прогноза</b>\n"
        f"<i>{source[:280]}</i>\n\n"
        f"Влияние: {item.impact}\n"
        f"Уверенность: {item.confidence:.0%}\n"
        f"{item.historical_note}\n\n"
        f"{item.advice}"
    )
