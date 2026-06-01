from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.domain.training.workout_day import WorkoutDay


@dataclass
class WorkoutProgram:
    user_id: UUID
    name: str
    is_active: bool = True
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    workout_days: list[WorkoutDay] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_day(self, day: WorkoutDay) -> None:
        if any(d.day_number == day.day_number for d in self.workout_days):
            raise ValueError(f"День №{day.day_number} уже существует в программе")
        self.workout_days.append(day)
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)