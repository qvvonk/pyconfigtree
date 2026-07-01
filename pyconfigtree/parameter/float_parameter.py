from __future__ import annotations


__all__ = [
    'float_serializer',
    'float_deserializer',
    'FloatParameter',
]


from typing import Any

from .base import TypedParameter


def float_serializer(node: FloatParameter, value: float) -> float:
    return value


def float_deserializer(node: FloatParameter, value: Any) -> float:
    return float(value)


class FloatParameter(TypedParameter[float]):
    _DEFAULT_SERIALIZER = staticmethod(float_serializer)
    _DEFAULT_DESERIALIZER = staticmethod(float_deserializer)
    _VALUE_TYPE = float
