from abc import ABC
from dataclasses import dataclass
from enum import Enum, EnumMeta
from typing import Any, TypeVar

from ohra.shared_kernel.domain.exception import ValueObjectEnumError

ValueObjectType = TypeVar("ValueObjectType", bound="ValueObject")


@dataclass(frozen=True)
class ValueObject(ABC):
    def __composite_values__(self):
        return tuple(self.__dict__.values())

    @classmethod
    def from_value(cls, value: Any) -> ValueObjectType:
        if isinstance(cls, EnumMeta):
            for item in cls:
                if item.value == value:
                    return item
            raise ValueObjectEnumError

        instance = cls(value=value)
        return instance


class RoomStatus(ValueObject, str, Enum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    OCCUPIED = "OCCUPIED"

    @property
    def is_available(self) -> bool:
        return self == RoomStatus.AVAILABLE

    @property
    def is_reserved(self) -> bool:
        return self == RoomStatus.RESERVED

    @property
    def is_occupied(self) -> bool:
        return self == RoomStatus.OCCUPIED


class ReservationStatus(ValueObject, str, Enum):
    IN_PROGRESS = "IN-PROGRESS"
    CANCELLED = "CANCELLED"
    COMPLETE = "COMPLETE"

    @property
    def in_progress(self) -> bool:
        return self == ReservationStatus.IN_PROGRESS
