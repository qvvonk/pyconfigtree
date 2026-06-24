from __future__ import annotations


__all__ = [
    'str_serializer',
    'str_deserializer',
    'StringParameter',
]


from typing import Any, Optional
from collections.abc import Callable

from .base import MutableParameter, UNSET, Validator, Serializer, Deserializer, ON_PARAMETER_VALUE_CHANGED_HOOK
from pyconfigtree.exceptions import DeserializationError, ValidationError


def str_serializer(value: str) -> str:
    return value


def str_deserializer(value: Any) -> str:
    return str(value)


class StringParameter(MutableParameter[str]):
    def __init__(
        self,
        *,
        node_id: str,
        name: str = '',
        description: str = '',
        default_value: bool = UNSET,
        default_factory: Callable[[], bool] = UNSET,
        validator: Optional[Validator['StringParameter', bool]] = None,
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
            serializer=serializer if serializer is not None else str_serializer,
            deserializer=deserializer if deserializer is not None else str_deserializer,
            validator=validator,
            on_value_changed_hook=on_value_changed_hook
        )

    def deserialize(self, value: Any) -> str:
        res = super().deserialize(value)
        if not isinstance(res, str):
            raise DeserializationError(
                f'Deserialized value of `StringParameter` '
                f'must be an instance of `str`, not {type(res)}.'
            )
        return res

    async def validate(self, value: Any) -> None:
        if not isinstance(value, str):
            raise ValidationError(
                f'Value of `StringParameter` must be an instance of `str`, not {type(value)}.'
            )
        return await (super().validate(value))