import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.workout_day import WorkoutDay
from app.infrastructure.postgres.repos.workout_days import PostgresWorkoutDayRepository
from app.infrastructure.postgres.models.workout_days import WorkoutDay as WorkoutDayModel


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    return PostgresWorkoutDayRepository(mock_session)


@pytest.fixture
def sample_day():
    return WorkoutDay(
        day_number=1,
        title="Day 1: Chest & Triceps",
    )


class TestPostgresWorkoutDayRepository:
    async def test_save_new_day(self, repo, mock_session, sample_day):
        mock_session.get.return_value = None

        await repo.save(sample_day, program_id=uuid4())

        mock_session.add.assert_called_once()
        added_model = mock_session.add.call_args[0][0]
        assert isinstance(added_model, WorkoutDayModel)
        assert added_model.day_number == 1
        assert added_model.title == "Day 1: Chest & Triceps"
        mock_session.flush.assert_called_once()

    async def test_save_existing_day(self, repo, mock_session, sample_day):
        existing_model = MagicMock(spec=WorkoutDayModel)
        mock_session.get.return_value = existing_model
        program_id = uuid4()

        await repo.save(sample_day, program_id=program_id)

        assert existing_model.day_number == 1
        assert existing_model.program_id == program_id
        assert existing_model.title == "Day 1: Chest & Triceps"
        mock_session.add.assert_not_called()
        mock_session.flush.assert_called_once()

    async def test_get_by_program_id(self, repo, mock_session):
        mock_model = MagicMock(spec=WorkoutDayModel)
        mock_model.id = uuid4()
        mock_model.day_number = 1
        mock_model.title = "Day 1"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.execute.return_value = mock_result

        days = await repo.get_by_program_id(uuid4())

        assert len(days) == 1
        assert days[0].day_number == 1
        assert days[0].title == "Day 1"

    async def test_get_by_program_id_empty(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        days = await repo.get_by_program_id(uuid4())

        assert days == []

    async def test_to_domain(self, repo):
        mock_model = MagicMock(spec=WorkoutDayModel)
        mock_model.id = uuid4()
        mock_model.day_number = 2
        mock_model.title = "Day 2"

        domain = repo._to_domain(mock_model)

        assert domain.day_number == 2
        assert domain.title == "Day 2"

    async def test_to_model(self, repo, sample_day):
        program_id = uuid4()
        model = repo._to_model(sample_day, program_id)

        assert isinstance(model, WorkoutDayModel)
        assert model.day_number == 1
        assert model.program_id == program_id
