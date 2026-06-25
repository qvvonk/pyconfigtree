from __future__ import annotations


__all__ = [
    'int_serializer',
    'int_deserializer',
    'IntParameter',
]


from typing import Any

from .base import TypedParameter


def int_serializer(value: int) -> int:
    return value


def int_deserializer(value: Any) -> int:
    return int(value)


class IntParameter(TypedParameter[int]):
    DEFAULT_SERIALIZER = int_serializer
    DEFAULT_DESERIALIZER = int_deserializer
    VALUE_TYPE = int
