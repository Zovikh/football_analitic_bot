from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from analytics.prematch import build_prematch_report, format_report
from bot.keyboards import fixtures_keyboard
from core.db import session_scope
from core.models import Subscription
from core.queries import get_or_create_user
from sports.aggregator import SportsHub

router = Router()


@router.message(Command("analyze"))
async def analyze_list(message: Message) -> None:
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        subs = list(
            (await session.execute(select(Subscription).where(Subscription.user_id == user.id))).scalars()
        )
    if not subs:
        await message.answer("Нет подписок. Открой /matches и подпишись на матч.")
        return
    from sports.base import Fixture

    items = [
        Fixture(s.fixture_id, s.league_id, s.league_id, s.home_team, s.away_team, s.kickoff, s.status)
        for s in subs
    ]
    await message.answer("Выбери матч для отчёта:", reply_markup=fixtures_keyboard(items, prefix="an"))


@router.callback_query(F.data.startswith("an:"))
async def run_analyze(callback: CallbackQuery, hub: SportsHub) -> None:
    fixture_id = callback.data.split(":", 1)[1]
    await callback.answer("Собираю статистику…")
    async with session_scope() as session:
        bundle = await hub.match_bundle(session, fixture_id)
    report = await build_prematch_report(bundle)
    await callback.message.answer(format_report(bundle, report))
