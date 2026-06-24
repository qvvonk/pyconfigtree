from collections.abc import Generator, Iterable, Callable, Awaitable
from typing import Optional, Union, TypeVar, Any, TypeAlias
from types import MappingProxyType
from .source import ConfigSource
from .source.base import NodeInfo, NodeType
from enum import Enum, auto


T = TypeVar('T', bound='Node')

ON_NODE_ATTACHED_HOOK: TypeAlias = Callable[['Node', 'Node'], Awaitable[Any]]
ON_NODE_DETACHED_HOOK: TypeAlias = Callable[['Node', 'Node'], Awaitable[Any]]


class BaseHookTypes(Enum):
    ON_NODE_ATTACHED = auto()
    ON_NODE_DETACHED = auto()


class Node:
    _allow_children: bool = True

    def __init__(
        self,
        node_id: str,
        name: str = '',
        description: str = '',
        source: Optional[ConfigSource] = None,
        flags: Optional[set[Any]] = None,
        on_node_attached_hook: Optional[ON_NODE_ATTACHED_HOOK] = None,
        on_node_detached_hook: Optional[ON_NODE_DETACHED_HOOK] = None,
    ):
        self._id: str = node_id
        self._name = name
        self._description = description
        self._parent: Optional['Node'] = None
        self._subnodes: dict[str, Node] = {}
        self._subnodes_proxy = MappingProxyType(self._subnodes)
        self._source = source
        self._flags = flags or set()

        self._hooks: dict[Any, Callable[..., Awaitable[Any]]] = {}
        self.on_node_attached_hook = on_node_attached_hook
        self.on_node_detached_hook = on_node_detached_hook

    @property
    def flags(self) -> frozenset[Any]:
        return frozenset(self._flags)

    @property
    def hooks(self) -> MappingProxyType[Any, Callable[..., Awaitable[Any]]]:
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
    def parent(self) -> Optional['Node']:
        return self._parent

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

    @property
    def source(self) -> Optional[ConfigSource]:
        return self._source

    @property
    def inherited_source(self) -> Optional[ConfigSource]:
        if self.source is not None:
            return self._source
        if self.parent is not None:
            return self.parent.inherited_source
        return None

    @property
    def on_node_attached_hook(self) -> Optional[ON_NODE_ATTACHED_HOOK]:
        return self._hooks.get(BaseHookTypes.ON_NODE_ATTACHED)

    @on_node_attached_hook.setter
    def on_node_attached_hook(self, hook: Optional[ON_NODE_ATTACHED_HOOK]):
        self._hooks[BaseHookTypes.ON_NODE_ATTACHED] = hook

    @property
    def on_node_detached_hook(self) -> Optional[ON_NODE_DETACHED_HOOK]:
        return self._hooks.get(BaseHookTypes.ON_NODE_DETACHED)

    @on_node_detached_hook.setter
    def on_node_detached_hook(self, hook: Optional[ON_NODE_DETACHED_HOOK]) -> None:
        self._hooks[BaseHookTypes.ON_NODE_DETACHED] = hook

    def _attach_node(self, node: T) -> T:
        self.check_can_attach_node(node)
        node._parent = self
        self._subnodes[node.id] = node
        return node

    async def attach_node(self, node: T, run_hook: bool = True) -> T:
        node = self._attach_node(node)
        if run_hook:
            await self.run_hook(BaseHookTypes.ON_NODE_ATTACHED, node, self)
        return node

    def _detach_node(self, node: Union[T, str]) -> Union[T, 'Node']:
        node_id = node if isinstance(node, str) else node.id
        if node_id not in self.subnodes:
            raise KeyError(f'Node {self.path} has no subnode with id {node_id}.')

        node = self._subnodes.pop(node_id)
        node._parent = None
        return node

    async def detach_node(self, node: Union[T, str], run_hook: bool = True) -> Union[T, 'Node']:
        node = self._detach_node(node)
        if run_hook:
            await self.run_hook(BaseHookTypes.ON_NODE_DETACHED, node, self)
        return node

    def get_node_info(self, same_source_only: bool = True) -> NodeInfo:
        return NodeInfo(
            id=self.id,
            name=self.name,
            description=self.description,
            type=NodeType.CONTAINER,
            subnodes={
                k: i.get_node_info(same_source_only=same_source_only)
                for k, i in self.subnodes.items()
                if (same_source_only and self.inherited_source == i.inherited_source)
                or not same_source_only
            }
        )

    def check_can_be_attached(self) -> None:
        if self._parent is not None:
            raise RuntimeError(f'Node {self.path} already has a parent and cannot be attached to another node.')

    def check_can_attach_node(self, node: 'Node') -> None:
        if not self._allow_children:
            raise TypeError(f'Node of type {type(self)} cannot contain subnodes.')

        node.check_can_be_attached()

        if node is self:
            raise ValueError('Node cannot be attached to itself.')

        if node.id in self.subnodes:
            raise ValueError(f'Node {self.path} already contains a subnodee with id {node.id}.')

        for i in node.chain_to_tails():
            if i is self:
                raise ValueError(f'Node loop.')  # todo
        return None

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

    async def save(self, same_source_only: bool = True) -> None:
        if self.source is None:
            if not self.inherited_source:
                raise RuntimeError(f'Cannot save node {self.path}: source not specified.')
            for i in self.chain_to_root():
                if i.source is not None:
                    return await i.save(same_source_only=same_source_only)

        node_info = self.get_node_info()
        await self.source.save(data=node_info)

    async def run_hook(self, hook_identifier: Any, *args, **kwargs) -> Any:
        hook = self.hooks.get(hook_identifier)
        if hook is not None:
            await hook(*args, **kwargs)
        if self.parent is not None:
            await self.parent.run_hook(hook_identifier, *args, **kwargs)
