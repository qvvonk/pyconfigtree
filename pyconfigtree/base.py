from __future__ import annotations


__all__ = ['Node', 'leaf', 'container']

from typing import Any, Literal, TypeVar, ClassVar, TypeAlias, overload
from enum import Enum, auto
from types import MappingProxyType
from collections.abc import Mapping, Callable, Iterable, Sequence, Awaitable, Generator

from .source import ConfigSource
from .exceptions import LeafNodeError, NodeLoopError, NoSourceError, NodeDuplicateError
from .source.base import NodeInfo, NodeType


T = TypeVar('T', bound='Node')

ON_NODE_ATTACHED_HOOK: TypeAlias = Callable[['Node', 'Node'], Awaitable[Any]]
ON_NODE_DETACHED_HOOK: TypeAlias = Callable[['Node', 'Node'], Awaitable[Any]]


class BaseHookTypes(Enum):
    ON_NODE_ATTACHED = auto()
    ON_NODE_DETACHED = auto()


def leaf(cls: type[T]) -> type[T]:
    cls._allow_children = False
    return cls


def container(cls: type[T]) -> type[T]:
    cls._allow_children = True
    return cls


class SubnodesController:
    def __init__(self, owner: Node):
        self.owner = owner

        self.id_to_node: dict[str, Node] = {}
        self.node_to_id: dict[Node, str] = {}
        self.virtual_nodes: dict[str, Node] = {}
        self.persistent_nodes: dict[str, Node] = {}

    def __contains__(self, node: Node | str) -> bool:
        if not isinstance(node, (Node, str)):
            return False

        return node in self.id_to_node if isinstance(node, str) else node in self.node_to_id

    @overload
    def __getitem__(self, node: str) -> Node: ...

    @overload
    def __getitem__(self, node: T) -> T: ...

    def __getitem__(self, node: str | T) -> Node | T:
        if isinstance(node, str):
            if node not in self.id_to_node:
                raise KeyError(f'{self.owner.path!r} does not contain node with ID {node!r}.')
            return self.id_to_node[node]
        if node not in self.node_to_id:
            raise KeyError(f'{self.owner.path!r} does not contain node {node!r}.')
        return node

    def get_node_id(self, node: Node | str) -> str:
        return self.node_to_id[self[node]]

    def gen_virtual_node_id(self, node: Node) -> str:
        id_template = f'__virtual_{node.id}_{{index}}__'

        index = 0
        while True:
            id = id_template.format(index=index)
            if id not in self.id_to_node:
                return id
            index += 1

    def add_node(self, node: Node, *, virtual: bool = False) -> None:
        node_id = node.id if not virtual else self.gen_virtual_node_id(node)

        if node_id in self.id_to_node:
            raise NodeDuplicateError(
                f'Node {self.owner.path!r} already has a subnode with id {node_id!r}.'
            )
        if node in self.node_to_id:
            raise NodeDuplicateError(f'Node {self.owner.path!r} already has a subnode {node!r}.')

        self.id_to_node[node_id] = node
        self.node_to_id[node] = node_id
        (self.virtual_nodes if virtual else self.persistent_nodes)[node_id] = node

    @overload
    def remove_node(self, node: str) -> Node | None: ...

    @overload
    def remove_node(self, node: T) -> T | None: ...

    def remove_node(self, node: str | T) -> Node | T | None:
        try:
            node_obj = self[node]
        except KeyError:
            return None
        node_id = self.get_node_id(node_obj)

        self.node_to_id.pop(node_obj)
        self.id_to_node.pop(node_id)
        self.persistent_nodes.pop(node_id, None)
        self.virtual_nodes.pop(node_id, None)
        return node_obj

    def is_virtual(self, node: Node | str) -> bool:
        return self.get_node_id(self[node]) in self.virtual_nodes


class Node:
    _allow_children: ClassVar[bool] = True

    def __init__(
        self,
        node_id: str,
        name: str = '',
        description: str = '',
        source: ConfigSource | None = None,
        metadata: dict[str, Any] | None = None,
        on_node_attached_hook: ON_NODE_ATTACHED_HOOK | None = None,
        on_node_detached_hook: ON_NODE_DETACHED_HOOK | None = None,
    ):
        self._id: str = node_id
        self._name = name
        self._description = description
        self._parent: Node | None = None

        self._subnodes = SubnodesController(self)
        self._subnodes_proxy = MappingProxyType(self._subnodes.id_to_node)
        self._virtual_nodes = MappingProxyType(self._subnodes.virtual_nodes)
        self._persistent_nodes = MappingProxyType(self._subnodes.persistent_nodes)
        self._source = source
        self._metadata = metadata if metadata is not None else {}

        self._hooks: dict[Any, Callable[..., Awaitable[Any]] | None] = {}
        self.on_node_attached_hook = on_node_attached_hook
        self.on_node_detached_hook = on_node_detached_hook

    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata

    @property
    def hooks(self) -> Mapping[Any, Callable[..., Awaitable[Any]] | None]:
        return MappingProxyType(self._hooks)

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parent(self) -> Node | None:
        return self._parent

    @property
    def subnodes(self) -> Mapping[str, Node]:
        return self._subnodes_proxy

    @property
    def persistent_subnodes(self) -> Mapping[str, Node]:
        return self._persistent_nodes

    @property
    def virtual_subnodes(self) -> Mapping[str, Node]:
        return self._virtual_nodes

    @property
    def root(self) -> Node:
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    @property
    def path(self) -> tuple[str, ...]:
        path = reversed([i.id for i in self.chain_to_root()])
        return tuple(path)[1:]

    @property
    def source(self) -> ConfigSource | None:
        return self._source

    @property
    def inherited_source(self) -> ConfigSource | None:
        if self.source is not None:
            return self._source
        if self.parent is not None:
            return self.parent.inherited_source
        return None

    @property
    def on_node_attached_hook(self) -> ON_NODE_ATTACHED_HOOK | None:
        return self._hooks.get(BaseHookTypes.ON_NODE_ATTACHED)

    @on_node_attached_hook.setter
    def on_node_attached_hook(self, hook: ON_NODE_ATTACHED_HOOK | None) -> None:
        self._hooks[BaseHookTypes.ON_NODE_ATTACHED] = hook

    @property
    def on_node_detached_hook(self) -> ON_NODE_DETACHED_HOOK | None:
        return self._hooks.get(BaseHookTypes.ON_NODE_DETACHED)

    @on_node_detached_hook.setter
    def on_node_detached_hook(self, hook: ON_NODE_DETACHED_HOOK | None) -> None:
        self._hooks[BaseHookTypes.ON_NODE_DETACHED] = hook

    def attach_node(self, node: T, *, virtual: bool = False) -> T:
        self.check_can_attach_node(node, virtual=virtual)
        self._subnodes.add_node(node, virtual=virtual)
        if not virtual:
            node._parent = self
        return node

    async def attach_node_with_hooks(self, node: T, *, virtual: bool = False) -> T:
        node = self.attach_node(node, virtual=virtual)
        if not virtual:
            await self.run_hook(BaseHookTypes.ON_NODE_ATTACHED, node, self)
        return node

    @overload
    def detach_node(self, node: str) -> Node | None: ...

    @overload
    def detach_node(self, node: T) -> T | None: ...

    def detach_node(self, node: T | str) -> T | Node | None:
        is_virtual = self._subnodes.is_virtual(node)
        to_return = self._subnodes.remove_node(node)
        if not is_virtual:
            to_return._parent = None  # type: ignore[union-attr]  # ->
            # if to_return is None, is_virtual would raise an exception.
        return to_return

    @overload
    async def detach_node_with_hooks(self, node: str) -> Node | None: ...

    @overload
    async def detach_node_with_hooks(self, node: T) -> T | None: ...

    async def detach_node_with_hooks(self, node: T | str) -> T | Node | None:
        is_virtual = self._subnodes.is_virtual(node)
        node_obj = self.detach_node(node)
        if node_obj is None:
            return None

        if not is_virtual:
            await self.run_hook(BaseHookTypes.ON_NODE_DETACHED, node_obj, self)
        return node_obj

    def get_node_info(self, same_source_only: bool = True) -> NodeInfo:
        subnodes = self.persistent_subnodes

        return NodeInfo(
            id=self.id,
            name=self.name,
            description=self.description,
            type=NodeType.CONTAINER,
            subnodes={
                k: i.get_node_info(same_source_only=same_source_only)
                for k, i in subnodes.items()
                if (same_source_only and self.inherited_source == i.inherited_source)
                or not same_source_only
            },
        )

    def check_can_be_attached(self, *, virtual: bool = False) -> None:
        if not virtual:
            if self._parent is not None:
                raise RuntimeError(
                    f'Node {self.path} already has a parent and '
                    f'cannot be attached to another node.',
                )

    def check_can_attach_node(self, node: Node, virtual: bool = False) -> None:
        if not self._allow_children:
            raise LeafNodeError(f'Node of type {type(self)} cannot contain subnodes.')

        node.check_can_be_attached(virtual=virtual)

        if not virtual:
            if node is self:
                raise NodeLoopError('Node cannot be attached to itself.')

            for i in node.chain_to_tails():
                if i is self:
                    raise NodeLoopError('Node loop.')  # todo

    def chain_to_root(self) -> Generator[Node, None, None]:
        node: Node | None = self
        while node is not None:
            yield node
            node = node.parent

    def chain_to_tails(self) -> Generator[Node, None, None]:
        yield self
        for i in self.persistent_subnodes.values():
            yield from i.chain_to_tails()

    def is_child_of(self, node: Node | Sequence[str], direct: bool = True) -> bool:
        path = node.path if isinstance(node, Node) else tuple(node)
        self_path = self.path

        if direct:
            if len(self_path) != len(path) + 1:
                return False
        else:
            if len(self_path) <= len(path):
                return False

        return self_path[: len(path)] == path

    def is_parent_of(self, node: Node | Sequence[str], direct: bool = True) -> bool:
        path = node.path if isinstance(node, Node) else node
        self_path = self.path

        if direct:
            if len(self_path) != len(path) - 1:
                return False
        else:
            if len(self_path) >= len(path):
                return False

        return path[: len(self_path)] == self_path

    async def save(self, same_source_only: bool = True) -> None:
        if self.source is None:
            if not self.inherited_source:
                raise NoSourceError(f'Cannot save node {self.path}: source not specified.')
            for i in self.chain_to_root():
                if i.source is not None:
                    return await i.save(same_source_only=same_source_only)
        else:
            node_info = self.get_node_info(same_source_only=same_source_only)
            return await self.source.save(data=node_info)

    async def load(self, validate: bool = True, run_hook: bool = False) -> None:
        if self.source is None:
            raise NoSourceError(f'Cannot load node {self.path}: source not specified.')

        data = await self.source.load()
        await self.load_from_dict(data, validate=validate, run_hook=run_hook)

        for source in self.persistent_subnodes.values():
            await source.load(validate=validate, run_hook=run_hook)

    async def load_from_dict(
        self,
        data_dict: dict[str, Any],
        validate: bool = True,
        run_hook: bool = False,
    ) -> None:
        persistent_subnodes = self.persistent_subnodes

        for k, data in data_dict.items():
            if k not in persistent_subnodes:
                continue
            node = self.subnodes[k]
            await node.load_from_dict(
                data_dict=data_dict[k],
                validate=validate,
                run_hook=run_hook,
            )

    async def run_hook(self, hook_identifier: Any, *args: Any, **kwargs: Any) -> Any:
        hook = self.hooks.get(hook_identifier)
        if hook is not None:
            await hook(*args, **kwargs)
        if self.parent is not None:
            await self.parent.run_hook(hook_identifier, *args, **kwargs)

    @overload
    def get_node(self, path: Iterable[str], _raise: Literal[True] = True) -> Node: ...

    @overload
    def get_node(self, path: Iterable[str], _raise: Literal[False]) -> Node | None: ...

    @overload
    def get_node(self, path: Iterable[str], _raise: bool = True) -> Node | None: ...

    def get_node(self, path: Iterable[str], _raise: bool = True) -> Node | None:
        if not path:
            return self

        node = self
        for i in path:
            if i not in node.subnodes:
                if not _raise:
                    return None
                raise LookupError(
                    f'Cannot find node `{path}` in `{self.path}`. '
                    f'Node {node.path} does not contain subnode with id `{i}`.'
                )
            node = node.subnodes[i]
        return node
