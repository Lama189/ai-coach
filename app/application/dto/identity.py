from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, UUID4, Field, ConfigDict

from app.domain.enums import UserGender, FitnessGoal, ExperienceLevel
from app.domain.identity.user_profile import UserProfile


class UserProfileCreateDTO(BaseModel):
    gender: UserGender
    age: int = Field(gt=10, lt=100)
    height_cm: int = Field(gt=50)
    weight_kg: float = Field(gt=20, lt=300)
    goal: FitnessGoal
    experience_level: ExperienceLevel

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
    password: str = Field(min_length=8)
    profile: UserProfileCreateDTO


class UserProfileResponseDTO(BaseModel):
    gender: UserGender
    age: int
    height_cm: int
    weight_kg: float
    goal: FitnessGoal
    experience_level: ExperienceLevel

    model_config = ConfigDict(from_attributes=True)


class UserResponseDTO(BaseModel):
    id: UUID4
    username: str
    profile: Optional[UserProfileResponseDTO] = None

    model_config = ConfigDict(from_attributes=True)