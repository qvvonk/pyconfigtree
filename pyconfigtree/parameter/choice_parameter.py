from types import MappingProxyType
from typing import Generic, TypeVar, Self, Any
from dataclasses import dataclass
from collections.abc import Sequence, Mapping
from .base import TypedParameter, _MutableParameterKwargs
from typing_extensions import Unpack


T = TypeVar('T')


@dataclass(kw_only=True, frozen=True)
class Choice(Generic[T]):
    id: str
    name: str = ''
    description: str = ''
    value: T

    def __post_init__(self):
        if not self.id:
            raise ValueError('Choice ID cannot be empty.')

        if not isinstance(id, str):
            raise TypeError('Choice ID must be a string.')


def choice_serializer(value: Choice[Any]) -> str:
    return value.id


def float_deserializer(value: Any) -> float:
    return float(value)


class ChoiceParameter(TypedParameter[Choice[T]], Generic[T]):
    _DEFAULT_SERIALIZER = choice_serializer
    _DEFAULT_DESERIALIZER = ...
    _VALUE_TYPE = ...
    def __init__(
        self,
        node_id: str,
        *,
        choices: Sequence[Choice],
        fallback_choice_id: str,
        **kwargs: Unpack[_MutableParameterKwargs[Choice, Self]]
    ):
        self._DEFAULT_DESERIALIZER = self._default_deserializer
        if not choices:
            raise ValueError('At least 1 choice must be provided.')

        self._choices: dict[str, Choice] = {}
        for i in choices:
            if i.id in self._choices:
                raise ValueError('Duplicate choice ID.')  # todo
            self._choices[i.id] = i

        if fallback_choice_id not in self._choices:
            raise ValueError('Fallback choice ID does not exists.')
        self._fallback_choice_id = fallback_choice_id

        super().__init__(
            node_id=node_id,
            **kwargs
        )

    @property
    def choices(self) -> Mapping[str, Choice[T]]:
        return MappingProxyType(self._choices)

    @property
    def fallback_choice_id(self) -> str:
        return self._fallback_choice_id

    def _default_deserializer(self, value: Any) -> Choice:
        value = str(value)
        return self.choices.get(value, self.choices[self.fallback_choice_id])
