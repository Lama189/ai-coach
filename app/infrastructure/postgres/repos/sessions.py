from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.session import WorkoutSessionDomain
from app.infrastructure.postgres.models.session import Session as WorkoutSessionModel
from app.application.interfaces.session import ISessionRepository


#TODO: Доделать
class PostgresSessionsRepository(ISessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    
    async def save(self, session: WorkoutSessionDomain) -> None:
        existing = await self._session.get(WorkoutSessionModel, session.id)

        if existing is None:
            model = self._to_model(session)
            self._session.add(model)
        else:
            existing.user_id = session.user_id
            existing.status = session.status

            if existing.program_id is not None:
                existing.program_id = session.program_id 

    
    async def get_by(self, with_relations: bool = True, **kwargs) -> WorkoutSessionDomain | None:
        ...


    def _to_model(self, model: WorkoutSessionDomain) -> WorkoutSessionModel:
        return WorkoutSessionModel(
            id=model.id,
            user_id=model.user_id,
            program_id=model.program_id,
            status=model.status
        )
    

    def _to_domain(self, model: WorkoutSessionModel) -> WorkoutSessionDomain:
        return WorkoutSessionModel(
            id=model.id,
            user_id=model.user_id,
            program_id=model.program_id,
            status=model.status,
            started_at=model.started_at,
            finished_at=model.finished_at
        )