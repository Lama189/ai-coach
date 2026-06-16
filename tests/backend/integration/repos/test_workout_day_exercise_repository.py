import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.workout_day_exercise import WorkoutDayExercise
from app.infrastructure.postgres.repos.workout_day_exercises import PostgresWorkoutDayExerciseRepository
from app.infrastructure.postgres.models.work_day_exercises import WorkoutDayExercise as WorkoutDayExerciseModel


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    return PostgresWorkoutDayExerciseRepository(mock_session)


@pytest.fixture
def sample_day_exercise():
    return WorkoutDayExercise(
        exercise_id=uuid4(),
        sets=3,
        reps=10,
        rest_seconds=90,
    )


class TestPostgresWorkoutDayExerciseRepository:
    async def test_save_new_exercise(self, repo, mock_session, sample_day_exercise):
        mock_session.get.return_value = None
        workout_day_id = uuid4()

        await repo.save(sample_day_exercise, workout_day_id)

        mock_session.add.assert_called_once()
        added_model = mock_session.add.call_args[0][0]
        assert isinstance(added_model, WorkoutDayExerciseModel)
        assert added_model.sets == 3
        assert added_model.reps == 10
        assert added_model.rest_seconds == 90
        assert added_model.workout_day_id == workout_day_id
        mock_session.flush.assert_called_once()

    async def test_save_existing_exercise(self, repo, mock_session, sample_day_exercise):
        existing_model = MagicMock(spec=WorkoutDayExerciseModel)
        mock_session.get.return_value = existing_model
        workout_day_id = uuid4()

        await repo.save(sample_day_exercise, workout_day_id)

        assert existing_model.workout_day_id == workout_day_id
        assert existing_model.exercise_id == sample_day_exercise.exercise_id
        assert existing_model.sets == 3
        assert existing_model.reps == 10
        assert existing_model.rest_seconds == 90
        mock_session.add.assert_not_called()
        mock_session.flush.assert_called_once()

    async def test_get_by_workout_day_id(self, repo, mock_session):
        mock_model = MagicMock(spec=WorkoutDayExerciseModel)
        mock_model.id = uuid4()
        mock_model.exercise_id = uuid4()
        mock_model.sets = 4
        mock_model.reps = 8
        mock_model.rest_seconds = 60

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.execute.return_value = mock_result

        exercises = await repo.get_by_workout_day_id(uuid4())

        assert len(exercises) == 1
        assert exercises[0].sets == 4
        assert exercises[0].reps == 8
        assert exercises[0].rest_seconds == 60

    async def test_get_by_workout_day_id_empty(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        exercises = await repo.get_by_workout_day_id(uuid4())

        assert exercises == []

    async def test_to_domain(self, repo):
        mock_model = MagicMock(spec=WorkoutDayExerciseModel)
        mock_model.id = uuid4()
        mock_model.exercise_id = uuid4()
        mock_model.sets = 5
        mock_model.reps = 12
        mock_model.rest_seconds = 45

        domain = repo._to_domain(mock_model)

        assert domain.sets == 5
        assert domain.reps == 12
        assert domain.rest_seconds == 45

    async def test_to_model(self, repo, sample_day_exercise):
        workout_day_id = uuid4()
        model = repo._to_model(sample_day_exercise, workout_day_id)

        assert isinstance(model, WorkoutDayExerciseModel)
        assert model.workout_day_id == workout_day_id
        assert model.sets == 3
        assert model.reps == 10
