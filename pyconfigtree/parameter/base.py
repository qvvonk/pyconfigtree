from ..base import Node
from typing import Any, Generic, TypeVar
from collections.abc import Callable
from abc import ABC, abstractmethod
from asyncio import Lock

from ..source.base import NodeInfo, NodeType, ALLOWED_TYPES

T = TypeVar('T')
S = TypeVar('S')
UNSET = object()


class Parameter(Node, Generic[T]):
    def __init__(
        self,
        node_id: str,
        value: T,
        name: str = '',
        description: str = '',
    ) -> None:
        super().__init__(node_id=node_id, name=name, description=description)
        self._value = value

    @property
    def value(self) -> T:
        return self._value


class MutableParameter(Parameter[T], ABC, Generic[T]):
    def __init__(
        self: S,
        node_id: str,
        name: str = '',
        description: str = '',
        value: T = UNSET,
        default_value: T = UNSET,
        default_factory: Callable[[], T] = UNSET,
        validator: Callable[[S, T], None] = None,
        serializer: Callable[[S], ALLOWED_TYPES] = None,
        deserializer: Callable[[Any], T] = None,
    ) -> None:
        if default_value is UNSET and default_factory is UNSET:
            raise ValueError('Default value or default factory must be set.')

        self._default_factory = default_factory
        self._default_value = default_value
        self._changing_lock = Lock()
        self._validator = validator
        self._serializer = serializer
        self._deserializer = deserializer

        super().__init__(
            node_id=node_id,
            value=value if value is not UNSET else self.default_value,
            name=name,
            description=description
        )

    @property
    def default_value(self) -> T:
        if self._default_factory is not UNSET:
            return self._default_factory()
        return self._default_value

    @property
    def serializer(self) -> Callable[[S], ALLOWED_TYPES] | None:
        return self._serializer

    @property
    def deserializer(self) -> Callable[[Any], T] | None:
        return self._deserializer

    @property
    def validator(self) -> Callable[[S, T], None] | None:
        return self._validator

    def get_node_info(self, same_source_only: bool = True) -> NodeInfo:
        return NodeInfo(
            id=self.id,
            name=self.name,
            description=self.description,
            type=NodeType.LEAF,
            value=self.serialize()
        )

    async def set_value(
        self,
        value: Any,
        *,
        skip_deserializer: bool = False,
        skip_validator: bool = False,
        skip_hook: bool = False,
        save: bool = True,
    ) -> None:
        async with self._changing_lock:
            if not skip_deserializer:
                value = self.deserialize(value)
            if not skip_validator:
                self.validate(value)

            self._value = value
            if save:
                ...

        if not skip_hook:
            ...

    def serialize(self) -> ALLOWED_TYPES:
        if self._serializer:
            return self._serializer(self._value)

    def validate(self, value: T) -> None:
        if not self._validator:
            return
        self._validator(self, value)