import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.domain.enums import UserGender, FitnessGoal, ExperienceLevel
from app.infrastructure.postgres.repos.identity import PostgresUserRepository
from app.infrastructure.postgres.models.users import User as UserModel
from app.infrastructure.postgres.models.profiles import UserProfile as UserProfileModel


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repository(mock_session):
    return PostgresUserRepository(mock_session)


@pytest.mark.asyncio
class TestPostgresUserRepository:
    async def test_save_new_user(self, user_repository: PostgresUserRepository, mock_session: AsyncSession, sample_user: User):
        mock_session.get.return_value = None
        mock_session.flush = AsyncMock()

        await user_repository.save(sample_user)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    async def test_save_existing_user(self, user_repository: PostgresUserRepository, mock_session: AsyncSession, sample_user: User):
        existing_model = MagicMock(spec=UserModel)
        existing_model.profile = MagicMock(spec=UserProfileModel)
        mock_session.get.return_value = existing_model
        mock_session.flush = AsyncMock()

        await user_repository.save(sample_user)

        assert existing_model.username == sample_user.username
        assert existing_model.phone == sample_user.phone
        mock_session.add.assert_not_called()
        mock_session.flush.assert_called_once()

    async def test_get_by_with_relations(self, user_repository: PostgresUserRepository, mock_session: AsyncSession, sample_user: User):
        mock_model = MagicMock(spec=UserModel)
        mock_model.id = sample_user.id
        mock_model.username = sample_user.username
        mock_model.phone = sample_user.phone
        mock_model.telegram_id = sample_user.telegram_id
        mock_model.password_hash = sample_user.password_hash
        mock_model.created_at = sample_user.created_at
        mock_model.updated_at = sample_user.updated_at
        mock_model.profile = MagicMock(spec=UserProfileModel)
        mock_model.profile.gender = UserGender.MALE
        mock_model.profile.age = 25
        mock_model.profile.height_cm = 180
        mock_model.profile.weight_kg = 75.0
        mock_model.profile.goal = FitnessGoal.GAIN_MUSCLE
        mock_model.profile.experience_level = ExperienceLevel.INTERMEDIATE
        mock_model.profile.created_at = datetime.now(timezone.utc)
        mock_model.profile.updated_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        user = await user_repository.get_by(with_relations=True, id=sample_user.id)

        assert user is not None
        assert user.username == sample_user.username
        mock_session.execute.assert_called_once()

    async def test_get_by_not_found(self, user_repository: PostgresUserRepository, mock_session: AsyncSession):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        user = await user_repository.get_by(with_relations=True, id=uuid4())

        assert user is None

    async def test_exists_by_true(self, user_repository: PostgresUserRepository, mock_session: AsyncSession):
        mock_result = MagicMock()
        mock_result.scalar.return_value = True
        mock_session.execute.return_value = mock_result

        exists = await user_repository.exists_by(username="testuser")

        assert exists is True

    async def test_exists_by_false(self, user_repository: PostgresUserRepository, mock_session: AsyncSession):
        mock_result = MagicMock()
        mock_result.scalar.return_value = False
        mock_session.execute.return_value = mock_result

        exists = await user_repository.exists_by(username="nonexistent")

        assert exists is False

    async def test_delete_existing_user(self, user_repository: PostgresUserRepository, mock_session: AsyncSession):
        mock_model = MagicMock(spec=UserModel)
        mock_session.get.return_value = mock_model
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()

        await user_repository.delete(uuid4())

        mock_session.delete.assert_called_once_with(mock_model)
        mock_session.flush.assert_called_once()

    async def test_delete_nonexistent_user(self, user_repository: PostgresUserRepository, mock_session: AsyncSession):
        mock_session.get.return_value = None
        mock_session.delete = AsyncMock()

        await user_repository.delete(uuid4())

        mock_session.delete.assert_not_called()
