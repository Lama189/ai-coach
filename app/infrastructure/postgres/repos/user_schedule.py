from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.user_schedule import UserSchedule
from app.application.interfaces.user_schedule import IUserScheduleRepository
from app.infrastructure.postgres.models.user_schedule import UserSchedule as UserScheduleModel


class PostgresUserScheduleRepository(IUserScheduleRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session


    async def save(self, schedule: UserSchedule) -> None:
        existing = await self._session.get(UserScheduleModel, schedule.id)

        if existing is None:
            model = self._to_model(schedule)
            self._session.add(model)
        else:
            existing.user_id = schedule.user_id
            existing.day_of_week = schedule.day_of_week
            existing.training_day_number = schedule.training_day_number

        await self._session.flush()


    async def get_by_id(self, schedule_id: UUID) -> UserSchedule | None:
        model = await self._session.get(UserScheduleModel, schedule_id)
        return self._to_domain(model) if model else None


    async def delete(self, schedule_id: UUID) -> None:
        model = await self._session.get(UserScheduleModel, schedule_id)
        if model:
            await self._session.delete(model)
            await self._session.flush()


    async def search_by(
        self,
        user_id: UUID | None = None,
        day_of_week: int | None = None,
        training_day_number: int | None = None,
    ) -> list[UserSchedule]:
        stmt = select(UserScheduleModel)

        if user_id is not None:
            stmt = stmt.where(UserScheduleModel.user_id == user_id)
        if day_of_week is not None:
            stmt = stmt.where(UserScheduleModel.day_of_week == day_of_week)
        if training_day_number is not None:
            stmt = stmt.where(UserScheduleModel.training_day_number == training_day_number)

        stmt = stmt.order_by(UserScheduleModel.day_of_week)

        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_domain(m) for m in models]


    def _to_domain(self, model: UserScheduleModel) -> UserSchedule:
        return UserSchedule(
            id=model.id,
            user_id=model.user_id,
            day_of_week=model.day_of_week,
            training_day_number=model.training_day_number,
        )


    def _to_model(self, schedule: UserSchedule) -> UserScheduleModel:
        return UserScheduleModel(
            id=schedule.id,
            user_id=schedule.user_id,
            day_of_week=schedule.day_of_week,
            training_day_number=schedule.training_day_number,
        )
