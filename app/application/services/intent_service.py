from typing import Callable, AsyncContextManager
from uuid import UUID

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.application.dto.program import GenerateProgram

from app.core.extensions import UserNotFoundError
from app.domain.identity.user import User
from app.domain.identity.insight import UserInsight
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService
from app.application.dto.intents import IntentSchema
from app.domain.identity.intents import UserIntent



class IntentService:
    def __init__(
        self,
        uow_factory: Callable[[], AsyncContextManager[IUnitOfWork]],
        embedder: SentenceTransformerEmbeddingService,
        api_key: str
    ):
        self._uow_factory = uow_factory
        self._embedder = embedder
        self._llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0.3,
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
            assert profile.gender is not None
            assert profile.goal is not None
            assert profile.experience_level is not None

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
    

    async def create_intent(self, dto: GenerateProgram) -> UserIntent:
        content_embedding = await self._embedder.get_embedding(f"{dto.content}")

        async with self._uow_factory() as uow:
            user = await uow.users.get_by(id=dto.user_id)
            if user is None:
                raise UserNotFoundError()
            
            insights = await uow.insights.search_by(
                user_id=dto.user_id,
                tags=["injury", "schedule", "preference"],
            )

            relevant_insights = await uow.insights.search_by(
                user_id=dto.user_id,
                query_embedding=content_embedding
            )

        all_insights = {i.id: i for i in insights + relevant_insights}.values()

        prompt = self._build_prompt(user, all_insights, dto)
        structured_llm = self._llm.with_structured_output(IntentSchema)

        intent = await structured_llm.ainvoke([
            SystemMessage(content=(
                "Ты анализируешь запрос пользователя и извлекаешь его намерение. "
                "Отвечай строго по схеме. Не придумывай данные которых нет."
            )),
            HumanMessage(content=prompt),
        ])

        intent_embedding = await self._embedder.get_embedding(self._build_intent_text(intent))

        async with self._uow_factory() as uow:
            await uow.intents.save(intent, intent_embedding)
            await uow.commit()

        if isinstance(intent, dict):
            return UserIntent.model_validate(intent)

        if isinstance(intent, UserIntent):
            return intent

        raise TypeError(f"Unexpected type: {type(intent)}")


