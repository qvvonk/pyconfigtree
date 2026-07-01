from __future__ import annotations


__all__ = [
    'int_serializer',
    'int_deserializer',
    'IntParameter',
]


from typing import Any

from .base import TypedParameter


def int_serializer(node: IntParameter, value: int) -> int:
    return value


def int_deserializer(node: IntParameter, value: Any) -> int:
    return int(value)


class IntParameter(TypedParameter[int]):
    _DEFAULT_SERIALIZER = staticmethod(int_serializer)
    _DEFAULT_DESERIALIZER = staticmethod(int_deserializer)
    _VALUE_TYPE = int
