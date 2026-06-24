from __future__ import annotations

from typing import Any, Optional
from collections.abc import Callable

from .base import MutableParameter, UNSET, Validator, Serializer, Deserializer, ON_PARAMETER_VALUE_CHANGED_HOOK
from pyconfigtree.exceptions import DeserializationError, ValidationError


def bool_serializer(value: bool) -> bool:
    return value


def bool_deserializer(value: Any) -> bool:
    return bool(value)


class BoolParameter(MutableParameter[bool]):
    def __init__(
        self,
        *,
        node_id: str,
        name: str,
        description: str,
        default_value: bool = UNSET,
        default_factory: Callable[[], bool] = UNSET,
        validator: Optional[Validator['BoolParameter', bool]] = None,
        serializer: Serializer[bool] | None = None,
        deserializer: Deserializer[bool] | None = None,
        on_value_changed_hook: Optional[ON_PARAMETER_VALUE_CHANGED_HOOK] = None,
    ) -> None:
        super().__init__(
            node_id=node_id,
            name=name,
            description=description,
            default_value=default_value,
            default_factory=default_factory,
            serializer=serializer if serializer is not None else bool_serializer,
            deserializer=deserializer if deserializer is not None else bool_deserializer,
            validator=validator,
            on_value_changed_hook=on_value_changed_hook
        )

    async def on(self, save: bool = True, run_hook: bool = True) -> None:
        await self.set_value(True, skip_deserializer=True, save=save, run_hook=run_hook)

    async def off(self, save: bool = True, run_hook: bool = True) -> None:
        await self.set_value(False, skip_deserializer=True, save=save, run_hook=run_hook)

    async def toggle(self, save: bool = True, run_hook: bool = True) -> None:
        await self.set_value(not self.value, skip_deserializer=True, save=save, run_hook=run_hook)

    async def next_value(self, save: bool = True, run_hook: bool = True) -> bool:
        await self.toggle(save=save, run_hook=run_hook)
        return self.value

    def __bool__(self) -> bool:
        return self.value

    def deserialize(self, value: Any) -> bool:
        res = super().deserialize(value)
        if not isinstance(res, bool):
            raise DeserializationError(
                f'Deserialized value must be an instance of bool, not {type(res)}.'
            )
        return res

    async def validate(self, value: Any) -> None:
        if not isinstance(value, bool):
            raise ValidationError(
                f'Value of `BoolParameter` must be an instance of bool, not {type(value)}.'
            )
        return await (super().validate(value))
