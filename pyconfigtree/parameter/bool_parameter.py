from __future__ import annotations


__all__ = [
    'bool_serializer',
    'bool_deserializer',
    'BoolParameter',
]


from typing import Any

from .base import TypedParameter
from pyconfigtree.exceptions import DeserializationError, ValidationError


def bool_serializer(value: bool) -> bool:
    return value


def bool_deserializer(value: Any) -> bool:
    return bool(value)


class BoolParameter(TypedParameter[bool]):
    DEFAULT_SERIALIZER = bool_serializer
    DEFAULT_DESERIALIZER = bool_deserializer

    async def on(self, save: bool = True, run_hook: bool = True) -> None:
        await self.set_value(True, skip_deserializer=True, save=save, run_hook=run_hook)

    async def off(self, save: bool = True, run_hook: bool = True) -> None:
        await self.set_value(False, skip_deserializer=True, save=save, run_hook=run_hook)

    async def toggle(self, save: bool = True, run_hook: bool = True) -> None:
        await self.set_value(not self.value, skip_deserializer=True, save=save, run_hook=run_hook)

    async def next_value(self, save: bool = True, run_hook: bool = True) -> bool:
        await self.toggle(save=save, run_hook=run_hook)
        return self.value

    def deserialize(self, value: Any) -> bool:
        res = super().deserialize(value)
        if not isinstance(res, bool):
            raise DeserializationError(
                f'Deserialized value must be an instance of bool, not {type(res)}.'
            )
        return res

    async def validate(self, value: Any) -> None:
        if not isinstance(value, bool):
            raise ValidationError(
                f'Value of `BoolParameter` must be an instance of bool, not {type(value)}.'
            )
        return await (super().validate(value))