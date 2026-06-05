from ..base import Node
from typing import Any, Generic, TypeVar
from collections.abc import Callable


T = TypeVar('T')
UNSET = object()

class Parameter(Node, Generic[T]):
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


class MutableParameter(Parameter[T], Generic[T]):
    def __init__(
        self,
        node_id: str,
        value: T = UNSET,
        default_value: T = UNSET,
        default_factory: Callable[[], T] = UNSET,
        name: str = '',
        description: str = '',
    ) -> None:
        if default_value is UNSET and default_factory is UNSET:
            raise ValueError('Default value or default factory must be set.')

        self._default_factory = default_factory
        self._default_value = default_value

        super().__init__(
            node_id=node_id,
            value=value if value is not UNSET else self.default_value,
            name=name,
            description=description
        )

    @property
    def default_value(self) -> T:
        if self._default_factory is not UNSET:
            return self._default_factory()
        return self._default_value
