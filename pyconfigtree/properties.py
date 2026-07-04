__all__ = ['Properties']


from .base import Node
from .parameter import Parameter


class Properties(Node):
    def get_parameter(self, path: list[str], _raise: bool = True):
        result = self.get_node(path, _raise)
        if not isinstance(result, Parameter) and _raise:
            raise LookupError(f"No parameter found at {path}.")
        return result

    def get_properties(self, path: list[str], _raise: bool = True):
        result = self.get_node(path, _raise)
        if not isinstance(result, Properties) and _raise:
            raise LookupError(f"No properties found at {path}.")
