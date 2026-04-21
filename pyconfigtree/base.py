from collections.abc import Generator
from typing import Optional
from types import MappingProxyType


class Node:
    def __init__(self, node_id: str):
        self._id: str = node_id
        self._parent: Optional['Node'] = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def parent(self) -> Optional['Node']:
        return self._parent

    @parent.setter
    def parent(self, value: Optional['Node']) -> None:
        self._parent = value

    @property
    def root(self) -> 'Node':
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    def chain_to_root(self) -> Generator['Node', None, None]:
        node = self
        while node is not None:
            yield node
            node = node.parent


class ContainerNode(Node):
    def __init__(self, node_id: str) -> None:
        super().__init__(node_id)
        self._subnodes: dict[str, Node] = {}

    @property
    def subnodes(self) -> MappingProxyType[str, 'Node']:
        return MappingProxyType(self._subnodes)
