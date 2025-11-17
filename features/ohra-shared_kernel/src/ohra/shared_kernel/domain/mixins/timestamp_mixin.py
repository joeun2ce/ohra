from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class TimestampMixin:
    """Mixin for timestamp fields"""

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now(timezone.utc)
