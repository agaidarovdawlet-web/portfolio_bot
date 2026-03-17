import logging
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from src.bot.content import ABOUT_TEXT, CONTACTS_TEXT, PROJECTS_TEXT, SKILLS_TEXT
from src.config import settings

logger = logging.getLogger(__name__)

# Системный промпт теперь содержит четкие правила по объему ответов
SYSTEM_PROMPT = f"""
Ты — профессиональный ИИ-ассистент Даулета Агайдарова. Твоя цель — представлять Даулета рекрутерам.

ДАННЫЕ:
1. О разработчике: {ABOUT_TEXT}
2. Проекты: {PROJECTS_TEXT}
3. Стек: {SKILLS_TEXT}
4. Контакты: {CONTACTS_TEXT}

ПРАВИЛА ОТВЕТА:
- На ПЕРВЫЙ вопрос или общие темы (стек, опыт) отвечай ПОДРОБНО с заголовками <b>.
- На УТОЧНЯЮЩИЕ вопросы в ходе диалога отвечай КРАТКО (до 3-4 предложений).
- Если тебя благодарят или прощаются — отвечай вежливо и лаконично.
- Форматирование: ТОЛЬКО HTML (<b>, <i>). Никакого Markdown (* или #).
- Вместо знаков "-" или "*" в списках используй "•".
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
                "temperature": 0.7,
                "top_p": 0.95,
                "max_output_tokens": 1000,
            }
        )

    async def ask_question(self, question: str, history: list = None) -> str:
        """
        Принимает вопрос и историю сообщений в формате Gemini:
        [{'role': 'user', 'parts': ['...']}, {'role': 'model', 'parts': ['...']}]
        """
        try:
            # Инициализируем чат. Первым сообщением ВСЕГДА идет системный промпт, 
            # чтобы модель знала контекст, даже если история пуста.
            chat = self.model.start_chat(history=history or [])
            
            # Если это начало диалога (история пуста), добавляем промпт к первому вопросу
            if not history:
                full_query = f"{SYSTEM_PROMPT}\n\nПользователь: {question}"
            else:
                full_query = question

            response = await chat.send_message_async(full_query)
            
            if response.candidates and response.text:
                return self._clean_response_text(response.text.strip())
            return "Извини, не удалось сформировать ответ."
            
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return "Произошла техническая ошибка. Попробуйте еще раз через минуту."

    def _clean_response_text(self, text: str) -> str:
        # Убираем Markdown жирный и курсив, заменяя на HTML
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
        # Убираем заголовки Markdown (#) и обратные кавычки
        text = text.replace('#', '').replace('`', '')
        # Заменяем маркеры списков на красивые буллиты
        text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)
        return text.strip()

ai_service = AIService()
