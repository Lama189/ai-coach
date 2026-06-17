from app.infrastructure.postgres.database import build_worker_session_maker
from app.infrastructure.postgres.unit_of_work import PostgresUnitOfWork
from app.application.services.exercise_service import ExerciseService
from app.application.dependencies import get_embedding_service
from app.application.dto.training import CreateExerciseDTO


async def run_exercises(dto_list: list[dict]):
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
