import asyncio
from uuid import UUID
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from celery import Celery

from app.infrastructure.postgres.database import build_worker_session_maker
from app.infrastructure.postgres.unit_of_work import PostgresUnitOfWork
from app.application.services.intent_service import IntentService
from app.application.services.exercise_service import ExerciseService
from app.application.ai.workout_context_builder import WorkoutContextBuilder
from app.application.ai.program_generator import WorkoutProgramGenerator
from app.application.ai.exercise_retriever import ExerciseRetriever
from app.application.dto.program import GenerateProgram
from app.application.dependencies import get_embedding_service, get_llm_api_key
from app.application.dto.training import CreateExerciseDTO
from app.core.extensions import UserNotFoundError


celery_app = Celery('ai_coach_workers', broker="amqp://guest:123@rabbitmq:5672//")


async def _run_generation(
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

    context_builder = WorkoutContextBuilder(
        uow_factory=uow_factory
    )

    exercise_retriever = ExerciseRetriever(
        uow_factory=uow_factory
    )

    generator = WorkoutProgramGenerator(
        api_key=api_key,
    )

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


async def _run_exercises(dto_list: list[dict]):
    session_maker, worker_engine = build_worker_session_maker()
    try:
        embedder = get_embedding_service()
        async with PostgresUnitOfWork(session_maker()) as uow:
            service = ExerciseService(
                uow=uow,
                embedder=embedder,
            )
            for dto_dict in dto_list:
                dto = CreateExerciseDTO(**dto_dict)
                await service.create_exercise(
                    name=dto.name,
                    muscle_group=dto.muscle_group,
                    equipment=dto.equipment,
                    movement_patterns=dto.movement_patterns,
                    description=dto.description,
                )
    finally:
        await worker_engine.dispose()


@celery_app.task(name="generate_workout_task")
def generate_workout_task(dto_dict: dict, task_id: str, user_id: str):
    dto = GenerateProgram(**dto_dict)
    task_uuid = UUID(task_id)
    user_uuid = UUID(user_id)
    try:
        result = asyncio.run(_run_generation(dto, task_uuid, user_uuid))
        return result
    except Exception as e:
        print(f"Error inside AI Worker execution: {e}")
        raise e


@celery_app.task(name="add_exercises_batch")
def add_exercises_batch(dto_list: list[dict]):
    asyncio.run(_run_exercises(dto_list))