from __future__ import annotations

from datetime import date, timedelta

from analytics.stats import avg


def mock_series(query: str) -> list[tuple[str, int]]:
    base = 40 + (sum(ord(ch) for ch in query) % 30)
    days = []
    today = date.today()
    wave = [0, 4, -2, 8, 12, 6, 15]
    for i, delta in enumerate(wave):
        day = today - timedelta(days=6 - i)
        days.append((day.isoformat(), max(5, base + delta)))
    return days


def fetch_trends(query: str) -> tuple[list[tuple[str, int]], str]:
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="ru-RU", tz=180, timeout=(5, 10))
        pytrends.build_payload([query], timeframe="now 7-d")
        frame = pytrends.interest_over_time()
        if frame is None or frame.empty:
            return mock_series(query), "mock"
        series: list[tuple[str, int]] = []
        col = query if query in frame.columns else frame.columns[0]
        for idx, value in frame[col].items():
            series.append((str(idx)[:10], int(value)))
        return series[-7:], "pytrends"
    except Exception:
        return mock_series(query), "mock"


def format_seo(query: str, series: list[tuple[str, int]], source: str) -> str:
    if not series:
        return "Нет данных"
    first, last = series[0][1], series[-1][1]
    change = last - first
    arrow = "рост" if change > 0 else "падение" if change < 0 else "без изменений"
    lines = "\n".join(f"{day}: {value}" for day, value in series)
    return (
        f"<b>SEO: «{query}»</b>\n"
        f"Источник: {source}\n"
        f"Среднее за неделю: {avg([v for _, v in series]):.0f}\n"
        f"Динамика: {arrow} ({change:+d})\n\n"
        f"{lines}"
    )
