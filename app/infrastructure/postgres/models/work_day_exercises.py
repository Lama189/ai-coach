from uuid import UUID, uuid4
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    Integer,
    Enum as SqlEnum
)

from app.infrastructure.postgres.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.exercises import Exercise
    from app.infrastructure.postgres.models.workout_days import WorkoutDay

class WorkoutDayExercise(BaseModel):
    __tablename__ = "workout_day_exercises" 

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid4)

    workout_day_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("workout_days.id", ondelete="CASCADE"),
        nullable=False
    )
    exercise_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=False
    )

    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    rest_seconds: Mapped[int] = mapped_column(Integer, nullable=True)

    workout_day: Mapped["WorkoutDay"] = relationship("WorkoutDay", back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship("Exercise", back_populates="workout_days")