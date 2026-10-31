from __future__ import annotations

import json
import re
from dataclasses import dataclass

import feedparser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from analytics.llm import get_llm

RSS_FEEDS = [
    "https://www.espn.com/espn/rss/soccer/news",
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
]


@dataclass
class SmmPost:
    headline: str
    fact: str
    question: str

    def as_text(self) -> str:
        return f"<b>{self.headline}</b>\n{self.fact}\n\n{self.question}"


PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Сгенерируй 3 коротких поста для Telegram/Twitter. JSON: "
            '{{"posts":[{{"headline":"...","fact":"...","question":"..."}}]}} '
            "Кликбейт, факт, вопрос для вовлечения. На русском.",
        ),
        ("human", "Новость:\n{title}\n{summary}"),
    ]
)


def fetch_headlines(limit: int = 5) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(url)
        except Exception:
            continue
        for entry in parsed.entries[:limit]:
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            if title:
                items.append((title, re.sub("<[^<]+?>", "", summary)[:400]))
        if items:
            break
    if not items:
        items = [
            (
                "Роналду получил травму перед ключевым матчем",
                "Нападающий пропустит ближайшую игру из-за повреждения мышцы.",
            )
        ]
    return items[:limit]


def _parse_posts(message) -> list[SmmPost]:
    content = message.content if hasattr(message, "content") else str(message)
    match = re.search(r"\{.*\}", content, re.S)
    raw = match.group(0) if match else content
    try:
        data = json.loads(raw)
        return [SmmPost(**row) for row in data.get("posts", [])][:3]
    except Exception:
        return [
            SmmPost("Шок в раздевалке", "Главная звезда под вопросом.", "Кто заменит лидера?"),
            SmmPost("Дерби без голеадора?", "Команда теряет остроту.", "Это уже влияние на тотал?"),
            SmmPost("Срочно в канал", "Новость разгоняется в агрегаторах.", "Как отреагирует рынок?"),
        ]


async def generate_posts(title: str, summary: str) -> list[SmmPost]:
    llm = get_llm("smm")
    chain = PROMPT | llm | RunnableLambda(_parse_posts)
    try:
        posts = await chain.ainvoke({"title": title, "summary": summary})
        return posts[:3]
    except Exception:
        return _parse_posts(type("M", (), {"content": ""})())
