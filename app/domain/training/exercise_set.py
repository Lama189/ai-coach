from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import Optional

@dataclass
class ExerciseSet:
    exercise_id: UUID
    set_number: int
    weight: float
    reps: int
    id: UUID = field(default_factory=uuid4)
    rpe: int | None = None 

    def __post_init__(self):
        if self.set_number <= 0:
            raise ValueError("Номер подхода должен быть положительным")
        if self.weight < 0:
            raise ValueError("Вес не может быть отрицательным")
        if self.reps <= 0:
            raise ValueError("Количество повторений должно быть > 0")
        if self.rpe is not None and not (1 <= self.rpe <= 10):
            raise ValueError("RPE должен быть в диапазоне от 1 до 10")

    def update_result(self, weight: float, reps: int, rpe: int | None = None) -> None:
        if weight < 0 or reps <= 0:
            raise ValueError("Некорректные значения веса или повторений")
        if rpe is not None and not (1 <= rpe <= 10):
            raise ValueError("RPE должен быть в диапазоне от 1 до 10")
            
        self.weight = weight
        self.reps = reps
        self.rpe = rpe