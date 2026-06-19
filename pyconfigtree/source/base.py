from abc import ABC, abstractmethod
from typing import Any, Union, TypeAlias
from dataclasses import dataclass
from enum import Enum, auto


SIMPLE_TYPES: TypeAlias = Union[int, float, bool, str]
CONTAINER_TYPES: TypeAlias = Union[
    dict[str, Union[SIMPLE_TYPES, 'CONTAINER_TYPES']],
    list[Union[SIMPLE_TYPES, 'CONTAINER_TYPES']],
]
ALLOWED_TYPES: TypeAlias = Union[SIMPLE_TYPES, CONTAINER_TYPES]


class ConfigSource(ABC):
    @abstractmethod
    async def load(self) -> dict[str, Any]: ...

    @abstractmethod
    async def save(self, data: dict[str, Any]): ...

    @abstractmethod
    def __eq__(self, other: Any) -> bool: ...


class NodeType(Enum):
    CONTAINER = auto()
    LEAF = auto()


@dataclass
class NodeInfo:
    name: str
    description: str
    type: NodeType
    subnodes: dict[str, 'NodeInfo']
    value: ALLOWED_TYPES | None = None

    def __post_init__(self):
        if self.type is NodeType.CONTAINER and self.value is not None:
            raise ValueError(f'Node of type {self.type} cannot contain value.')
