__all__ = [
    'ParameterHookTypes',
    'Serializer',
    'Deserializer',
    'Validator',
    'Parameter',
    'MutableParameter',
    'TypedParameter',
    'UNSET',
    'ON_PARAMETER_VALUE_CHANGED_HOOK'
]

from ..base import Node
from typing import Any, Generic, TypeVar, TypeAlias, Optional, Protocol, Type
from collections.abc import Callable, Awaitable
from enum import Enum, auto
from asyncio import Lock
from pyconfigtree.exceptions import DeserializationError, ValidationError

from ..source.base import NodeInfo, NodeType, ALLOWED_TYPES


T = TypeVar('T')
S = TypeVar('S')
UNSET = object()


ON_PARAMETER_VALUE_CHANGED_HOOK: TypeAlias = Callable[['MutableParameter[Any]'], Awaitable[Any]]


class ParameterHookTypes(Enum):
    PARAMETER_VALUE_CHANGED = auto()


class Serializer(Protocol[T]):
    def __call__(self, value: T) -> ALLOWED_TYPES: ...


class Deserializer(Protocol[T]):
    def __call__(self, value: ALLOWED_TYPES) -> T: ...


class Validator(Protocol[S, T]):
    async def __call__(self, node: S, value: T) -> None: ...



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

    async def load_from_dict(self, data_dict: Any) -> None:
        # Parameter is immutable and its value cannot be set.
        return


class MutableParameter(Parameter[T], Generic[T]):
    def __init__(
        self: S,
        *,
        node_id: str,
        name: str = '',
        description: str = '',
        value: T = UNSET,
        default_value: T = UNSET,
        default_factory: Callable[[], T] = UNSET,
        validator: Optional[Validator[S, T]] = None,
        serializer: Serializer[T],
        deserializer: Deserializer[T],
        on_value_changed_hook: Optional[ON_PARAMETER_VALUE_CHANGED_HOOK] = None,
    ) -> None:
        if default_value is UNSET and default_factory is UNSET:
            raise ValueError('Default value or default factory must be set.')

        self._default_factory = default_factory
        self._default_value = default_value
        self._changing_lock = Lock()
        self._validator = validator
        self._serializer = serializer
        self._deserializer = deserializer

        super().__init__(
            node_id=node_id,
            value=value if value is not UNSET else self.default_value,
            name=name,
            description=description
        )

        self.on_value_changed_hook = on_value_changed_hook

    @property
    def default_value(self) -> T:
        if self._default_factory is not UNSET:
            return self._default_factory()
        return self._default_value

    @property
    def serializer(self) -> Serializer[T]:
        return self._serializer

    @property
    def deserializer(self) -> Deserializer[T]:
        return self._deserializer

    @property
    def validator(self) -> Optional[Validator[S, T]]:
        return self._validator

    @property
    def on_value_changed_hook(self) -> Optional[ON_PARAMETER_VALUE_CHANGED_HOOK]:
        return self.hooks.get(ParameterHookTypes.PARAMETER_VALUE_CHANGED)

    @on_value_changed_hook.setter
    def on_value_changed_hook(self, hook: Optional[ON_PARAMETER_VALUE_CHANGED_HOOK]) -> None:
        self._hooks[ParameterHookTypes.PARAMETER_VALUE_CHANGED] = hook

    def get_node_info(self, same_source_only: bool = True) -> NodeInfo:
        return NodeInfo(
            id=self.id,
            name=self.name,
            description=self.description,
            type=NodeType.LEAF,
            value=self.serialize()
        )

    async def load_from_dict(self, data_dict: Any) -> None:
        await self.set_value(data_dict, save=False, run_hook=False)

    async def set_value(
        self,
        value: Any,
        *,
        skip_deserializer: bool = True,
        skip_validator: bool = False,
        run_hook: bool = True,
        save: bool = True,
    ) -> None:
        async with self._changing_lock:
            if not skip_deserializer:
                value = self.deserialize(value)
            if not skip_validator:
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
        if self._validator:
            await self.validator(self, value)


TS = TypeVar('TS')
TT = TypeVar('TT')


class TypedParameter(MutableParameter[TT], Generic[TT]):
    _DEFAULT_SERIALIZER: Serializer[TT]
    _DEFAULT_DESERIALIZER: Deserializer[TT]
    _VALUE_TYPE: Type[TT]

    def __init_subclass__(cls, **kwargs):
        if cls is TypedParameter:
            return

        for i in [
            '_DEFAULT_SERIALIZER',
            '_DEFAULT_DESERIALIZER',
            '_VALUE_TYPE',
        ]:
            if i not in cls.__dict__:
                raise TypeError(f'`{cls.__name__}` must define `{i}`.')

    def __init__(
        self: TS,
        *,
        node_id: str,
        name: str = '',
        description: str = '',
        default_value: TT = UNSET,
        default_factory: Callable[[], TT] = UNSET,
        validator: Optional[Validator[TS, TT]] = None,
        serializer: Serializer[TT] | None = None,
        deserializer: Deserializer[TT] | None = None,
        on_value_changed_hook: Optional[ON_PARAMETER_VALUE_CHANGED_HOOK] = None,
    ) -> None:
        super().__init__(
            node_id=node_id,
            name=name,
            description=description,
            default_value=default_value,
            default_factory=default_factory,
            serializer=serializer if serializer is not None else self.DEFAULT_SERIALIZER,
            deserializer=deserializer if deserializer is not None else self.DEFAULT_DESERIALIZER,
            validator=validator,
            on_value_changed_hook=on_value_changed_hook
        )

    def deserialize(self, value: Any) -> bool:
        res = super().deserialize(value)
        if not isinstance(res, self._VALUE_TYPE):
            raise DeserializationError(
                f'Deserialized value of `{self.__class__.__name__}` must be an instance of '
                f'`{self._VALUE_TYPE.__name__}`, not `{type(res)}`.'
            )
        return res

    async def validate(self, value: Any) -> None:
        if not isinstance(value, self._VALUE_TYPE):
            raise ValidationError(
                f'Value of `{self.__class__.__name__}` must be an instance of '
                f'`{self._VALUE_TYPE.__name__}`, not `{type(value)}`.'
            )
        return await (super().validate(value))