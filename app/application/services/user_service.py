from uuid import UUID

from app.core.security import SecurityUtils
from app.core.extensions import UserNotFoundError, InvalidPasswordError
from app.domain.identity.user import User, UserProfile
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.application.dto.identity import LoginDTO
from app.infrastructure.redis.repos.repository import RedisRepository
from app.application.dto.tokens import TokenResponseDTO
from app.application.dto.identity import UserCachedDTO


class UserService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_user(
        self,
        username: str,
        password_hash: str,
        phone: str,
        telegram_id: int,
        profile: UserProfile,
    ) -> User:
        if await self._uow.users.exists_by(username=username):
            raise ValueError(f"Username '{username}' уже занят")

        user = User(
            username=username,
            password_hash=password_hash,
            phone=phone,
            telegram_id=telegram_id,
        )
        user.assign_profile(profile)

        await self._uow.users.save(user)
        await self._uow.commit()
        return user

    async def get_user(self, user_id: UUID) -> User | None:
        return await self._uow.users.get_by(True, id=user_id)

    async def get_user_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self._uow.users.get_by(True, telegram_id=telegram_id)

    async def check_phone(self, phone: str) -> bool:
        return await self._uow.users.exists_by(phone=phone)

    async def update_weight(self, user_id: UUID, new_weight: float) -> User:
        user = await self._uow.users.get_by(True, id=user_id)

        if not user or not user.profile:
            raise ValueError("Пользователь или профиль не найдены")

        user.profile.update_metrics(
            weight_kg=new_weight,
            height_cm=user.profile.height_cm,
        )

        await self._uow.users.save(user)
        await self._uow.commit()
        return user
    

class AuthService:
    def __init__(self, uow: IUnitOfWork, redis: RedisRepository) -> None:
        self._uow = uow
        self._redis = redis

    async def login(self, dto: LoginDTO) -> TokenResponseDTO:
        user = await self._uow.users.get_by(True, phone=dto.phone)
        if not user:
            raise UserNotFoundError()


        if not SecurityUtils.verify_password(dto.password, user.password_hash):
            raise InvalidPasswordError()

        payload = {
            "sub": str(user.id),
            "telegram_id": user.telegram_id,
        }

        access_token = SecurityUtils.generate_access_token(payload)
        refresh_token = SecurityUtils.generate_refresh_token(payload)

        await self._redis.set_refresh_token(
            user_id=str(user.id),
            token=refresh_token,
        )

        await self._redis.set_user(
            user_id=str(user.id),
            user=UserCachedDTO.model_validate(user),
        )

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=user.id
        )

    async def refresh(self, refresh_token: str) -> TokenResponseDTO:
        payload = SecurityUtils.verify_token(refresh_token, expected_type="refresh")
        user_id = payload.get("sub")

        stored_token = await self._redis.get_refresh_token(user_id)
        if not stored_token or stored_token != refresh_token:
            raise ValueError("Refresh токен недействителен")

        new_access = SecurityUtils.generate_access_token({"sub": user_id})

        return TokenResponseDTO(
            access_token=new_access,
            refresh_token=refresh_token,
            user_id=user_id
        )

    async def logout(self, user_id: str) -> None:
        await self._redis.delete_refresh_token(user_id)
        await self._redis.delete_user(user_id)