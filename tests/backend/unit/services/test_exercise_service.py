import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.domain.training.exercise import Exercise
from app.domain.enums import MuscleGroup
from app.application.services.exercise_service import ExerciseService
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService


@pytest.fixture
def mock_embedder():
    return AsyncMock(spec=SentenceTransformerEmbeddingService)


@pytest.mark.asyncio
class TestExerciseService:
    async def test_create_exercise_success(self, mock_uow: IUnitOfWork, mock_embedder: SentenceTransformerEmbeddingService):
        mock_uow.exercises.get_by.return_value = None
        mock_uow.exercises.find_familiar.return_value = None
        mock_uow.exercises.save_exercise = AsyncMock()
        mock_embedder.get_embedding.return_value = [0.1] * 384

        service = ExerciseService(mock_uow, mock_embedder)

        exercise = await service.create_exercise(
            name="Bench Press",
            muscle_group=MuscleGroup.CHEST,
            description="Classic chest exercise"
        )

        assert exercise.name == "Bench Press"
        assert exercise.muscle_group == MuscleGroup.CHEST
        mock_uow.exercises.save_exercise.assert_called_once()
        mock_uow.commit.assert_called_once()

    async def test_create_exercise_name_taken(self, mock_uow: IUnitOfWork, mock_embedder: SentenceTransformerEmbeddingService):
        existing_exercise = Exercise(
            id=uuid4(),
            name="Bench Press",
            muscle_group=MuscleGroup.CHEST,
        )
        mock_uow.exercises.get_by.return_value = existing_exercise

        service = ExerciseService(mock_uow, mock_embedder)

        with pytest.raises(ValueError) as exc_info:
            await service.create_exercise(
                name="Bench Press",
                muscle_group=MuscleGroup.CHEST,
            )
        
        assert "уже занято" in str(exc_info.value)
        mock_uow.exercises.save_exercise.assert_not_called()

    async def test_create_exercise_similar_exists(self, mock_uow: IUnitOfWork, mock_embedder: SentenceTransformerEmbeddingService):
        mock_uow.exercises.get_by.return_value = None
        mock_embedder.get_embedding.return_value = [0.1] * 384

        similar_exercise = Exercise(
            id=uuid4(),
            name="Bench Press",
            muscle_group=MuscleGroup.CHEST,
        )
        mock_uow.exercises.find_familiar.return_value = similar_exercise

        service = ExerciseService(mock_uow, mock_embedder)

        with pytest.raises(ValueError) as exc_info:
            await service.create_exercise(
                name="Barbell Bench Press",
                muscle_group=MuscleGroup.CHEST,
            )
        
        assert "Такое упражнение уже существует" in str(exc_info.value)
        mock_uow.exercises.save_exercise.assert_not_called()

    async def test_get_exercise_found(self, mock_uow: IUnitOfWork, mock_embedder: SentenceTransformerEmbeddingService, sample_exercise: Exercise):
        mock_uow.exercises.get_by.return_value = sample_exercise

        service = ExerciseService(mock_uow, mock_embedder)
        exercise = await service.get_exercise(sample_exercise.id)

        assert exercise == sample_exercise
        mock_uow.exercises.get_by.assert_called_once_with(id=sample_exercise.id)

    async def test_get_exercise_not_found(self, mock_uow: IUnitOfWork, mock_embedder: SentenceTransformerEmbeddingService):
        mock_uow.exercises.get_by.return_value = None

        service = ExerciseService(mock_uow, mock_embedder)
        exercise = await service.get_exercise(uuid4())

        assert exercise is None

    async def test_delete_exercise_success(self, mock_uow: IUnitOfWork, mock_embedder: SentenceTransformerEmbeddingService, sample_exercise: Exercise):
        mock_uow.exercises.get_by.return_value = sample_exercise
        mock_uow.exercises.delete = AsyncMock()

        service = ExerciseService(mock_uow, mock_embedder)
        await service.delete_exercise(sample_exercise.id)

        mock_uow.exercises.delete.assert_called_once_with(sample_exercise.id)
        mock_uow.commit.assert_called_once()

    async def test_delete_exercise_not_found(self, mock_uow: IUnitOfWork, mock_embedder: SentenceTransformerEmbeddingService):
        mock_uow.exercises.get_by.return_value = None

        service = ExerciseService(mock_uow, mock_embedder)

        with pytest.raises(ValueError) as exc_info:
            await service.delete_exercise(uuid4())
        
        assert "не найдено" in str(exc_info.value)
        mock_uow.exercises.delete.assert_not_called()

    async def test_search(self, mock_uow: IUnitOfWork, mock_embedder: SentenceTransformerEmbeddingService):
        mock_uow.exercises.search.return_value = []

        service = ExerciseService(mock_uow, mock_embedder)
        exercises = await service.search(query="Bench", muscle_group=MuscleGroup.CHEST)

        assert exercises == []
        mock_uow.exercises.search.assert_called_once_with(
            query="Bench",
            muscle_group=MuscleGroup.CHEST,
            limit=50,
            offset=0
        )
