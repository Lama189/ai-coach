from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class UserInsight(BaseModel):
    user_id: UUID
    id: UUID = Field(default_factory=uuid4)
    content: str = Field(..., description="Текст кванта памяти о пользователе")
    embedding: list[float] = Field(..., description="Векторный эмбеддинг")