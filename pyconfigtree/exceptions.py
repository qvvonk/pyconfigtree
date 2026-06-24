__all__ = [
    'PyConfigTreeError',
    'ValidationError',
    'SerializationError',
    'DeserializationError',
    'NoSourceError'
]


class PyConfigTreeError(Exception): ...


class ValidationError(PyConfigTreeError): ...


class SerializationError(PyConfigTreeError): ...


class DeserializationError(PyConfigTreeError): ...


class NoSourceError(PyConfigTreeError): ...