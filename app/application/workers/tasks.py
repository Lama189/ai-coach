import asyncio
import logging
from uuid import UUID

from celery import Celery
from app.application.workers.pipelines.exercises import run_exercises
from app.application.workers.pipelines.programs import run_generation
from app.application.workers.pipelines.upload_pdf import process_pdf_task
from app.application.dto.program import GenerateProgram


logger = logging.getLogger(__name__)


celery_app = Celery('ai_coach_workers', broker="amqp://guest:123@rabbitmq:5672//")


@celery_app.task(name="add_exercises_batch")
def add_exercises_batch(dto_list: list[dict]):
    asyncio.run(run_exercises(dto_list))


@celery_app.task(name="generate_workout_task")
def generate_workout_task(dto_dict: dict, task_id: str, user_id: str):
    dto = GenerateProgram(**dto_dict)
    task_uuid = UUID(task_id)
    user_uuid = UUID(user_id)
    try:
        result = asyncio.run(run_generation(dto, task_uuid, user_uuid))
        return result
    except Exception as e:
        logger.error("Error inside AI Worker execution: %s", e)
        raise e


@celery_app.task(name="upload_pdf_task")
def process_pdf_pipeline(
    task_id: str,
    user_id: str,
    bucket_name: str,
    object_name: str,
):
    return asyncio.run(
        process_pdf_task(task_id, user_id, bucket_name, object_name)
    )
