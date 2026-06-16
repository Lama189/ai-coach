import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.identity.insight import UserInsight
from app.domain.enums import InsightTag
from app.infrastructure.postgres.repos.insights import PostgresUserInsightRepository
from app.infrastructure.postgres.models.insights import UserInsight as UserInsightModel


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    return PostgresUserInsightRepository(mock_session)


@pytest.fixture
def sample_insight():
    return UserInsight(
        user_id=uuid4(),
        content="Травма колена",
        tag=InsightTag.injury,
    )


class TestPostgresUserInsightRepository:
    async def test_save_new_insight(self, repo, mock_session, sample_insight):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await repo.save(sample_insight, embedding=[0.1] * 384)

        mock_session.add.assert_called_once()
        added_model = mock_session.add.call_args[0][0]
        assert isinstance(added_model, UserInsightModel)
        assert added_model.content == "Травма колена"
        assert added_model.tag == InsightTag.injury
        mock_session.flush.assert_called_once()

    async def test_save_existing_insight(self, repo, mock_session, sample_insight):
        existing_model = MagicMock(spec=UserInsightModel)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_model
        mock_session.execute.return_value = mock_result

        new_insight = UserInsight(
            id=sample_insight.id,
            user_id=sample_insight.user_id,
            content="Обновлённый контент",
            tag=InsightTag.progress,
        )

        await repo.save(new_insight, embedding=[0.2] * 384)

        assert existing_model.content == "Обновлённый контент"
        assert existing_model.tag == InsightTag.progress
        mock_session.add.assert_not_called()

    async def test_search_by_user_id(self, repo, mock_session):
        mock_model = MagicMock(spec=UserInsightModel)
        mock_model.id = uuid4()
        mock_model.user_id = uuid4()
        mock_model.content = "Test"
        mock_model.tag = InsightTag.injury

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.execute.return_value = mock_result

        results = await repo.search_by(user_id=uuid4())

        assert len(results) == 1
        assert results[0].content == "Test"

    async def test_search_by_tags(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.search_by(
            user_id=uuid4(),
            tags=[InsightTag.injury, InsightTag.progress],
        )

        mock_session.execute.assert_called_once()

    async def test_search_by_embedding(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.search_by(
            user_id=uuid4(),
            query_embedding=[0.1] * 384,
        )

        mock_session.execute.assert_called_once()

    async def test_search_by_limit(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.search_by(user_id=uuid4(), limit=10)

        mock_session.execute.assert_called_once()

    async def test_update_insight(self, repo, mock_session):
        insight_id = uuid4()
        mock_model = MagicMock(spec=UserInsightModel)
        mock_session.get.return_value = mock_model

        await repo.update(insight_id, content="Updated", tag=InsightTag.progress)

        assert mock_model.content == "Updated"
        assert mock_model.tag == InsightTag.progress
        mock_session.flush.assert_called_once()

    async def test_update_insight_not_found(self, repo, mock_session):
        mock_session.get.return_value = None

        with pytest.raises(ValueError, match="Инсайт не найден"):
            await repo.update(uuid4(), content="test")

    async def test_delete_insight(self, repo, mock_session):
        mock_model = MagicMock(spec=UserInsightModel)
        mock_session.get.return_value = mock_model

        await repo.delete(uuid4())

        mock_session.delete.assert_called_once_with(mock_model)
        mock_session.flush.assert_called_once()

    async def test_delete_nonexistent_insight(self, repo, mock_session):
        mock_session.get.return_value = None

        await repo.delete(uuid4())

        mock_session.delete.assert_not_called()
