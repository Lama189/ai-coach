import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from google.genai.errors import ServerError, APIError
from app.infrastructure.logging.decorators import log_duration

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._system_instruction = (
            "Ты — профессиональный ИИ-тренер, эксперт по anatomy фитнеса и калистенике.\n"
            "Ответь на вопрос пользователя, опираясь на предоставленные факты из базы знаний.\n"
            "Если предоставленный контекст не содержит ответа или информации недостаточно,\n"
            "используй свои общие экспертные знания, но обязательно сделай пометку,\n"
            "что этого механизма не было в загруженных методических материалах.\n"
            "Строго запрещай упражнения, если пользователь жалуется на острую боль в связках или суставах."
        )

        self._main_llm = ChatGoogleGenerativeAI(
            google_api_key=self._api_key,
            model="gemini-3.5-flash",  
            temperature=0.3,
            model_kwargs={"system_instruction": self._system_instruction},
            max_retries=5,         
            timeout=45.0,
        )

    @log_duration
    async def generate(self, user_message: str, context_text: str) -> str:
        prompt = self._build_prompt(user_message, context_text)
        
        try:
            response = await self._main_llm.ainvoke(prompt)
            return str(response.content)
            
        except (ServerError, APIError, Exception) as e:
            logger.warning(
                f"Модель gemini-3.5-flash выдала ошибку: {e}. Переключаюсь на фолбэк."
            )
            
            fallback_llm = ChatGoogleGenerativeAI(
                google_api_key=self._api_key,
                model="gemini-2.5-flash",  
                temperature=0.3,
                model_kwargs={"system_instruction": self._system_instruction},
                max_retries=3
            )
        
            response = await fallback_llm.ainvoke(prompt)
            return str(response.content)
    
    def _build_prompt(self, user_message: str, context: str) -> str:
        return f"""
                ДОСТУПНАЯ БАЗА ЗНАНИЙ ИЗ МЕТОДИЧЕСКИХ КНИГ:
                {context}
                
                ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
                {user_message}
                """