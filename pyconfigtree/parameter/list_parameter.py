from __future__ import annotations

import json
from typing import Any, Generic, TypeVar, cast
from json import JSONDecodeError
from collections.abc import Callable, Awaitable

from typing_extensions import Self, Unpack

from pyconfigtree.exceptions import SerializationError, DeserializationError
from pyconfigtree.source.base import ALLOWED_TYPES

from .base import (
    ValueSpec,
    MutableParameter,
    ParameterHookTypes,
    _MutableParameterKwargs,
)


__all__ = [
    'list_serializer',
    'list_deserializer',
    'ListParameter',
]


def _serialize_list(value: list[Any]) -> list[ALLOWED_TYPES]:
    result: list[ALLOWED_TYPES] = []
    for i in value:
        if type(i) in (int, str, float, bool):
            result.append(i)
        elif isinstance(i, list):
            result.append(_serialize_list(i))
        else:
            raise SerializationError(f'Unable to serialize list item {i!r}.')
    return result


def list_serializer(node: 'ListParameter[Any]', value: list[Any]) -> list[ALLOWED_TYPES]:
    return _serialize_list(value)


def list_deserializer(node: 'ListParameter[Any]', value: Any) -> list[Any]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except JSONDecodeError as exc:
            raise DeserializationError(f'Unable to convert string {value!r} to list.') from exc

    if isinstance(value, list):
        return [node.deserialize_item(i) for i in value]

    raise DeserializationError(f'Unable to convert {value!r} to list.')


def _is_serializable_list_item(value: object) -> bool:
    if type(value) in (int, str, float, bool):
        return True
    if isinstance(value, list):
        return all(_is_serializable_list_item(item) for item in value)
    return False


T = TypeVar('T')


def list_accepts(node: 'ListParameter[Any]', value: object) -> bool:
    return isinstance(value, list) and all(_is_serializable_list_item(item) for item in value)


LIST_VALUE_SPEC = ValueSpec(
    serializer=list_serializer,
    deserializer=list_deserializer,
    validator=list_accepts,
)


class ListParameter(MutableParameter[list[T]], Generic[T]):
    SPEC = LIST_VALUE_SPEC

    def __init__(
        self,
        node_id: str,
        *,
        item_deserializer: Callable[[Any], T] | None = None,
        add_item_validator: Callable[[T, ListParameter[T]], Awaitable[None]] | None = None,
        remove_item_validator: Callable[[T, ListParameter[T]], Awaitable[None]] | None = None,
        **kwargs: Unpack[_MutableParameterKwargs[Self, list[T]]],
    ) -> None:
        self.item_deserializer = item_deserializer
        self.add_item_validator = add_item_validator
        self.remove_item_validator = remove_item_validator
        super().__init__(node_id=node_id, **kwargs)

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
                item = self.deserialize_item(item)
            self._ensure_value_type([item])
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
        return cast(T, item) if self.item_deserializer is None else self.item_deserializer(item)
