from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sports.base import LEAGUES, Fixture


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Матчи"), KeyboardButton(text="Профиль")],
            [KeyboardButton(text="Value"), KeyboardButton(text="Инсайт")],
            [KeyboardButton(text="SMM"), KeyboardButton(text="SEO")],
            [KeyboardButton(text="HR"), KeyboardButton(text="График")],
        ],
        resize_keyboard=True,
    )


def leagues_keyboard(selected: set[str] | None = None) -> InlineKeyboardMarkup:
    selected = selected or set()
    builder = InlineKeyboardBuilder()
    for league in LEAGUES:
        mark = "✓ " if league.id in selected else ""
        builder.button(text=f"{mark}{league.name}", callback_data=f"lg:{league.id}")
    builder.button(text="Готово", callback_data="lg:done")
    builder.adjust(2)
    return builder.as_markup()


def fixtures_keyboard(items: list[Fixture], prefix: str = "fx") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items[:12]:
        when = item.kickoff.strftime("%d.%m %H:%M")
        builder.button(text=f"{item.home} — {item.away} · {when}", callback_data=f"{prefix}:{item.id}")
    builder.adjust(1)
    return builder.as_markup()


def fixture_actions(fixture_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Подписаться", callback_data=f"sub:{fixture_id}"),
                InlineKeyboardButton(text="Анализ", callback_data=f"an:{fixture_id}"),
            ],
            [
                InlineKeyboardButton(text="Value", callback_data=f"val:{fixture_id}"),
                InlineKeyboardButton(text="График xG", callback_data=f"xg:{fixture_id}"),
            ],
        ]
    )


def value_toggle(enabled: bool) -> InlineKeyboardMarkup:
    label = "Выключить алерты" if enabled else "Включить алерты"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data="value:toggle")]]
    )
