import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from fastapi import HTTPException

from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.application.services.user_service import AuthService
from app.application.dto.identity import LoginDTO
from app.core.extensions import UserNotFoundError, InvalidPasswordError
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.redis.repos.repository import RedisRepository
from app.core.security import SecurityUtils


@pytest.mark.asyncio
class TestAuthService:
    @pytest.fixture
    def auth_service(self, mock_uow: IUnitOfWork, mock_redis_repo: RedisRepository):
        return AuthService(mock_uow, mock_redis_repo)

    async def test_login_success(self, auth_service: AuthService, mock_uow: IUnitOfWork, mock_redis_repo: RedisRepository, sample_user: User):
        mock_uow.users.get_by.return_value = sample_user

        with patch.object(SecurityUtils, "verify_password", return_value=True), \
             patch.object(SecurityUtils, "generate_access_token", return_value="access_token"), \
             patch.object(SecurityUtils, "generate_refresh_token", return_value="refresh_token"):
            
            login_dto = LoginDTO(
                phone="+998901234567",
                password="correct_password",
                telegram_id=123456789,
            )
            
            result = await auth_service.login(login_dto)

            assert result.access_token == "access_token"
            assert result.refresh_token == "refresh_token"
            mock_redis_repo.set_refresh_token.assert_called_once()
            mock_redis_repo.set_user.assert_called_once()

    async def test_login_user_not_found(self, auth_service: AuthService, mock_uow: IUnitOfWork):
        mock_uow.users.get_by.return_value = None

        login_dto = LoginDTO(
            phone="+998901234567",
            password="password",
            telegram_id=123456789,
        )

        with pytest.raises(UserNotFoundError):
            await auth_service.login(login_dto)

    async def test_login_invalid_password(self, auth_service: AuthService, mock_uow: IUnitOfWork, sample_user: User):
        mock_uow.users.get_by.return_value = sample_user

        with patch.object(SecurityUtils, "verify_password", return_value=False):
            login_dto = LoginDTO(
                phone="+998901234567",
                password="wrong_password",
                telegram_id=123456789,
            )

            with pytest.raises(InvalidPasswordError):
                await auth_service.login(login_dto)

    async def test_refresh_success(self, auth_service: AuthService, mock_redis_repo: RedisRepository):
        user_id = str(uuid4())
        refresh_token = "valid_refresh_token"

        mock_redis_repo.get_refresh_token.return_value = refresh_token

        with patch.object(SecurityUtils, "verify_token", return_value={"sub": user_id, "type": "refresh"}), \
             patch.object(SecurityUtils, "generate_access_token", return_value="new_access_token"):
            
            result = await auth_service.refresh(refresh_token)

            assert result.access_token == "new_access_token"
            assert result.refresh_token == refresh_token

    async def test_refresh_invalid_token(self, auth_service: AuthService, mock_redis_repo: RedisRepository):
        mock_redis_repo.get_refresh_token.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh("invalid_token")
        
        assert exc_info.value.status_code == 401

    async def test_logout_success(self, auth_service: AuthService, mock_redis_repo: RedisRepository):
        user_id = str(uuid4())

        await auth_service.logout(user_id)

        mock_redis_repo.delete_refresh_token.assert_called_once_with(user_id)
        mock_redis_repo.delete_user.assert_called_once_with(user_id)
