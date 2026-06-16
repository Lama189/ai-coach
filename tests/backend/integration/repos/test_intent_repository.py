import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.intents import UserIntent
from app.domain.enums import MuscleGroup, Location
from app.infrastructure.postgres.repos.intents import PostgresUserIntentRepository
from app.infrastructure.postgres.models.intents import UserIntentModel


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    return PostgresUserIntentRepository(mock_session)


@pytest.fixture
def sample_intent():
    return UserIntent(
        user_id=uuid4(),
        goal="Набор массы",
        constraints=["no_knee_load"],
        focus_areas=[MuscleGroup.CHEST, MuscleGroup.BACK],
        location=Location.gym,
        context="Тренируюсь 3 раза в неделю",
        program_id=None,
    )


class TestPostgresUserIntentRepository:
    async def test_save_intent(self, repo, mock_session, sample_intent):
        await repo.save(sample_intent, embedding=[0.1] * 384)

        mock_session.add.assert_called_once()
        added_model = mock_session.add.call_args[0][0]
        assert isinstance(added_model, UserIntentModel)
        assert added_model.goal == "Набор массы"
        assert added_model.location == "gym"
        mock_session.flush.assert_called_once()

    async def test_save_intent_without_embedding(self, repo, mock_session, sample_intent):
        await repo.save(sample_intent, embedding=None)

        mock_session.add.assert_called_once()
        added_model = mock_session.add.call_args[0][0]
        assert added_model.embedding is None

    async def test_get_by_user(self, repo, mock_session):
        mock_model = MagicMock(spec=UserIntentModel)
        mock_model.id = uuid4()
        mock_model.user_id = uuid4()
        mock_model.goal = "Test"
        mock_model.constraints = []
        mock_model.focus_areas = []
        mock_model.location = "gym"
        mock_model.context = ""
        mock_model.program_id = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.execute.return_value = mock_result

        intents = await repo.get_by_user(uuid4())

        assert len(intents) == 1
        assert intents[0].goal == "Test"

    async def test_get_by_user_empty(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        intents = await repo.get_by_user(uuid4())

        assert intents == []

    async def test_update_intent(self, repo, mock_session):
        intent_id = uuid4()
        mock_model = MagicMock(spec=UserIntentModel)
        mock_session.get.return_value = mock_model

        await repo.update(intent_id, goal="New goal", context="New context")

        assert mock_model.goal == "New goal"
        assert mock_model.context == "New context"
        mock_session.flush.assert_called_once()

    async def test_update_intent_not_found(self, repo, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(ValueError, match="Интент не найден"):
            await repo.update(uuid4(), goal="test")

    async def test_delete_intent(self, repo, mock_session):
        mock_model = MagicMock(spec=UserIntentModel)
        mock_session.get.return_value = mock_model

        await repo.delete(uuid4())

        mock_session.delete.assert_called_once_with(mock_model)
        mock_session.flush.assert_called_once()

    async def test_delete_nonexistent_intent(self, repo, mock_session):
        mock_session.get.return_value = None

        await repo.delete(uuid4())

        mock_session.delete.assert_not_called()

    async def test_to_domain(self, repo):
        mock_model = MagicMock(spec=UserIntentModel)
        mock_model.id = uuid4()
        mock_model.user_id = uuid4()
        mock_model.goal = "Test"
        mock_model.constraints = ["no_knee_load"]
        mock_model.focus_areas = ["chest"]
        mock_model.location = "gym"
        mock_model.context = "context"
        mock_model.program_id = None

        domain = repo._to_domain(mock_model)

        assert domain.goal == "Test"
        assert domain.constraints == ["no_knee_load"]
        assert domain.location == "gym"
