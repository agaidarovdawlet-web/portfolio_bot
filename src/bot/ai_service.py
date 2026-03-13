import logging
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from src.bot.content import ABOUT_TEXT, CONTACTS_TEXT, PROJECTS_TEXT, SKILLS_TEXT
from src.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""
Ты — умный ИИ-ассистент Даулета Агайдарова. Презентуй его как Python-разработчика.
ИНФОРМАЦИЯ: {ABOUT_TEXT} {PROJECTS_TEXT} {SKILLS_TEXT} {CONTACTS_TEXT}
ПРАВИЛА: Используй ТОЛЬКО HTML (<b>, <i>). Списки через "•".
"""

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key.get_secret_value())
        
        safe_config = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            safety_settings=safe_config
        )

    async def ask_question(self, question: str) -> str:
        try:
            full_prompt = f"{SYSTEM_PROMPT}\n\nВопрос: {question}"
            response = await self.model.generate_content_async(full_prompt)
            
            if response.candidates and response.text:
                return self._clean_response_text(response.text.strip())
            return "Извини, я не могу ответить на этот вопрос."
            
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return "Техническая заминка с ИИ."

    def _clean_response_text(self, text: str) -> str:
        text = re.sub(r'</?(p|div|span|section|article)>', '\n', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = text.replace('#', '').replace('_', '').replace('`', '')
        text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)
        return text.strip()

ai_service = AIService()
