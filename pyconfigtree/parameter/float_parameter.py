from __future__ import annotations


__all__ = [
    'float_serializer',
    'float_deserializer',
    'FloatParameter',
]


from typing import Any

from .base import TypedParameter


def float_serializer(value: float) -> float:
    return value


def float_deserializer(value: Any) -> float:
    return float(value)


class FloatParameter(TypedParameter[float]):
    DEFAULT_SERIALIZER = float_serializer
    DEFAULT_DESERIALIZER = float_deserializer
    VALUE_TYPE = float