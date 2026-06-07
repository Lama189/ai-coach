from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain.enums import UserGender, FitnessGoal, ExperienceLevel


@dataclass
class UserProfile:
    gender: UserGender | None
    age: int | None
    height_cm: int | None
    weight_kg: float | None
    goal: FitnessGoal | None
    experience_level: ExperienceLevel | None
    created_at: datetime
    updated_at: datetime

    def update_metrics(self, weight_kg: float, height_cm: int) -> None:
        if weight_kg <= 0 or height_cm <= 0:
            raise ValueError("Метрики должны быть положительными")
        
        self.weight_kg = weight_kg
        self.height_cm = height_cm
        self.updated_at = datetime.now(timezone.utc)

    def is_complete(self) -> bool:
        return all([
            self.gender is not None,
            self.age is not None,
            self.height_cm is not None,
            self.weight_kg is not None,
            self.goal is not None,
            self.experience_level is not None
        ])