from ..base import Node
from typing import Any, Generic, TypeVar


T = TypeVar('T')


class Parameter(Node, Generic[T]):
    def __init__(self, node_id: str, value: T) -> None:
        super().__init__(node_id=node_id)
        self._value = value

    @property
    def value(self) -> T:
        return self._value


class MutableParameter(Node):
    ...
