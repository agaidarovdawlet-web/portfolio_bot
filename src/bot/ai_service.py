import logging
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from src.bot.content import ABOUT_TEXT, CONTACTS_TEXT, PROJECTS_TEXT, SKILLS_TEXT
from src.config import settings

logger = logging.getLogger(__name__)

# Обновленный промпт для глубоких ответов
SYSTEM_PROMPT = f"""
Ты — профессиональный ИИ-ассистент Даулета Агайдарова. Твоя цель — максимально подробно и технически грамотно представлять Даулета рекрутерам и заказчикам.

ДАННЫЕ ДЛЯ РАБОТЫ:
1. О разработчике: {ABOUT_TEXT}
2. Технические кейсы: {PROJECTS_TEXT}
3. Стек технологий: {SKILLS_TEXT}
4. Контакты: {CONTACTS_TEXT}

ИНСТРУКЦИИ ПО ОТВЕТУ:
- Отвечай РАЗВЕРНУТО и информативно. Если спрашивают про стек — перечисляй его по категориям.
- Если спрашивают про опыт — связывай его с конкретными достижениями и компаниями (ЭнергосбыТ Плюс, Т-Банк).
- При описании проектов делай акцент на технических сложностях (Race Condition, FSM, Asyncio).
- Соблюдай структуру: используй <b> для заголовков и важных терминов, и "•" для списков.
- Форматирование: ТОЛЬКО HTML (<b>, <i>). Не используй Markdown (* или #).
- Если вопрос не касается Даулета или IT, вежливо вернись к теме его профессиональных навыков.
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
                "temperature": 0.7,      # Умеренная креативность для живого общения
                "top_p": 0.95,
                "max_output_tokens": 1500, # Увеличили лимит для длинных ответов
            }
        )

    async def ask_question(self, question: str) -> str:
        try:
            # Убрали пометку "(кратко)" из запроса
            prompt = f"{SYSTEM_PROMPT}\n\nВопрос пользователя: {question}\nТвой развернутый ответ ассистента:"
            response = await self.model.generate_content_async(prompt)
            
            if response.candidates and response.text:
                return self._clean_response_text(response.text.strip())
            return "Извини, не удалось сформировать подробный ответ."
            
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return "Произошла техническая ошибка при обращении к ИИ."

    def _clean_response_text(self, text: str) -> str:
        # Очистка от Markdown и лишних тегов
        text = re.sub(r'</?(p|div|span|section|article)>', '\n', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        text = text.replace('#', '').replace('_', '').replace('`', '')
        text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)
        return text.strip()

ai_service = AIService()
