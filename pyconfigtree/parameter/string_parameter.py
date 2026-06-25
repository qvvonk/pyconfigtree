from __future__ import annotations


__all__ = [
    'str_serializer',
    'str_deserializer',
    'StringParameter',
]


from typing import Any

from .base import TypedParameter


def str_serializer(value: str) -> str:
    return value


def str_deserializer(value: Any) -> str:
    return str(value)


class StringParameter(TypedParameter[str]):
    DEFAULT_SERIALIZER = str_serializer
    DEFAULT_DESERIALIZER = str_deserializer