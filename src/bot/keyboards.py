"""
Inline keyboard factories for the portfolio bot.

Keeping keyboards in a dedicated module makes it trivial to add or
reorder buttons without touching handler logic.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Return the main menu keyboard shown after /start."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👤 О себе",    callback_data="about"),
        InlineKeyboardButton(text="🚀 Проекты",   callback_data="projects"),
    )
    builder.row(
        InlineKeyboardButton(text="🛠 Навыки",    callback_data="skills"),
        InlineKeyboardButton(text="📬 Контакты",  callback_data="contacts"),
    )
    builder.row(
        InlineKeyboardButton(text="🤖 Спросить ИИ", callback_data="ask_ai"),
    )
    return builder.as_markup()


def back_keyboard() -> InlineKeyboardMarkup:
    """Return a single «← Назад» button that returns to the main menu."""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="← Главное меню", callback_data="main_menu"))
    return builder.as_markup()


def ai_chat_keyboard() -> InlineKeyboardMarkup:
    """Return a keyboard for AI chat mode with back to menu button."""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="main_menu"))
    return builder.as_markup()
