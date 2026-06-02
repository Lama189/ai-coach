from pydantic import BaseModel, Field
from uuid import UUID

class SearchExercisesInput(BaseModel):
    query: str
    muscle_group: str | None = None


class CreateExerciseInput(BaseModel):
    name: str = Field(..., description="Название упражнения")
    muscle_group: str = Field(..., description="Группа мышц: chest, back, legs, shoulders, biceps, triceps, core, full_body, cardio")
    description: str | None = Field(None, description="Описание упражнения")


class CreateExercisesBatchInput(BaseModel):
    exercises: list[CreateExerciseInput] = Field(..., description="Список упражнений для создания")


class WorkoutDayExerciseAI(BaseModel):
    exercise_id: UUID
    sets: int
    reps: int
    rest_seconds: int | None = None


class WorkoutDayAI(BaseModel):
    day_number: int
    title: str
    exercises: list[WorkoutDayExerciseAI]


class WorkoutProgramAI(BaseModel):
    name: str
    description: str | None = None
    workout_days: list[WorkoutDayAI]


class SearchExercisesBatchInput(BaseModel):
    queries: list[str] = Field(..., description="Список названий упражнений для поиска")