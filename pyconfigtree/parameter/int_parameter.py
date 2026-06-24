from __future__ import annotations


__all__ = [
    'int_serializer',
    'int_deserializer',
    'IntParameter',
]


from typing import Any, Optional
from collections.abc import Callable

from .base import MutableParameter, UNSET, Validator, Serializer, Deserializer, ON_PARAMETER_VALUE_CHANGED_HOOK
from pyconfigtree.exceptions import DeserializationError, ValidationError


def int_serializer(value: int) -> int:
    return value


def int_deserializer(value: Any) -> int:
    return int(value)


class IntParameter(MutableParameter[int]):
    def __init__(
        self,
        *,
        node_id: str,
        name: str = '',
        description: str = '',
        default_value: int = UNSET,
        default_factory: Callable[[], int] = UNSET,
        validator: Optional[Validator['IntParameter', int]] = None,
        serializer: Serializer[int] | None = None,
        deserializer: Deserializer[int] | None = None,
        on_value_changed_hook: Optional[ON_PARAMETER_VALUE_CHANGED_HOOK] = None,
    ) -> None:
        super().__init__(
            node_id=node_id,
            name=name,
            description=description,
            default_value=default_value,
            default_factory=default_factory,
            serializer=serializer if serializer is not None else int_serializer,
            deserializer=deserializer if deserializer is not None else int_deserializer,
            validator=validator,
            on_value_changed_hook=on_value_changed_hook
        )

    def deserialize(self, value: Any) -> int:
        res = super().deserialize(value)
        if not isinstance(res, int):
            raise DeserializationError(
                f'Deserialized value of `IntParameter` '
                f'must be an instance of `int`, not {type(res)}.'
            )
        return res

    async def validate(self, value: Any) -> None:
        if not isinstance(value, int):
            raise ValidationError(
                f'Value of `IntParameter` must be an instance of `int`, not {type(value)}.'
            )
        return await (super().validate(value))