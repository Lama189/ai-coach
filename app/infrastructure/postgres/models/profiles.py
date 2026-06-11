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

from app.domain.enums import ExperienceLevel, FitnessGoal, UserGender,Location


class UserProfile(BaseModel):
    __tablename__ = "user_profiles"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True, 
        nullable=False
    )

    gender: Mapped[UserGender | None] = mapped_column(SqlEnum(UserGender, name="gender"), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    goal: Mapped[FitnessGoal | None] = mapped_column(SqlEnum(FitnessGoal, name="fitness_goal"), nullable=True)
    experience_level: Mapped[ExperienceLevel | None] = mapped_column(SqlEnum(ExperienceLevel, name="experience_level"), nullable=True)
    location: Mapped[Location | None] = mapped_column(SqlEnum(Location, name="location"), nullable=True)

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
