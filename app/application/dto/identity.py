from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, UUID4, Field, ConfigDict

from app.domain.enums import UserGender, FitnessGoal, ExperienceLevel
from app.domain.identity.user_profile import UserProfile


class UserProfileCreateDTO(BaseModel):
    gender: UserGender | None = None
    age: int | None = Field(gt=10, lt=100, default=None)
    height_cm: int | None = Field(gt=50, default=None)
    weight_kg: float | None = Field(gt=20, lt=300, default=None)
    goal: FitnessGoal | None = None
    experience_level: ExperienceLevel | None = None

    def to_domain(self) -> UserProfile:
        now = datetime.now(timezone.utc)
        return UserProfile(
            gender=self.gender,
            age=self.age,
            height_cm=self.height_cm,
            weight_kg=self.weight_kg,
            goal=self.goal,
            experience_level=self.experience_level,
            created_at=now,
            updated_at=now,
        )


class UserCreateDTO(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    phone: str = Field(min_length=5, max_length=50)
    password: str = Field(min_length=8)
    telegram_id: int | None = None
    profile: UserProfileCreateDTO = Field(default_factory=UserProfileCreateDTO)


class UserProfileResponseDTO(BaseModel):
    gender: UserGender | None
    age: int | None
    height_cm: int | None
    weight_kg: float | None
    goal: FitnessGoal | None
    experience_level: ExperienceLevel | None

    model_config = ConfigDict(from_attributes=True)


class UserResponseDTO(BaseModel):
    id: UUID4
    username: str
    phone: str
    telegram_id: int | None = None
    profile: UserProfileResponseDTO | None = None

    model_config = ConfigDict(from_attributes=True)