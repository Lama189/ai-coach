from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    String,
    Text,
    Enum as SqlEnum
)

from app.infrastructure.postgres.models.base_model import BaseModel
from app.domain.enums import MuscleGroup

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.work_day_exercises import WorkoutDayExercise    
    

class Exercise(BaseModel):
    __tablename__ = "exercises" 

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    muscle_group: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    workout_days: Mapped[list["WorkoutDayExercise"]] = relationship("WorkoutDayExercise", back_populates="exercise")