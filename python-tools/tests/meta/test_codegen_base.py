#!/usr/bin/env python3
"""Tests for base code generation infrastructure."""

from meta.codegen_python import PythonCodeGenerator
from meta.codegen_base import BuiltinResult


def test_generator_instance_isolation():
    """Test that generator instances don't share state."""
    gen1 = PythonCodeGenerator()
    gen2 = PythonCodeGenerator()

    # Register a custom builtin on gen1
    gen1.register_builtin("custom_op",
        lambda args, lines, indent: BuiltinResult(f"custom({args[0]})", []))

    # gen1 should have the custom builtin
    assert "custom_op" in gen1.builtin_registry

    # gen2 should NOT have the custom builtin
    assert "custom_op" not in gen2.builtin_registry


if __name__ == "__main__":
    test_generator_instance_isolation()
