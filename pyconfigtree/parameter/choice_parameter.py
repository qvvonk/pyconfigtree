from typing import Any, Generic, TypeVar
from types import MappingProxyType
from dataclasses import dataclass
from collections.abc import Mapping, Sequence

from typing_extensions import Self, Unpack

from .base import ValueSpec, MutableParameter, _MutableParameterKwargs


T = TypeVar('T')


@dataclass(kw_only=True, frozen=True)
class Choice(Generic[T]):
    id: str
    name: str = ''
    description: str = ''
    value: T

    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError('Choice ID must be a string.')
        if not self.id:
            raise ValueError('Choice ID cannot be empty.')

    def __str__(self) -> str:
        return self.id


def choice_serializer(value: Choice[Any], node: 'ChoiceParameter[Any]') -> str:
    return value.id


def choice_deserializer(value: Any, node: 'ChoiceParameter[Any]') -> Choice[Any]:
    value = str(value)
    return node.choices.get(value, node.choices[node.fallback_choice_id])


def choice_accepts(value: object, node: 'ChoiceParameter[Any]') -> bool:
    return isinstance(value, Choice) and value in node.choices.values()


CHOICE_VALUE_SPEC = ValueSpec(
    serializer=choice_serializer,
    deserializer=choice_deserializer,
    validator=choice_accepts,
)


class ChoiceParameter(MutableParameter[Choice[T]], Generic[T]):
    SPEC = CHOICE_VALUE_SPEC

    def __init__(
        self,
        node_id: str,
        *,
        choices: Sequence[Choice[T]],
        fallback_choice_id: str,
        **kwargs: Unpack[_MutableParameterKwargs[Self, Choice[T]]],
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

        super().__init__(node_id=node_id, **kwargs)

    @property
    def choices(self) -> Mapping[str, Choice[T]]:
        return MappingProxyType(self._choices)

    @property
    def fallback_choice_id(self) -> str:
        return self._fallback_choice_id

    async def set_value(
        self,
        value: Choice[T] | str,
        *,
        deserialize: bool = True,
        validate: bool = True,
        run_hook: bool = True,
        save: bool = True,
    ) -> None:
        await super().set_value(
            value, deserialize=deserialize, validate=validate, run_hook=run_hook, save=save
        )
