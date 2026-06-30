from typing import Any

from .base import ConfigSource, NodeInfo, NodeType
from pathlib import Path
import tomllib
import tomli_w


class TOMLSource(ConfigSource):
    def __init__(self, path: str | Path, encoding: str = 'utf-8') -> None:
        self._path =  Path(path)
        self._encoding = encoding

    async def load(self) -> dict[str, Any]:
       with open(self._path, 'rb') as f:
           data = tomllib.load(f)
       return data

    async def save(self, data: NodeInfo) -> None:
        dicted = self.node_info_to_dict(data)
        with open(self._path, 'w', encoding='utf-8') as f:
            f.write(tomli_w.dumps(dicted, multiline_strings=True, indent=4))
        return

    def node_info_to_dict(self, node: NodeInfo) -> dict[str, Any]:
        if node.type is NodeType.LEAF:
            return node.value
        return {k: self.node_info_to_dict(v) for k, v in node.subnodes.items()}

    @property
    def path(self) -> Path:
        return self._path

    @property
    def encoding(self) -> str:
        return self._encoding

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TOMLSource):
            return self.path == other.path
        elif isinstance(other, (str, Path)):
            return self.path == Path(other)
        return False
