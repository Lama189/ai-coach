from typing import TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    ForeignKey,
    DateTime,
    Boolean,
    String,
    Text,
    func
)

from app.infrastructure.postgres.models.base_model import BaseModel
if TYPE_CHECKING:
    from app.infrastructure.postgres.models.users import User
    from app.infrastructure.postgres.models.workout_days import WorkoutDay
    from app.infrastructure.postgres.models.session import Session


class WorkoutProgram(BaseModel):
    __tablename__ = "workout_programs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid4)
    
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    task_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True, unique=True, index=True)

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="workout_programs")
    workout_days: Mapped[list["WorkoutDay"]] = relationship("WorkoutDay", back_populates="workout_program")
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="workout_program")