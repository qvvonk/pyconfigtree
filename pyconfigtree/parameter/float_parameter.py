from __future__ import annotations


__all__ = [
    'float_serializer',
    'float_deserializer',
    'FloatParameter',
]


from typing import Any

from .base import TypedParameter
from pyconfigtree.exceptions import DeserializationError, ValidationError


def float_serializer(value: float) -> float:
    return value


def float_deserializer(value: Any) -> float:
    return float(value)


class FloatParameter(TypedParameter[float]):
    DEFAULT_SERIALIZER = float_serializer
    DEFAULT_DESERIALIZER = float_deserializer

    def deserialize(self, value: Any) -> float:
        res = super().deserialize(value)
        if not isinstance(res, float):
            raise DeserializationError(
                f'Deserialized value of `FloatParameter` '
                f'must be an instance of `float`, not {type(res)}.'
            )
        return res

    async def validate(self, value: Any) -> None:
        if not isinstance(value, float):
            raise ValidationError(
                f'Value of `FloatParameter` must be an instance of `float`, not {type(value)}.'
            )
        return await (super().validate(value))