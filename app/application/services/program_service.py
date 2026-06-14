from uuid import UUID

from app.application.interfaces.unit_of_work import IUnitOfWork
from app.domain.training.program import WorkoutProgram
from app.domain.training.workout_day import WorkoutDay
from app.domain.training.workout_day_exercise import WorkoutDayExercise
from app.application.dto.program import WorkoutProgramCreate, WorkoutProgramResponse, WorkoutDayResponse, WorkoutDayExerciseResponse


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


    async def get_actual_program_for_user(self, user_id: UUID) -> WorkoutProgramResponse:
        existing_program = await self._uow.programs.get_actual_by_user_id(user_id)
        if existing_program is None:
            raise ValueError("Для данного пользователя нет программ тренировок")
        
        days = await self._uow.workout_days.get_by_program_id(existing_program.id)
        if not days:
            raise ValueError("Для данной программы отсутствуют тренировочные дни")

        all_exercise_ids = set()
        day_exercises_map: dict[UUID, list] = {}

        for day in days:
            exercises = await self._uow.workout_days_exercise.get_by_workout_day_id(day.id)
            day_exercises_map[day.id] = exercises
            for ex in exercises:
                all_exercise_ids.add(ex.exercise_id)

        exercise_names: dict[UUID, str] = {}
        if all_exercise_ids:
            exercises = await self._uow.exercises.get_by_ids(list(all_exercise_ids))
            exercise_names = {e.id: e.name for e in exercises}

        return WorkoutProgramResponse(
            id=existing_program.id,
            user_id=existing_program.user_id,
            name=existing_program.name,
            description=existing_program.description,
            is_active=existing_program.is_active,
            workout_days=[
                WorkoutDayResponse(
                    id=day.id,
                    day_number=day.day_number,
                    title=day.title,
                    exercises=[
                        WorkoutDayExerciseResponse(
                            id=ex.id,
                            exercise_id=ex.exercise_id,
                            exercise_name=exercise_names.get(ex.exercise_id),
                            sets=ex.sets,
                            reps=ex.reps,
                            rest_seconds=ex.rest_seconds,
                        )
                        for ex in day_exercises_map[day.id]
                    ],
                )
                for day in days
            ],
        )