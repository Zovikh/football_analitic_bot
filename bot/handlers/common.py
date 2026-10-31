from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from core.db import session_scope
from core.models import Subscription, UserLeague
from core.queries import get_or_create_user, users_apl_bankroll_over

router = Router()


@router.message(Command("me"))
@router.message(F.text == "Профиль")
async def profile(message: Message) -> None:
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        leagues = list((await session.execute(select(UserLeague).where(UserLeague.user_id == user.id))).scalars())
        subs = list((await session.execute(select(Subscription).where(Subscription.user_id == user.id))).scalars())
        vip = await users_apl_bankroll_over(session, 1000)
    league_names = ", ".join(x.league_name for x in leagues) or "не выбраны"
    sub_lines = "\n".join(f"• {s.home_team} — {s.away_team}" for s in subs) or "нет"
    await message.answer(
        f"<b>Профиль</b>\nБанкролл: {user.bankroll:g}\nValue-алерты: {'да' if user.notify_value else 'нет'}\n"
        f"Лиги: {league_names}\nПодписки:\n{sub_lines}\n\n"
        f"JOIN-пример (АПЛ и банкролл > 1000): {len(vip)} польз."
    )


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "/start — лиги и банкролл\n"
        "/matches — ближайшие матчи\n"
        "/analyze — предматчевый отчёт\n"
        "/value — валуйные алерты\n"
        "/insight — разбор текста\n"
        "/chart — график xG\n"
        "/smm — посты из новостей\n"
        "/hr — скрининг стажёра\n"
        "/seo — частотность запроса\n"
        "/me — профиль"
    )
