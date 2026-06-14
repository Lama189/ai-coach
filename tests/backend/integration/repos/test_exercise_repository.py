import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.exercise import Exercise
from app.domain.enums import MuscleGroup, MovementPattern
from app.infrastructure.postgres.repos.exercises import PostgresExerciseRepository
from app.infrastructure.postgres.models.exercises import Exercise as ExerciseModel


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def exercise_repository(mock_session):
    return PostgresExerciseRepository(mock_session)


@pytest.mark.asyncio
class TestPostgresExerciseRepository:
    async def test_get_by_found(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession, sample_exercise: Exercise):
        mock_model = MagicMock(spec=ExerciseModel)
        mock_model.id = sample_exercise.id
        mock_model.name = sample_exercise.name
        mock_model.muscle_group = sample_exercise.muscle_group.value
        mock_model.equipment = sample_exercise.equipment
        mock_model.movement_patterns = [p.value for p in sample_exercise.movement_patterns]
        mock_model.description = sample_exercise.description

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        exercise = await exercise_repository.get_by(id=sample_exercise.id)

        assert exercise is not None
        assert exercise.name == sample_exercise.name
        assert exercise.muscle_group == sample_exercise.muscle_group
        assert exercise.equipment == sample_exercise.equipment
        assert exercise.movement_patterns == sample_exercise.movement_patterns
        mock_session.execute.assert_called_once()

    async def test_get_by_not_found(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        exercise = await exercise_repository.get_by(id=uuid4())

        assert exercise is None

    async def test_save_new_exercise(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession, sample_exercise: Exercise):
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        await exercise_repository.save_exercise(sample_exercise, embedding=[0.1] * 384)

        mock_session.add.assert_called_once()

    async def test_save_existing_exercise(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession, sample_exercise: Exercise):
        existing_model = MagicMock(spec=ExerciseModel)
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = existing_model
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        await exercise_repository.save_exercise(sample_exercise, embedding=[0.1] * 384)

        assert existing_model.muscle_group == sample_exercise.muscle_group
        mock_session.add.assert_not_called()

    async def test_delete_existing_exercise(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_model = MagicMock(spec=ExerciseModel)
        mock_session.get.return_value = mock_model
        mock_session.delete = AsyncMock()
        mock_session.flush = AsyncMock()

        await exercise_repository.delete(uuid4())

        mock_session.delete.assert_called_once_with(mock_model)
        mock_session.flush.assert_called_once()

    async def test_delete_nonexistent_exercise(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_session.get.return_value = None
        mock_session.delete = AsyncMock()

        await exercise_repository.delete(uuid4())

        mock_session.delete.assert_not_called()

    async def test_search_with_query(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_model = MagicMock(spec=ExerciseModel)
        mock_model.id = uuid4()
        mock_model.name = "Bench Press"
        mock_model.muscle_group = "chest"
        mock_model.description = "Test"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.execute.return_value = mock_result

        exercises = await exercise_repository.search(query="Bench")

        assert len(exercises) == 1
        assert exercises[0].name == "Bench Press"

    async def test_search_with_muscle_group(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        exercises = await exercise_repository.search(muscle_group=MuscleGroup.CHEST)

        assert len(exercises) == 0

    async def test_get_by_ids(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_model = MagicMock(spec=ExerciseModel)
        mock_model.id = uuid4()
        mock_model.name = "Squat"
        mock_model.muscle_group = "legs"
        mock_model.description = "Leg exercise"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.execute.return_value = mock_result

        exercises = await exercise_repository.get_by_ids([uuid4()])

        assert len(exercises) == 1

    async def test_get_by_ids_empty(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        exercises = await exercise_repository.get_by_ids([])

        assert exercises == []
        mock_session.execute.assert_not_called()

    async def test_search_relevant_basic(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_model = MagicMock(spec=ExerciseModel)
        mock_model.id = uuid4()
        mock_model.name = "Bench Press"
        mock_model.muscle_group = "chest"
        mock_model.equipment = "barbell"
        mock_model.movement_patterns = ["push_horizontal"]
        mock_model.description = "Chest exercise"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.execute.return_value = mock_result

        exercises = await exercise_repository.search_relevant(
            muscle_groups=["chest"],
            excluded_patterns=[],
            excluded_equipment=[],
            embedding=None,
            limit=50,
        )

        assert len(exercises) == 1
        assert exercises[0].name == "Bench Press"
        assert exercises[0].muscle_group == MuscleGroup.CHEST
        assert exercises[0].movement_patterns == [MovementPattern.PUSH_HORIZONTAL]

    async def test_search_relevant_no_results(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        exercises = await exercise_repository.search_relevant(
            muscle_groups=["chest"],
            excluded_patterns=[],
            excluded_equipment=[],
            embedding=None,
            limit=50,
        )

        assert exercises == []

    async def test_search_relevant_with_excluded_patterns(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await exercise_repository.search_relevant(
            muscle_groups=["chest", "legs"],
            excluded_patterns=["push_vertical", "squat"],
            excluded_equipment=[],
            embedding=None,
            limit=50,
        )

        mock_session.execute.assert_called_once()

    async def test_search_relevant_with_excluded_equipment(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await exercise_repository.search_relevant(
            muscle_groups=["chest"],
            excluded_patterns=[],
            excluded_equipment=["barbell"],
            embedding=None,
            limit=50,
        )

        mock_session.execute.assert_called_once()

    async def test_search_relevant_with_embedding(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_model = MagicMock(spec=ExerciseModel)
        mock_model.id = uuid4()
        mock_model.name = "Push Up"
        mock_model.muscle_group = "chest"
        mock_model.equipment = "bodyweight"
        mock_model.movement_patterns = ["push_horizontal"]
        mock_model.description = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.execute.return_value = mock_result

        embedding = [0.1] * 384

        exercises = await exercise_repository.search_relevant(
            muscle_groups=["chest"],
            excluded_patterns=[],
            excluded_equipment=[],
            embedding=embedding,
            limit=10,
        )

        assert len(exercises) == 1
        assert exercises[0].description is None
        mock_session.execute.assert_called_once()

    async def test_search_relevant_limit(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await exercise_repository.search_relevant(
            muscle_groups=["chest"],
            excluded_patterns=[],
            excluded_equipment=[],
            embedding=None,
            limit=5,
        )

        mock_session.execute.assert_called_once()

    async def test_search_relevant_multiple_muscle_groups(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_model_1 = MagicMock(spec=ExerciseModel)
        mock_model_1.id = uuid4()
        mock_model_1.name = "Bench Press"
        mock_model_1.muscle_group = "chest"
        mock_model_1.equipment = "barbell"
        mock_model_1.movement_patterns = ["push_horizontal"]
        mock_model_1.description = "Chest"

        mock_model_2 = MagicMock(spec=ExerciseModel)
        mock_model_2.id = uuid4()
        mock_model_2.name = "Squat"
        mock_model_2.muscle_group = "legs"
        mock_model_2.equipment = "barbell"
        mock_model_2.movement_patterns = ["squat"]
        mock_model_2.description = "Legs"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model_1, mock_model_2]
        mock_session.execute.return_value = mock_result

        exercises = await exercise_repository.search_relevant(
            muscle_groups=["chest", "legs"],
            excluded_patterns=[],
            excluded_equipment=[],
            embedding=None,
            limit=50,
        )

        assert len(exercises) == 2

    async def test_search_relevant_all_filters(self, exercise_repository: PostgresExerciseRepository, mock_session: AsyncSession):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        exercises = await exercise_repository.search_relevant(
            muscle_groups=["chest", "back"],
            excluded_patterns=["push_vertical"],
            excluded_equipment=["barbell"],
            embedding=[0.1] * 384,
            limit=20,
        )

        assert exercises == []
        mock_session.execute.assert_called_once()
