from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from analytics.value import find_value_bets
from bot.keyboards import value_toggle
from core.db import session_scope
from core.models import Subscription
from core.queries import get_or_create_user, users_apl_bankroll_over
from sports.aggregator import SportsHub

router = Router()


@router.message(Command("value"))
@router.message(F.text == "Value")
async def value_menu(message: Message, hub: SportsHub) -> None:
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        enabled = user.notify_value
        subs = list(
            (await session.execute(select(Subscription).where(Subscription.user_id == user.id))).scalars()
        )
        vip = await users_apl_bankroll_over(session, 1000)
        lines = []
        for sub in subs[:5]:
            bundle = await hub.match_bundle(session, sub.fixture_id)
            bets = find_value_bets(bundle)
            if not bets:
                continue
            lines.append(f"<b>{bundle.fixture.title()}</b>\n" + "\n".join(b.as_text() for b in bets))
    text = "\n\n".join(lines) if lines else "Пока нет валуйных расхождений по твоим матчам."
    extra = f"\n\nПользователей АПЛ с банкроллом > 1000: {len(vip)}"
    await message.answer(
        f"{text}{extra}\n\n<i>Не является рекомендацией ставить.</i>",
        reply_markup=value_toggle(enabled),
    )


@router.callback_query(F.data == "value:toggle")
async def toggle_value(callback: CallbackQuery) -> None:
    async with session_scope() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        user.notify_value = not user.notify_value
        enabled = user.notify_value
    await callback.message.edit_reply_markup(reply_markup=value_toggle(enabled))
    await callback.answer("Алерты включены" if enabled else "Алерты выключены")


@router.callback_query(F.data.startswith("val:"))
async def value_one(callback: CallbackQuery, hub: SportsHub) -> None:
    fixture_id = callback.data.split(":", 1)[1]
    async with session_scope() as session:
        bundle = await hub.match_bundle(session, fixture_id)
        bets = find_value_bets(bundle)
    if not bets:
        await callback.message.answer("По этому матчу модель не видит edge выше порога.")
    else:
        body = "\n".join(b.as_text() for b in bets)
        await callback.message.answer(
            f"<b>Value · {bundle.fixture.title()}</b>\n{body}\n\n<i>Не является рекомендацией ставить.</i>"
        )
    await callback.answer()
