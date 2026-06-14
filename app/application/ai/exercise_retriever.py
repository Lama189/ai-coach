import logging
from typing import Callable, AsyncContextManager

from app.application.interfaces.unit_of_work import IUnitOfWork
from app.application.dto.for_ai import PlanningContext, ExerciseBundle, CandidateExercise
from app.application.policies.exercise_constraints import PATTERN_EXCLUSIONS, EQUIPMENT_EXCLUSIONS
from app.domain.enums import Constraint

logger = logging.getLogger(__name__)


class ExerciseRetriever:
    def __init__(
        self,
        uow_factory: Callable[[], AsyncContextManager[IUnitOfWork]],
    ) -> None:
        self._uow_factory = uow_factory

    async def retrieve(
        self,
        context: PlanningContext,
        embedding: list[float] | None = None,
    ) -> ExerciseBundle:

        muscle_groups = context.focus_areas

        excluded_patterns, excluded_equipment = self._resolve_exclusions(
            context.constraints
        )

        logger.info(
            "exercise_retrieval_started",
            extra={
                "muscle_groups": muscle_groups,
                "excluded_patterns": excluded_patterns,
                "excluded_equipment": excluded_equipment,
                "has_embedding": embedding is not None,
            },
        )

        async with self._uow_factory() as uow:
            exercises = await uow.exercises.search_relevant(
                muscle_groups=muscle_groups,
                excluded_patterns=excluded_patterns,
                excluded_equipment=excluded_equipment,
                embedding=embedding,
                limit=80,
            )

        logger.info(
            "exercise_retrieval_finished",
            extra={"total": len(exercises)},
        )

        return ExerciseBundle(
            exercises=[
                CandidateExercise(
                    id=e.id,
                    name=e.name,
                    muscle_group=e.muscle_group,
                    equipment=e.equipment,
                    movement_patterns=e.movement_patterns,
                    description=e.description,
                )
                for e in exercises
            ]
        )

    def _resolve_exclusions(
        self,
        constraints: list[str],
    ) -> tuple[list[str], list[str]]:

        excluded_patterns: set = set()
        excluded_equipment: set = set()

        for raw in constraints:
            try:
                constraint = Constraint(raw)
            except ValueError:
                logger.warning(
                    "unknown_constraint_skipped",
                    extra={"constraint": raw},
                )
                continue

            excluded_patterns |= {
                p.value for p in PATTERN_EXCLUSIONS.get(constraint, set())
            }
            excluded_equipment |= EQUIPMENT_EXCLUSIONS.get(constraint, set())

        return list(excluded_patterns), list(excluded_equipment)