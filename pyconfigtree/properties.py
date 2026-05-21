from .base import Node
from typing import Union, overload, Literal, TypeVar
from collections.abc import Awaitable


T = TypeVar('T', bound=Node)


class Properties(Node):
    def __init__(self, node_id: str):
        super().__init__(node_id)

    def _attach_node(self, node: T) -> T:
        if node.id in self.subnodes:
            raise ValueError(f'Node {self.path} already has subnode with id {node.id}')

        node.parent = self
        self._subnodes[node.id] = node
        return node

    async def attach_node(self, node: T, run_hook: bool = True) -> T:
        node = self._attach_node(node)
        if run_hook:
            # run hook
            ...
        return node

    @overload
    def _detach_node(self, node: T) -> T: ...

    @overload
    def _detach_node(self, node: str) -> Node:
        ...

    def _detach_node(self, node: T | str) -> T | Node:
        node_id = node if isinstance(node, str) else node.id
        if node_id not in self.subnodes:
            raise KeyError(f'Node {self.path} has no subnode with id {node_id}.')

        node.parent = None
        del self._subnodes[node_id]
        return node

    @overload
    def detach_node(self, node: T) -> T: ...

    @overload
    def detach_node(self, node: str) -> Node: ...

    async def detach_node(self, node: T | str, run_hook: bool = True) -> T | Node:
        node = self._detach_node(node)
        if run_hook:
            # run hook
            ...
        return node
