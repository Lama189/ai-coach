import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.program import WorkoutProgram
from app.infrastructure.postgres.repos.programs import PostgresWorkoutProgramRepository
from app.infrastructure.postgres.models.workout_programs import WorkoutProgram as WorkoutProgramModel


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    return PostgresWorkoutProgramRepository(mock_session)


@pytest.fixture
def sample_program():
    return WorkoutProgram(
        user_id=uuid4(),
        name="Test Program",
        description="A test program",
        is_active=True,
    )


class TestPostgresWorkoutProgramRepository:
    async def test_save_new_program(self, repo, mock_session, sample_program):
        mock_session.get.return_value = None

        await repo.save(sample_program)

        mock_session.add.assert_called_once()
        added_model = mock_session.add.call_args[0][0]
        assert isinstance(added_model, WorkoutProgramModel)
        assert added_model.name == "Test Program"

    async def test_save_existing_program(self, repo, mock_session, sample_program):
        existing_model = MagicMock(spec=WorkoutProgramModel)
        mock_session.get.return_value = existing_model

        await repo.save(sample_program, task_id=uuid4())

        assert existing_model.name == "Test Program"
        assert existing_model.is_active is True
        mock_session.add.assert_not_called()

    async def test_save_existing_program_with_task_id(self, repo, mock_session, sample_program):
        task_id = uuid4()
        existing_model = MagicMock(spec=WorkoutProgramModel)
        mock_session.get.return_value = existing_model

        await repo.save(sample_program, task_id=task_id)

        assert existing_model.task_id == task_id

    async def test_get_actual_by_user_id_found(self, repo, mock_session, sample_program):
        mock_model = MagicMock(spec=WorkoutProgramModel)
        mock_model.id = sample_program.id
        mock_model.user_id = sample_program.user_id
        mock_model.name = sample_program.name
        mock_model.description = sample_program.description
        mock_model.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repo.get_actual_by_user_id(sample_program.user_id)

        assert result is not None
        assert result.name == "Test Program"
        assert result.is_active is True

    async def test_get_actual_by_user_id_not_found(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_actual_by_user_id(uuid4())

        assert result is None

    async def test_get_by_task_id_found(self, repo, mock_session):
        task_id = uuid4()
        mock_model = MagicMock(spec=WorkoutProgramModel)
        mock_model.id = uuid4()
        mock_model.user_id = uuid4()
        mock_model.name = "Program"
        mock_model.description = "desc"
        mock_model.is_active = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_model
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_task_id(task_id)

        assert result is not None
        assert result.name == "Program"

    async def test_get_by_task_id_not_found(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_task_id(uuid4())

        assert result is None

    async def test_deactivate_all_for_user(self, repo, mock_session):
        user_id = uuid4()

        await repo.deactivate_all_for_user(user_id)

        mock_session.execute.assert_called_once()

    async def test_to_domain(self, repo, sample_program):
        mock_model = MagicMock(spec=WorkoutProgramModel)
        mock_model.id = sample_program.id
        mock_model.user_id = sample_program.user_id
        mock_model.name = "Test"
        mock_model.description = "desc"
        mock_model.is_active = True

        domain = repo._to_domain(mock_model)

        assert domain.name == "Test"
        assert domain.is_active is True

    async def test_to_model(self, repo, sample_program):
        model = repo._to_model(sample_program, task_id=None)

        assert isinstance(model, WorkoutProgramModel)
        assert model.name == "Test Program"
        assert model.task_id is None
