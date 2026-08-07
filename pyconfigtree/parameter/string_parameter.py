from __future__ import annotations


__all__ = [
    'str_serializer',
    'str_deserializer',
    'StringParameter',
]


from typing import Any

from .base import ValueSpec, MutableParameter


def str_serializer(node: StringParameter, value: str) -> str:
    return value


def str_deserializer(node: StringParameter, value: Any) -> str:
    return str(value)


def str_accepts(node: StringParameter, value: object) -> bool:
    return type(value) is str


STRING_VALUE_SPEC = ValueSpec(
    serializer=str_serializer,
    deserializer=str_deserializer,
    accepts=str_accepts,
    expected_type='a `str`',
)


class StringParameter(MutableParameter[str]):
    SPEC = STRING_VALUE_SPEC
