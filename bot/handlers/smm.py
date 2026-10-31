from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from automation.smm import fetch_headlines, generate_posts

router = Router()


@router.message(Command("smm"))
@router.message(F.text == "SMM")
async def smm_cmd(message: Message) -> None:
    headlines = fetch_headlines(3)
    title, summary = headlines[0]
    posts = await generate_posts(title, summary)
    chunks = [f"<b>Источник:</b> {title}"] + [f"{i}. {p.as_text()}" for i, p in enumerate(posts, 1)]
    await message.answer("\n\n".join(chunks))
