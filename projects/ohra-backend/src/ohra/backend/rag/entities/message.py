from dataclasses import dataclass, field
from ohra.shared_kernel.domain.entity import Entity
from ohra.shared_kernel.domain.mixins.timestamp_mixin import TimestampMixin


@dataclass
class Message(Entity, TimestampMixin):
    id: str = field(default="")
    conversation_id: str = field(default="")
    role: str = field(default="")
    content: str = field(default="")
