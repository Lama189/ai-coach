from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from pgvector.sqlalchemy import Vector

from app.infrastructure.postgres.models.base_model import BaseModel

class UserInsight(BaseModel):
    __tablename__ = "user_insights"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
   
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)