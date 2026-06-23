__all__ = [
    'PyConfigTreeError',
    'ValidationError',
    'SerializationError',
    'DeserializationError'
]


class PyConfigTreeError(Exception): ...


class ValidationError(PyConfigTreeError): ...


class SerializationError(PyConfigTreeError): ...


class DeserializationError(PyConfigTreeError): ...