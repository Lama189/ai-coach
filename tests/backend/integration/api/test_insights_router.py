import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.application.dependencies import get_uow, get_embedding_service, get_current_user
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.domain.enums import UserGender, FitnessGoal, ExperienceLevel


@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)
    uow.insights = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_embedder():
    embedder = AsyncMock()
    embedder.get_embedding.return_value = [0.1] * 384
    return embedder


@pytest.fixture
def current_user():
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        username="admin",
        phone="+998901111111",
        password_hash="hashed",
        telegram_id=111111,
        profile=UserProfile(
            gender=UserGender.MALE,
            age=25,
            height_cm=180,
            weight_kg=75,
            goal=FitnessGoal.GAIN_MUSCLE,
            experience_level=ExperienceLevel.INTERMEDIATE,
            location=None,
            created_at=now,
            updated_at=now,
        ),
    )


@pytest.fixture(autouse=True)
def setup_deps(mock_uow, mock_embedder, current_user):
    app.dependency_overrides[get_uow] = lambda: mock_uow
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedder
    app.dependency_overrides[get_current_user] = lambda: current_user
    yield
    app.dependency_overrides.clear()


class TestInsightsRouter:
    async def test_create_insight_success(self, mock_uow, mock_embedder):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/insights/",
                json={
                    "content": "Травма колена",
                    "tag": "injury",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Травма колена"
        assert data["tag"] == "injury"
        mock_uow.insights.save.assert_called_once()
        mock_uow.commit.assert_called_once()

    async def test_create_insight_all_tags(self, mock_uow, mock_embedder):
        tags = [
            "injury", "progress", "fatigue", "preference",
            "schedule", "nutrition", "technique", "mental",
        ]
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for tag in tags:
                response = await client.post(
                    "/api/v1/insights/",
                    json={"content": f"Test {tag}", "tag": tag},
                )
                assert response.status_code == 201, f"Failed for tag: {tag}"
