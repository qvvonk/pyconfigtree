from .base import Node
from typing import overload, TypeVar


T = TypeVar('T', bound=Node)


class Properties(Node):
    def __init__(self, node_id: str):
        super().__init__(node_id)
