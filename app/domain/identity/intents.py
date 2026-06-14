from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.domain.enums import MuscleGroup
from enum import Enum

from app.domain.enums import Location, Constraint

class UserIntent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    program_id: UUID | None
    goal: str
    constraints: list[Constraint]
    focus_areas: list[MuscleGroup]
    location: Location
    context: str