import asyncio
from uuid import UUID
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from celery import Celery
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.postgres.database import build_worker_session_maker
from app.infrastructure.postgres.unit_of_work import PostgresUnitOfWork
from app.application.services.intent_service import IntentService
from app.application.services.exercise_service import ExerciseService
from app.application.dto.program import GenerateProgram
from app.application.dependencies import get_embedding_service, get_llm_api_key
from app.application.dto.training import CreateExerciseDTO


celery_app = Celery('ai_coach_workers', broker="amqp://guest:123@rabbitmq:5672//")


async def _run_generation(dto: GenerateProgram, task_uuid: UUID):
    session_maker, worker_engine = build_worker_session_maker()

    @asynccontextmanager
    async def uow_factory():
        async with PostgresUnitOfWork(session_maker()) as uow:
            yield uow

    embedder = get_embedding_service()
    api_key = get_llm_api_key()

    service = IntentService(
        uow_factory=uow_factory,
        embedder=embedder,
        api_key=api_key,
    )

    try:
        return await service.create_intent(dto)
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
                    movement_pattern=dto.movement_pattern,
                    description=dto.description,
                )
    finally:
        await worker_engine.dispose()


@celery_app.task(name="generate_workout_task")
def generate_workout_task(dto_dict: dict, task_id: str):
    dto = GenerateProgram(**dto_dict)
    task_uuid = UUID(task_id)

    try:
        result = asyncio.run(_run_generation(dto, task_uuid))
        return result
    except Exception as e:
        print(f"Error inside AI Worker execution: {e}")
        raise e
    

@celery_app.task(name="add_exercises_batch")
def add_exercises_batch(dto_list: list[dict]):
    asyncio.run(_run_exercises(dto_list))

