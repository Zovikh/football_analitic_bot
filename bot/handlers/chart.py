from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy import select

from core.db import session_scope
from core.models import Subscription
from core.queries import get_or_create_user
from sports.aggregator import SportsHub
from viz.charts import xg_chart

router = Router()


@router.message(Command("chart"))
@router.message(F.text == "График")
async def chart_cmd(message: Message, hub: SportsHub) -> None:
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        sub = (
            await session.execute(
                select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.kickoff.asc())
            )
        ).scalars().first()
        team = sub.home_team if sub else "Зенит"
        series = await hub.team_xg_series(session, team)
    photo = BufferedInputFile(xg_chart(team, series), filename="xg.png")
    await message.answer_photo(photo, caption=f"Динамика xG: {team}")


@router.callback_query(F.data.startswith("xg:"))
async def chart_fixture(callback: CallbackQuery, hub: SportsHub) -> None:
    fixture_id = callback.data.split(":", 1)[1]
    async with session_scope() as session:
        bundle = await hub.match_bundle(session, fixture_id)
        series = bundle.xg_home or await hub.team_xg_series(session, bundle.fixture.home)
    photo = BufferedInputFile(xg_chart(bundle.fixture.home, series), filename="xg.png")
    await callback.message.answer_photo(photo, caption=f"xG {bundle.fixture.home}")
    await callback.answer()
