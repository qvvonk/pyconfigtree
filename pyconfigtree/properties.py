from .base import Node
from typing import Optional, TypeVar
from .source import ConfigSource


T = TypeVar('T', bound=Node)


class Properties(Node):
    def __init__(
        self,
        node_id: str,
        name: str = '',
        description: str = '',
        source: Optional[ConfigSource] = None,
    ):
        super().__init__(node_id, name=name, description=description)
        self._source = source

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