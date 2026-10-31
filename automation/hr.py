from __future__ import annotations

import ast
import re
from dataclasses import dataclass

QUESTIONS = [
    {
        "key": "sql_xg",
        "kind": "sql",
        "text": (
            "SQL: напиши запрос, который вернёт топ-5 игроков по сумме xG. "
            "Таблица players(id, name), shots(id, player_id, xg)."
        ),
    },
    {
        "key": "sql_join",
        "kind": "sql",
        "text": (
            "SQL: найди все матчи АПЛ, где обе команды забили. "
            "Таблицы matches(id, league, home_goals, away_goals), leagues(id, name)."
        ),
    },
    {
        "key": "py_form",
        "kind": "python",
        "text": (
            "Python: напиши функцию last_n_form(results: list[str], n: int) -> str, "
            "которая вернёт строку формы из последних n матчей (например 'WDLWW')."
        ),
    },
]


@dataclass
class CheckResult:
    passed: bool
    comment: str


def check_sql(answer: str) -> CheckResult:
    text = answer.lower()
    need = ["select", "group by", "order by", "limit"]
    missing = [token for token in need if token not in text]
    join_ok = "join" in text or "from matches" in text
    if missing:
        return CheckResult(False, f"Не хватает конструкций: {', '.join(missing)}")
    if "sum" not in text and "join" not in text and not join_ok:
        return CheckResult(False, "Ожидалась агрегация или JOIN")
    return CheckResult(True, "Формат SQL выглядит валидным")


def check_sql_join(answer: str) -> CheckResult:
    text = answer.lower()
    need = ["select", "join"]
    missing = [t for t in need if t not in text]
    if "home_goals" not in text or "away_goals" not in text:
        missing.append("фильтр по голам обеих команд")
    if missing:
        return CheckResult(False, f"Не хватает: {', '.join(missing)}")
    return CheckResult(True, "JOIN и фильтр по голам на месте")


def check_python(answer: str) -> CheckResult:
    snippet = answer.strip()
    snippet = re.sub(r"^```(?:python)?", "", snippet)
    snippet = re.sub(r"```$", "", snippet).strip()
    try:
        tree = ast.parse(snippet)
    except SyntaxError as exc:
        return CheckResult(False, f"Синтаксическая ошибка: {exc.msg}")
    has_fn = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    if not has_fn:
        return CheckResult(False, "Нужна функция def")
    if "return" not in snippet:
        return CheckResult(False, "Нет return")
    return CheckResult(True, "Python-синтаксис и функция в порядке")


def evaluate(question_key: str, answer: str) -> CheckResult:
    if question_key == "sql_xg":
        return check_sql(answer)
    if question_key == "sql_join":
        return check_sql_join(answer)
    return check_python(answer)
