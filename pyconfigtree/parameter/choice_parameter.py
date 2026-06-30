from typing import Generic, TypeVar
from dataclasses import dataclass


T = TypeVar('T')


@dataclass(kw_only=True)
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
