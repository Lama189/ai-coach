import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.application.services.insight_service import InsightService
from app.application.dto.identity import CreateInsightDTO
from app.domain.enums import InsightTag
from app.infrastructure.ai.embedding_service import SentenceTransformerEmbeddingService


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.insights = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_embedder():
    embedder = AsyncMock(spec=SentenceTransformerEmbeddingService)
    embedder.get_embedding.return_value = [0.1] * 384
    return embedder


class TestInsightService:
    async def test_create_insight_success(self, mock_uow, mock_embedder):
        dto = CreateInsightDTO(
            content="Травма колена",
            tag=InsightTag.injury,
        )
        user_id = uuid4()

        service = InsightService(mock_uow, mock_embedder)
        insight = await service.create_insight(user_id, dto)

        assert insight.content == "Травма колена"
        assert insight.tag == InsightTag.injury
        assert insight.user_id == user_id
        mock_embedder.get_embedding.assert_called_once_with("injury Травма колена")
        mock_uow.insights.save.assert_called_once()
        mock_uow.commit.assert_called_once()

    async def test_create_insight_different_tags(self, mock_uow, mock_embedder):
        for tag in InsightTag:
            dto = CreateInsightDTO(content=f"Test {tag.value}", tag=tag)
            service = InsightService(mock_uow, mock_embedder)
            insight = await service.create_insight(uuid4(), dto)
            assert insight.tag == tag
