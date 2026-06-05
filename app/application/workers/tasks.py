import asyncio
from uuid import UUID
from contextlib import asynccontextmanager

from celery import Celery

from app.application.services.ai_service import AIService
from app.application.dto.program import GenerateProgram
from app.application.dependencies import (
    get_embedding_service, 
    get_llm_api_key, 
    get_uow
)


celery_app = Celery('ai_coach_workers', broker="amqp://guest:123@rabbitmq:5672//")


async def _run_generation(dto: GenerateProgram, task_uuid: UUID):
    uow_factory = lambda: asynccontextmanager(get_uow)()
    
    embedder = get_embedding_service()
    api_key = get_llm_api_key()

    service = AIService(
        uow_factory=uow_factory, 
        embedder=embedder, 
        api_key=api_key
    )
    return await service.generate_workout(dto, task_uuid)



@celery_app.task(name="generate_workout_task")
def generate_workout_task(dto_dict: dict, task_id: str):
    dto = GenerateProgram(**dto_dict)
    task_uuid = UUID(task_id)
    uow = get_uow()
    embedder = get_embedding_service()
    api_key = get_llm_api_key()

    try:
        result = asyncio.run(_run_generation(dto, task_uuid))
        return result
    except Exception as e:
        print(f"Error inside AI Worker execution: {e}")
        raise e