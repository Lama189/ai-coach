from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class UserSchedule:
    user_id: UUID
    day_of_week: int
    training_day_number: int
    id: UUID = field(default_factory=uuid4)
