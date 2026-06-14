import time
import logging
from uuid import UUID
from typing import Callable, AsyncContextManager

from app.application.interfaces.unit_of_work import IUnitOfWork
from app.application.dto.for_ai import PlanningContext
from app.domain.identity.intents import UserIntent
from app.domain.identity.insight import UserInsight, InsightBundle
from app.domain.identity.user import User
from app.domain.enums import InsightTag


logger = logging.getLogger(__name__)


class WorkoutContextBuilder:
    def __init__(
        self,
        uow_factory: Callable[[], AsyncContextManager[IUnitOfWork]],
    ) -> None:
        self._uow_factory = uow_factory


    async def _load_relevant_insights(
        self,
        user_id: UUID,
        query_embedding: list[float] | None = None,
    ) -> tuple[list[UserInsight], list[UserInsight], list[UserInsight], list[UserInsight]]:

        start = time.time()

        async with self._uow_factory() as uow:

            logger.info(
                "insights_retrieval_started",
                extra={"user_id": str(user_id)}
            )

            hard = await uow.insights.search_by(
                user_id=user_id,
                tags=[InsightTag.injury, InsightTag.fatigue],
                limit=5
            )

            logger.info(
                "insights_hard_loaded",
                extra={
                    "user_id": str(user_id),
                    "count": len(hard)
                }
            )

            context = await uow.insights.search_by(
                user_id=user_id,
                tags=[InsightTag.schedule, InsightTag.mental],
                limit=3
            )

            logger.info(
                "insights_context_loaded",
                extra={
                    "user_id": str(user_id),
                    "count": len(context)
                }
            )

            prefs = await uow.insights.search_by(
                user_id=user_id,
                tags=[InsightTag.preference, InsightTag.technique],
                limit=5
            )

            logger.info(
                "insights_prefs_loaded",
                extra={
                    "user_id": str(user_id),
                    "count": len(prefs)
                }
            )

            semantic = []
            if query_embedding:
                semantic = await uow.insights.search_by(
                    user_id=user_id,
                    query_embedding=query_embedding,
                    limit=5
                )

                logger.info(
                    "insights_semantic_loaded",
                    extra={
                        "user_id": str(user_id),
                        "count": len(semantic)
                    }
                )

            duration_ms = int((time.time() - start) * 1000)
            total_count = len(hard) + len(context) + len(prefs) + len(semantic)

            logger.info(
                "insights_retrieval_finished",
                extra={
                    "user_id": str(user_id),
                    "total": total_count,
                    "duration_ms": duration_ms
                }
            )

            return hard, context, prefs, semantic


    async def build(
        self,
        user: User,
        intent: UserIntent,
        embedding: list[float] | None = None
    ) -> PlanningContext:

        start = time.time()

        logger.info(
            "context_build_started",
            extra={"user_id": str(user.id)}
        )

        hard, context_insights, prefs, semantic = await self._load_relevant_insights(
            user_id=user.id,
            query_embedding=embedding
        )

        profile = user.profile
        if profile is None:
            logger.error(
                "profile_missing",
                extra={"user_id": str(user.id)}
            )
            raise ValueError("Профиль пользователя пустой")

        if profile.gender is None:
            raise ValueError("User profile has no gender")

        if profile.goal is None:
            raise ValueError("User profile has no goal")

        if profile.experience_level is None:
            raise ValueError("User profile has no experience level")

        logger.info(
            "profile_validated",
            extra={
                "user_id": str(user.id),
                "goal": profile.goal.value,
                "experience": profile.experience_level.value,
            }
        )

        seen_ids = set()
        
        unique_hard = []
        for i in hard:
            if i.id not in seen_ids:
                seen_ids.add(i.id)
                unique_hard.append(i)

        unique_context = []
        for i in context_insights:
            if i.id not in seen_ids:
                seen_ids.add(i.id)
                unique_context.append(i)

        unique_prefs = []
        for i in prefs:
            if i.id not in seen_ids:
                seen_ids.add(i.id)
                unique_prefs.append(i)

        unique_semantic = []
        for i in semantic:
            if i.id not in seen_ids:
                seen_ids.add(i.id)
                unique_semantic.append(i)

        bundle = InsightBundle(
            hard=unique_hard,
            context=unique_context,
            preferences=unique_prefs,
            semantic=unique_semantic
        )

        has_insights = len(seen_ids) > 0

        context_dto = PlanningContext(
            age=profile.age,
            gender=profile.gender.value,
            goal=profile.goal.value,
            experience_level=profile.experience_level.value,

            intent_goal=intent.goal,
            constraints=[c.value for c in intent.constraints],
            focus_areas=[f.value for f in intent.focus_areas],
            location=intent.location.value,
            context=intent.context,

            insights=bundle,
            has_insights=has_insights,
        )

        logger.info(
            "context_build_finished",
            extra={
                "user_id": str(user.id),
                "has_insights": has_insights,
                "insights_count": len(seen_ids),
                "duration_ms": int((time.time() - start) * 1000)
            }
        )

        return context_dto