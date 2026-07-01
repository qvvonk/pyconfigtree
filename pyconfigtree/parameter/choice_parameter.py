from typing import Any, Generic, TypeVar
from types import MappingProxyType
from dataclasses import dataclass
from collections.abc import Mapping, Sequence

from typing_extensions import Self, Unpack

from .base import TypedParameter, _MutableParameterKwargs


T = TypeVar('T')


@dataclass(kw_only=True, frozen=True)
class Choice(Generic[T]):
    id: str
    name: str = ''
    description: str = ''
    value: T

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError('Choice ID cannot be empty.')

        if not isinstance(id, str):
            raise TypeError('Choice ID must be a string.')

    def __str__(self) -> str:
        return self.id


def choice_serializer(value: Choice[Any]) -> str:
    return value.id


class ChoiceParameter(TypedParameter[Choice[T]], Generic[T]):
    _DEFAULT_SERIALIZER = choice_serializer
    _DEFAULT_DESERIALIZER = ...
    _VALUE_TYPE = Choice

    def __init__(
        self,
        node_id: str,
        *,
        choices: Sequence[Choice[T]],
        fallback_choice_id: str,
        **kwargs: Unpack[_MutableParameterKwargs[Choice[T], Self]],
    ) -> None:
        if not choices:
            raise ValueError('At least 1 choice must be provided.')

        self._choices: dict[str, Choice[T]] = {}
        for i in choices:
            if i.id in self._choices:
                raise ValueError('Duplicate choice ID.')  # todo
            self._choices[i.id] = i

        if fallback_choice_id not in self._choices:
            raise ValueError('Fallback choice ID does not exists.')
        self._fallback_choice_id = fallback_choice_id

        self._DEFAULT_DESERIALIZER = self._default_deserializer
        super().__init__(node_id=node_id, **kwargs)

    @property
    def choices(self) -> Mapping[str, Choice[T]]:
        return MappingProxyType(self._choices)

    @property
    def fallback_choice_id(self) -> str:
        return self._fallback_choice_id

    def _default_deserializer(self, value: Any) -> Choice[T]:
        value = str(value)
        return self.choices.get(value, self.choices[self.fallback_choice_id])

    async def set_value(
        self,
        value: Choice[T] | str,
        *,
        deserialize: bool = True,
        validate: bool = True,
        run_hook: bool = True,
        save: bool = True,
    ) -> None:
        choice = self.choices.get(value) if isinstance(value, str) else value
        if choice not in self.choices.values():
            raise ValueError('Invalid choice.')

        await super().set_value(
            choice, deserialize=deserialize, validate=validate, run_hook=run_hook, save=save
        )
