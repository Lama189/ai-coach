from uuid import UUID
from pydantic import BaseModel, Field


class TaskAcceptedResponse(BaseModel):
    task_id: UUID = Field(..., description="Уникальный идентификатор задачи")
    status: str = Field(..., description="Текущий статус фоновой задачи (processing, completed, failed)")
    message: str = Field(..., description="Сообщение для клиента")
