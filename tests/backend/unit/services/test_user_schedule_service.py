import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.domain.identity.user_schedule import UserSchedule
from app.application.services.user_schedule_service import UserScheduleService
from app.application.interfaces.unit_of_work import IUnitOfWork


@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)
    uow.user_schedules = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def sample_schedule():
    return UserSchedule(
        user_id=uuid4(),
        day_of_week=0,
        training_day_number=1,
    )


class TestUserScheduleService:
    async def test_create_schedule(self, mock_uow, sample_schedule):
        mock_uow.user_schedules.save = AsyncMock()

        service = UserScheduleService(mock_uow)
        result = await service.create_schedule(
            user_id=sample_schedule.user_id,
            day_of_week=0,
            training_day_number=1,
        )

        assert result.user_id == sample_schedule.user_id
        assert result.day_of_week == 0
        assert result.training_day_number == 1
        mock_uow.user_schedules.save.assert_called_once()
        mock_uow.commit.assert_called_once()

    async def test_get_schedule_found(self, mock_uow, sample_schedule):
        mock_uow.user_schedules.get_by_id.return_value = sample_schedule

        service = UserScheduleService(mock_uow)
        result = await service.get_schedule(sample_schedule.id)

        assert result == sample_schedule
        mock_uow.user_schedules.get_by_id.assert_called_once_with(sample_schedule.id)

    async def test_get_schedule_not_found(self, mock_uow):
        mock_uow.user_schedules.get_by_id.return_value = None

        service = UserScheduleService(mock_uow)
        result = await service.get_schedule(uuid4())

        assert result is None

    async def test_get_by_day_found(self, mock_uow, sample_schedule):
        mock_uow.user_schedules.search_by.return_value = [sample_schedule]

        service = UserScheduleService(mock_uow)
        result = await service.get_by_day(sample_schedule.user_id, 0)

        assert result == sample_schedule
        mock_uow.user_schedules.search_by.assert_called_once_with(
            user_id=sample_schedule.user_id, day_of_week=0,
        )

    async def test_get_by_day_not_found(self, mock_uow):
        mock_uow.user_schedules.search_by.return_value = []

        service = UserScheduleService(mock_uow)
        result = await service.get_by_day(uuid4(), 0)

        assert result is None

    async def test_list_all_by_user(self, mock_uow, sample_schedule):
        mock_uow.user_schedules.search_by.return_value = [sample_schedule]

        service = UserScheduleService(mock_uow)
        result = await service.list_all_by_user(sample_schedule.user_id)

        assert len(result) == 1
        assert result[0] == sample_schedule
        mock_uow.user_schedules.search_by.assert_called_once_with(user_id=sample_schedule.user_id)

    async def test_search_schedules(self, mock_uow, sample_schedule):
        mock_uow.user_schedules.search_by.return_value = [sample_schedule]

        service = UserScheduleService(mock_uow)
        result = await service.search_schedules(
            user_id=sample_schedule.user_id,
            day_of_week=0,
            training_day_number=1,
        )

        assert len(result) == 1
        mock_uow.user_schedules.search_by.assert_called_once_with(
            user_id=sample_schedule.user_id,
            day_of_week=0,
            training_day_number=1,
        )

    async def test_delete_schedule(self, mock_uow):
        mock_uow.user_schedules.delete = AsyncMock()

        service = UserScheduleService(mock_uow)
        await service.delete_schedule(uuid4())

        mock_uow.user_schedules.delete.assert_called_once()
        mock_uow.commit.assert_called_once()

    async def test_delete_by_day(self, mock_uow, sample_schedule):
        mock_uow.user_schedules.search_by.return_value = [sample_schedule]
        mock_uow.user_schedules.delete = AsyncMock()

        service = UserScheduleService(mock_uow)
        await service.delete_by_day(sample_schedule.user_id, 0)

        mock_uow.user_schedules.delete.assert_called_once_with(sample_schedule.id)
        mock_uow.commit.assert_called_once()

    async def test_delete_by_day_multiple(self, mock_uow):
        s1 = UserSchedule(user_id=uuid4(), day_of_week=2, training_day_number=1)
        s2 = UserSchedule(user_id=uuid4(), day_of_week=2, training_day_number=3)
        mock_uow.user_schedules.search_by.return_value = [s1, s2]
        mock_uow.user_schedules.delete = AsyncMock()

        service = UserScheduleService(mock_uow)
        await service.delete_by_day(s1.user_id, 2)

        assert mock_uow.user_schedules.delete.call_count == 2
        mock_uow.commit.assert_called_once()
