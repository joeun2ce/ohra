from dataclasses import dataclass, field
from typing import Optional
from ohra.shared_kernel.domain.entity import Entity
from ohra.shared_kernel.domain.mixins.timestamp_mixin import TimestampMixin


@dataclass
class User(Entity, TimestampMixin):
    id: str = field(default="")
    external_user_id: Optional[str] = field(default=None)
    email: str = field(default="")
    name: str = field(default="unknown")
    is_active: bool = True
    is_admin: bool = False
