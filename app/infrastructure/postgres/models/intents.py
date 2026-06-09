from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import Text, DateTime, ForeignKey, String, ARRAY, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from pgvector.sqlalchemy import Vector

from app.infrastructure.postgres.models.base_model import BaseModel


class UserIntentModel(BaseModel):
    __tablename__ = "user_intents"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal: Mapped[str] = mapped_column(String, nullable=False)
    constraints: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    focus_areas: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    location: Mapped[str] = mapped_column(String(20), nullable=False)
    context: Mapped[str] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=True)
    program_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("workout_programs.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())