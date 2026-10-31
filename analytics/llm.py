from __future__ import annotations

import httpx
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from core.config import settings

MOCK_PREMATCH = """{
  "headline": "Обе команды регулярно пропускают после 75-й минуты.",
  "form_summary": "Хозяева: W D W L W. Гости: L W W D W. Поздние пропущенные голы — системная проблема.",
  "h2h_summary": "В последних очных встречах часто забивают обе стороны.",
  "referee_note": "Судья назначает в среднем 4 угловых в первом тайме.",
  "key_duel": "Левый фланг хозяев против скоростного вингера гостей.",
  "prob_over_15": 0.78,
  "prob_over_25": 0.58,
  "prob_btts": 0.62,
  "value_hint": "ТБ(1.5) выглядит завышенным относительно рынка."
}"""

MOCK_INSIGHT = """{
  "impact": "негативно для фаворита",
  "confidence": 0.64,
  "historical_note": "Когда тренер анонсировал ротацию/второй состав, фаворит чаще не брал фору -1.5.",
  "advice": "Снизить уверенность в победе хозяев, смотреть тотал и обе забьют."
}"""

MOCK_SMM = """{
  "posts": [
    {"headline": "Шок: звезда выбывает перед дерби", "fact": "Источник сообщает о травме лидера атаки.", "question": "Кто закроет его зону?"},
    {"headline": "Дерби без главного голеадора?", "fact": "Последние 5 матчей команды без него — среднее 0.8 гола.", "question": "Это уже value на андер?"},
    {"headline": "Ротация или катастрофа", "fact": "Тренер намекает на второй состав.", "question": "Кто из молодёжи выстрелит?"}
  ]
}"""


def ollama_available() -> bool:
    if settings.use_mock_llm:
        return False
    try:
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=1.5)
        return response.status_code == 200
    except Exception:
        return False


def get_llm(kind: str = "prematch"):
    if ollama_available():
        try:
            from langchain_ollama import ChatOllama

            return ChatOllama(model=settings.ollama_model, base_url=settings.ollama_base_url, temperature=0.2)
        except Exception:
            pass
    content = {"prematch": MOCK_PREMATCH, "insight": MOCK_INSIGHT, "smm": MOCK_SMM}.get(kind, MOCK_PREMATCH)
    return FakeListChatModel(responses=[content])
