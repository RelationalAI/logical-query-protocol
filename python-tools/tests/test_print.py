import pytest
import os
import dataclasses
from pytest_snapshot.plugin import Snapshot

from lqp import parser
from lqp import print as lqp_print
from lqp import ir

def get_lqp_input_files():
    lqp_input_dir = "tests/test_files/lqp_input"
    return [os.path.join(lqp_input_dir, f) for f in os.listdir(lqp_input_dir) if f.endswith(".lqp")]

def assert_lqp_nodes_equal(obj1, obj2):
    if isinstance(obj1, ir.LqpNode) and isinstance(obj2, ir.LqpNode):
        if obj1.__class__ is not obj2.__class__:
            raise AssertionError(f"Node types differ: {obj1.__class__} vs {obj2.__class__}")
        for field_info in dataclasses.fields(type(obj1)):
            if field_info.name == 'meta': continue
            if field_info.name.startswith('debug_'): continue
            assert_lqp_nodes_equal(getattr(obj1, field_info.name), getattr(obj2, field_info.name))
    elif isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
        if len(obj1) != len(obj2):
            raise AssertionError(f"Sequence lengths differ: {len(obj1)} vs {len(obj2)}")
        for i, (item1, item2) in enumerate(zip(obj1, obj2)):
            assert_lqp_nodes_equal(item1, item2)
    elif obj1 != obj2:
        raise AssertionError(f"Values differ: {obj1} vs {obj2}")

@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_print_snapshot(snapshot, input_file):
    with open(input_file, "r") as f:
        original_lqp_str = f.read()
    parsed_node = parser.parse_lqp(input_file, original_lqp_str)
    options = lqp_print.ugly_config.copy()
    options[str(lqp_print.PrettyOptions.PRINT_DEBUG)] = False
    printed_lqp_str = lqp_print.to_string(parsed_node, options)
    snapshot.snapshot_dir = "tests/lqp_output"
    snapshot.assert_match(printed_lqp_str, os.path.basename(input_file))
    re_parsed_node = parser.parse_lqp("reparsed_output.lqp", printed_lqp_str)
    assert_lqp_nodes_equal(re_parsed_node, parsed_node)

@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_print_debug_snapshot(snapshot, input_file):
    with open(input_file, "r") as f:
        original_lqp_str = f.read()
    parsed_node = parser.parse_lqp(input_file, original_lqp_str)
    options = lqp_print.ugly_config.copy()
    options[str(lqp_print.PrettyOptions.PRINT_DEBUG)] = True
    printed_lqp_str = lqp_print.to_string(parsed_node, options)
    snapshot.snapshot_dir = "tests/lqp_debug_output"
    snapshot.assert_match(printed_lqp_str, os.path.basename(input_file))
    re_parsed_node = parser.parse_lqp("reparsed_output.lqp", printed_lqp_str)
    assert_lqp_nodes_equal(re_parsed_node, parsed_node)

@pytest.mark.parametrize("input_file", get_lqp_input_files())
def test_print_pretty_snapshot(snapshot, input_file):
    with open(input_file, "r") as f:
        original_lqp_str = f.read()
    parsed_node = parser.parse_lqp(input_file, original_lqp_str)
    printed_lqp_str = lqp_print.to_string(parsed_node, {})
    options = lqp_print.ugly_config.copy()
    options[str(lqp_print.PrettyOptions.PRINT_NAMES)] = True
    options[str(lqp_print.PrettyOptions.PRINT_DEBUG)] = False
    pretty_printed_lqp_str = lqp_print.to_string(parsed_node, options)
    snapshot.snapshot_dir = "tests/lqp_pretty_output"
    snapshot.assert_match(pretty_printed_lqp_str, os.path.basename(input_file))
    re_parsed_node = parser.parse_lqp("reparsed_output.lqp", pretty_printed_lqp_str)
    assert_lqp_nodes_equal(re_parsed_node, parsed_node)
