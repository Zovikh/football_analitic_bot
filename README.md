# Scores24Bot — личный футбольный аналитик в Telegram

Бот не транслирует счёт. Он собирает открытую статистику, считает вероятности, ищет расхождения с коэффициентами и готовит короткие инсайты через локальную модель (Ollama + LangChain). Есть демо-модули SMM, HR и SEO.

Это учебный аналитический инструмент, а не финансовая рекомендация.

## Стек

- Python 3.12+, aiogram 3, SQLAlchemy 2, SQLite
- LangChain + Ollama (если модели нет — встроенный мок-LLM)
- API-Football, TheSportsDB, The Odds API, RSS, pytrends, Google Sheets
- matplotlib, APScheduler

Без ключей внешних API бот полностью работает на `MockSportsProvider` (Зенит–Спартак и топ-дерби).

## Быстрый старт

```powershell
cd d:\Scores24Bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

В `.env` укажите `BOT_TOKEN` от [@BotFather](https://t.me/BotFather).

Опционально локальная модель:

```powershell
ollama serve
ollama pull llama3.2
```

Если Ollama не запущена, аналитика всё равно отвечает шаблоном/моком.

```powershell
python -m bot.main
```

Тесты:

```powershell
pytest
```

## Команды

| Команда | Смысл |
|---|---|
| `/start` | Лиги и банкролл |
| `/matches` | Ближайшие матчи, подписка |
| `/analyze` | Предматчевый отчёт (H2H, форма, судья, вероятности) |
| `/value` | Валуйные алерты vs коэффициенты |
| `/insight` | Разбор текста новости или прогноза |
| `/chart` | График xG |
| `/smm` | 3 поста из RSS |
| `/hr` | Скрининг стажёра SQL/Python → CSV или Google Sheets |
| `/seo` | Частотность запроса за неделю |
| `/me` | Профиль и JOIN «АПЛ + банкролл > 1000» |

За час до матча планировщик сам шлёт отчёт подписчикам.

## LangChain-цепочка предматча

`статистика API → очистка JSON → ChatPromptTemplate → Ollama/мок → Pydantic-валидация → Telegram`

Если JSON модели ломается, пользователь получает отчёт из той же эвристики без ИИ.

## Переменные окружения

См. `.env.example`. Для Google Sheets: путь к JSON service account и имя таблицы (`GOOGLE_SHEETS_CREDENTIALS`, `GOOGLE_SHEETS_SPREADSHEET`).
