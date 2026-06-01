from dataclasses import dataclass,  field
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class WorkoutDayExercise:
    exercise_id: UUID
    sets: int
    reps: int
    id: UUID = field(default_factory=uuid4)
    rest_seconds: Optional[int] = None

    def __post_init__(self):
        if self.sets <= 0 or self.reps <= 0:
            raise ValueError("Количество подходов и повторений должно быть > 0")
        if self.rest_seconds is not None and self.rest_seconds < 0:
            raise ValueError("Время отдыха не может быть отрицательным")
        