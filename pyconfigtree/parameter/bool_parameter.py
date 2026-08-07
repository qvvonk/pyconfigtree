from __future__ import annotations


__all__ = [
    'bool_serializer',
    'bool_deserializer',
    'BoolParameter',
]


from typing import Any

from pyconfigtree.exceptions import DeserializationError

from .base import ValueSpec, MutableParameter


def bool_serializer(node: 'BoolParameter', value: bool) -> bool:
    return value


def bool_deserializer(node: 'BoolParameter', value: Any) -> bool:
    if type(value) is bool:
        return value
    if type(value) is int and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized_value = value.strip().casefold()
        if normalized_value in {'true', '1', 'yes', 'on'}:
            return True
        if normalized_value in {'false', '0', 'no', 'off'}:
            return False
    raise DeserializationError(f'Unable to deserialize {value!r} as a boolean.')


def bool_validator(node: BoolParameter, value: object) -> bool:
    return type(value) is bool


BOOL_VALUE_SPEC = ValueSpec(
    serializer=bool_serializer,
    deserializer=bool_deserializer,
    validator=bool_validator,
)


class BoolParameter(MutableParameter[bool]):
    SPEC = BOOL_VALUE_SPEC

    async def on(self, save: bool = True, run_hook: bool = True, validate: bool = True) -> None:
        await self.set_value(
            True,
            deserialize=False,
            validate=validate,
            run_hook=run_hook,
            save=save,
        )

    async def off(self, save: bool = True, run_hook: bool = True, validate: bool = True) -> None:
        await self.set_value(
            False,
            deserialize=False,
            validate=validate,
            run_hook=run_hook,
            save=save,
        )

    async def toggle(
        self, save: bool = True, run_hook: bool = True, validate: bool = True
    ) -> bool:
        await self.set_value(
            not self.value,
            deserialize=False,
            validate=validate,
            run_hook=run_hook,
            save=save,
        )
        return self.value
