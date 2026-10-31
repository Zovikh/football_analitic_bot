from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import delete, select

from bot.keyboards import leagues_keyboard, main_menu
from bot.states import Onboarding
from core.db import session_scope
from core.models import UserLeague
from core.queries import get_or_create_user
from sports.base import LEAGUE_BY_ID

router = Router()

DISCLAIMER = (
    "Я не транслирую счёт — я собираю статистику, считаю вероятности и готовлю инсайты.\n"
    "Это учебный аналитический инструмент, а не финансовая рекомендация."
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        selected = {row.league_id for row in (await session.execute(
            select(UserLeague).where(UserLeague.user_id == user.id)
        )).scalars()}
    await state.clear()
    await message.answer(
        f"Привет! Я личный футбольный аналитик.\n\n{DISCLAIMER}\n\nВыбери лиги:",
        reply_markup=leagues_keyboard(selected),
    )
    await message.answer("Главное меню:", reply_markup=main_menu())


@router.callback_query(F.data.startswith("lg:"))
async def pick_league(callback: CallbackQuery, state: FSMContext) -> None:
    code = callback.data.split(":", 1)[1]
    async with session_scope() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        selected = {row.league_id for row in (await session.execute(
            select(UserLeague).where(UserLeague.user_id == user.id)
        )).scalars()}
        if code == "done":
            await callback.message.edit_text("Лиги сохранены. Теперь укажи банкролл числом (можно 0).")
            await state.set_state(Onboarding.bankroll)
            await callback.answer()
            return
        if code in selected:
            await session.execute(
                delete(UserLeague).where(UserLeague.user_id == user.id, UserLeague.league_id == code)
            )
            selected.discard(code)
        else:
            league = LEAGUE_BY_ID[code]
            session.add(UserLeague(user_id=user.id, league_id=league.id, league_name=league.name))
            selected.add(code)
    await callback.message.edit_reply_markup(reply_markup=leagues_keyboard(selected))
    await callback.answer()


@router.message(Onboarding.bankroll)
async def set_bankroll(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").replace(",", ".").strip()
    try:
        value = float(raw)
    except ValueError:
        await message.answer("Пришли число, например 1500")
        return
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        user.bankroll = value
    await state.clear()
    await message.answer(f"Банкролл: {value:g}. Команды: /matches /analyze /value /insight /chart /smm /hr /seo /me")
