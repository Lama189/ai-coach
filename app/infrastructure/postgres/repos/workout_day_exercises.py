from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.workout_day_exercise import WorkoutDayExercise
from app.domain.interfaces.workout_day_exercise import IWorkoutDayExerciseRepository
from app.infrastructure.postgres.models.work_day_exercises import WorkoutDayExercise as WorkoutDayExerciseModel


class PostgresWorkoutDayExerciseRepository(IWorkoutDayExerciseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, workout_day_exercise: WorkoutDayExercise, workout_day_id: UUID) -> None:
        existing = await self._session.get(WorkoutDayExerciseModel, workout_day_exercise.id)

        if existing is None:
            model = self._to_model(workout_day_exercise, workout_day_id)
            self._session.add(model)
        else:
            existing.workout_day_id = workout_day_id
            existing.exercise_id = workout_day_exercise.exercise_id
            existing.sets = workout_day_exercise.sets
            existing.reps = workout_day_exercise.reps
            existing.rest_seconds = int(workout_day_exercise.rest_seconds)

        await self._session.flush()

    def _to_domain(self, model: WorkoutDayExerciseModel) -> WorkoutDayExercise:
        return WorkoutDayExercise(
            id=model.id,
            exercise_id=model.exercise_id,
            sets=model.sets,
            reps=model.reps,
            rest_seconds=model.rest_seconds
        )

    def _to_model(self, domain: WorkoutDayExercise, workout_day_id: UUID) -> WorkoutDayExerciseModel:
        return WorkoutDayExerciseModel(
            id=domain.id,
            workout_day_id=workout_day_id,
            exercise_id=domain.exercise_id,
            sets=domain.sets,
            reps=domain.reps,
            rest_seconds=domain.rest_seconds
        )