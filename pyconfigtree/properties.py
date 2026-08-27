from __future__ import annotations


__all__ = ['Properties']

from typing import Any, Literal, overload

from .base import Node
from .parameter import Parameter


class Properties(Node):
    @overload
    def get_parameter(self, path: list[str], _raise: Literal[True] = True) -> Parameter[Any]: ...

    @overload
    def get_parameter(self, path: list[str], _raise: Literal[False]) -> Parameter[Any]: ...

    @overload
    def get_parameter(self, path: list[str], _raise: bool = True) -> Parameter[Any] | None: ...

    def get_parameter(self, path: list[str], _raise: bool = True) -> Parameter[Any] | None:
        result = self.get_node(path, _raise)
        if not isinstance(result, Parameter):
            if _raise:
                raise LookupError(f'No parameter found at {path}.')
            return None
        return result

    @overload
    def get_properties(self, path: list[str], _raise: Literal[True] = True) -> Properties: ...

    @overload
    def get_properties(self, path: list[str], _raise: Literal[False]) -> Properties: ...

    @overload
    def get_properties(self, path: list[str], _raise: bool = True) -> Properties | None: ...

    def get_properties(self, path: list[str], _raise: bool = True) -> Properties | None:
        result = self.get_node(path, _raise)
        if not isinstance(result, Properties):
            if _raise:
                raise LookupError(f'No properties found at {path}.')
            return None
        return result
