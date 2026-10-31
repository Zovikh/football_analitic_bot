from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from analytics.insight import analyze_text, format_insight
from bot.states import InsightStates

router = Router()


@router.message(Command("insight"))
@router.message(F.text == "Инсайт")
async def ask_insight(message: Message, state: FSMContext) -> None:
    await state.set_state(InsightStates.waiting_text)
    await message.answer("Пришли текст новости или прогноза. Например: «тренер сказал, что выпустит второй состав».")


@router.message(InsightStates.waiting_text)
async def handle_insight(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    await state.clear()
    result = await analyze_text(text)
    await message.answer(format_insight(result, text))
