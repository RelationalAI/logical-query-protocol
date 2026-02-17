#!/usr/bin/env python3
"""Tests for base code generation infrastructure."""

from meta.codegen_base import BuiltinResult
from meta.codegen_python import PythonCodeGenerator
from meta.codegen_templates import JULIA_TEMPLATES, PYTHON_TEMPLATES


def test_generator_instance_isolation():
    """Test that generator instances don't share state."""
    gen1 = PythonCodeGenerator()
    gen2 = PythonCodeGenerator()

    # Register a custom builtin on gen1
    gen1.register_builtin(
        "custom_op", lambda args, lines, indent: BuiltinResult(f"custom({args[0]})", [])
    )

    # gen1 should have the custom builtin
    assert "custom_op" in gen1.builtin_registry

    # gen2 should NOT have the custom builtin
    assert "custom_op" not in gen2.builtin_registry


def test_template_dictionaries_have_matching_keys():
    """Test that Python and Julia template dictionaries have the same keys."""
    python_keys = set(PYTHON_TEMPLATES.keys())
    julia_keys = set(JULIA_TEMPLATES.keys())

    missing_in_julia = python_keys - julia_keys
    missing_in_python = julia_keys - python_keys

    assert not missing_in_julia, f"Templates missing in Julia: {missing_in_julia}"
    assert not missing_in_python, f"Templates missing in Python: {missing_in_python}"


if __name__ == "__main__":
    test_generator_instance_isolation()
    test_template_dictionaries_have_matching_keys()
