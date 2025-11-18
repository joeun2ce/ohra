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
