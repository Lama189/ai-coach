import asyncio

from app.application.workers.celery_app import celery_app
from app.application.workers.pipelines.exercises import run_exercises


@celery_app.task(name="add_exercises_batch")
def add_exercises_batch(dto_list: list[dict]):
    asyncio.run(run_exercises(dto_list))
