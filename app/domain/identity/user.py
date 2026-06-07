from dataclasses import dataclass, field
from uuid import UUID, uuid4
from datetime import datetime, timezone

from app.domain.identity.user_profile import UserProfile


@dataclass
class User:
    username: str
    phone: str
    password_hash: str
    id: UUID = field(default_factory=uuid4)
    telegram_id: int | None = None
    profile: UserProfile | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def assighn_profile(self, profile: UserProfile) -> None:
        if self.profile is not None:
            raise ValueError("Профиль уже создан.")
        
        self.profile = profile
        self.updated_at = datetime.now(timezone.utc)
