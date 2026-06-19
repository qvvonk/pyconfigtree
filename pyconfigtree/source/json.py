from typing import Any, Union

from .base import ConfigSource
from pathlib import Path
import json


class JSONSource(ConfigSource):
    def __init__(self, path: Union[str, Path], encoding: str = 'utf-8') -> None:
        self._path = Path(path)
        self._encoding = encoding

    async def load(self) -> dict[str, Any]:
        with open(self._path, 'r', encoding=self.encoding) as f:
            data = json.load(f)
        return data

    async def save(self, data: dict[str, Any]) -> None:
        with open(self._path, 'w', encoding=self.encoding) as f:
            f.write(json.dumps(data, indent=4))

    @property
    def path(self) -> Path:
        return self._path

    @property
    def encoding(self) -> str:
        return self._encoding

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, JSONSource):
            return self.path == other.path
        elif isinstance(other, (str, Path)):
            return self.path == Path(other)
        return False
