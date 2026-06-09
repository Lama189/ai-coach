from pydantic import BaseModel
from app.domain.enums import MuscleGroup
from enum import Enum

from app.domain.enums import Location

class IntentSchema(BaseModel):
    goal: str
    constraints: list[str]
    focus_areas: list[MuscleGroup]
    location: Location
    context: str