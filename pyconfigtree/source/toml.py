from typing import Any, Union

from .base import ConfigSource
from pathlib import Path
import tomllib
import tomli_w


class TOMLSource(ConfigSource):
    def __init__(self, path: Union[str, Path], encoding: str = 'utf-8') -> None:
        self._path =  Path(path)
        self._encoding = encoding

    async def load(self) -> dict[str, Any]:
       with open(self._path, 'r', encoding='utf-8') as f:
           data = tomllib.load(f)
       return data

    async def save(self, data: dict[str, Any]) -> None:
        with open(self._path, 'w', encoding='utf-8') as f:
            f.write(tomli_w.dumps(data, multiline_strings=True, indent=4))
        return

    @property
    def path(self) -> Path:
        return self._path

    @property
    def encoding(self) -> str:
        return self._encoding

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, TOMLSource):
            return self.path == other.path
        elif isinstance(other, Union[str, Path]):
            return self.path == Path(other)
        return False
