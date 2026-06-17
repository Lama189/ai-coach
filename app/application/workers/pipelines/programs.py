from uuid import UUID
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from app.infrastructure.postgres.database import build_worker_session_maker
from app.infrastructure.postgres.unit_of_work import PostgresUnitOfWork
from app.application.services.intent_service import IntentService
from app.application.ai.workout_context_builder import WorkoutContextBuilder
from app.application.ai.program_generator import WorkoutProgramGenerator
from app.application.ai.exercise_retriever import ExerciseRetriever
from app.application.dto.program import GenerateProgram
from app.application.dependencies import get_embedding_service, get_llm_api_key
from app.core.extensions import UserNotFoundError


async def run_generation(
    dto: GenerateProgram,
    task_uuid: UUID,
    user_id: UUID,
):
    session_maker, worker_engine = build_worker_session_maker()

    @asynccontextmanager
    async def uow_factory() -> AsyncGenerator[PostgresUnitOfWork, None]:
        async with PostgresUnitOfWork(session_maker()) as uow:
            yield uow

    embedder = get_embedding_service()
    api_key = get_llm_api_key()

    intent_service = IntentService(
        uow_factory=uow_factory,
        embedder=embedder,
        api_key=api_key,
    )

    context_builder = WorkoutContextBuilder(uow_factory=uow_factory)
    exercise_retriever = ExerciseRetriever(uow_factory=uow_factory)
    generator = WorkoutProgramGenerator(api_key=api_key,)

    try:
        content_embedding = await embedder.get_embedding(
            dto.content or ""
        )

        async with uow_factory() as uow:
            user = await uow.users.get_by(
                id=user_id,
                with_relations=True,
            )

        if user is None:
            raise UserNotFoundError()

        intent = await intent_service.create_intent(
            dto,
            user,
            content_embedding,
        )

        context = await context_builder.build(
            user,
            intent,
            content_embedding,
        )

        intent_embedding = await embedder.get_embedding(
            " ".join(
                [
                    intent.goal,
                    intent.location.value,
                    " ".join(
                        c.value
                        for c in intent.constraints
                    ),
                    " ".join(
                        f.value
                        for f in intent.focus_areas
                    ),
                    intent.context,
                ]
            )
        )

        exercise_bundle = await exercise_retriever.retrieve(
            context=context,
            embedding=intent_embedding,
        )

        exercise_names = {e.id: e.name for e in exercise_bundle.exercises}

        program_ai = await generator.generate(
            user_id=user_id,
            context=context,
            exercises=exercise_bundle,
        )

        valid_exercise_ids = {e.id for e in exercise_bundle.exercises}
        for day in program_ai.workout_days:
            for ex in day.exercises:
                if ex.exercise_id not in valid_exercise_ids:
                    raise ValueError(
                        f"LLM вернул несуществующий exercise_id: {ex.exercise_id}"
                    )

        domain_program = generator.map_to_domain(
            user_id=user_id,
            response=program_ai,
        )

        async with uow_factory() as uow:
            await uow.programs.deactivate_all_for_user(user_id)
            await uow.programs.save(domain_program,task_uuid,)

            for day in domain_program.workout_days:
                await uow.workout_days.save(day, domain_program.id,)

                for exercise in day.exercises:
                    await uow.workout_days_exercise.save(exercise, day.id,)

            await uow.commit()

        return generator.map_to_response(domain_program, exercise_names=exercise_names)

    finally:
        await worker_engine.dispose()
