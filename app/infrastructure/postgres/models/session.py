from typing import TYPE_CHECKING
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    ForeignKey,
    DateTime,
    func,
    Text,
    String
)

from app.infrastructure.postgres.models.base_model import BaseModel
from app.domain.enums import SessionStatus

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.users import User
    from app.infrastructure.postgres.models.workout_programs import WorkoutProgram
    from app.infrastructure.postgres.models.exerc_set import ExerciseSet


class Session(BaseModel):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid4)

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    program_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workout_programs.id", ondelete="SET NULL"), 
        nullable=True
    )

   
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    workout_program: Mapped["WorkoutProgram"] = relationship("WorkoutProgram", back_populates="sessions")

    status: Mapped[str] = mapped_column(
        String(20),
        default=SessionStatus.active,
        nullable=False,
    )
    started_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,  
    )

    notes: Mapped[str] = mapped_column(Text, nullable=True)

    exercise_sets: Mapped[list["ExerciseSet"]] = relationship("ExerciseSet", back_populates="session")
