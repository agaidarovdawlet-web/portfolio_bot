import logging
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from src.bot.content import ABOUT_TEXT, CONTACTS_TEXT, PROJECTS_TEXT, SKILLS_TEXT
from src.config import settings

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = f"""
Ты — краткий ассистент разработчика Даулета Агайдарова.
ИНФОРМАЦИЯ: {ABOUT_TEXT} {PROJECTS_TEXT} {SKILLS_TEXT} {CONTACTS_TEXT}

ПРАВИЛА:
1. Отвечай максимально КРАТКО (1-3 предложения).
2. Только СУТЬ. Без приветствий, без "конечно", без "рад помочь".
3. Формат: ТОЛЬКО HTML (<b>, <i>). Списки через "•".
4. Если информации нет — пиши: "Данные отсутствуют."
"""

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key.get_secret_value())
        
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
            generation_config={
                "temperature": 0.3, 
                "top_p": 0.8,
                "max_output_tokens": 150, 
            }
        )

    async def ask_question(self, question: str) -> str:
        try:
            
            prompt = f"{SYSTEM_PROMPT}\n\nВопрос: {question}\nОтвет (кратко):"
            response = await self.model.generate_content_async(prompt)
            
            if response.candidates and response.text:
                return self._clean_response_text(response.text.strip())
            return "Нет ответа."
            
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return "Ошибка ИИ."

    def _clean_response_text(self, text: str) -> str:
        text = re.sub(r'</?(p|div|span|section|article)>', '\n', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = text.replace('#', '').replace('_', '').replace('`', '')
        text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)
        return text.strip()

ai_service = AIService()
