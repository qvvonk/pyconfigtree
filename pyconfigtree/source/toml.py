from typing import Any

from .base import ConfigSource
from pathlib import Path
import tomllib
import tomli_w


class TOMLSource(ConfigSource):
    def __init__(self, path: str | Path, encoding: str = 'utf-8') -> None:
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
