import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.training.session import WorkoutSessionDomain
from app.domain.enums import SessionStatus
from app.infrastructure.postgres.repos.sessions import PostgresSessionsRepository
from app.infrastructure.postgres.models.session import Session as SessionModel


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    class ConcreteSessionRepo(PostgresSessionsRepository):
        async def get_user_sessions(self, user_id, from_date=None, to_date=None, limit=20, offset=0):
            return []

        async def count_user_sessions(self, user_id):
            return 0

    return ConcreteSessionRepo(mock_session)


@pytest.fixture
def sample_session():
    return WorkoutSessionDomain(
        user_id=uuid4(),
        program_id=uuid4(),
        status=SessionStatus.active,
        notes="Test session",
    )


class TestPostgresSessionsRepository:
    async def test_save_new_session(self, repo, mock_session, sample_session):
        mock_session.get.return_value = None

        await repo.save(sample_session)

        mock_session.add.assert_called_once()
        added_model = mock_session.add.call_args[0][0]
        assert isinstance(added_model, SessionModel)
        assert added_model.user_id == sample_session.user_id
        assert added_model.status == SessionStatus.active

    async def test_save_existing_session(self, repo, mock_session, sample_session):
        existing_model = MagicMock(spec=SessionModel)
        existing_model.program_id = sample_session.program_id
        mock_session.get.return_value = existing_model

        await repo.save(sample_session)

        assert existing_model.user_id == sample_session.user_id
        assert existing_model.status == sample_session.status
        mock_session.add.assert_not_called()

    async def test_save_existing_session_update_program_id(self, repo, mock_session):
        session = WorkoutSessionDomain(
            user_id=uuid4(),
            program_id=uuid4(),
            status=SessionStatus.active,
        )
        existing_model = MagicMock(spec=SessionModel)
        existing_model.program_id = uuid4()
        mock_session.get.return_value = existing_model

        await repo.save(session)

        assert existing_model.program_id == session.program_id

    async def test_to_domain(self, repo):
        mock_model = MagicMock(spec=SessionModel)
        mock_model.id = uuid4()
        mock_model.user_id = uuid4()
        mock_model.program_id = uuid4()
        mock_model.status = SessionStatus.completed
        mock_model.started_at = datetime.now(timezone.utc)
        mock_model.finished_at = datetime.now(timezone.utc)
        mock_model.notes = "Done"

        domain = repo._to_domain(mock_model)

        assert domain.status == SessionStatus.completed
        assert domain.notes == "Done"

    async def test_to_model(self, repo, sample_session):
        model = repo._to_model(sample_session)

        assert isinstance(model, SessionModel)
        assert model.user_id == sample_session.user_id
        assert model.status == SessionStatus.active
        assert model.notes == "Test session"
