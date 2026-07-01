from __future__ import annotations

import json
from typing import Generic, TypeVar, Iterable
from json import JSONDecodeError
from collections.abc import Callable

from typing_extensions import Unpack, Self

from pyconfigtree.exceptions import DeserializationError

from .base import ALLOWED_TYPES, _TypedParameterKwargs


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
        add_item_validator: Callable[[T, Self], None] | None = None,
        remove_item_validator: Callable[[T], None] | None = None,
        **kwargs: Unpack[_TypedParameterKwargs[list[T], Self]],
    ) -> None:
        super().__init__(node_id=node_id, **kwargs)
        self.item_deserializer = item_deserializer
        self.add_item_validator = add_item_validator
        self.remove_item_validator = remove_item_validator