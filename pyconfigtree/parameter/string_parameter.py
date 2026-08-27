from __future__ import annotations


__all__ = [
    'str_serializer',
    'str_deserializer',
    'StringParameter',
]


from typing import Any

from .base import ValueSpec, MutableParameter


def str_serializer(value: str, node: StringParameter) -> str:
    return value


def str_deserializer(value: Any, node: StringParameter) -> str:
    return str(value)


def str_accepts(value: object, node: StringParameter) -> bool:
    return type(value) is str


class StringParameter(MutableParameter[str]):
    SPEC = ValueSpec(
        serializer=str_serializer, deserializer=str_deserializer, validator=str_accepts
    )
