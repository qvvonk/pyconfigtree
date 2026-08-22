from __future__ import annotations


__all__ = [
    'ParameterHookTypes',
    'Serializer',
    'Deserializer',
    'Validator',
    'ValueSpec',
    'Parameter',
    'MutableParameter',
    'ON_PARAMETER_VALUE_CHANGED_HOOK',
    '_MutableParameterKwargs',
]


from typing import Any, Generic, TypeVar, ClassVar, Protocol, TypeAlias, cast
from enum import Enum, auto
from asyncio import Lock
from dataclasses import dataclass
from collections.abc import Callable, Awaitable

from typing_extensions import Self, TypedDict, NotRequired

from pyconfigtree.base import Node, leaf
from pyconfigtree.exceptions import ValidationError, DeserializationError
from pyconfigtree.source.base import ALLOWED_TYPES, NodeInfo, NodeType


ON_PARAMETER_VALUE_CHANGED_HOOK: TypeAlias = Callable[['MutableParameter[Any]'], Awaitable[Any]]


class ParameterHookTypes(Enum):
    PARAMETER_VALUE_CHANGED = auto()


_VALUE_contra = TypeVar('_VALUE_contra', contravariant=True)
_VALUE_co = TypeVar('_VALUE_co', covariant=True)
_NODE = TypeVar('_NODE', contravariant=True)


class Serializer(Protocol[_NODE, _VALUE_contra]):
    def __call__(self, node: _NODE, value: _VALUE_contra) -> ALLOWED_TYPES: ...


class Deserializer(Protocol[_NODE, _VALUE_co]):
    def __call__(self, node: _NODE, value: ALLOWED_TYPES) -> _VALUE_co: ...


class Validator(Protocol[_NODE, _VALUE_contra]):
    async def __call__(self, node: _NODE, value: _VALUE_contra) -> None: ...


T = TypeVar('T')


@dataclass(frozen=True, slots=True)
class ValueSpec(Generic[_NODE, T]):
    serializer: Serializer[_NODE, T]
    deserializer: Deserializer[_NODE, T]
    validator: Callable[[_NODE, object], bool]


@leaf
class Parameter(Node, Generic[T]):
    def __init__(
        self,
        node_id: str,
        value: T,
        name: str = '',
        description: str = '',
        flags: set[Any] | None = None,
    ) -> None:
        super().__init__(node_id=node_id, name=name, description=description, flags=flags)
        self._value = value

    @property
    def value(self) -> T:
        return self._value

    async def load_from_dict(
        self,
        data_dict: dict[str, Any],
        validate: bool = True,
        run_hook: bool = False,
    ) -> None:
        # Parameter is immutable and its value cannot be set.
        return


class _Missing:
    __slots__ = ()


_MISSING = _Missing()

_VALUE_TYPE = TypeVar('_VALUE_TYPE')
_PARAM_CLASS = TypeVar('_PARAM_CLASS')


class _MutableParameterKwargs(TypedDict, Generic[_PARAM_CLASS, _VALUE_TYPE]):
    name: NotRequired[str]
    description: NotRequired[str]
    value: NotRequired[_VALUE_TYPE]
    default_value: NotRequired[_VALUE_TYPE]
    default_factory: NotRequired[Callable[[], _VALUE_TYPE] | None]
    validator: NotRequired[Validator[_PARAM_CLASS, _VALUE_TYPE] | None]
    spec: NotRequired[ValueSpec[_PARAM_CLASS, _VALUE_TYPE] | None]
    on_value_changed_hook: NotRequired[ON_PARAMETER_VALUE_CHANGED_HOOK | None]
    flags: NotRequired[set[Any] | None]


class MutableParameter(Parameter[T], Generic[T]):
    SPEC: ClassVar[ValueSpec[Any, Any] | None] = None

    def __init__(
        self,
        node_id: str,
        *,
        name: str = '',
        description: str = '',
        value: T | _Missing = _MISSING,
        default_value: T | _Missing = _MISSING,
        default_factory: Callable[[], T] | None = None,
        validator: Validator[Self, T] | None = None,
        spec: ValueSpec[Self, T] | None = None,
        on_value_changed_hook: ON_PARAMETER_VALUE_CHANGED_HOOK | None = None,
        flags: set[Any] | None = None,
    ) -> None:
        if default_value is _MISSING and default_factory is None:
            raise ValueError('Either `default_value` or `default_factory` must be specified.')
        if default_value is not _MISSING and default_factory is not None:
            raise ValueError(
                'Either `default_value` or `default_factory` must be specified, '
                'but not both of them.',
            )

        resolved_spec = spec if spec is not None else type(self).SPEC
        if resolved_spec is None:
            raise TypeError(
                f'`{type(self).__name__}` must define `SPEC` or receive `spec` in its constructor.'
            )

        self._spec = resolved_spec
        self._default_factory = default_factory
        self._default_value = default_value
        self._validator = validator
        self._changing_lock = Lock()

        initial_value = cast(T, self.default_value if value is _MISSING else value)
        self._ensure_value_type(initial_value)

        super().__init__(
            node_id=node_id,
            value=initial_value,
            name=name,
            description=description,
            flags=flags,
        )

        self.on_value_changed_hook = on_value_changed_hook

    @property
    def default_value(self) -> T:
        value = self._default_value if self._default_factory is None else self._default_factory()
        self._ensure_value_type(value)
        return cast(T, value)

    @property
    def spec(self) -> ValueSpec[Self, T]:
        return self._spec

    @property
    def serializer(self) -> Serializer[Self, T]:
        return self.spec.serializer

    @property
    def deserializer(self) -> Deserializer[Self, T]:
        return self.spec.deserializer

    @property
    def validator(self) -> Validator[Self, T] | None:
        return self._validator

    @property
    def on_value_changed_hook(self) -> ON_PARAMETER_VALUE_CHANGED_HOOK | None:
        return self.hooks.get(ParameterHookTypes.PARAMETER_VALUE_CHANGED)

    @on_value_changed_hook.setter
    def on_value_changed_hook(self, hook: ON_PARAMETER_VALUE_CHANGED_HOOK | None) -> None:
        self._hooks[ParameterHookTypes.PARAMETER_VALUE_CHANGED] = hook

    def _ensure_value_type(
        self,
        value: object,
        error_type: type[Exception] = ValidationError,
    ) -> None:
        try:
            if not self.spec.validator(self, value):
                raise error_type('Validation error.')  # todo: error msg
        except Exception as exc:
            raise error_type('Unable to validate value.') from exc  # todo: error msg

    def get_node_info(self, same_source_only: bool = True) -> NodeInfo:
        return NodeInfo(
            id=self.id,
            name=self.name,
            description=self.description,
            type=NodeType.LEAF,
            value=self.serialize(),
        )

    async def load_from_dict(
        self,
        data_dict: Any,
        validate: bool = True,
        run_hook: bool = False,
    ) -> None:
        await self.set_value(data_dict, save=False, run_hook=run_hook, validate=validate)

    async def set_value(
        self,
        value: Any,
        *,
        deserialize: bool = True,
        validate: bool = True,
        run_hook: bool = True,
        save: bool = True,
    ) -> None:
        async with self._changing_lock:
            if deserialize:
                candidate = self.deserialize(value)
            else:
                self._ensure_value_type(value)
                candidate = cast(T, value)

            if validate:
                await self.validate(candidate)

            self._value = candidate
            if save:
                await self.save()

        if run_hook:
            await self.run_hook(ParameterHookTypes.PARAMETER_VALUE_CHANGED, self)

    def serialize(self) -> ALLOWED_TYPES:
        return self.serializer(self, self.value)

    def deserialize(self, value: Any) -> T:
        try:
            result = self.deserializer(self, value)
        except DeserializationError:
            raise
        except Exception as exc:
            raise DeserializationError(
                f'Unable to deserialize {value!r} for `{type(self).__name__}`.'
            ) from exc

        self._ensure_value_type(result, DeserializationError)
        return result

    async def validate(self, value: T) -> None:
        if self.validator is not None:
            await self.validator(self, value)
