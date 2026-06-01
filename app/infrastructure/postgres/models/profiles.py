from typing import TYPE_CHECKING
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    ForeignKey,
    DateTime,
    Float,
    Integer,
    func,
    Enum as SqlEnum
)

from app.infrastructure.postgres.models.base_model import BaseModel
if TYPE_CHECKING:
    from app.infrastructure.postgres.models.users import User
from app.domain.enums import ExperienceLevel, FitnessGoal, UserGender


class UserProfile(BaseModel):
    __tablename__ = "user_profiles"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True, 
        nullable=False
    )

    gender: Mapped[UserGender] = mapped_column(SqlEnum(UserGender, name="gender"), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    height_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)

    goal: Mapped[FitnessGoal] = mapped_column(SqlEnum(FitnessGoal, name="fitness_goal"), nullable=False)
    experience_level: Mapped[ExperienceLevel] = mapped_column(SqlEnum(ExperienceLevel, name="experience_level"), nullable=False)

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")
