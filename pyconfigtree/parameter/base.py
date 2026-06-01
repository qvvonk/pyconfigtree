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

    def _attach_node(self, node):
        raise RuntimeError('Parameter cannot contain subnodes.')

    async def attach_node(self, node: T, run_hook: bool = True) -> T:
        raise RuntimeError('Parameter cannot contain subnodes.')


class MutableParameter(Node):
    ...
