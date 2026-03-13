"""
AI service for Gemini API integration.
"""

import logging
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from src.bot.content import ABOUT_TEXT, CONTACTS_TEXT, PROJECTS_TEXT, SKILLS_TEXT
from src.config import settings

logger = logging.getLogger(__name__)

# Улучшенный системный промт
SYSTEM_PROMPT = f"""
Ты — умный ИИ-ассистент Даулета Агайдарова. Твоя задача — презентовать его как Python-разработчика.

ИНФОРМАЦИЯ О ВЛАДЕЛЬЦЕ:
{ABOUT_TEXT}
{PROJECTS_TEXT}
{SKILLS_TEXT}
{CONTACTS_TEXT}

ПРИОРИТЕТЫ В ОТВЕТАХ:
1. Обязательно упоминай благодарность от Яндекс Практикума, если спрашивают об успехах в ИИ или обучении.
2. При вопросах об опыте делай акцент на работе в Т-Банке, Энергосбыт Плюс и стажировке в ОРЕНБУРГ БАНКЕ.
3. Используй профессиональную лексику: "ведение отчетности для группы" вместо "староста".

ПРАВИЛА ОФОРМЛЕНИЯ (СТРОГО):
- Используй ТОЛЬКО HTML: <b>жирный</b>, <i>курсив</i>.
- НИКАКИХ символов #, *, _, ** или ---.
- Списки только через буллит "•".
- НЕ используй теги <p>, <div>, <span>.
"""

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key.get_secret_value())
        self.model_name = 'gemini-2.5-flash'
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        logger.info(f"AI service initialized with {self.model_name}")

    async def ask_question(self, question: str) -> str:
        try:
            full_prompt = f"{SYSTEM_PROMPT}\n\nВопрос пользователя: {question}"
            response = await self.model.generate_content_async(full_prompt)
            
            if response and response.text:
                return self._clean_response_text(response.text.strip())
            return "Извините, я не смог сформировать ответ. Попробуйте перефразировать вопрос."
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return "Произошла ошибка при обращении к ИИ. Попробуйте спросить позже."

    def _clean_response_text(self, text: str) -> str:
        """Очищает текст ответа от Markdown и неподдерживаемых HTML-тегов."""
    
        text = re.sub(r'</?(p|div|span|section|article)>', '\n', text)
        
        
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        
        
        text = text.replace('#', '').replace('_', '').replace('`', '')
        
        
        text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()


ai_service = AIService()
