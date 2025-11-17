from abc import ABC
from dataclasses import dataclass
from typing import Any, TypeVar

EntityType = TypeVar("EntityType", bound="Entity")


@dataclass
class Entity(ABC):
    id: str

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


class AggregateRoot(Entity):
    pass
