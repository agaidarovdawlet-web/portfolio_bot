import logging
from typing import Dict
from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from google.api_core import exceptions as google_exceptions

from src.bot.ai_service import ai_service
from src.bot.content import ABOUT_TEXT, CONTACTS_TEXT, PROJECTS_TEXT, SKILLS_TEXT
from src.bot.keyboards import back_keyboard, main_menu_keyboard, ai_chat_keyboard
from src.config import settings
from src.db.models import User
from src.db.session import get_session

logger = logging.getLogger(__name__)
router = Router(name="portfolio")

class AIChatStates(StatesGroup):
    chatting = State()

# ── Helpers ───────────────────────────────────────────────────────────────────

async def _upsert_user(telegram_id: int, username: str | None, first_name: str) -> None:
    stmt = (
        sqlite_upsert(User)
        .values(telegram_id=telegram_id, username=username, first_name=first_name)
        .on_conflict_do_nothing(index_elements=["telegram_id"])
    )
    async with get_session() as session:
        await session.execute(stmt)

async def safe_edit_text(callback: CallbackQuery, text: str, reply_markup=None, **kwargs):
    """Безопасное редактирование текста без лишних callback.answer()"""
    try:
        await callback.message.edit_text(
            text=text, 
            reply_markup=reply_markup, 
            parse_mode="HTML", 
            **kwargs
        )
    except TelegramBadRequest as e:
        if "message is not modified" in e.message:
            return
        logger.error(f"Safe edit error: {e.message}")

# ── Handlers ──────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    if not user: return
    
    await _upsert_user(user.id, user.username, user.first_name or "")
    
    greeting = (
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        f"Я — бот-портфолио <b>{settings.owner_name}</b>.\n"
        "Выбери раздел 👇"
    )
    await message.answer(text=greeting, reply_markup=main_menu_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery) -> None:
    await callback.answer() # Сначала отвечаем Telegram
    user = callback.from_user
    text = f"Привет, <b>{user.first_name}</b>! Выбери раздел 👇"
    await safe_edit_text(callback, text, main_menu_keyboard())

@router.callback_query(F.data == "about")
async def cb_about(callback: CallbackQuery) -> None:
    await callback.answer()
    await safe_edit_text(callback, ABOUT_TEXT, back_keyboard(), disable_web_page_preview=True)

@router.callback_query(F.data == "projects")
async def cb_projects(callback: CallbackQuery) -> None:
    await callback.answer()
    await safe_edit_text(callback, PROJECTS_TEXT, back_keyboard(), disable_web_page_preview=True)

@router.callback_query(F.data == "skills")
async def cb_skills(callback: CallbackQuery) -> None:
    await callback.answer()
    await safe_edit_text(callback, SKILLS_TEXT, back_keyboard())

@router.callback_query(F.data == "contacts")
async def cb_contacts(callback: CallbackQuery) -> None:
    await callback.answer()
    await safe_edit_text(callback, CONTACTS_TEXT, back_keyboard(), disable_web_page_preview=True)

# ── AI CHAT LOGIC ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "ask_ai")
async def cb_ask_ai(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer() # Критично вызвать до тяжелых операций
    await state.set_state(AIChatStates.chatting)
    await state.update_data(chat_history=[]) 
    
    text = (
        "🤖 <b>Я готов к общению!</b>\n\n"
        "Задайте любой вопрос о Даулете. Я запоминаю контекст нашей беседы."
    )
    await safe_edit_text(callback, text, ai_chat_keyboard())

@router.message(AIChatStates.chatting, F.text == "⬅️ Назад в меню")
async def handle_back_to_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = message.from_user
    text = f"Привет, <b>{user.first_name}</b>! Выбери раздел 👇"
    await message.answer(text=text, reply_markup=main_menu_keyboard(), parse_mode="HTML")

@router.message(AIChatStates.chatting)
async def handle_ai_question(message: Message, state: FSMContext) -> None:
    if not message.text or message.text == "⬅️ Назад в меню": return
    
    data = await state.get_data()
    history = data.get("chat_history", [])

    thinking = await message.answer("🤔 Думаю...")
    
    try:
        response = await ai_service.ask_question(message.text, history=history)
        
        # Обновляем историю
        history.append({"role": "user", "parts": [message.text]})
        history.append({"role": "model", "parts": [response]})
        await state.update_data(chat_history=history[-6:]) # Держим 3 полных диалога
        
        await thinking.delete()
        await message.answer(
            text=response,
            reply_markup=ai_chat_keyboard(),
            parse_mode="HTML",
            disable_web_page_preview=True
        )
    except google_exceptions.ResourceExhausted:
        await thinking.edit_text(
            "⚠️ <b>Лимит запросов исчерпан.</b>\n\n"
            "На бесплатном тарифе есть ограничения. Пожалуйста, попробуйте через пару минут."
        )
    except Exception as e:
        logger.error(f"AI Error: {e}")
        await thinking.edit_text("😔 Ошибка ИИ. Попробуйте позже или переформулируйте вопрос.")
