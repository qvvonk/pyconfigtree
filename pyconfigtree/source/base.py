from abc import ABC, abstractmethod
from typing import Any, TypeAlias
from dataclasses import dataclass, field
from enum import Enum, auto


SIMPLE_TYPES: TypeAlias = int | float | bool | str
CONTAINER_TYPES: TypeAlias = (
    dict[str, SIMPLE_TYPES | 'CONTAINER_TYPES'] | list[SIMPLE_TYPES | 'CONTAINER_TYPES']
)
ALLOWED_TYPES: TypeAlias = SIMPLE_TYPES | CONTAINER_TYPES


class ConfigSource(ABC):
    @abstractmethod
    async def load(self) -> dict[str, Any]: ...

    @abstractmethod
    async def save(self, data: 'NodeInfo'): ...

    @abstractmethod
    def __eq__(self, other: Any) -> bool: ...


class NodeType(Enum):
    CONTAINER = auto()
    LEAF = auto()


@dataclass
class NodeInfo:
    id: str
    name: str
    description: str
    type: NodeType
    subnodes: dict[str, 'NodeInfo'] = field(default_factory=dict)
    value: ALLOWED_TYPES | None = None

    def __post_init__(self):
        if self.type is NodeType.CONTAINER and self.value is not None:
            raise ValueError(f'Node of type {self.type} cannot contain value.')
