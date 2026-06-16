import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.application.dependencies import get_uow, get_embedding_service, get_current_user
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.domain.enums import MuscleGroup, MovementPattern, UserGender, FitnessGoal, ExperienceLevel
from app.domain.training.exercise import Exercise


@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)
    uow.exercises = AsyncMock()
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


@pytest.fixture
def sample_exercise():
    return Exercise(
        id=uuid4(),
        name="Bench Press",
        muscle_group=MuscleGroup.CHEST,
        equipment="barbell",
        movement_patterns=[MovementPattern.PUSH_HORIZONTAL],
        description="Classic chest exercise",
    )


@pytest.fixture(autouse=True)
def setup_deps(mock_uow, mock_embedder, current_user):
    app.dependency_overrides[get_uow] = lambda: mock_uow
    app.dependency_overrides[get_embedding_service] = lambda: mock_embedder
    app.dependency_overrides[get_current_user] = lambda: current_user
    yield
    app.dependency_overrides.clear()


class TestExercisesRouter:
    async def test_create_exercise_success(self, mock_uow, mock_embedder, sample_exercise):
        mock_uow.exercises.get_by.return_value = None
        mock_uow.exercises.find_familiar.return_value = None

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/exercises/",
                json={
                    "name": "Bench Press",
                    "muscle_group": "chest",
                    "equipment": "barbell",
                    "movement_patterns": ["push_horizontal"],
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Bench Press"
        assert data["muscle_group"] == "chest"

    async def test_create_exercise_name_taken(self, mock_uow, mock_embedder, sample_exercise):
        mock_uow.exercises.get_by.return_value = sample_exercise

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/exercises/",
                json={
                    "name": "Bench Press",
                    "muscle_group": "chest",
                    "equipment": "barbell",
                    "movement_patterns": ["push_horizontal"],
                },
            )

        assert response.status_code == 400
        assert "уже занято" in response.json()["detail"]

    async def test_delete_exercise_success(self, mock_uow, mock_embedder, sample_exercise):
        mock_uow.exercises.get_by.return_value = sample_exercise

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/v1/exercises/{sample_exercise.id}")

        assert response.status_code == 204

    async def test_delete_exercise_not_found(self, mock_uow, mock_embedder):
        mock_uow.exercises.get_by.return_value = None

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/v1/exercises/{uuid4()}")

        assert response.status_code == 404
        assert "не найдено" in response.json()["detail"]

    async def test_add_exercises_batch(self, mock_uow):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch(
                "app.api.v1.routes.exercises.add_exercises_batch_task"
            ) as mock_task:
                response = await client.post(
                    "/api/v1/exercises/batch",
                    json=[
                        {
                            "name": "Squat",
                            "muscle_group": "legs",
                            "equipment": "barbell",
                            "movement_patterns": ["squat"],
                        }
                    ],
                )

        assert response.status_code == 202
        assert response.json()["status"] == "processing"
        mock_task.delay.assert_called_once()
