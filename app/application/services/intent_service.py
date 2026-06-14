from typing import Callable, AsyncContextManager
from uuid import uuid4

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.application.dto.program import GenerateProgram

from app.domain.identity.user import User
from app.domain.identity.insight import UserInsight
from app.domain.identity.intents import UserIntent
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.application.dto.intents import IntentSchema



class IntentService:
    def __init__(
        self,
        uow_factory: Callable[[], AsyncContextManager[IUnitOfWork]],
        embedder: SentenceTransformerEmbeddingService,
        api_key: str
    ):
        self._uow_factory = uow_factory
        self._embedder = embedder
        self._llm = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model="gemini-3.1-flash-lite",
            temperature=0.1,
        )


    def _build_prompt(
        self,
        user: User,
        insights: list[UserInsight],
        dto: GenerateProgram
    ) -> str:
        profile = user.profile
        if profile is None:
                raise ValueError("Профиль пользователя отсутствует")

        insights_text = "\n".join(
            f"[{i.tag.value}] {i.content}"
            for i in insights
        )

        importance_map = {
            "low":    "Прими во внимание, но не обязательно строго следуй",
            "medium": "Старайся учитывать",
            "high":   "Это приоритет, обязательно учти",
        }
        importance = importance_map.get(dto.importance, importance_map["medium"])
        
        if profile.is_complete:
            if profile.gender is None:
                raise ValueError("User profile has no gender")

            if profile.goal is None:
                raise ValueError("User profile has no goal")

            if profile.experience_level is None:
                raise ValueError("User profile has no experience level")
            
            return f"""
                    Профиль пользователя:
                    - Пол: {profile.gender.value}
                    - Возраст: {profile.age}
                    - Цель: {profile.goal.value}
                    - Уровень: {profile.experience_level.value}

                    Заметки о пользователе:
                    {insights_text}

                    Запрос пользователя ({importance}):
                    {dto.content}

                    Извлеки намерение пользователя:
                    - goal: скорректированная цель с учётом запроса и профиля (свободный текст)
                    - constraints: физические ограничения из заметок (например no_knee_load, no_overhead)
                    - focus_areas: группы мышц которые нужно приоритизировать
                    - location: где тренируется (gym / home / outdoor)
                    - context: всё остальное важное что нужно учесть при составлении программы
                    """
        else:
             raise ValueError("Профиль не заполнен")


    def _build_intent_text(self, intent: IntentSchema) -> str:
        parts = [
            intent.goal,
            intent.location.value,
            " ".join(intent.constraints),
            " ".join(f.value for f in intent.focus_areas),
            intent.context,
        ]

        return " ".join(p for p in parts if p)
    

    async def create_intent(
        self,
        dto: GenerateProgram,
        user: User,
        content_embedding: list[float],
    ) -> UserIntent:
        async with self._uow_factory() as uow:
            insights = await uow.insights.search_by(
                user_id=user.id,
                tags=["injury", "schedule", "preference"],
            )
            relevant_insights = await uow.insights.search_by(
                user_id=user.id,
                query_embedding=content_embedding,
            )

        all_insights = {
            i.id: i
            for i in insights + relevant_insights
        }.values()

        prompt = self._build_prompt(user, all_insights, dto)

        structured_llm = self._llm.with_structured_output(IntentSchema)
        raw_intent = await structured_llm.ainvoke(
            [
                SystemMessage(
                    content=(
                        "Ты анализируешь запрос пользователя и извлекаешь его намерение. "
                        "Отвечай строго по схеме. Не придумывай данные которых нет."
                    )
                ),
                HumanMessage(content=prompt),
            ]
        )
        intent = IntentSchema.model_validate(raw_intent)

        intent_embedding = await self._embedder.get_embedding(
            self._build_intent_text(intent)
        )

        user_intent = UserIntent(
            id=uuid4(),
            user_id=user.id,
            goal=intent.goal,
            constraints=intent.constraints,
            focus_areas=intent.focus_areas,
            location=intent.location,
            context=intent.context,
            program_id=None,
        )

        async with self._uow_factory() as uow:
            await uow.intents.save(user_intent, intent_embedding)
            await uow.commit()

        return user_intent