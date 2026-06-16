import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.domain.training.program import WorkoutProgram
from app.domain.training.workout_day import WorkoutDay
from app.domain.training.workout_day_exercise import WorkoutDayExercise
from app.domain.training.exercise import Exercise
from app.domain.enums import MuscleGroup, MovementPattern
from app.application.services.program_service import WorkoutProgramService
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.application.dto.program import WorkoutProgramCreate, WorkoutDayCreate, WorkoutDayExerciseCreate


@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)
    uow.programs = AsyncMock()
    uow.workout_days = AsyncMock()
    uow.workout_days_exercise = AsyncMock()
    uow.exercises = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def sample_exercise_id():
    return uuid4()


@pytest.fixture
def sample_exercise(sample_exercise_id):
    return Exercise(
        id=sample_exercise_id,
        name="Bench Press",
        muscle_group=MuscleGroup.CHEST,
        equipment="barbell",
        movement_patterns=[MovementPattern.PUSH_HORIZONTAL],
    )


class TestWorkoutProgramServiceCreate:
    async def test_create_program_success(self, mock_uow, sample_exercise, sample_exercise_id):
        mock_uow.exercises.get_by_ids.return_value = [sample_exercise]

        dto = WorkoutProgramCreate(
            user_id=uuid4(),
            name="Test Program",
            description="A test program",
            days=[
                WorkoutDayCreate(
                    name="Day 1",
                    day_number=1,
                    exercises=[
                        WorkoutDayExerciseCreate(
                            exercise_id=sample_exercise_id,
                            sets=3,
                            reps=10,
                            rest_seconds=90,
                        )
                    ],
                )
            ],
        )

        service = WorkoutProgramService(mock_uow)
        program = await service.create_program(dto)

        assert isinstance(program, WorkoutProgram)
        assert program.name == "Test Program"
        assert program.is_active is True
        mock_uow.programs.deactivate_all_for_user.assert_called_once_with(dto.user_id)
        mock_uow.programs.save.assert_called_once()
        mock_uow.workout_days.save.assert_called_once()
        mock_uow.workout_days_exercise.save.assert_called_once()
        mock_uow.commit.assert_called_once()

    async def test_create_program_nonexistent_exercises(self, mock_uow):
        mock_uow.exercises.get_by_ids.return_value = []

        dto = WorkoutProgramCreate(
            user_id=uuid4(),
            name="Test Program",
            days=[
                WorkoutDayCreate(
                    name="Day 1",
                    day_number=1,
                    exercises=[
                        WorkoutDayExerciseCreate(
                            exercise_id=uuid4(),
                            sets=3,
                            reps=10,
                        )
                    ],
                )
            ],
        )

        service = WorkoutProgramService(mock_uow)

        with pytest.raises(ValueError, match="несуществующие упражнения"):
            await service.create_program(dto)

        mock_uow.programs.save.assert_not_called()
        mock_uow.commit.assert_not_called()

    async def test_create_program_multiple_days(self, mock_uow, sample_exercise, sample_exercise_id):
        mock_uow.exercises.get_by_ids.return_value = [sample_exercise]

        dto = WorkoutProgramCreate(
            user_id=uuid4(),
            name="Multi Day",
            days=[
                WorkoutDayCreate(
                    name="Day 1",
                    day_number=1,
                    exercises=[
                        WorkoutDayExerciseCreate(exercise_id=sample_exercise_id, sets=3, reps=10)
                    ],
                ),
                WorkoutDayCreate(
                    name="Day 2",
                    day_number=2,
                    exercises=[
                        WorkoutDayExerciseCreate(exercise_id=sample_exercise_id, sets=4, reps=8)
                    ],
                ),
            ],
        )

        service = WorkoutProgramService(mock_uow)
        program = await service.create_program(dto)

        assert mock_uow.workout_days.save.call_count == 2
        assert mock_uow.workout_days_exercise.save.call_count == 2


class TestWorkoutProgramServiceGet:
    async def test_get_actual_program_for_user_success(self, mock_uow):
        program_id = uuid4()
        user_id = uuid4()
        day_id = uuid4()
        exercise_id = uuid4()
        day_exercise_id = uuid4()

        program = WorkoutProgram(
            id=program_id,
            user_id=user_id,
            name="Test Program",
            is_active=True,
        )

        day = WorkoutDay(id=day_id, day_number=1, title="Day 1")

        day_exercise = WorkoutDayExercise(
            id=day_exercise_id,
            exercise_id=exercise_id,
            sets=3,
            reps=10,
            rest_seconds=90,
        )

        exercise = Exercise(
            id=exercise_id,
            name="Bench Press",
            muscle_group=MuscleGroup.CHEST,
            equipment="barbell",
            movement_patterns=[MovementPattern.PUSH_HORIZONTAL],
        )

        mock_uow.programs.get_actual_by_user_id.return_value = program
        mock_uow.workout_days.get_by_program_id.return_value = [day]
        mock_uow.workout_days_exercise.get_by_workout_day_id.return_value = [day_exercise]
        mock_uow.exercises.get_by_ids.return_value = [exercise]

        service = WorkoutProgramService(mock_uow)
        response = await service.get_actual_program_for_user(user_id)

        assert response.id == program_id
        assert response.name == "Test Program"
        assert len(response.workout_days) == 1
        assert response.workout_days[0].day_number == 1
        assert len(response.workout_days[0].exercises) == 1
        assert response.workout_days[0].exercises[0].exercise_name == "Bench Press"
        assert response.workout_days[0].exercises[0].sets == 3

    async def test_get_actual_program_no_program(self, mock_uow):
        mock_uow.programs.get_actual_by_user_id.return_value = None

        service = WorkoutProgramService(mock_uow)

        with pytest.raises(ValueError, match="нет программ тренировок"):
            await service.get_actual_program_for_user(uuid4())

    async def test_get_actual_program_no_days(self, mock_uow):
        program = WorkoutProgram(
            user_id=uuid4(),
            name="Test",
            is_active=True,
        )
        mock_uow.programs.get_actual_by_user_id.return_value = program
        mock_uow.workout_days.get_by_program_id.return_value = []

        service = WorkoutProgramService(mock_uow)

        with pytest.raises(ValueError, match="отсутствуют тренировочные дни"):
            await service.get_actual_program_for_user(program.user_id)
