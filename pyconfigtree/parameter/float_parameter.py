from __future__ import annotations


__all__ = [
    'float_serializer',
    'float_deserializer',
    'FloatParameter',
]


from typing import Any, Optional
from collections.abc import Callable

from .base import MutableParameter, UNSET, Validator, Serializer, Deserializer, ON_PARAMETER_VALUE_CHANGED_HOOK
from pyconfigtree.exceptions import DeserializationError, ValidationError


def float_serializer(value: float) -> float:
    return value


def float_deserializer(value: Any) -> float:
    return float(value)


class FloatParameter(MutableParameter[float]):
    def __init__(
        self,
        *,
        node_id: str,
        name: str = '',
        description: str = '',
        default_value: float = UNSET,
        default_factory: Callable[[], float] = UNSET,
        validator: Optional[Validator['FloatParameter', float]] = None,
        serializer: Serializer[float] | None = None,
        deserializer: Deserializer[float] | None = None,
        on_value_changed_hook: Optional[ON_PARAMETER_VALUE_CHANGED_HOOK] = None,
    ) -> None:
        super().__init__(
            node_id=node_id,
            name=name,
            description=description,
            default_value=default_value,
            default_factory=default_factory,
            serializer=serializer if serializer is not None else float_serializer,
            deserializer=deserializer if deserializer is not None else float_deserializer,
            validator=validator,
            on_value_changed_hook=on_value_changed_hook
        )

    def deserialize(self, value: Any) -> float:
        res = super().deserialize(value)
        if not isinstance(res, float):
            raise DeserializationError(
                f'Deserialized value of `FloatParameter` '
                f'must be an instance of `float`, not {type(res)}.'
            )
        return res

    async def validate(self, value: Any) -> None:
        if not isinstance(value, float):
            raise ValidationError(
                f'Value of `FloatParameter` must be an instance of `float`, not {type(value)}.'
            )
        return await (super().validate(value))