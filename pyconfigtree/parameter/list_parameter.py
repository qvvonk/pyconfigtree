from __future__ import annotations

import json
from typing import Any, Generic, TypeVar, cast
from copy import deepcopy
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


def list_serializer(value: list[Any], node: 'ListParameter[Any]') -> list[ALLOWED_TYPES]:
    return _serialize_list(value)


def list_deserializer(value: Any, node: 'ListParameter[Any]') -> list[Any]:
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


def list_accepts(value: object, node: 'ListParameter[Any]') -> bool:
    return isinstance(value, list) and all(_is_serializable_list_item(item) for item in value)


class ListParameter(MutableParameter[list[T]], Generic[T]):
    SPEC = ValueSpec(
        serializer=list_serializer,
        deserializer=list_deserializer,
        validator=list_accepts,
    )

    def __init__(
        self,
        node_id: str,
        *,
        item_deserializer: Callable[[Any], T] | None = None,
        item_validator: Callable[[T, Self], Awaitable[None]] | None = None,
        **kwargs: Unpack[_MutableParameterKwargs[Self, list[T]]],
    ) -> None:
        self.item_deserializer = item_deserializer
        self.item_validator = item_validator
        super().__init__(node_id=node_id, **kwargs)

    @property
    def value(self) -> list[T]:
        return deepcopy(self._value)

    async def add_items(
        self,
        *items: T,
        deserialize: bool = True,
        run_hook: bool = True,
        save: bool = True,
    ) -> None:
        async with self._changing_lock:
            old_value = deepcopy(self._value)
            if deserialize:
                deserialized = [self.deserialize_item(i) for i in items]
            else:
                deserialized = list(items)
            for item in deserialized:
                self._ensure_value_type([item])
                await self.validate_item(deepcopy(item))

            new_value = deepcopy(old_value)
            new_value.extend(deserialized)
            await self.validate(deepcopy(new_value))
            self._value = new_value
            if save:
                await self._save_with_rollback(old_value)

        if run_hook:
            await self.run_hook(ParameterHookTypes.PARAMETER_VALUE_CHANGED, self)

    async def pop_items(self, *indexes: int, run_hook: bool = True, save: bool = True) -> None:
        async with self._changing_lock:
            result_indexes = []
            for index in indexes:
                if index < 0 or index >= len(self.value) or index in result_indexes:
                    continue
                result_indexes.append(index)
            if not result_indexes:
                return

            result_indexes.sort(reverse=True)

            old_value = deepcopy(self._value)
            new_value = deepcopy(old_value)
            for i in result_indexes:
                new_value.pop(i)
            await self.validate(deepcopy(new_value))
            self._value = new_value

            if save:
                await self._save_with_rollback(old_value)

        if run_hook:
            await self.run_hook(ParameterHookTypes.PARAMETER_VALUE_CHANGED, self)

    async def insert_items(
        self,
        *items: tuple[T, int],
        deserialize: bool = True,
        run_hook: bool = True,
        save: bool = True,
    ) -> None:
        async with self._changing_lock:
            old_value = deepcopy(self._value)
            if deserialize:
                deserialized = [(self.deserialize_item(item), index) for item, index in items]
            else:
                deserialized = list(items)

            for item_tuple in deserialized:
                self._ensure_value_type([item_tuple[0]])
                await self.validate_item(deepcopy(item_tuple[0]))

            deserialized.sort(key=lambda item: item[1], reverse=True)
            new_value = deepcopy(old_value)
            for item, index in deserialized:
                new_value.insert(index, item)

            await self.validate(deepcopy(new_value))
            self._value = new_value
            if save:
                await self._save_with_rollback(old_value)

        if run_hook:
            await self.run_hook(ParameterHookTypes.PARAMETER_VALUE_CHANGED, self)

    async def validate_item(self, item: T) -> None:
        if self.item_validator is not None:
            await self.item_validator(item, self)

    async def _save_with_rollback(self, old_value: list[T]) -> None:
        try:
            await self.save()
        except Exception:
            self._value = old_value
            raise

    def deserialize_item(self, item: Any) -> T:
        return cast(T, item) if self.item_deserializer is None else self.item_deserializer(item)
