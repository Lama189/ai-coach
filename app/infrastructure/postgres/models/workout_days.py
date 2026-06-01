from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    text,
)

from app.infrastructure.postgres.models.base_model import BaseModel
if TYPE_CHECKING:
    from app.infrastructure.postgres.models.workout_programs import WorkoutProgram
    from app.infrastructure.postgres.models.work_day_exercises import WorkoutDayExercise


class WorkoutDay(BaseModel):
    __tablename__ = "workout_days"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid4)
    
    program_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workout_programs.id", ondelete="CASCADE"),
        nullable=False
    )

    day_number: Mapped[int] = mapped_column(Integer, nullable=False) 
    title: Mapped[str] = mapped_column(String(100), nullable=False)

    workout_program: Mapped["WorkoutProgram"] = relationship("WorkoutProgram", back_populates="workout_days")
    exercises: Mapped[list["WorkoutDayExercise"]] = relationship("WorkoutDayExercise", back_populates="workout_day")