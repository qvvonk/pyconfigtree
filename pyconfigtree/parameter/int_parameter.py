from __future__ import annotations


__all__ = [
    'int_serializer',
    'int_deserializer',
    'IntParameter',
]


from typing import Any

from pyconfigtree.exceptions import DeserializationError

from .base import ValueSpec, MutableParameter


def int_serializer(node: IntParameter, value: int) -> int:
    return value


def int_deserializer(node: IntParameter, value: Any) -> int:
    if isinstance(value, bool):
        raise DeserializationError('Boolean values cannot be deserialized as integers.')
    return int(value)


def int_accepts(node: IntParameter, value: object) -> bool:
    return type(value) is int


INT_VALUE_SPEC = ValueSpec(
    serializer=int_serializer,
    deserializer=int_deserializer,
    validator=int_accepts,
)


class IntParameter(MutableParameter[int]):
    SPEC = INT_VALUE_SPEC
