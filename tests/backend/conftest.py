import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.domain.training.exercise import Exercise
from app.domain.enums import UserGender, FitnessGoal, ExperienceLevel, MuscleGroup
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.postgres.repos.identity import PostgresUserRepository
from app.infrastructure.postgres.repos.exercises import PostgresExerciseRepository
from app.infrastructure.redis.repos.repository import RedisRepository


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_user_profile() -> UserProfile:
    return UserProfile(
        gender=UserGender.MALE,
        age=25,
        height_cm=180,
        weight_kg=75,
        goal=FitnessGoal.GAIN_MUSCLE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        location=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_user(sample_user_profile: UserProfile) -> User:
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


@pytest.fixture
def mock_uow() -> IUnitOfWork:
    uow = AsyncMock(spec=IUnitOfWork)
    uow.users = AsyncMock(spec=PostgresUserRepository)
    uow.exercises = AsyncMock(spec=PostgresExerciseRepository)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture
def mock_redis_repo() -> RedisRepository:
    repo = AsyncMock(spec=RedisRepository)
    return repo


@pytest.fixture
def mock_user_repository():
    repo = AsyncMock(spec=PostgresUserRepository)
    return repo


@pytest.fixture
def sample_exercise() -> Exercise:
    return Exercise(
        id=uuid4(),
        name="Bench Press",
        muscle_group=MuscleGroup.CHEST,
        equipment="barbell",
        movement_pattern="push",
        description="Classic chest exercise",
    )


@pytest.fixture
def mock_exercise_repository():
    repo = AsyncMock(spec=PostgresExerciseRepository)
    return repo


@pytest.fixture
def mock_exercise_session():
    return AsyncMock(spec=AsyncSession)
