from uuid import UUID
from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.domain.interfaces.identity import IUserRepository
from app.infrastructure.postgres.models.users import User as UserModel
from app.infrastructure.postgres.models.profiles import UserProfile as UserProfileModel


class PostgresUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    

    async def save(self, user: User) -> None:
        existing = await self._session.get(UserModel, user.id)

        if existing is None:
            model = self._to_model(user)
            self._session.add(model)
        else:
            existing.username = user.username
            existing.phone = user.phone
            existing.telegram_id = user.telegram_id
            existing.password_hash = user.password_hash
            existing.updated_at = user.updated_at
            
            if user.profile and existing.profile:
                existing.profile.gender = user.profile.gender
                existing.profile.age = user.profile.age
                existing.profile.height_cm = user.profile.height_cm
                existing.profile.weight_kg = user.profile.weight_kg
                existing.profile.goal = user.profile.goal
                existing.profile.experience_level = user.profile.experience_level
                existing.profile.updated_at = user.profile.updated_at
            elif user.profile and not existing.profile:
                existing.profile = self._profile_to_model(user.profile, user.id)

        await self._session.flush()
    

    async def get_by(self, with_relations: bool = True, **kwargs) -> User | None:
        stmt = select(UserModel).filter_by(**kwargs)

        if with_relations:
            stmt = stmt.options(
                selectinload(UserModel.profile),
                selectinload(UserModel.sessions),
                selectinload(UserModel.workout_programs),
            )

        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None
    

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(UserModel).filter_by(**kwargs).exists())

        result = await self._session.execute(stmt)
        return bool(result.scalar())
    

    async def delete(self, user_id: UUID) -> None:
        model = await self._session.get(UserModel, user_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()


    def _to_domain(self, model: UserModel) -> User:
        profile = None
        if model.profile:
            profile = UserProfile(
                gender=model.profile.gender,
                age=model.profile.age,
                height_cm=model.profile.height_cm,
                weight_kg=model.profile.weight_kg,
                goal=model.profile.goal,
                experience_level=model.profile.experience_level,
                created_at=model.profile.created_at,
                updated_at=model.profile.updated_at,
            )

        return User(
            id=model.id,
            username=model.username,
            phone=model.phone,
            telegram_id=model.telegram_id,
            password_hash=model.password_hash,
            profile=profile,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


    def _to_model(self, user: User) -> UserModel:
        model = UserModel(
            id=user.id,
            username=user.username,
            phone=user.phone,
            telegram_id=user.telegram_id,
            password_hash=user.password_hash,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        
        if user.profile:
            model.profile = self._profile_to_model(user.profile, user.id)
        return model
    

    @staticmethod
    def _profile_to_model(profile: UserProfile, user_id: UUID) -> UserProfileModel:
        return UserProfileModel(
            user_id=user_id,
            gender=profile.gender,
            age=profile.age,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
            goal=profile.goal,
            experience_level=profile.experience_level,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )