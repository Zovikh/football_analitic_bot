from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message

from automation.seo import fetch_trends, format_seo
from bot.states import SeoStates
from viz.charts import seo_chart

router = Router()


@router.message(Command("seo"))
@router.message(F.text == "SEO")
async def seo_ask(message: Message, state: FSMContext) -> None:
    await state.set_state(SeoStates.waiting_query)
    await message.answer("Какой запрос проверить? Например: прогноз Зенит Спартак")


@router.message(SeoStates.waiting_query)
async def seo_run(message: Message, state: FSMContext) -> None:
    query = (message.text or "").strip()
    await state.clear()
    series, source = fetch_trends(query)
    photo = BufferedInputFile(seo_chart(query, series), filename="seo.png")
    await message.answer_photo(photo, caption=format_seo(query, series, source))
