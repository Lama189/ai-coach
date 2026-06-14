import logging
from uuid import UUID
from typing import Callable, AsyncContextManager, cast

from langchain_google_genai import ChatGoogleGenerativeAI

from app.domain.training.program import WorkoutProgram
from app.domain.training.workout_day import WorkoutDay
from app.domain.training.workout_day_exercise import WorkoutDayExercise
from app.application.dto.for_ai import (
    PlanningContext,
    ExerciseBundle,
    WorkoutProgramAI,
)

from app.application.dto.program import (
    WorkoutProgramResponse,
    WorkoutDayResponse,
    WorkoutDayExerciseResponse,
)

logger = logging.getLogger(__name__)


class WorkoutProgramGenerator:
    def __init__(
        self,
        api_key: str,
    ) -> None:
        self._llm = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model="gemini-3.5-flash",
            temperature=0.2
        )

    
    async def generate(
        self,
        user_id: UUID,
        context: PlanningContext,
        exercises: ExerciseBundle,
    ) -> WorkoutProgramAI:

        structured_llm = self._llm.with_structured_output(
            WorkoutProgramAI,
            method="json_mode",
        )

        prompt = self._build_prompt(
            context=context,
            exercises=exercises,
        )

        logger.info(
            "program_generation_started",
            extra={
                "exercise_count": len(exercises.exercises),
                "goal": context.goal,
                "experience": context.experience_level,
            },
        )

        program = cast(
            WorkoutProgramAI,
            await structured_llm.ainvoke(prompt)
        )

        logger.info(
            "program_generation_finished",
            extra={
                "days": len(program.workout_days),
                "program_name": program.name,
            },
        )

        return program

    def _build_prompt(
        self,
        context: PlanningContext,
        exercises: ExerciseBundle,
    ) -> str:

        exercises_text = "\n".join(
            [
                (
                    f"id={exercise.id}\n"
                    f"name={exercise.name}\n"
                    f"muscle_group={exercise.muscle_group}\n"
                    f"equipment={exercise.equipment}\n"
                    f"movement_patterns={','.join(exercise.movement_patterns)}\n"
                )
                for exercise in exercises.exercises
            ]
        )

        hard_insights = "\n".join(
            insight.content
            for insight in context.insights.hard
        )

        context_insights = "\n".join(
            insight.content
            for insight in context.insights.context
        )

        preferences = "\n".join(
            insight.content
            for insight in context.insights.preferences
        )

        semantic = "\n".join(
            insight.content
            for insight in context.insights.semantic
        )

        return f"""
                Ты профессиональный фитнес-тренер.

                Твоя задача:
                Составить программу тренировок используя ТОЛЬКО упражнения,
                которые были переданы ниже.

                ====================
                ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
                ====================

                Возраст: {context.age}
                Пол: {context.gender}
                Цель: {context.goal}
                Уровень: {context.experience_level}

                ====================
                ИНТЕНТ
                ====================

                Основная цель:
                {context.intent_goal}

                Ограничения:
                {', '.join(context.constraints) if context.constraints else 'нет'}

                Приоритетные группы мышц:
                {', '.join(context.focus_areas)}

                Локация:
                {context.location}

                Контекст:
                {context.context}

                ====================
                ИНСАЙТЫ
                ====================

                Критичные:
                {hard_insights if hard_insights else 'нет'}

                Контекстные:
                {context_insights if context_insights else 'нет'}

                Предпочтения:
                {preferences if preferences else 'нет'}

                Семантически релевантные:
                {semantic if semantic else 'нет'}

                ====================
                ДОСТУПНЫЕ УПРАЖНЕНИЯ
                ====================

                {exercises_text}

                ====================
                ПРАВИЛА
                ====================

                1. Используй только упражнения из списка выше.

                2. Никогда не придумывай UUID.

                3. Используй exercise_id только из списка выше.

                4. Не добавляй упражнения, которых нет среди доступных.

                5. Если есть ограничения или травмы —
                исключай конфликтующие упражнения полностью.

                6. Не повторяй одинаковые упражнения
                в разные тренировочные дни.

                7. Названия дней должны отражать
                мышечные группы.

                Примеры:
                - Chest and Triceps
                - Legs and Core
                - Back and Biceps

                Не использовать:
                - Day 1
                - Workout A

                8. Количество тренировочных дней:

                beginner:
                3 дня

                intermediate:
                3-4 дня

                advanced:
                4-5 дней

                9. Количество упражнений:

                beginner:
                3-4 упражнения

                intermediate:
                4-5 упражнений

                advanced:
                5-6 упражнений

                10. Для цели gain_muscle:

                базово:
                sets = 3-5
                reps = 6-12
                rest_seconds = 60-90

                11. Для цели lose_weight:

                sets = 2-4
                reps = 12-20
                rest_seconds = 30-45

                12. Для цели endurance:

                sets = 2-4
                reps = 15-25
                rest_seconds = 20-40

                13. Каждая группа мышц из focus_areas
                должна быть представлена в программе.

                14. Верни только структуру WorkoutProgramAI.

                15. Не объясняй решения.

                16. Не возвращай markdown.

                17. Не возвращай текст.

                18. Верни только JSON.
                """
    
    def map_to_domain(self, user_id: UUID, response: WorkoutProgramAI) -> WorkoutProgram:
        program = WorkoutProgram(
            user_id=user_id,
            name=response.name,
            description=response.description,
            is_active=True,
        )

        for day_dto in response.workout_days:
            day = WorkoutDay(
                day_number=day_dto.day_number,
                title=day_dto.title,
            )
            for exercise_dto in day_dto.exercises:
                exercise = WorkoutDayExercise(
                    exercise_id=exercise_dto.exercise_id,
                    sets=exercise_dto.sets,
                    reps=exercise_dto.reps,
                    rest_seconds=exercise_dto.rest_seconds,
                )
                day.add_exercise(exercise)
            program.add_day(day)

        return program


    def map_to_response(
        self,
        program: WorkoutProgram,
        exercise_names: dict[UUID, str] | None = None,
    ) -> WorkoutProgramResponse:
        return WorkoutProgramResponse(
            id=program.id,
            user_id=program.user_id,
            name=program.name,
            description=program.description,
            is_active=program.is_active,
            workout_days=[
                WorkoutDayResponse(
                    id=day.id,
                    day_number=day.day_number,
                    title=day.title,
                    exercises=[
                        WorkoutDayExerciseResponse(
                            id=exercise.id,
                            exercise_id=exercise.exercise_id,
                            exercise_name=exercise_names.get(exercise.exercise_id) if exercise_names else None,
                            sets=exercise.sets,
                            reps=exercise.reps,
                            rest_seconds=exercise.rest_seconds,
                        )
                        for exercise in day.exercises
                    ],
                )
                for day in program.workout_days
            ],
        )