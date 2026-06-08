from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.domain.enums import InsightTag

class UserInsight(BaseModel):
    user_id: UUID
    id: UUID = Field(default_factory=uuid4)
    content: str = Field(..., description="Текст кванта памяти о пользователе")
    tag: InsightTag