import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.domain.enums import UserGender, FitnessGoal, ExperienceLevel
from app.application.services.user_service import UserService
from app.application.interfaces.unit_of_work import IUnitOfWork


@pytest.mark.asyncio
class TestUserService:
    async def test_create_user_success(self, mock_uow: IUnitOfWork, sample_user_profile: UserProfile):
        mock_uow.users.exists_by.return_value = False
        mock_uow.users.save = AsyncMock()

        service = UserService(mock_uow)

        user = await service.create_user(
            username="newuser", 
            password_hash="hashed_password",
            phone="+998901234567",
            telegram_id=123456789,
            profile=sample_user_profile,
        )

        assert user.username == "newuser"
        assert user.phone == "+998901234567"
        assert user.telegram_id == 123456789
        assert user.profile == sample_user_profile
        mock_uow.users.save.assert_called_once()
        mock_uow.commit.assert_called_once()


    async def test_create_username_taken(self, mock_uow: IUnitOfWork, sample_user_profile: UserProfile):
        mock_uow.users.exists_by.return_value = True

        service = UserService(mock_uow)

        with pytest.raises(ValueError) as exc_info:
            await service.create_user(
                username="existinguser",
                password_hash="hashed_password",
                phone="+998901234567",
                telegram_id=123456789,
                profile=sample_user_profile,
            )

        assert "уже занят" in str(exc_info.value)
        mock_uow.users.save.assert_not_called()


    async def test_get_user_found(self, mock_uow: IUnitOfWork, sample_user: User):
        mock_uow.users.get_by.return_value = sample_user

        service = UserService(mock_uow)
        user = await service.get_user(sample_user.id)

        assert user == sample_user
        mock_uow.users.get_by.assert_called_once_with(True, id=sample_user.id)


    async def test_get_user_not_found(self, mock_uow: IUnitOfWork):
        mock_uow.users.get_by.return_value = None

        service = UserService(mock_uow)
        user = await service.get_user(uuid4())

        assert user is None


    async def test_get_user_by_telegram_id_found(self, mock_uow: IUnitOfWork, sample_user: User):
        mock_uow.users.get_by.return_value = sample_user

        service = UserService(mock_uow)
        user = await service.get_user_by_telegram_id(sample_user.telegram_id)

        assert user == sample_user
        mock_uow.users.get_by.assert_called_once_with(True, telegram_id=sample_user.telegram_id)


    async def test_get_user_by_telegram_id_not_found(self, mock_uow: IUnitOfWork):
        mock_uow.users.get_by.return_value = None

        service = UserService(mock_uow)
        user = await service.get_user_by_telegram_id(999999999)

        assert user is None


    async def test_check_phone_exists(self, mock_uow: IUnitOfWork):
        mock_uow.users.exists_by.return_value = True

        service = UserService(mock_uow)
        exists = await service.check_phone("+998901234567")

        assert exists is True
        mock_uow.users.exists_by.assert_called_once_with(phone="+998901234567")


    async def test_check_phone_not_exists(self, mock_uow: IUnitOfWork):
        mock_uow.users.exists_by.return_value = False

        service = UserService(mock_uow)
        exists = await service.check_phone("+998999999999")

        assert exists is False


    async def test_update_weight_success(self, mock_uow: IUnitOfWork, sample_user: User):
        mock_uow.users.get_by.return_value = sample_user
        mock_uow.users.save = AsyncMock()

        service = UserService(mock_uow)
        updated_user = await service.update_weight(sample_user.id, 80.0)

        assert updated_user.profile.weight_kg == 80.0
        mock_uow.users.save.assert_called_once()
        mock_uow.commit.assert_called_once()


    async def test_update_weight_user_not_found(self, mock_uow: IUnitOfWork):
        mock_uow.users.get_by.return_value = None

        service = UserService(mock_uow)
        
        with pytest.raises(ValueError) as exc_info:
            await service.update_weight(uuid4(), 80.0)
        
        assert "не найдены" in str(exc_info.value)


    async def test_update_weight_profile_not_found(self, mock_uow: IUnitOfWork):
        user = User(
            id=uuid4(),
            username="testuser",
            phone="+998901234567",
            password_hash="hashed",
            telegram_id=123456789,
            profile=None,
        )
        mock_uow.users.get_by.return_value = user

        service = UserService(mock_uow)
        
        with pytest.raises(ValueError) as exc_info:
            await service.update_weight(user.id, 80.0)
        
        assert "не найдены" in str(exc_info.value)
