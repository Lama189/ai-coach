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
    exercise_id: UUID = Field(..., description="UUID упражнения из базы данных")
    sets: int = Field(..., description="Количество подходов")
    reps: int = Field(..., description="Количество повторений")
    rest_seconds: int = Field(..., description="Время отдыха в секундах")

class WorkoutDayAI(BaseModel):
    day_number: int = Field(..., description="Порядковый номер дня, начиная с 1")
    title: str = Field(..., description="Название дня, например 'Legs and Back'")
    exercises: list[WorkoutDayExerciseAI]

class WorkoutProgramAI(BaseModel):
    name: str = Field(..., description="Название программы")
    description: str = Field(..., description="Описание программы")
    workout_days: list[WorkoutDayAI]


class SearchExercisesBatchInput(BaseModel):
    queries: list[str] = Field(..., description="Список названий упражнений для поиска")