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
    _DEFAULT_SERIALIZER = str_serializer
    _DEFAULT_DESERIALIZER = str_deserializer
    _VALUE_TYPE = str