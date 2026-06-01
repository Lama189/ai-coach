from uuid import UUID

from app.domain.training.exercise import Exercise
from app.domain.enums import MuscleGroup
from app.infrastructure.postgres.unit_of_work import IUnitOfWork


class ExerciseService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow


    async def create_exercise(
        self, 
        name: str, 
        muscle_group: MuscleGroup, 
        description: str | None = None
    ) -> Exercise:
        if await self._uow.exercises.exists(name):
            raise ValueError(f"Название упражнения '{name}' уже занято")
        
        exercise = Exercise(name=name, muscle_group=muscle_group, description=description)

        await self._uow.exercises.save_exercise(exercise)
        await self._uow.commit()
        return exercise
    

    async def get_exercise(self, exercise_id: int) -> Exercise | None:
        return await self._uow.exercises.get_by_id(exercise_id)
    

    async def search(
        self,
        query: str | None = None,
        muscle_group: MuscleGroup | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Exercise]:
        return await self._uow.exercises.search(
            query=query,
            muscle_group=muscle_group,
            limit=limit,
            offset=offset
        )