from uuid import UUID

from app.domain.training.exercise import Exercise
from app.domain.enums import MuscleGroup
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService

class ExerciseService:
    def __init__(self, uow: IUnitOfWork, embedder: SentenceTransformerEmbeddingService) -> None:
        self._uow = uow
        self._embedder = embedder 


    async def create_exercise(
        self, 
        name: str, 
        muscle_group: MuscleGroup, 
        description: str | None = None
    ) -> Exercise:
        if await self._uow.exercises.get_by_name(name):
            raise ValueError(f"Название упражнения '{name}' уже занято")
        
        embedding = await self._embedder.get_embedding(f"{name} {muscle_group}")
        similar = await self._uow.exercises.find_familiar(embedding)
        if similar:
            raise ValueError(f"Такое упражнение уже существует: f{similar.name}")
        
        exercise = Exercise(name=name, muscle_group=muscle_group, description=description)

        await self._uow.exercises.save_exercise(exercise, embedding)
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