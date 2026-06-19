from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

from app.domain.enums import MovementPattern
from app.domain.identity.insight import UserInsight, InsightBundle

class SearchExercisesInput(BaseModel):
    query: str
    muscle_group: str | None = None


class CreateExerciseInput(BaseModel):
    name: str = Field(..., description="Название упражнения")
    muscle_group: str = Field(..., description="Группа мышц: chest, back, legs, shoulders, biceps, triceps, core, full_body, cardio")
    equipment: str = Field(..., description="Оборудование: barbell, dumbbell, machine, bodyweight, cable, kettlebell")
    movement_patterns: list[MovementPattern] = Field(..., description="Типы движения: push_horizontal, push_vertical, pull_horizontal, pull_vertical, squat, hinge, lunge, carry, core")
    description: str | None = Field(None, description="Описание упражнения")


class CreateExercisesBatchInput(BaseModel):
    exercises: list[CreateExerciseInput] = Field(..., description="Список упражнений для создания")


class WorkoutDayExerciseAI(BaseModel):
    exercise_id: UUID = Field(..., description="UUID упражнения из базы данных")
    sets: int = Field(..., description="Количество подходов")
    reps: int = Field(..., description="Количество повторений")
    rest_seconds: int | None = Field(None, description="Время отдыха в секундах")

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


class PlanningContext(BaseModel):
    age: int
    gender: str
    goal: str
    experience_level: str

    intent_goal: str
    constraints: list[str]
    focus_areas: list[str]
    location: str
    context: str

    insights: InsightBundle
    has_insights: bool


class CandidateExercise(BaseModel):
    id: UUID
    name: str
    muscle_group: str
    equipment: str
    movement_patterns: list[str]
    description: str | None = None


class ExerciseBundle(BaseModel):
    exercises: list[CandidateExercise]


class ChatRequest(BaseModel):
    message: str = Field(description="Текст вопроса пользователя к ИИ-тренеру")


class ChunkResponseDTO(BaseModel):
    chunk_index: int = Field(..., description="Индекс чанка в документе")
    document_name: str | None = Field(None, description="Название документа, откуда взят чанк")
    similarity: float = Field(..., description="Косинусное сходство чанка с запросом")

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Сгенерированный ИИ-тренером ответ пользлователю")
    sources: list[ChunkResponseDTO] = Field(
        default_factory=list,
        description="Список фрагментов из базы знаний, которые были использованы для контекста"
    )

    model_config = ConfigDict(from_attributes=True)