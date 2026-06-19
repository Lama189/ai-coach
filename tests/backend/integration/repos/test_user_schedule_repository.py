import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.user_schedule import UserSchedule
from app.infrastructure.postgres.repos.user_schedule import PostgresUserScheduleRepository
from app.infrastructure.postgres.models.user_schedule import UserSchedule as UserScheduleModel


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def schedule_repository(mock_session):
    return PostgresUserScheduleRepository(mock_session)


@pytest.fixture
def sample_schedule():
    return UserSchedule(
        user_id=uuid4(),
        day_of_week=0,
        training_day_number=1,
    )


class TestPostgresUserScheduleRepository:
    async def test_save_new(self, schedule_repository, mock_session, sample_schedule):
        mock_session.get.return_value = None
        mock_session.flush = AsyncMock()

        await schedule_repository.save(sample_schedule)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    async def test_save_existing(self, schedule_repository, mock_session, sample_schedule):
        existing = MagicMock(spec=UserScheduleModel)
        mock_session.get.return_value = existing
        mock_session.flush = AsyncMock()

        await schedule_repository.save(sample_schedule)

        assert existing.user_id == sample_schedule.user_id
        assert existing.day_of_week == sample_schedule.day_of_week
        assert existing.training_day_number == sample_schedule.training_day_number
        mock_session.add.assert_not_called()
        mock_session.flush.assert_called_once()

    async def test_get_by_id_found(self, schedule_repository, mock_session, sample_schedule):
        mock_model = MagicMock(spec=UserScheduleModel)
        mock_model.id = sample_schedule.id
        mock_model.user_id = sample_schedule.user_id
        mock_model.day_of_week = sample_schedule.day_of_week
        mock_model.training_day_number = sample_schedule.training_day_number
        mock_session.get.return_value = mock_model

        result = await schedule_repository.get_by_id(sample_schedule.id)

        assert result is not None
        assert result.user_id == sample_schedule.user_id
        assert result.day_of_week == 0

    async def test_get_by_id_not_found(self, schedule_repository, mock_session):
        mock_session.get.return_value = None

        result = await schedule_repository.get_by_id(uuid4())

        assert result is None

    async def test_delete_existing(self, schedule_repository, mock_session):
        mock_model = MagicMock(spec=UserScheduleModel)
        mock_session.get.return_value = mock_model
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()

        await schedule_repository.delete(uuid4())

        mock_session.delete.assert_called_once_with(mock_model)
        mock_session.flush.assert_called_once()

    async def test_delete_nonexistent(self, schedule_repository, mock_session):
        mock_session.get.return_value = None
        mock_session.delete = AsyncMock()

        await schedule_repository.delete(uuid4())

        mock_session.delete.assert_not_called()

    async def test_search_by_user_id(self, schedule_repository, mock_session, sample_schedule):
        mock_model = MagicMock(spec=UserScheduleModel)
        mock_model.id = sample_schedule.id
        mock_model.user_id = sample_schedule.user_id
        mock_model.day_of_week = sample_schedule.day_of_week
        mock_model.training_day_number = sample_schedule.training_day_number

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.execute.return_value = mock_result

        results = await schedule_repository.search_by(user_id=sample_schedule.user_id)

        assert len(results) == 1
        assert results[0].user_id == sample_schedule.user_id
        mock_session.execute.assert_called_once()

    async def test_search_by_day_of_week(self, schedule_repository, mock_session, sample_schedule):
        mock_model = MagicMock(spec=UserScheduleModel)
        mock_model.id = sample_schedule.id
        mock_model.user_id = sample_schedule.user_id
        mock_model.day_of_week = 2
        mock_model.training_day_number = sample_schedule.training_day_number

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.execute.return_value = mock_result

        results = await schedule_repository.search_by(day_of_week=2)

        assert len(results) == 1
        assert results[0].day_of_week == 2

    async def test_search_by_no_results(self, schedule_repository, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        results = await schedule_repository.search_by(user_id=uuid4(), day_of_week=5)

        assert len(results) == 0
