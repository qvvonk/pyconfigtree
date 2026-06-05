from ..base import Node
from typing import Any, Generic, TypeVar
from collections.abc import Callable


T = TypeVar('T')


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


class MutableParameter(Parameter[T], Generic[T]):
    def __init__(
        self,
        node_id: str,
        value: T,
        default_value: T,
        default_factory: Callable[[], T],
        name: str = '',
        description: str = '',
    ) -> None:
        super().__init__(
            node_id=node_id,
            value=value,
            name=name,
            description=description
        )
