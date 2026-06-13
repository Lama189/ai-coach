from pydantic import BaseModel, UUID4, Field, ConfigDict
from app.domain.enums import MuscleGroup


class CreateExerciseDTO(BaseModel):
    name: str = Field(max_length=100, min_length=3)
    muscle_group: MuscleGroup
    equipment: str = Field(max_length=50)
    movement_pattern: str = Field(max_length=50)
    description: str | None = None


class ExerciseResponseDTO(BaseModel):
    id: UUID4
    name: str
    muscle_group: MuscleGroup
    equipment: str
    movement_pattern: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ExerciseSetLogDTO(BaseModel):
    exercise_id: UUID4
    set_number: int = Field(gt=0)
    weight: float = Field(ge=0) 
    reps: int = Field(gt=0)
    rpe: int | None = Field(default=None, ge=1, le=10)


class SessionCreateDTO(BaseModel):
    program_id: UUID4 | None = None
    notes: str | None = None
    exercise_sets: list[ExerciseSetLogDTO]


class AddExercisesBatchResponse(BaseModel):
    status: str = Field(..., description="Текущий статус фоновой задачи (processing, completed, failed)")
    message: str = Field(default="Операция добавления батча упражнений запущена")