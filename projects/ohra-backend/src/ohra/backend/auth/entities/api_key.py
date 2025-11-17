from dataclasses import dataclass, field
from datetime import datetime
from ohra.shared_kernel.domain.entity import Entity
from ohra.shared_kernel.domain.mixins.timestamp_mixin import TimestampMixin


@dataclass
class APIKey(Entity, TimestampMixin):
    id: str = field(default="")
    user_id: str = field(default="")
    key_hash: str = field(default="")
    name: str = field(default="")
    expires_at: datetime = None
    is_active: bool = True

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def is_valid(self) -> bool:
        return self.is_active and not self.is_expired()
