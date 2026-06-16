import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.domain.identity.user import User
from app.domain.identity.user_profile import UserProfile
from app.domain.identity.insight import UserInsight
from app.domain.identity.intents import UserIntent
from app.domain.enums import (
    UserGender, FitnessGoal, ExperienceLevel, InsightTag,
    MuscleGroup, Location, Constraint,
)
from app.application.services.intent_service import IntentService
from app.application.dto.program import GenerateProgram
from app.application.dto.intents import IntentSchema


@pytest.fixture
def sample_user_profile():
    return UserProfile(
        gender=UserGender.MALE,
        age=25,
        height_cm=180,
        weight_kg=75,
        goal=FitnessGoal.GAIN_MUSCLE,
        experience_level=ExperienceLevel.INTERMEDIATE,
        location=Location.gym,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_user(sample_user_profile):
    return User(
        id=uuid4(),
        username="testuser",
        phone="+998901234567",
        password_hash="hashed",
        telegram_id=123456789,
        profile=sample_user_profile,
    )


@pytest.fixture
def user_without_profile():
    return User(
        id=uuid4(),
        username="testuser",
        phone="+998901234567",
        password_hash="hashed",
        telegram_id=123456789,
        profile=None,
    )


@pytest.fixture
def sample_insight():
    return UserInsight(
        user_id=uuid4(),
        content="Травма колена",
        tag=InsightTag.injury,
    )


@pytest.fixture
def sample_dto():
    return GenerateProgram(content="Хочу набрать массу", importance="medium")


@pytest.fixture
def mock_uow_factory():
    uow = AsyncMock()
    uow.insights = AsyncMock()
    uow.intents = AsyncMock()
    uow.commit = AsyncMock()

    factory = MagicMock()
    factory.__aenter__ = AsyncMock(return_value=uow)
    factory.__aexit__ = AsyncMock(return_value=False)
    factory.return_value = factory

    return factory, uow


@pytest.fixture
def mock_embedder():
    embedder = AsyncMock()
    embedder.get_embedding.return_value = [0.1] * 384
    return embedder


class TestIntentServiceBuildPrompt:
    async def test_build_prompt_success(self, sample_user, sample_insight, sample_dto):
        service = IntentService.__new__(IntentService)
        service._llm = MagicMock()

        prompt = service._build_prompt(sample_user, [sample_insight], sample_dto)

        assert "male" in prompt
        assert "25" in prompt
        assert "gain_muscle" in prompt
        assert "Травма колена" in prompt
        assert "Хочу набрать массу" in prompt

    async def test_build_prompt_no_profile(self, user_without_profile, sample_dto):
        service = IntentService.__new__(IntentService)
        service._llm = MagicMock()

        with pytest.raises(ValueError, match="Профиль пользователя отсутствует"):
            service._build_prompt(user_without_profile, [], sample_dto)

    async def test_build_prompt_missing_gender(self, sample_dto):
        incomplete_profile = UserProfile(
            gender=None,
            age=25,
            height_cm=180,
            weight_kg=75,
            goal=FitnessGoal.GAIN_MUSCLE,
            experience_level=ExperienceLevel.INTERMEDIATE,
            location=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        user = User(
            id=uuid4(),
            username="test",
            phone="+998901234567",
            password_hash="hashed",
            telegram_id=123,
            profile=incomplete_profile,
        )

        service = IntentService.__new__(IntentService)
        service._llm = MagicMock()

        with pytest.raises(ValueError, match="User profile has no gender"):
            service._build_prompt(user, [], sample_dto)

    async def test_build_prompt_importance_levels(self, sample_user, sample_dto):
        service = IntentService.__new__(IntentService)
        service._llm = MagicMock()

        for level in ["low", "medium", "high"]:
            dto = GenerateProgram(content="test", importance=level)
            prompt = service._build_prompt(sample_user, [], dto)
            assert "test" in prompt


class TestIntentServiceBuildIntentText:
    async def test_build_intent_text(self, sample_user):
        service = IntentService.__new__(IntentService)

        intent = IntentSchema(
            goal="Набор массы",
            constraints=["no_knee_load"],
            focus_areas=[MuscleGroup.CHEST, MuscleGroup.BACK],
            location=Location.gym,
            context="Тренируюсь 3 раза в неделю",
        )

        text = service._build_intent_text(intent)

        assert "Набор массы" in text
        assert "gym" in text
        assert "no_knee_load" in text
        assert "chest" in text
        assert "back" in text
        assert "Тренируюсь 3 раза в неделю" in text

    async def test_build_intent_text_empty_parts(self, sample_user):
        service = IntentService.__new__(IntentService)

        intent = IntentSchema(
            goal="",
            constraints=[],
            focus_areas=[],
            location=Location.gym,
            context="",
        )

        text = service._build_intent_text(intent)
        assert "gym" in text
