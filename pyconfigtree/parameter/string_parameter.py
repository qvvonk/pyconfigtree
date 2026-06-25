from __future__ import annotations


__all__ = [
    'str_serializer',
    'str_deserializer',
    'StringParameter',
]


from typing import Any

from .base import TypedParameter
from pyconfigtree.exceptions import DeserializationError, ValidationError


def str_serializer(value: str) -> str:
    return value


def str_deserializer(value: Any) -> str:
    return str(value)


class StringParameter(TypedParameter[str]):
    DEFAULT_SERIALIZER = str_serializer
    DEFAULT_DESERIALIZER = str_deserializer

    def deserialize(self, value: Any) -> str:
        res = super().deserialize(value)
        if not isinstance(res, str):
            raise DeserializationError(
                f'Deserialized value of `StringParameter` '
                f'must be an instance of `str`, not {type(res)}.'
            )
        return res

    async def validate(self, value: Any) -> None:
        if not isinstance(value, str):
            raise ValidationError(
                f'Value of `StringParameter` must be an instance of `str`, not {type(value)}.'
            )
        return await (super().validate(value))