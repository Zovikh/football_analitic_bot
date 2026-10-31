from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from automation.hr import QUESTIONS, evaluate
from automation.sheets import save_hr_result
from bot.states import HrStates
from core.db import session_scope
from core.models import HrAnswer, HrSession
from core.queries import get_or_create_user

router = Router()

STATE_ORDER = [HrStates.q1, HrStates.q2, HrStates.q3]


@router.message(Command("hr"))
@router.message(F.text == "HR")
async def hr_start(message: Message, state: FSMContext) -> None:
    async with session_scope() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        hr = HrSession(user_id=user.id, candidate_name=message.from_user.full_name)
        session.add(hr)
        await session.flush()
        await state.update_data(session_id=hr.id, score=0, details=[])
    await state.set_state(HrStates.q1)
    await message.answer("Скрининг стажёра. 3 вопроса.\n\n" + QUESTIONS[0]["text"])


@router.message(HrStates.q1)
async def hr_q1(message: Message, state: FSMContext) -> None:
    await _accept(message, state, 0, HrStates.q2)


@router.message(HrStates.q2)
async def hr_q2(message: Message, state: FSMContext) -> None:
    await _accept(message, state, 1, HrStates.q3)


@router.message(HrStates.q3)
async def hr_q3(message: Message, state: FSMContext) -> None:
    await _accept(message, state, 2, None)


async def _accept(message: Message, state: FSMContext, index: int, next_state) -> None:
    question = QUESTIONS[index]
    result = evaluate(question["key"], message.text or "")
    data = await state.get_data()
    score = int(data.get("score", 0)) + (1 if result.passed else 0)
    details = list(data.get("details", []))
    details.append(f"{question['key']}: {'ok' if result.passed else 'fail'} ({result.comment})")
    async with session_scope() as session:
        session.add(
            HrAnswer(
                session_id=data["session_id"],
                question_key=question["key"],
                answer_text=message.text or "",
                passed=result.passed,
                comment=result.comment,
            )
        )
    await state.update_data(score=score, details=details)
    mark = "✅" if result.passed else "❌"
    await message.answer(f"{mark} {result.comment}")
    if next_state:
        await state.set_state(next_state)
        await message.answer(QUESTIONS[index + 1]["text"])
        return
    status = "pass" if score >= 2 else "fail"
    dest = save_hr_result(
        message.from_user.id,
        message.from_user.username,
        score,
        status,
        "; ".join(details),
    )
    async with session_scope() as session:
        hr = await session.get(HrSession, data["session_id"])
        if hr:
            hr.status = status
            hr.score = score
    await state.clear()
    await message.answer(f"Итог: {score}/3, статус {status}. Записано в {dest}.")
