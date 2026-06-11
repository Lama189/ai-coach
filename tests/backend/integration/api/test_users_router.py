import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.domain.enums import UserGender, FitnessGoal, ExperienceLevel
from app.infrastructure.postgres.unit_of_work import IUnitOfWork
from app.infrastructure.redis.repos.repository import RedisRepository
from app.application.dependencies import get_uow, get_redis_repository
from app.infrastructure.security.password import hash_password
from app.core.security import SecurityUtils


@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)
    uow.users = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_redis_repo():
    return AsyncMock(spec=RedisRepository)


@pytest.fixture
def sample_user_profile():
    return UserProfile(
        gender=UserGender.MALE,
        age=25,
        height_cm=180,
        weight_kg=75,
        goal=FitnessGoal.GAIN_MUSCLE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_user(sample_user_profile):
    return User(
        id=uuid4(),
        username="testuser",
        phone="+998901234567",
        password_hash="hashed_password",
        telegram_id=123456789,
        profile=sample_user_profile,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
class TestUsersRouter:
    async def test_create_user_success(self, mock_uow, sample_user_profile):
        mock_uow.users.exists_by.return_value = False

        app.dependency_overrides[get_uow] = lambda: mock_uow

        with patch("app.api.v1.routes.users.hash_password", return_value="hashed_password"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/users/register",
                    json={
                        "username": "newuser",
                        "phone": "+998901234567",
                        "password": "password123",
                        "telegram_id": 123456789,
                    }
                )

        app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["phone"] == "+998901234567"

    async def test_create_user_username_taken(self, mock_uow):
        mock_uow.users.exists_by.return_value = True

        app.dependency_overrides[get_uow] = lambda: mock_uow

        with patch("app.api.v1.routes.users.hash_password", return_value="hashed_password"):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/users/register",
                    json={
                        "username": "existinguser",
                        "phone": "+998901234567",
                        "password": "password123",
                    }
                )

        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert "уже занят" in response.json()["detail"]


    async def test_login_success(self, mock_uow, mock_redis_repo, sample_user):
        mock_uow.users.get_by.return_value = sample_user

        app.dependency_overrides[get_uow] = lambda: mock_uow
        app.dependency_overrides[get_redis_repository] = lambda: mock_redis_repo

        with patch.object(SecurityUtils, "verify_password", return_value=True), \
             patch.object(SecurityUtils, "generate_access_token", return_value="access_token"), \
             patch.object(SecurityUtils, "generate_refresh_token", return_value="refresh_token"):
            
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/users/login",
                    json={
                        "phone": "+998901234567",
                        "password": "correct_password",
                        "telegram_id": 123456789,
                    }
                )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token"
        assert data["refresh_token"] == "refresh_token"


    async def test_login_user_not_found(self, mock_uow, mock_redis_repo):
        mock_uow.users.get_by.return_value = None

        app.dependency_overrides[get_uow] = lambda: mock_uow
        app.dependency_overrides[get_redis_repository] = lambda: mock_redis_repo

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/users/login",
                json={
                    "phone": "+998901234567",
                    "password": "password",
                    "telegram_id": 123456789,
                }
            )

        app.dependency_overrides.clear()

        assert response.status_code == 404


    async def test_get_user_by_telegram_id_success(self, mock_uow, sample_user):
        mock_uow.users.get_by.return_value = sample_user

        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/users/telegram/{sample_user.telegram_id}")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == sample_user.telegram_id


    async def test_get_user_by_telegram_id_not_found(self, mock_uow):
        mock_uow.users.get_by.return_value = None

        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/users/telegram/999999999")

        app.dependency_overrides.clear()

        assert response.status_code == 404


    async def test_exists_by_phone_true(self, mock_uow):
        mock_uow.users.exists_by.return_value = True

        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/users/exists/phone/+998901234567")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json() is True


    async def test_exists_by_phone_false(self, mock_uow):
        mock_uow.users.exists_by.return_value = False

        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/users/exists/phone/+998999999999")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json() is False


    async def test_get_user_success(self, mock_uow, sample_user):
        mock_uow.users.get_by.return_value = sample_user

        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/users/{sample_user.id}")

        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == sample_user.username


    async def test_get_user_not_found(self, mock_uow):
        mock_uow.users.get_by.return_value = None

        app.dependency_overrides[get_uow] = lambda: mock_uow

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/users/{uuid4()}")

        app.dependency_overrides.clear()

        assert response.status_code == 404
