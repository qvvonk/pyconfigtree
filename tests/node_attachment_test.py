from typing import Any

import pytest

from pyconfigtree import Node, parameter
from pyconfigtree.exceptions import LeafNodeError, NodeLoopError, NodeDuplicateError


@pytest.mark.parametrize(
    'param',
    [
        parameter.StringParameter('test', default_value=''),
        parameter.IntParameter('test', default_value=1),
        parameter.FloatParameter('test', default_value=0.1),
        parameter.BoolParameter('test', default_value=True),
    ],
)
def test_cannot_attach_node_to_parameter(param: parameter.Parameter[Any]) -> None:
    node = Node('test')
    assert pytest.raises(
        LeafNodeError,
        param._attach_node,
        node,
    )


def test_cannot_attach_node_to_itself() -> None:
    node = Node('test')
    assert pytest.raises(
        NodeLoopError,
        node._attach_node,
        node,
    )


def test_cannot_attach_node_with_a_loop() -> None:
    node_1 = Node('1')
    node_2 = Node('2')
    node_1._attach_node(node_2)
    assert pytest.raises(
        NodeLoopError,
        node_2._attach_node,
        node_1,
    )


def test_cannot_attach_node_with_same_id() -> None:
    node_1 = Node('1')
    node_2 = Node('2')
    node_3 = Node('2')

    node_1._attach_node(node_2)
    assert pytest.raises(
        NodeDuplicateError,
        node_1._attach_node,
        node_3,
    )
