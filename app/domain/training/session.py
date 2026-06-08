from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta

from app.domain.training.exercise_set import ExerciseSet
from app.domain.enums import SessionStatus

@dataclass
class WorkoutSessionDomain:
    user_id: UUID
    id: UUID = field(default_factory=uuid4)
    program_id: UUID | None = None
    status: SessionStatus = SessionStatus.active
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    notes: str | None = None

    def complete(self, notes: str | None = None) -> None:
        if self.status != SessionStatus.active:
            raise ValueError("Можно завершить только активную сессию")
        self.status = SessionStatus.completed
        self.finished_at = datetime.now(timezone.utc)
        self.notes = notes

    def cancel(self) -> None:
        if self.status != SessionStatus.active:
            return
        self.status = SessionStatus.cancelled
        self.finished_at = datetime.now(timezone.utc)

    @property
    def duration(self) -> timedelta | None:
        if self.finished_at is None:
            return None
        return self.finished_at - self.started_at