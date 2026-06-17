import asyncio
from uuid import UUID

from app.application.workers.celery_app import celery_app
from app.application.workers.pipelines.upload_pdf import upload_pdf


@celery_app.task(name="upload_pdf_task")
def upload_pdf_task(file_bytes: bytes, user_id: str, task_id: str):
    try:
        task_uuid = UUID(task_id)
        object_name = asyncio.run(upload_pdf(file_bytes, user_id))

        return {
            "status": "completed",
            "object_name": object_name,
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
        }