import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.application.dependencies import get_uow, get_current_user
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.domain.identity.user_schedule import UserSchedule
from app.domain.enums import UserGender, FitnessGoal, ExperienceLevel


@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)
    uow.user_schedules = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def current_user():
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        username="testuser",
        phone="+998901234567",
        password_hash="hashed",
        telegram_id=111111,
        profile=UserProfile(
            gender=UserGender.MALE,
            age=25,
            height_cm=180,
            weight_kg=75,
            goal=FitnessGoal.GAIN_MUSCLE,
            experience_level=ExperienceLevel.INTERMEDIATE,
            location=None,
            created_at=now,
            updated_at=now,
        ),
    )


@pytest.fixture(autouse=True)
def setup_deps(mock_uow, current_user):
    app.dependency_overrides[get_uow] = lambda: mock_uow
    app.dependency_overrides[get_current_user] = lambda: current_user
    yield
    app.dependency_overrides.clear()


class TestUserScheduleRouter:
    async def test_create_schedule(self, mock_uow, current_user):
        mock_uow.user_schedules.save = AsyncMock()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/users/schedule/add_day",
                json={"day_of_week": 0, "training_day_number": 1},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["day_of_week"] == 0
        assert data["training_day_number"] == 1
        assert data["user_id"] == str(current_user.id)
        mock_uow.user_schedules.save.assert_called_once()
        mock_uow.commit.assert_called_once()

    async def test_list_schedules(self, mock_uow, current_user):
        schedule = UserSchedule(
            user_id=current_user.id,
            day_of_week=0,
            training_day_number=1,
        )
        mock_uow.user_schedules.search_by.return_value = [schedule]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/users/schedule")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["day_of_week"] == 0

    async def test_get_schedule_by_day_found(self, mock_uow, current_user):
        schedule = UserSchedule(
            user_id=current_user.id,
            day_of_week=3,
            training_day_number=2,
        )
        mock_uow.user_schedules.search_by.return_value = [schedule]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/users/schedule/3")

        assert response.status_code == 200
        data = response.json()
        assert data["day_of_week"] == 3
        assert data["training_day_number"] == 2

    async def test_get_schedule_by_day_not_found(self, mock_uow):
        mock_uow.user_schedules.search_by.return_value = []

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/users/schedule/5")

        assert response.status_code == 404

    async def test_delete_schedule_by_day(self, mock_uow, current_user):
        schedule = UserSchedule(
            user_id=current_user.id,
            day_of_week=1,
            training_day_number=1,
        )
        mock_uow.user_schedules.search_by.return_value = [schedule]
        mock_uow.user_schedules.delete = AsyncMock()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/v1/users/schedule/1")

        assert response.status_code == 204
        mock_uow.user_schedules.delete.assert_called_once()
        mock_uow.commit.assert_called_once()
