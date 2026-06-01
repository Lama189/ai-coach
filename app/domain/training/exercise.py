from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.enums import MuscleGroup


@dataclass
class Exercise:
    name: str
    muscle_group: MuscleGroup
    id: UUID = field(default_factory=uuid4)
    description: str | None = None

    def update_details(self, name: str, description: str | None) -> None:
        self.name = name
        self.description = description