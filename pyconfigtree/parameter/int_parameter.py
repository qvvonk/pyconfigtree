from __future__ import annotations


__all__ = [
    'int_serializer',
    'int_deserializer',
    'IntParameter',
]


from typing import Any

from .base import TypedParameter
from pyconfigtree.exceptions import DeserializationError, ValidationError


def int_serializer(value: int) -> int:
    return value


def int_deserializer(value: Any) -> int:
    return int(value)


class IntParameter(TypedParameter[int]):
    DEFAULT_SERIALIZER = int_serializer
    DEFAULT_DESERIALIZER = int_deserializer

    def deserialize(self, value: Any) -> int:
        res = super().deserialize(value)
        if not isinstance(res, int):
            raise DeserializationError(
                f'Deserialized value of `IntParameter` '
                f'must be an instance of `int`, not {type(res)}.'
            )
        return res

    async def validate(self, value: Any) -> None:
        if not isinstance(value, int):
            raise ValidationError(
                f'Value of `IntParameter` must be an instance of `int`, not {type(value)}.'
            )
        return await (super().validate(value))