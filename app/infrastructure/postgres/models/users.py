from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    String,
    BigInteger,
    DateTime,
    func
)

from app.infrastructure.postgres.models.base_model import BaseModel
if TYPE_CHECKING:
    from app.infrastructure.postgres.models.profiles import UserProfile
    from app.infrastructure.postgres.models.workout_programs import WorkoutProgram
    from app.infrastructure.postgres.models.session import Session


class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid4)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

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

    profile: Mapped["UserProfile"] = relationship("UserProfile", back_populates="user", uselist=False)
    workout_programs: Mapped[list["WorkoutProgram"]] = relationship("WorkoutProgram", back_populates="user")
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user")
