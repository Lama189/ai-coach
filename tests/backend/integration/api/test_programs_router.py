import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.application.dependencies import get_uow, get_current_user
from app.application.interfaces.unit_of_work import IUnitOfWork
from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.domain.training.program import WorkoutProgram
from app.domain.training.workout_day import WorkoutDay
from app.domain.training.workout_day_exercise import WorkoutDayExercise
from app.domain.training.exercise import Exercise
from app.domain.enums import (
    MuscleGroup, MovementPattern, UserGender, FitnessGoal, ExperienceLevel
)


@pytest.fixture
def mock_uow():
    uow = AsyncMock(spec=IUnitOfWork)
    uow.programs = AsyncMock()
    uow.workout_days = AsyncMock()
    uow.workout_days_exercise = AsyncMock()
    uow.exercises = AsyncMock()
    uow.commit = AsyncMock()
    return uow


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
def setup_deps(mock_uow, current_user):
    app.dependency_overrides[get_uow] = lambda: mock_uow
    app.dependency_overrides[get_current_user] = lambda: current_user
    yield
    app.dependency_overrides.clear()


class TestProgramsRouterCreate:
    async def test_create_workout_program_success(self, mock_uow):
        exercise_id = uuid4()
        exercise = Exercise(
            id=exercise_id,
            name="Bench Press",
            muscle_group=MuscleGroup.CHEST,
            equipment="barbell",
            movement_patterns=[MovementPattern.PUSH_HORIZONTAL],
        )
        mock_uow.exercises.get_by_ids.return_value = [exercise]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/programs/",
                json={
                    "user_id": str(uuid4()),
                    "name": "Test Program",
                    "description": "A test",
                    "days": [
                        {
                            "name": "Day 1",
                            "day_number": 1,
                            "exercises": [
                                {
                                    "exercise_id": str(exercise_id),
                                    "sets": 3,
                                    "reps": 10,
                                    "rest_seconds": 90,
                                }
                            ],
                        }
                    ],
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Program"
        assert data["is_active"] is True

    async def test_create_workout_program_invalid_exercises(self, mock_uow):
        mock_uow.exercises.get_by_ids.return_value = []

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/programs/",
                json={
                    "user_id": str(uuid4()),
                    "name": "Test",
                    "days": [
                        {
                            "name": "Day 1",
                            "day_number": 1,
                            "exercises": [
                                {
                                    "exercise_id": str(uuid4()),
                                    "sets": 3,
                                    "reps": 10,
                                }
                            ],
                        }
                    ],
                },
            )

        assert response.status_code == 400
        assert "несуществующие упражнения" in response.json()["detail"]


class TestProgramsRouterGet:
    async def test_get_program_by_user_id_success(self, mock_uow):
        user_id = uuid4()
        program = WorkoutProgram(
            id=uuid4(),
            user_id=user_id,
            name="My Program",
            is_active=True,
        )
        day = WorkoutDay(id=uuid4(), day_number=1, title="Day 1")
        exercise_id = uuid4()
        day_exercise = WorkoutDayExercise(
            id=uuid4(),
            exercise_id=exercise_id,
            sets=3,
            reps=10,
            rest_seconds=90,
        )
        exercise = Exercise(
            id=exercise_id,
            name="Squat",
            muscle_group=MuscleGroup.LEGS,
            equipment="barbell",
            movement_patterns=[MovementPattern.SQUAT],
        )

        mock_uow.programs.get_actual_by_user_id.return_value = program
        mock_uow.workout_days.get_by_program_id.return_value = [day]
        mock_uow.workout_days_exercise.get_by_workout_day_id.return_value = [day_exercise]
        mock_uow.exercises.get_by_ids.return_value = [exercise]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/programs/{user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "My Program"
        assert len(data["workout_days"]) == 1

    async def test_get_program_by_user_id_not_found(self, mock_uow):
        mock_uow.programs.get_actual_by_user_id.return_value = None

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/programs/{uuid4()}")

        assert response.status_code == 404
        assert "нет программ тренировок" in response.json()["detail"]

    async def test_get_program_no_days(self, mock_uow):
        program = WorkoutProgram(
            user_id=uuid4(),
            name="Empty",
            is_active=True,
        )
        mock_uow.programs.get_actual_by_user_id.return_value = program
        mock_uow.workout_days.get_by_program_id.return_value = []

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/programs/{uuid4()}")

        assert response.status_code == 404
        assert "отсутствуют тренировочные дни" in response.json()["detail"]


class TestProgramsRouterGenerate:
    async def test_generate_workout_program(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            with patch(
                "app.api.v1.routes.programs.generate_workout_task"
            ) as mock_task:
                response = await client.post(
                    "/api/v1/programs/generate",
                    json={"content": "Хочу набрать массу", "importance": "medium"},
                )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "processing"
        assert "task_id" in data
        mock_task.apply_async.assert_called_once()
