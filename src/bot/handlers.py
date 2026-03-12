"""
Aiogram 3 message and callback handlers for the portfolio bot.

Handler registration is done via a ``Router`` — import ``router`` in
``main.py`` and include it in the root Dispatcher.
"""

import logging
from typing import Dict
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

from src.bot.ai_service import ai_service
from src.bot.content import ABOUT_TEXT, CONTACTS_TEXT, PROJECTS_TEXT, SKILLS_TEXT
from src.bot.keyboards import back_keyboard, main_menu_keyboard, ai_chat_keyboard
from src.config import settings
from src.db.models import User
from src.db.session import get_session

logger = logging.getLogger(__name__)
router = Router(name="portfolio")


class AIChatStates(StatesGroup):
    """FSM states for AI chat functionality."""
    chatting = State()


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _upsert_user(
    telegram_id: int,
    username: str | None,
    first_name: str,
) -> None:
    """Insert a new user row, or silently skip if ``telegram_id`` already exists.

    SQLite's ``INSERT OR IGNORE`` is used so that ``first_seen`` is never
    overwritten on subsequent /start calls.

    Args:
        telegram_id: Telegram numeric user ID.
        username:    Telegram @username, may be ``None``.
        first_name:  Telegram display first name.
    """
    stmt = (
        sqlite_upsert(User)
        .values(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
        )
        .on_conflict_do_nothing(index_elements=["telegram_id"])
    )
    async with get_session() as session:
        await session.execute(stmt)

    logger.debug("upsert user telegram_id=%s username=%s", telegram_id, username)


# ── /start ────────────────────────────────────────────────────────────────────


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle the /start command.

    1. Upserts the user record into the database.
    2. Replies with a welcome message and the main menu keyboard.

    Args:
        message: Incoming Telegram message object.
    """
    user = message.from_user
    if user is None:
        return  # Safety guard for channel posts, etc.

    await _upsert_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name or "",
    )

    greeting = (
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        f"Я — бот-портфолио <b>{settings.owner_name}</b>.\n"
        "Выбери раздел, который тебя интересует 👇"
    )

    await message.answer(
        text=greeting,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


# ── Inline callbacks ──────────────────────────────────────────────────────────


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery) -> None:
    """Return the user to the main menu.

    Args:
        callback: Incoming callback query.
    """
    user = callback.from_user
    text = (
        f"Привет, <b>{user.first_name}</b>! Выбери раздел 👇"
    )
    await callback.message.edit_text(  # type: ignore[union-attr]
        text=text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "about")
async def cb_about(callback: CallbackQuery) -> None:
    """Show 'About me' section.

    Args:
        callback: Incoming callback query.
    """
    await callback.message.edit_text(  # type: ignore[union-attr]
        text=ABOUT_TEXT,
        reply_markup=back_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "projects")
async def cb_projects(callback: CallbackQuery) -> None:
    """Show 'Projects' section.

    Args:
        callback: Incoming callback query.
    """
    await callback.message.edit_text(  # type: ignore[union-attr]
        text=PROJECTS_TEXT,
        reply_markup=back_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "skills")
async def cb_skills(callback: CallbackQuery) -> None:
    """Show 'Skills' section.

    Args:
        callback: Incoming callback query.
    """
    await callback.message.edit_text(  # type: ignore[union-attr]
        text=SKILLS_TEXT,
        reply_markup=back_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "contacts")
async def cb_contacts(callback: CallbackQuery) -> None:
    """Show 'Contacts' section.

    Args:
        callback: Incoming callback query.
    """
    await callback.message.edit_text(  # type: ignore[union-attr]
        text=CONTACTS_TEXT,
        reply_markup=back_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "ask_ai")
async def cb_ask_ai(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle 'Ask AI' button press.

    Args:
        callback: Incoming callback query.
        state: FSM context for managing conversation state.
    """
    await state.set_state(AIChatStates.chatting)
    
    await callback.message.edit_text(  # type: ignore[union-attr]
        text="🤖 Задайте мне любой вопрос о владельце портфолио, проектах или навыках!\n\n"
             "Например:\n"
             "• Какой опыт работы у разработчика?\n"
             "• Какие технологии он использует?\n"
             "• Расскажи подробнее о проектах\n"
             "• Как с ним связаться?",
        reply_markup=ai_chat_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AIChatStates.chatting)
async def handle_ai_question(message: Message, state: FSMContext) -> None:
    """Handle user's question to AI in continuous chat mode.

    Args:
        message: Incoming message with user's question.
        state: FSM context for managing conversation state.
    """
    if not message.text:
        await message.answer("Пожалуйста, отправьте текстовое сообщение с вопросом.")
        return
    
    # Show typing indicator
    await message.answer("🤔 Думаю...")
    
    try:
        # Get AI response
        response = await ai_service.ask_question(message.text)
        
        # Additional cleaning for any remaining forbidden symbols
        cleaned_response = _clean_ai_response(response)
        
        # Send response with HTML parsing
        await message.answer(
            text=cleaned_response,
            reply_markup=ai_chat_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
        
    except Exception as e:
        logger.error(f"Error in AI question handler: {e}")
        await message.answer(
            text="😔 Произошла ошибка при обработке вопроса. Попробуйте позже.",
            reply_markup=ai_chat_keyboard(),
        )
    
    # IMPORTANT: Don't clear state to maintain continuous chat


def _clean_ai_response(text: str) -> str:
    """Дополнительная очистка ответа ИИ перед отправкой."""
    # Удаляем оставшиеся markdown символы, если они есть
    text = text.replace('**', '').replace('*', '').replace('_', '').replace('#', '')
    # Заменяем множественные пробелы на одинарные
    import re
    text = re.sub(r' {2,}', ' ', text)
    # Обеспечиваем правильное форматирование буллетов
    text = re.sub(r'^\s*[-*]\s*', '• ', text, flags=re.MULTILINE)
    
    return text.strip()


@router.message(AIChatStates.chatting, F.text == "⬅️ Назад в меню")
async def handle_back_to_menu(message: Message, state: FSMContext) -> None:
    """Handle 'Back to menu' text in AI chat state.

    Args:
        message: Incoming message with back command.
        state: FSM context for managing conversation state.
    """
    await state.clear()
    
    user = message.from_user
    if user is None:
        return
    
    text = (
        f"Привет, <b>{user.first_name}</b>! Выбери раздел 👇"
    )
    
    await message.answer(
        text=text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )
