from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.keyboards import fixture_actions, fixtures_keyboard
from core.db import session_scope
from core.models import Subscription, UserLeague
from core.queries import get_or_create_user
from sports.aggregator import SportsHub

router = Router()


@router.message(Command("matches"))
@router.message(F.text == "Матчи")
async def list_matches(message: Message, hub: SportsHub) -> None:
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        leagues = list(
            (await session.execute(select(UserLeague).where(UserLeague.user_id == user.id))).scalars()
        )
        if not leagues:
            await message.answer("Сначала выбери лиги через /start")
            return
        fixtures = []
        for league in leagues:
            fixtures.extend(await hub.upcoming(session, league.league_id))
        fixtures.sort(key=lambda x: x.kickoff)
        if not fixtures:
            await message.answer("Ближайших матчей нет")
            return
        await message.answer("Ближайшие матчи:", reply_markup=fixtures_keyboard(fixtures[:12]))


@router.callback_query(F.data.startswith("fx:"))
async def fixture_card(callback: CallbackQuery, hub: SportsHub) -> None:
    fixture_id = callback.data.split(":", 1)[1]
    async with session_scope() as session:
        bundle = await hub.match_bundle(session, fixture_id)
    extra = ""
    card = await hub.team_card(bundle.fixture.home)
    if card and card.get("stadium"):
        extra = f"\nСтадион: {card['stadium']}"
    await callback.message.answer(
        f"<b>{bundle.fixture.title()}</b>\n{bundle.fixture.league_name}"
        f"\n{bundle.fixture.kickoff.strftime('%d.%m %H:%M UTC')}{extra}",
        reply_markup=fixture_actions(fixture_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub:"))
async def subscribe(callback: CallbackQuery, hub: SportsHub) -> None:
    fixture_id = callback.data.split(":", 1)[1]
    async with session_scope() as session:
        user = await get_or_create_user(session, callback.from_user.id, callback.from_user.username)
        exists = await session.execute(
            select(Subscription).where(Subscription.user_id == user.id, Subscription.fixture_id == fixture_id)
        )
        if exists.scalar_one_or_none():
            await callback.answer("Уже подписан", show_alert=True)
            return
        bundle = await hub.match_bundle(session, fixture_id)
        session.add(
            Subscription(
                user_id=user.id,
                fixture_id=fixture_id,
                home_team=bundle.fixture.home,
                away_team=bundle.fixture.away,
                league_id=bundle.fixture.league_id if bundle.fixture.league_id in {"PL", "RL", "PD", "BL1", "SA", "FL1"} else _guess_league(bundle.fixture.league_name),
                kickoff=bundle.fixture.kickoff,
                status=bundle.fixture.status,
            )
        )
    await callback.answer("Подписка оформлена. Отчёт придёт за час до матча.")
    await callback.message.answer("Готово. Можно открыть анализ кнопкой ниже.")


def _guess_league(name: str) -> str:
    mapping = {
        "Premier": "PL",
        "АПЛ": "PL",
        "РПЛ": "RL",
        "La Liga": "PD",
        "Ла Лига": "PD",
        "Bundes": "BL1",
        "Serie": "SA",
        "Ligue": "FL1",
    }
    for key, value in mapping.items():
        if key.lower() in name.lower():
            return value
    return "PL"
