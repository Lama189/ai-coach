from uuid import UUID
from pydantic import BaseModel, Field
from typing import Literal


class WorkoutDayExerciseCreate(BaseModel):
    exercise_id: UUID
    sets: int = Field(..., gt=0, description="Количество подходов")
    reps: int = Field(..., gt=0, description="Количество повторений")
    rest_seconds: int | None = Field(None, ge=0, description="Отдыхъ между пожходами в секундах")


class WorkoutDayCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    exercises: list[WorkoutDayExerciseCreate] = Field(..., min_length=1)
    day_number: int = Field(..., gt=0, lt=8)


class WorkoutProgramCreate(BaseModel):
    user_id: UUID
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = None
    days: list[WorkoutDayCreate] = Field(..., min_length=1)


class WorkoutDayExerciseResponse(BaseModel):
    id: UUID = Field(..., description="Уникальный ID связи упражнения с днем")
    exercise_id: UUID = Field(..., description="ID самого упражнения из справочника")
    exercise_name: str | None = Field(None, description="Название упражнения")
    sets: int = Field(..., description="Количество подходов")
    reps: int = Field(..., description="Количество повторений")
    rest_seconds: int | None = Field(None, description="Время отдыха в секундах")

    class Config:
        from_attributes = True


class WorkoutDayResponse(BaseModel):
    id: UUID = Field(..., description="Уникальный ID тренировочного дня")
    day_number: int = Field(..., description="Порядковый номер дня (1-7)")
    title: str = Field(..., description="Название дня (например, 'День 1: Ноги')")
    exercises: list[WorkoutDayExerciseResponse] = Field(..., description="Список упражнений в этот день")

    class Config:
        from_attributes = True


class WorkoutProgramResponse(BaseModel):
    id: UUID = Field(..., description="Уникальный ID созданной программы")
    user_id: UUID = Field(..., description="ID владельца программы")
    name: str = Field(..., description="Название программы")
    description: str | None = Field(None, description="Описание программы")
    is_active: bool = Field(..., description="Флаг активности программы")
    workout_days: list[WorkoutDayResponse] = Field(..., description="Список тренировочных дней")

    class Config:
        from_attributes = True


class GenerateProgram(BaseModel):
    content: str | None = Field(None, description="Пожелания пользователя к программе")
    importance: Literal["low", "medium", "high"] = Field(
        default="medium", 
        description="Насколько строго учитывать пожелания"
    )


