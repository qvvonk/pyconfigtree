__all__ = [
    'ParameterHookTypes',
    'Serializer',
    'Deserializer',
    'Validator',
    'Parameter',
    'MutableParameter',
    'TypedParameter',
    'ON_PARAMETER_VALUE_CHANGED_HOOK',
    '_MutableParameterKwargs',
]


from typing import Any, Type, Generic, TypeVar, Protocol, TypeAlias
from enum import Enum, auto
from asyncio import Lock
from collections.abc import Callable, Awaitable

from typing_extensions import Self, Unpack, Required, TypedDict, NotRequired

from pyconfigtree.exceptions import ValidationError, DeserializationError

from ..base import Node
from ..source.base import ALLOWED_TYPES, NodeInfo, NodeType


ON_PARAMETER_VALUE_CHANGED_HOOK: TypeAlias = Callable[['MutableParameter[Any]'], Awaitable[Any]]


class ParameterHookTypes(Enum):
    PARAMETER_VALUE_CHANGED = auto()


_ST = TypeVar('_ST', contravariant=True)


class Serializer(Protocol[_ST]):
    def __call__(self, value: _ST) -> ALLOWED_TYPES: ...


_DT = TypeVar('_DT', covariant=True)


class Deserializer(Protocol[_DT]):
    def __call__(self, value: ALLOWED_TYPES) -> _DT: ...


_VT = TypeVar('_VT', contravariant=True)
_VS = TypeVar('_VS', contravariant=True)


class Validator(Protocol[_VS, _VT]):
    async def __call__(self, node: _VS, value: _VT) -> None: ...


T = TypeVar('T')


class Parameter(Node, Generic[T]):
    _allow_children = False

    def __init__(
        self,
        node_id: str,
        value: T,
        name: str = '',
        description: str = '',
    ) -> None:
        super().__init__(node_id=node_id, name=name, description=description)
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


_KT = TypeVar('_KT')  # Parameter value type
_KP = TypeVar('_KP')  # Parameter class


class _CommonMutableParameterKwargs(TypedDict, Generic[_KT, _KP]):
    name: NotRequired[str]
    description: NotRequired[str]
    value: NotRequired[_KT | None]
    default_value: NotRequired[_KT | None]
    default_factory: NotRequired[Callable[[], _KT] | None]
    validator: NotRequired[Validator[_KP, _KT] | None]
    on_value_changed_hook: NotRequired[ON_PARAMETER_VALUE_CHANGED_HOOK | None]


class _MutableParameterKwargs(_CommonMutableParameterKwargs[_KT, _KP], Generic[_KT, _KP]):
    serializer: Required[Serializer[_KT]]
    deserializer: Required[Deserializer[_KT]]


class _TypedParameterKwargs(_CommonMutableParameterKwargs[_KT, _KP], Generic[_KT, _KP]):
    serializer: NotRequired[Serializer[_KT]]
    deserializer: NotRequired[Deserializer[_KT]]


class MutableParameter(Parameter[T], Generic[T]):
    def __init__(
        self,
        node_id: str,
        *,
        name: str = '',
        description: str = '',
        value: T | None = None,
        default_value: T | None = None,
        default_factory: Callable[[], T] | None = None,
        validator: Validator[Self, T] | None = None,
        serializer: Serializer[T],
        deserializer: Deserializer[T],
        on_value_changed_hook: ON_PARAMETER_VALUE_CHANGED_HOOK | None = None,
    ) -> None:
        if value is None and default_value is None:
            raise ValueError('Either `default_value` or `default_factory` must be specified.')
        if value is not None and default_factory is not None:
            raise ValueError(
                'Either `default_value` or `default_factory` must be specified, '
                'but not both of them.',
            )

        self._default_factory = default_factory
        self._default_value = default_value
        self._changing_lock = Lock()
        self._validator = validator
        self._serializer = serializer
        self._deserializer = deserializer

        super().__init__(
            node_id=node_id,
            value=value if value is not None else self.default_value,
            name=name,
            description=description,
        )

        self.on_value_changed_hook = on_value_changed_hook

    @property
    def default_value(self) -> T:
        if self._default_factory is not None:
            return self._default_factory()
        return self._default_value

    @property
    def serializer(self) -> Serializer[T]:
        return self._serializer

    @property
    def deserializer(self) -> Deserializer[T]:
        return self._deserializer

    @property
    def validator(self) -> Validator[Self, T] | None:
        return self._validator

    @property
    def on_value_changed_hook(self) -> ON_PARAMETER_VALUE_CHANGED_HOOK | None:
        return self.hooks.get(ParameterHookTypes.PARAMETER_VALUE_CHANGED)

    @on_value_changed_hook.setter
    def on_value_changed_hook(self, hook: ON_PARAMETER_VALUE_CHANGED_HOOK | None) -> None:
        self._hooks[ParameterHookTypes.PARAMETER_VALUE_CHANGED] = hook

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
        await self.set_value(
            data_dict,
            save=False,
            run_hook=run_hook,
            validate=validate,
        )

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
                value = self.deserialize(value)
            if validate:
                await self.validate(value)

            self._value = value
            if save:
                await self.save()

        if run_hook:
            await self.run_hook(ParameterHookTypes.PARAMETER_VALUE_CHANGED, self)

    def serialize(self) -> ALLOWED_TYPES:
        return self._serializer(self.value)

    def deserialize(self, value: Any) -> T:
        return self.deserializer(value)

    async def validate(self, value: T) -> None:
        if self.validator is not None:
            await self.validator(self, value)


TT = TypeVar('TT')


class TypedParameter(MutableParameter[TT], Generic[TT]):
    _DEFAULT_SERIALIZER: Serializer[TT]
    _DEFAULT_DESERIALIZER: Deserializer[TT]
    _VALUE_TYPE: Type[TT]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if cls is TypedParameter:
            return

        for i in [
            '_DEFAULT_SERIALIZER',
            '_DEFAULT_DESERIALIZER',
            '_VALUE_TYPE',
        ]:
            if i not in cls.__dict__:
                raise TypeError(f'`{cls.__name__}` must define `{i}`.')

    def __init__(self, node_id: str, **kwargs: Unpack[_TypedParameterKwargs[TT, Self]]) -> None:
        super().__init__(node_id=node_id, **kwargs)

    def deserialize(self, value: Any) -> TT:
        res = super().deserialize(value)
        if not isinstance(res, self._VALUE_TYPE):
            raise DeserializationError(
                f'Deserialized value of `{self.__class__.__name__}` must be an instance of '
                f'`{self._VALUE_TYPE.__name__}`, not `{type(res)}`.',
            )
        return res

    async def validate(self, value: Any) -> None:
        if not isinstance(value, self._VALUE_TYPE):
            raise ValidationError(
                f'Value of `{self.__class__.__name__}` must be an instance of '
                f'`{self._VALUE_TYPE.__name__}`, not `{type(value)}`.',
            )
        return await super().validate(value)
