from abc import ABC, abstractmethod
from typing import Any


class ConfigSource(ABC):
    @abstractmethod
    async def load(self) -> dict[str, Any]: ...

    @abstractmethod
    async def save(self, data: dict[str, Any]): ...
