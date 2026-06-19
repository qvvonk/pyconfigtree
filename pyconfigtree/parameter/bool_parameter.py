from __future__ import annotations

from typing import Any
from types import EllipsisType
from collections.abc import Callable, Iterable, Awaitable

from .base import MutableParameter, UNSET


class BoolParameter(MutableParameter[bool]):
    def __init__(
        self,
        *,
        node_id: str,
        name: str,
        description: str,
        default_value: bool = UNSET,
        default_factory: Callable[[], bool] = UNSET,
        validator: Callable[['BoolParameter', bool], None] | None = None,
    ) -> None:
        super().__init__(
            node_id=node_id,
            name=name,
            description=description,
            default_value=default_value,
            default_factory=default_factory,
            validator=validator,
        )

    async def on(self, save: bool = True, skip_hook: bool = False) -> None:
        await self.set_value(True, skip_deserializer=True, save=save, skip_hook=skip_hook)

    async def off(self, save: bool = True, skip_hook: bool = False) -> None:
        await self.set_value(False, skip_deserializer=True, save=save, skip_hook=skip_hook)

    async def toggle(self, save: bool = True, skip_hook: bool = False) -> None:
        await self.set_value(not self.value, skip_deserializer=True, save=save, skip_hook=skip_hook)

    async def next_value(self, save: bool = True, skip_hook: bool = False) -> bool:
        await self.toggle(save=save, skip_hook=skip_hook)
        return self.value

    def __bool__(self) -> bool:
        return self.value

    def serialize(self) -> bool:
        return self.value

    def deserialize(self, val: Any) -> bool:
        return bool(val)
