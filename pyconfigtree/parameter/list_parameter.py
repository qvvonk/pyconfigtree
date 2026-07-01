from __future__ import annotations

import json
from typing import Generic, TypeVar
from json import JSONDecodeError
from collections.abc import Callable, Iterable, Awaitable

from typing_extensions import Self, Unpack

from pyconfigtree.exceptions import DeserializationError

from .base import ALLOWED_TYPES, ParameterHookTypes, _TypedParameterKwargs


__all__ = [
    'list_serializer',
    'list_deserializer',
    'ListParameter',
]


from typing import Any

from pyconfigtree.exceptions import SerializationError

from .base import TypedParameter


def list_serializer(value: list[Any]) -> list[ALLOWED_TYPES]:
    result: list[ALLOWED_TYPES] = []
    for i in value:
        if isinstance(i, (int, str, float, bool)):
            result.append(i)
        elif isinstance(i, list):
            result.append(list_serializer(i))
        else:
            raise SerializationError(f'Unable to serialize list item {i!r}.')
    return result


def list_deserializer(value: Any) -> list[Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except JSONDecodeError:
            raise DeserializationError(f'Unable to convert string {value!r} to list.')

    if isinstance(value, Iterable):
        return [str(i) if not isinstance(i, (int, str, float, bool)) else i for i in value]

    raise DeserializationError(f'Unable to convert {value!r} to list of strings.')


T = TypeVar('T')


class ListParameter(TypedParameter[list[T]], Generic[T]):
    _DEFAULT_SERIALIZER = staticmethod(list_serializer)
    _DEFAULT_DESERIALIZER = staticmethod(list_deserializer)
    _VALUE_TYPE = list

    def __init__(
        self,
        node_id: str,
        *,
        item_deserializer: Callable[[Any], T] | None = None,
        add_item_validator: Callable[[T, Self], Awaitable[None]] | None = None,
        remove_item_validator: Callable[[T, Self], Awaitable[None]] | None = None,
        **kwargs: Unpack[_TypedParameterKwargs[list[T], Self]],
    ) -> None:
        super().__init__(node_id=node_id, **kwargs)
        self.item_deserializer = item_deserializer
        self.add_item_validator = add_item_validator
        self.remove_item_validator = remove_item_validator

    async def add_item(
        self,
        item: T,
        deserialize: bool = True,
        validate: bool = True,
        run_hook: bool = True,
        save: bool = True,
    ) -> None:
        async with self._changing_lock:
            if deserialize:
                item = await self.deserialize_item(item)
            if validate:
                await self.add_item_validate(item)

            self._value.append(item)
            if save:
                await self.save()

        if run_hook:
            await self.run_hook(ParameterHookTypes.PARAMETER_VALUE_CHANGED, self)

    async def pop_item(
        self, index: int, validate: bool = True, run_hook: bool = True, save: bool = True
    ) -> T | None:
        if index < 0 or index >= len(self.value):
            return None

        async with self._changing_lock:
            if validate:
                item = self._value[index]
                await self.remove_item_validate(item)

            result = self._value.pop(index)
            if save:
                await self.save()

        if run_hook:
            await self.run_hook(ParameterHookTypes.PARAMETER_VALUE_CHANGED, self)

        return result

    async def remove_item(
        self, item: T, validate: bool = True, run_hook: bool = True, save: bool = True
    ) -> None:
        if item not in self._value:
            return

        async with self._changing_lock:
            if validate:
                await self.remove_item_validate(item)

            self._value.remove(item)
            if save:
                await self.save()

        if run_hook:
            await self.run_hook(ParameterHookTypes.PARAMETER_VALUE_CHANGED, self)

    async def add_item_validate(self, item: T) -> None:
        if self.add_item_validator is not None:
            await self.add_item_validator(item, self)

    async def remove_item_validate(self, item: T) -> None:
        if self.remove_item_validator is not None:
            await self.remove_item_validator(item, self)

    def deserialize_item(self, item: Any) -> T:
        return item if self.item_deserializer is None else self.item_deserializer(item)
