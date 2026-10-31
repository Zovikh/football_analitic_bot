from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bot.handlers import setup_routers
from bot.middlewares import HubMiddleware, ThrottleMiddleware
from core.config import settings
from core.db import init_db
from jobs.scheduler import setup_scheduler
from sports.aggregator import SportsHub


async def main() -> None:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    if not settings.bot_token or settings.bot_token == "CHANGE_ME":
        raise SystemExit("Укажи BOT_TOKEN в файле .env")

    await init_db()
    hub = SportsHub()
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(ThrottleMiddleware())
    dp.update.middleware(HubMiddleware(hub))
    dp.include_router(setup_routers())

    scheduler = setup_scheduler(bot, hub)
    scheduler.start()
    logging.getLogger(__name__).info("Bot started (long polling)")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await hub.aclose()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
