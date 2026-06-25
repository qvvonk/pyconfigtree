from __future__ import annotations


__all__ = [
    'bool_serializer',
    'bool_deserializer',
    'BoolParameter',
]


from typing import Any

from .base import TypedParameter


def bool_serializer(value: bool) -> bool:
    return value


def bool_deserializer(value: Any) -> bool:
    return bool(value)


class BoolParameter(TypedParameter[bool]):
    _DEFAULT_SERIALIZER = staticmethod(bool_serializer)
    _DEFAULT_DESERIALIZER = staticmethod(bool_deserializer)
    _VALUE_TYPE = bool

    async def on(self, save: bool = True, run_hook: bool = True) -> None:
        await self.set_value(True, skip_deserializer=True, save=save, run_hook=run_hook)

    async def off(self, save: bool = True, run_hook: bool = True) -> None:
        await self.set_value(False, skip_deserializer=True, save=save, run_hook=run_hook)

    async def toggle(self, save: bool = True, run_hook: bool = True) -> None:
        await self.set_value(not self.value, skip_deserializer=True, save=save, run_hook=run_hook)

    async def next_value(self, save: bool = True, run_hook: bool = True) -> bool:
        await self.toggle(save=save, run_hook=run_hook)
        return self.value
