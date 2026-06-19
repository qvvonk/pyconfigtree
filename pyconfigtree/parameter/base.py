from ..base import Node
from typing import Any, Generic, TypeVar
from collections.abc import Callable
from abc import ABC, abstractmethod
from asyncio import Lock

from ..source.base import NodeInfo, NodeType, ALLOWED_TYPES

T = TypeVar('T')
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
        self,
        node_id: str,
        name: str = '',
        description: str = '',
        value: T = UNSET,
        default_value: T = UNSET,
        default_factory: Callable[[], T] = UNSET,
    ) -> None:
        if default_value is UNSET and default_factory is UNSET:
            raise ValueError('Default value or default factory must be set.')

        self._default_factory = default_factory
        self._default_value = default_value
        self._changing_lock = Lock()

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
        skip_converter: bool = False,
        skip_validator: bool = False,
        skip_hook: bool = False,
        save: bool = True,
    ) -> None:
        async with self._changing_lock:
            if not skip_converter:
                ...
            if not skip_validator:
                ...

            self._value = value
            if save:
                ...

        if not skip_hook:
            ...

    @abstractmethod
    def serialize(self) -> ALLOWED_TYPES: ...

    @abstractmethod
    def deserialize(self, value: ALLOWED_TYPES) -> T: ...