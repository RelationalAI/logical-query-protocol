#!/usr/bin/env python3
"""Integration tests for meta.cli.

Tests the full CLI workflow including validation, parser generation,
and protobuf output using small test cases.
"""

import subprocess
import tempfile
from pathlib import Path
from textwrap import dedent
import sys


def create_test_files():
    """Create small test protobuf and grammar files.

    Returns:
        tuple: (proto_path, grammar_path, temp_dir)
    """
    temp_dir = Path(tempfile.mkdtemp())

    # Create a minimal protobuf file with transactions structure
    proto_content = dedent("""
    syntax = "proto3";
    package transactions;

    message Transaction {
        string name = 1;
        int32 value = 2;
    }
    """)

    proto_path = temp_dir / "test.proto"
    proto_path.write_text(proto_content)

    # Create a complete grammar that covers the Transaction message
    # Note: module name comes from filename stem (test), not package name
    grammar_content = dedent("""
    (terminal STRING String)
    (terminal INT Int32)

    (rule
      (lhs transaction (Message test Transaction))
      (rhs "(" "transaction" STRING INT ")")
      (construct
        ((name String) (value Int32))
        (Message test Transaction)
        (new-message test Transaction
          (name (var name String))
          (value (var value Int32)))))
    """)

    grammar_path = temp_dir / "grammar.sexp"
    grammar_path.write_text(grammar_content)

    return proto_path, grammar_path, temp_dir


def create_invalid_grammar():
    """Create a grammar that fails validation (missing coverage).

    Returns:
        tuple: (proto_path, grammar_path, temp_dir)
    """
    temp_dir = Path(tempfile.mkdtemp())

    # Create a protobuf with two messages
    proto_content = dedent("""
    syntax = "proto3";
    package transactions;

    message Transaction {
        oneof data {
            Person person = 1;
            Address address = 2;
        }
    }

    message Person {
        string name = 1;
    }

    message Address {
        string street = 1;
    }
    """)

    proto_path = temp_dir / "test.proto"
    proto_path.write_text(proto_content)

    # Grammar only covers Transaction with Person, not Address (validation failure)
    # Note: module name comes from filename stem (test), not package name
    grammar_content = dedent("""
    (terminal STRING String)

    (rule
      (lhs transaction (Message test Transaction))
      (rhs "(" "person" STRING ")")
      (construct
        ((name String))
        (Message test Transaction)
        (new-message test Transaction
          (data (call (oneof person)
            (new-message test Person
              (name (var name String))))))))

    (rule
      (lhs person (Message test Person))
      (rhs "(" "person" STRING ")")
      (construct
        ((name String))
        (Message test Person)
        (new-message test Person (name (var name String)))))
    """)

    grammar_path = temp_dir / "grammar.sexp"
    grammar_path.write_text(grammar_content)

    return proto_path, grammar_path, temp_dir


def run_cli(*args):
    """Run the meta.cli module with given arguments.

    Returns:
        tuple: (returncode, stdout, stderr)
    """
    import os
    cmd = [sys.executable, "-m", "meta.cli"] + list(args)
    src_dir = Path(__file__).parent.parent.parent / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_dir)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
        env=env
    )
    return result.returncode, result.stdout, result.stderr


class TestCLIValidation:
    """Test validation functionality."""

    def test_validate_valid_grammar(self):
        """Test that validation succeeds for a valid grammar."""
        proto_path, grammar_path, temp_dir = create_test_files()
        try:
            returncode, stdout, stderr = run_cli(
                str(proto_path),
                "--grammar", str(grammar_path),
                "--validate"
            )

            assert returncode == 0, f"Expected success, got {returncode}\nstdout: {stdout}\nstderr: {stderr}"
            assert "Grammar validation passed" in stdout or "VALID" in stdout or "valid" in stdout.lower()
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_invalid_grammar(self):
        """Test that validation fails for an incomplete grammar."""
        proto_path, grammar_path, temp_dir = create_invalid_grammar()
        try:
            returncode, stdout, stderr = run_cli(
                str(proto_path),
                "--grammar", str(grammar_path),
                "--validate"
            )

            assert returncode != 0, "Expected validation to fail"
            assert "address" in stdout or "address" in stderr
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parser_blocked_on_validation_failure(self):
        """Test that parser generation is blocked when validation fails."""
        proto_path, grammar_path, temp_dir = create_invalid_grammar()
        try:
            # Try to generate IR parser with invalid grammar
            returncode, _stdout, stderr = run_cli(
                str(proto_path),
                "--grammar", str(grammar_path),
                "--parser", "ir"
            )

            assert returncode != 0, "Expected parser generation to fail"
            assert "Cannot generate parser" in stderr or "validation" in stderr.lower()

            # Try to generate Python parser with invalid grammar
            returncode, _stdout, stderr = run_cli(
                str(proto_path),
                "--grammar", str(grammar_path),
                "--parser", "python"
            )

            assert returncode != 0, "Expected parser generation to fail"
            assert "Cannot generate parser" in stderr or "validation" in stderr.lower()
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestCLIProtoOutput:
    """Test --proto output functionality."""

    def test_proto_output(self):
        """Test that --proto outputs parsed protobuf specification."""
        proto_path, grammar_path, temp_dir = create_test_files()
        try:
            returncode, stdout, stderr = run_cli(
                str(proto_path),
                "--proto"
            )

            assert returncode == 0, f"Expected success, got {returncode}\nstderr: {stderr}"
            assert "message Transaction" in stdout
            assert "string name" in stdout
            assert "int32 value" in stdout
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_proto_output_to_file(self):
        """Test that --proto -o writes to file."""
        proto_path, _grammar_path, temp_dir = create_test_files()
        output_path = temp_dir / "proto_output.txt"
        try:
            returncode, _stdout, stderr = run_cli(
                str(proto_path),
                "--proto",
                "-o", str(output_path)
            )

            assert returncode == 0, f"Expected success, got {returncode}\nstderr: {stderr}"
            assert output_path.exists(), "Output file was not created"

            output_content = output_path.read_text()
            assert "message Transaction" in output_content
            assert "string name" in output_content
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestCLIParserIR:
    """Test --parser ir functionality."""

    def test_parser_ir_output(self):
        """Test that --parser ir generates intermediate representation."""
        proto_path, grammar_path, temp_dir = create_test_files()
        try:
            returncode, stdout, stderr = run_cli(
                str(proto_path),
                "--grammar", str(grammar_path),
                "--parser", "ir"
            )

            assert returncode == 0, f"Expected success, got {returncode}\nstderr: {stderr}"
            # IR output should contain parse function definitions
            assert "parse" in stdout.lower() or "def" in stdout.lower()
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parser_ir_output_to_file(self):
        """Test that --parser ir -o writes to file."""
        proto_path, grammar_path, temp_dir = create_test_files()
        output_path = temp_dir / "parser_ir.txt"
        try:
            returncode, _stdout, stderr = run_cli(
                str(proto_path),
                "--grammar", str(grammar_path),
                "--parser", "ir",
                "-o", str(output_path)
            )

            assert returncode == 0, f"Expected success, got {returncode}\nstderr: {stderr}"
            assert output_path.exists(), "Output file was not created"

            output_content = output_path.read_text()
            assert len(output_content) > 0, "Output file is empty"
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestCLIParserPython:
    """Test --parser python functionality."""

    def test_parser_python_output(self):
        """Test that --parser python generates Python code."""
        proto_path, grammar_path, temp_dir = create_test_files()
        try:
            returncode, stdout, stderr = run_cli(
                str(proto_path),
                "--grammar", str(grammar_path),
                "--parser", "python"
            )

            assert returncode == 0, f"Expected success, got {returncode}\nstderr: {stderr}"
            # Python output should contain valid Python code
            assert "def " in stdout or "class " in stdout
            assert "import" in stdout or "from" in stdout
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parser_python_output_to_file(self):
        """Test that --parser python -o writes to file."""
        proto_path, grammar_path, temp_dir = create_test_files()
        output_path = temp_dir / "parser.py"
        try:
            returncode, _stdout, stderr = run_cli(
                str(proto_path),
                "--grammar", str(grammar_path),
                "--parser", "python",
                "-o", str(output_path)
            )

            assert returncode == 0, f"Expected success, got {returncode}\nstderr: {stderr}"
            assert output_path.exists(), "Output file was not created"

            output_content = output_path.read_text()
            assert len(output_content) > 0, "Output file is empty"
            assert "def " in output_content or "class " in output_content
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parser_python_is_valid_syntax(self):
        """Test that generated Python code has valid syntax."""
        proto_path, grammar_path, temp_dir = create_test_files()
        output_path = temp_dir / "parser.py"
        try:
            returncode, _stdout, stderr = run_cli(
                str(proto_path),
                "--grammar", str(grammar_path),
                "--parser", "python",
                "-o", str(output_path)
            )

            assert returncode == 0, f"Expected success, got {returncode}\nstderr: {stderr}"
            assert output_path.exists(), "Output file was not created"

            # Try to compile the Python file to check syntax
            import py_compile
            py_compile.compile(str(output_path), doraise=True)
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestCLIErrorHandling:
    """Test error handling."""

    def test_missing_proto_file(self):
        """Test error when proto file doesn't exist."""
        returncode, _stdout, stderr = run_cli(
            "nonexistent.proto",
            "--proto"
        )

        assert returncode != 0, "Expected failure for missing file"
        assert "not found" in stderr.lower() or "error" in stderr.lower()

    def test_missing_grammar_file(self):
        """Test error when grammar file doesn't exist."""
        proto_path, _grammar_path, temp_dir = create_test_files()
        try:
            returncode, _stdout, stderr = run_cli(
                str(proto_path),
                "--grammar", "nonexistent.sexp",
                "--validate"
            )

            assert returncode != 0, "Expected failure for missing grammar"
            assert "not found" in stderr.lower() or "error" in stderr.lower()
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_parser_requires_grammar(self):
        """Test that --parser requires --grammar."""
        proto_path, _grammar_path, temp_dir = create_test_files()
        try:
            returncode, _stdout, stderr = run_cli(
                str(proto_path),
                "--parser", "python"
            )

            assert returncode != 0, "Expected failure when --grammar is missing"
            assert "grammar" in stderr.lower() or "required" in stderr.lower()
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_requires_grammar(self):
        """Test that --validate requires --grammar."""
        proto_path, _grammar_path, temp_dir = create_test_files()
        try:
            returncode, _stdout, stderr = run_cli(
                str(proto_path),
                "--validate"
            )

            assert returncode != 0, "Expected failure when --grammar is missing"
            assert "grammar" in stderr.lower() or "required" in stderr.lower()
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
