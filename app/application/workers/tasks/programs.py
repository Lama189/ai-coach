import asyncio
from uuid import UUID

from app.application.workers.celery_app import celery_app
from app.application.workers.pipelines.programs import run_generation
from app.application.dto.program import GenerateProgram


@celery_app.task(name="generate_workout_task")
def generate_workout_task(dto_dict: dict, task_id: str, user_id: str):
    dto = GenerateProgram(**dto_dict)
    task_uuid = UUID(task_id)
    user_uuid = UUID(user_id)
    try:
        result = asyncio.run(run_generation(dto, task_uuid, user_uuid))
        return result
    except Exception as e:
        print(f"Error inside AI Worker execution: {e}")
        raise e
