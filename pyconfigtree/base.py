from collections.abc import Generator, Iterable
from typing import Optional, Union
from types import MappingProxyType


class Node:
    def __init__(self, node_id: str):
        self._id: str = node_id
        self._parent: Optional['Node'] = None
        self._subnodes: dict[str, Node] = {}
        self._subnodes_proxy = MappingProxyType(self._subnodes)

    @property
    def id(self) -> str:
        return self._id

    @property
    def parent(self) -> Optional['Node']:
        return self._parent

    @parent.setter
    def parent(self, value: Optional['Node']) -> None:
        self._parent = value  # todo: checks

    @property
    def subnodes(self) -> MappingProxyType[str, 'Node']:
        return self._subnodes_proxy

    @property
    def root(self) -> 'Node':
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    @property
    def path(self) -> tuple[str, ...]:
        path = [i.id for i in self.chain_to_root()]
        path.reverse()
        return tuple(path)

    def chain_to_root(self) -> Generator['Node', None, None]:
        node = self
        while node is not None:
            yield node
            node = node.parent

    def chain_to_tails(self) -> Generator['Node', None, None]:
        yield self
        for i in self.subnodes.values():
            yield from i.chain_to_tails()

    def is_child_of(self, node: Union['Node', Iterable[str]], direct: bool = True) -> bool:
        path = node.path if isinstance(node, Node) else tuple(node)
        self_path = self.path

        if direct:
            if len(self_path) != len(path) + 1:
                return False
        else:
            if len(self_path) <= len(path):
                return False

        return self_path[:len(path)] == path

    def is_parent_of(self, node: Union['Node', Iterable[str]], direct: bool = True) -> bool:
        path = node.path if isinstance(node, Node) else node
        self_path = self.path

        if direct:
            if len(self_path) != len(path) - 1:
                return False
        else:
            if len(self_path) >= len(path):
                return False

        return path[:len(self_path)] == self_path
