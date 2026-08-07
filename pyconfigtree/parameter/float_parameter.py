from __future__ import annotations


__all__ = [
    'float_serializer',
    'float_deserializer',
    'FloatParameter',
]


from typing import Any

from pyconfigtree.exceptions import DeserializationError

from .base import ValueSpec, MutableParameter


def float_serializer(node: FloatParameter, value: float) -> float:
    return value


def float_deserializer(node: FloatParameter, value: Any) -> float:
    if isinstance(value, bool):
        raise DeserializationError('Boolean values cannot be deserialized as floats.')
    return float(value)


def float_accepts(node: FloatParameter, value: object) -> bool:
    return type(value) is float


FLOAT_VALUE_SPEC = ValueSpec(
    serializer=float_serializer,
    deserializer=float_deserializer,
    validator=float_accepts,
)


class FloatParameter(MutableParameter[float]):
    SPEC = FLOAT_VALUE_SPEC
