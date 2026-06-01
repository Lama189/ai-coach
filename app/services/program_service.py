from uuid import UUID

from app.infrastructure.postgres.unit_of_work import IUnitOfWork
from app.domain.training.program import WorkoutProgram
from app.domain.training.workout_day import WorkoutDay
from app.domain.training.workout_day_exercise import WorkoutDayExercise
from app.application.dto.program import WorkoutProgramCreate


class WorkoutProgramService:
    def __init__(self, uow: IUnitOfWork):
        self._uow = uow

    
    async def create_program(self, dto: WorkoutProgramCreate) -> WorkoutProgram:
        unique_exercise_ids = {
            exercise.exercise_id
            for day in dto.days
            for exercise in day.exercises
        }

        existing_exercises = await self._uow.exercises.get_by_ids(unique_exercise_ids)

        if len(existing_exercises) != len(unique_exercise_ids):
            raise ValueError("В структуре программы переданы несуществующие упражнения")
        
        await self._uow.programs.deactivate_all_for_user(dto.user_id)

        program = WorkoutProgram(
            user_id=dto.user_id,
            name=dto.name,
            description=dto.description,
            is_active=True
        )

        await self._uow.programs.save(program)

        for day_dto in dto.days:
            day = WorkoutDay(
                day_number=day_dto.day_number,
                title=day_dto.name
            )
            await self._uow.workout_days.save(day, program.id)
            program.add_day(day)

            for ex_dto in day_dto.exercises:
                day_exercise = WorkoutDayExercise(
                    exercise_id=ex_dto.exercise_id,
                    sets=ex_dto.sets,
                    reps=ex_dto.reps,
                    rest_seconds=ex_dto.rest_seconds
                )
                await self._uow.workout_days_exercise.save(day_exercise, day.id)
                day.add_exercise(day_exercise)

        await self._uow.commit()
        return program

