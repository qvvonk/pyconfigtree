__all__ = [
    'PyConfigTreeError',
    'ValidationError',
    'SerializationError',
    'DeserializationError',
    'NoSourceError',
    'NodeLoopError',
    'NodeDuplicateError',
    'LeafNodeError'
]


class PyConfigTreeError(Exception): ...


class ValidationError(PyConfigTreeError): ...


class SerializationError(PyConfigTreeError): ...


class DeserializationError(PyConfigTreeError): ...


class NoSourceError(PyConfigTreeError): ...


class NodeLoopError(PyConfigTreeError): ...


class NodeDuplicateError(PyConfigTreeError): ...


class LeafNodeError(PyConfigTreeError): ...