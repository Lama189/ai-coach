from uuid import UUID

from app.domain.identity.user import User, UserProfile
from app.infrastructure.postgres.unit_of_work import IUnitOfWork

class UserService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_user(self, username: str, password_hash: str, profile: UserProfile) -> User:
        if await self._uow.users.exists_by_username(username):
            raise ValueError(f"Username '{username}' уже занят")
        
        user = User(username=username, password_hash=password_hash)
        user.assighn_profile(profile)

        await self._uow.users.save(user)
        await self._uow.commit()
        return user
    
    async def get_user(self, user_id: UUID) -> User | None:
        return await self._uow.users.get_by_id(user_id)
    
    async def update_weight(self, user_id: UUID, new_weight: float) -> User:
        user = await self._uow.users.get_by_id(user_id)
        if not user or not user.profile:
            raise ValueError("Пользователь или профиль не найдены")
        
        user.profile.update_metrics(weight_kg=new_weight, height_cm=user.profile.height_cm)

        await self._uow.users.save(user)
        await self._uow.commit()
        return user