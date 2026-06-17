from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile, File
from starlette import status

from app.application.dependencies import get_current_user, get_minio_storage
from app.application.dto.tasks import TaskAcceptedResponse
from app.application.workers.tasks.uploads import upload_pdf_task
from app.application.interfaces.object_storage import IObjectStorage


router = APIRouter(prefix="/api/v1/knowledge")


@router.post(
    path="/upload",
    response_model=TaskAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def upload_pdf(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    storage: IObjectStorage = Depends(get_minio_storage)
):
    file_bytes = await file.read()
    task_id = str(uuid4())
    object_name = f"{current_user.id}/{uuid4()}.pdf"

    await storage.upload("knowledge", object_name, file_bytes)

    return TaskAcceptedResponse(
        task_id=task_id,
        status="processing",
        message="Загрузка PDF начата"
    )