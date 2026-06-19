from uuid import UUID

from app.domain.identity.user_schedule import UserSchedule
from app.application.interfaces.unit_of_work import IUnitOfWork


class UserScheduleService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow


    async def create_schedule(
        self,
        user_id: UUID,
        day_of_week: int,
        training_day_number: int,
    ) -> UserSchedule:
        schedule = UserSchedule(
            user_id=user_id,
            day_of_week=day_of_week,
            training_day_number=training_day_number,
        )
        await self._uow.user_schedules.save(schedule)
        await self._uow.commit()
        return schedule


    async def get_schedule(self, schedule_id: UUID) -> UserSchedule | None:
        return await self._uow.user_schedules.get_by_id(schedule_id)


    async def get_by_day(self, user_id: UUID, day_of_week: int) -> UserSchedule | None:
        results = await self._uow.user_schedules.search_by(
            user_id=user_id, day_of_week=day_of_week,
        )
        return results[0] if results else None


    async def search_schedules(
        self,
        user_id: UUID | None = None,
        day_of_week: int | None = None,
        training_day_number: int | None = None,
    ) -> list[UserSchedule]:
        return await self._uow.user_schedules.search_by(
            user_id=user_id,
            day_of_week=day_of_week,
            training_day_number=training_day_number,
        )


    async def list_all_by_user(self, user_id: UUID) -> list[UserSchedule]:
        return await self._uow.user_schedules.search_by(user_id=user_id)


    async def delete_schedule(self, schedule_id: UUID) -> None:
        await self._uow.user_schedules.delete(schedule_id)
        await self._uow.commit()


    async def delete_by_day(self, user_id: UUID, day_of_week: int) -> None:
        results = await self._uow.user_schedules.search_by(
            user_id=user_id, day_of_week=day_of_week,
        )
        for s in results:
            await self._uow.user_schedules.delete(s.id)
        await self._uow.commit()
