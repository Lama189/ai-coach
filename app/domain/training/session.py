from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.domain.training.exercise_set import ExerciseSet

@dataclass
class Session:
    user_id: UUID
    id: UUID = field(default_factory=uuid4)
    program_id: UUID | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    notes: str | None = None
    exercise_sets: list[ExerciseSet] = field(default_factory=list)

    def add_set(self, exercise_set: ExerciseSet) -> None:
        if self.finished_at is not None:
            raise ValueError("Нельзя добавить подход к завершенной тренировке")
        self.exercise_sets.append(exercise_set)

    def finish(self, notes: str | None = None) -> None:
        if self.finished_at is not None:
            raise ValueError("Тренировка уже завершена")
        if not self.exercise_sets:
            raise ValueError("Нельзя завершить пустую тренировку (нет подходов)")
        self.finished_at = datetime.now(timezone.utc)
        self.notes = notes