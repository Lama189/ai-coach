from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import (
    ForeignKey,
    Integer,
    Float,
)

from app.infrastructure.postgres.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.session import Session


class ExerciseSet(BaseModel):
    __tablename__ = "exercise_sets"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    session_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    exercise_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="RESTRICT"))

    set_number: Mapped[int] = mapped_column(Integer) 
    weight: Mapped[float] = mapped_column(Float)    
    reps: Mapped[int] = mapped_column(Integer)     
    rpe: Mapped[int] = mapped_column(Integer, nullable=True) 

    session: Mapped["Session"] = relationship("Session", back_populates="exercise_sets")