from dataclasses import dataclass, field
from ohra.shared_kernel.domain.entity import Entity
from ohra.shared_kernel.domain.mixins.timestamp_mixin import TimestampMixin


@dataclass
class Feedback(Entity, TimestampMixin):
    id: str = field(default="")
    message_id: str = field(default="")
    user_id: str = field(default="")
    rating: int = field(default=0)
    comment: str = field(default="")
