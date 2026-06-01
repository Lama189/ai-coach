from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain.enums import UserGender, FitnessGoal, ExperienceLevel


@dataclass
class UserProfile:
    gender: UserGender
    age: int
    height_cm: int
    weight_kg: float
    goal: FitnessGoal
    experience_level: ExperienceLevel
    created_at: datetime
    updated_at: datetime

    def update_metrics(self, weight_kg: float, height_cm: int) -> None:
        if weight_kg <= 0 or height_cm <= 0:
            raise ValueError("Метрики должны быть положительными")
        
        self.weight_kg = weight_kg
        self.height_cm = height_cm
        self.updated_at = datetime.now(timezone.utc)