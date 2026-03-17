import logging
import re
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from src.bot.content import ABOUT_TEXT, CONTACTS_TEXT, PROJECTS_TEXT, SKILLS_TEXT
from src.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""
Ты — технический ассистент Даулета Агайдарова. Твоя задача — быстро и четко выдавать данные из базы знаний.

БАЗА ЗНАНИЙ:
1. О Даулете: {ABOUT_TEXT}
2. Проекты: {PROJECTS_TEXT}
3. Стек: {SKILLS_TEXT}
4. Контакты: {CONTACTS_TEXT}

ПРАВИЛА ОТВЕТА (КРИТИЧНО):
1. НИКАКОЙ ВОДЫ. Не пиши фразы вроде "Отличный запрос!", "Рад представить вам..." или "Чтобы дать полную картину...". 
2. СРАЗУ К СУТИ. Если спросили про стек — начни ответ сразу с заголовка <b>🛠 Технологический стек</b>.
3. СТРУКТУРА. Используй только HTML (<b>, <i>). Списки делай через "•".
4. ОБЪЕМ. На вопрос "подробно" выдавай ВСЕ пункты из соответствующего раздела базы знаний, не сокращая их.
5. КОНТЕКСТ. Помни предыдущие вопросы, не представляйся заново в каждом сообщении.
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
