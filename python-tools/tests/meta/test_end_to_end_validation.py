#!/usr/bin/env python3
"""End-to-end tests for grammar validation.

These tests validate complete grammar files against protobuf specifications,
testing all validation error and warning cases.
"""

from pathlib import Path
import tempfile
from textwrap import dedent

from meta.proto_parser import ProtoParser
from meta.grammar_validator import validate_grammar
from meta.sexp_grammar import load_grammar_config_file
from meta.grammar import Grammar


def create_temp_file(content: str, suffix: str = ".txt") -> Path:
    """Create a temporary file with given content."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with open(fd, 'w') as f:
        f.write(dedent(content))
    return Path(path)


def parse_and_validate(grammar_content: str, proto_content: str, expected_unreachable=None):
    """Parse grammar and proto files and run validation."""
    if expected_unreachable is None:
        expected_unreachable = set()

    # Create temporary files with consistent names
    # Use "test" as the module name by using test.proto as the filename
    import os
    import tempfile
    temp_dir = tempfile.mkdtemp()
    grammar_file = Path(temp_dir) / "grammar.sexp"
    proto_file = Path(temp_dir) / "test.proto"

    grammar_file.write_text(dedent(grammar_content))
    proto_file.write_text(dedent(proto_content))

    try:
        # Load grammar
        grammar_config = load_grammar_config_file(grammar_file)

        # Determine start symbol from grammar
        start = None
        for lhs in grammar_config.rules.keys():
            start = lhs
            break

        if not start:
            raise ValueError("Grammar has no rules")

        grammar = Grammar(start=start)
        for lhs, rules in grammar_config.rules.items():
            for rule in rules:
                grammar.add_rule(rule)

        # Parse proto
        proto_parser = ProtoParser()
        proto_parser.parse_file(proto_file)

        # Validate
        result = validate_grammar(grammar, proto_parser, expected_unreachable)
        return result
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestCompletenessErrors:
    """Tests for completeness validation (missing rules for proto messages)."""

    def test_missing_message_rule(self):
        """Test that missing grammar rule for proto message is detected."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Person {
            string name = 1;
        }

        message Address {
            string street = 1;
        }
        """

        grammar_content = """
        ;; Only define rule for Person, not Address
        (rule
          (lhs person (Message test Person))
          (rhs (term STRING String))
          (lambda ((name String)) (Message test Person)
            (new-message test Person (name (var name String)))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        assert any("Address" in e.message for e in result.errors)
        assert any(e.category == "completeness" for e in result.errors)


class TestTypeErrors:
    """Tests for type checking errors."""

    def test_return_type_mismatch(self):
        """Test lambda return type doesn't match nonterminal type."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Record {
            string value = 1;
        }
        """

        grammar_content = """
        ;; Lambda returns String but nonterminal expects test.Record
        (rule
          (lhs record (Message test Record))
          (rhs (term STRING String))
          (lambda ((value String)) String
            (var value String)))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        assert any(e.category == "type_return" for e in result.errors)

    def test_getelement_out_of_bounds(self):
        """Test GetElement with index out of bounds."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Pair {
            string first = 1;
            string second = 2;
        }
        """

        grammar_content = """
        (rule
          (lhs pair (Message test Pair))
          (rhs (term STRING String) (term STRING String))
          (lambda ((first String) (second String)) (Message test Pair)
            (let (tuple (Tuple String String))
              (call (builtin make_tuple) (var first String) (var second String))
              (new-message test Pair
                (first (get-element (var tuple (Tuple String String)) 5))
                (second (var second String))))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid, f"Expected errors but got: {result.summary()}"
        assert any(e.category == "type_tuple_element" for e in result.errors), f"Expected type_tuple_element error, got: {[e.category for e in result.errors]}"
        assert any("out of bounds" in e.message for e in result.errors)

    def test_getelement_non_tuple_type(self):
        """Test GetElement with non-tuple expression."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Record {
            string value = 1;
        }
        """

        grammar_content = """
        (rule
          (lhs record (Message test Record))
          (rhs (term STRING String))
          (lambda ((value String)) (Message test Record)
            (new-message test Record
              (value (get-element (var value String) 0)))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        assert any(e.category == "type_tuple_element" for e in result.errors)
        assert any("expects tuple type" in e.message for e in result.errors)

    def test_message_constructor_arity_error(self):
        """Test message constructor with missing fields generates warning."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Person {
            string name = 1;
            int32 age = 2;
        }
        """

        grammar_content = """
        ;; Message with only 1 field provided (age field missing)
        (rule
          (lhs person (Message test Person))
          (rhs (term STRING String))
          (lambda ((name String)) (Message test Person)
            (new-message test Person (name (var name String)))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        # With NewMessage, missing fields are warnings, not errors
        assert result.is_valid
        assert any(w.category == "field_coverage" for w in result.warnings)
        assert any("age" in w.message for w in result.warnings)

    def test_builtin_unwrap_option_or_non_option_arg(self):
        """Test unwrap_option_or with non-option argument."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Record {
            string value = 1;
        }
        """

        grammar_content = """
        (rule
          (lhs record (Message test Record))
          (rhs (term STRING String))
          (lambda ((value String)) (Message test Record)
            (new-message test Record
              (value (call (builtin unwrap_option_or) (var value String) (lit "default"))))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        assert any(e.category == "type_builtin_arg" for e in result.errors)
        assert any("expected Option" in e.message for e in result.errors)

    def test_builtin_length_non_list_arg(self):
        """Test length builtin with non-list argument."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Record {
            int64 count = 1;
        }
        """

        grammar_content = """
        (rule
          (lhs record (Message test Record))
          (rhs (term STRING String))
          (lambda ((value String)) (Message test Record)
            (new-message test Record
              (count (call (builtin length) (var value String))))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        assert any(e.category == "type_builtin_arg" for e in result.errors)
        assert any("expected List" in e.message for e in result.errors)


class TestOneofCoverage:
    """Tests for oneof coverage validation."""

    def test_missing_oneof_variant(self):
        """Test missing grammar rule for oneof variant."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Value {
            oneof kind {
                string text = 1;
                int64 number = 2;
            }
        }
        """

        grammar_content = """
        ;; Only handle text variant, missing number variant
        (rule
          (lhs value (Message test Value))
          (rhs (term STRING String))
          (lambda ((text String)) (Message test Value)
            (new-message test Value
              (kind (call (oneof text) (var text String))))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        assert any(e.category == "oneof_coverage" for e in result.errors)
        assert any("number" in e.message for e in result.errors)


class TestSoundnessWarnings:
    """Tests for soundness warnings (rules without proto backing)."""

    def test_rule_without_proto_backing(self):
        """Test warning for rule without corresponding proto message."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Person {
            string name = 1;
        }
        """

        grammar_content = """
        (rule
          (lhs person (Message test Person))
          (rhs (term STRING String))
          (lambda ((name String)) (Message test Person)
            (new-message test Person (name (var name String)))))

        ;; This rule has no proto backing
        (rule
          (lhs unknown_rule String)
          (rhs (term STRING String))
          (lambda ((value String)) String
            (var value String)))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert any(w.category == "soundness" for w in result.warnings)
        assert any("unknown_rule" in w.message for w in result.warnings)


class TestUnreachableRules:
    """Tests for unreachable rule detection."""

    def test_unreachable_rule_warning(self):
        """Test warning for unreachable rule."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Start {
            string value = 1;
        }

        message Orphan {
            string data = 1;
        }
        """

        grammar_content = """
        (rule
          (lhs start (Message test Start))
          (rhs (term STRING String))
          (lambda ((value String)) (Message test Start)
            (new-message test Start (value (var value String)))))

        ;; This rule is never referenced from start
        (rule
          (lhs orphan (Message test Orphan))
          (rhs (term STRING String))
          (lambda ((data String)) (Message test Orphan)
            (new-message test Orphan (data (var data String)))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert any(w.category == "unreachable" for w in result.warnings)
        assert any("orphan" in w.message for w in result.warnings)

    def test_expected_unreachable_no_warning(self):
        """Test that expected unreachable rules don't produce warnings."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Start {
            string value = 1;
        }

        message Orphan {
            string data = 1;
        }
        """

        grammar_content = """
        (rule
          (lhs start (Message test Start))
          (rhs (term STRING String))
          (lambda ((value String)) (Message test Start)
            (new-message test Start (value (var value String)))))

        (rule
          (lhs orphan (Message test Orphan))
          (rhs (term STRING String))
          (lambda ((data String)) (Message test Orphan)
            (new-message test Orphan (data (var data String)))))
        """

        result = parse_and_validate(grammar_content, proto_content, expected_unreachable={'orphan'})
        # Should not have unreachable warning for orphan
        assert not any("orphan" in w.message and w.category == "unreachable" for w in result.warnings)


class TestValidGrammar:
    """Tests for valid grammars that should pass validation."""

    def test_simple_valid_grammar(self):
        """Test a simple valid grammar passes all validation."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Person {
            string name = 1;
            int32 age = 2;
        }
        """

        grammar_content = """
        (rule
          (lhs person (Message test Person))
          (rhs (term STRING String) (term INT Int64))
          (lambda ((name String) (age Int64)) (Message test Person)
            (new-message test Person (name (var name String)) (age (call (builtin int64_to_int32) (var age Int64))))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_grammar_with_oneof(self):
        """Test valid grammar with oneof coverage."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Value {
            oneof kind {
                string text = 1;
                int64 number = 2;
            }
        }
        """

        grammar_content = """
        (rule
          (lhs value (Message test Value))
          (rhs (term STRING String))
          (lambda ((text String)) (Message test Value)
            (new-message test Value
              (kind (call (oneof text) (var text String))))))

        (rule
          (lhs value (Message test Value))
          (rhs (term INT Int64))
          (lambda ((number Int64)) (Message test Value)
            (new-message test Value
              (kind (call (oneof number) (var number Int64))))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_grammar_with_repeated_fields(self):
        """Test valid grammar with repeated fields."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Record {
            repeated string values = 1;
        }
        """

        grammar_content = """
        (rule
          (lhs record (Message test Record))
          (rhs (star (term STRING String)))
          (lambda ((values (List String))) (Message test Record)
            (new-message test Record (values (var values (List String))))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_grammar_with_optional_fields(self):
        """Test valid grammar with optional fields."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Record {
            optional string value = 1;
        }
        """

        grammar_content = """
        (rule
          (lhs record (Message test Record))
          (rhs (option (term STRING String)))
          (lambda ((opt_value (Option String))) (Message test Record)
            (new-message test Record (value (var opt_value (Option String))))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_grammar_with_nested_messages(self):
        """Test valid grammar with nested message references."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Person {
            string name = 1;
            Address address = 2;
        }

        message Address {
            string street = 1;
        }
        """

        grammar_content = """
        (rule
          (lhs person (Message test Person))
          (rhs (term STRING String) (nonterm address (Message test Address)))
          (lambda ((name String) (addr (Message test Address))) (Message test Person)
            (new-message test Person (name (var name String)) (address (var addr (Message test Address))))))

        (rule
          (lhs address (Message test Address))
          (rhs (term STRING String))
          (lambda ((street String)) (Message test Address)
            (new-message test Address (street (var street String)))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert result.is_valid
        assert len(result.errors) == 0


class TestComplexValidationScenarios:
    """Tests for complex validation scenarios."""

    def test_multiple_errors_in_single_grammar(self):
        """Test grammar with multiple validation errors."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Person {
            string name = 1;
            int32 age = 2;
        }

        message Address {
            string street = 1;
        }
        """

        grammar_content = """
        ;; Wrong return type
        (rule
          (lhs person (Message test Person))
          (rhs (term STRING String) (term INT Int64))
          (lambda ((name String) (age Int64)) String
            (var name String)))

        ;; Missing rule for Address
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        # Should have both type_return error and completeness error
        assert any(e.category == "type_return" for e in result.errors)
        assert any(e.category == "completeness" for e in result.errors)
        assert any("Address" in e.message for e in result.errors)

    def test_grammar_with_getelement_operations(self):
        """Test grammar with valid GetElement operations."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Pair {
            string first = 1;
            string second = 2;
        }
        """

        grammar_content = """
        (rule
          (lhs pair (Message test Pair))
          (rhs (term STRING String) (term STRING String))
          (lambda ((first String) (second String)) (Message test Pair)
            (let (tuple (Tuple String String))
              (call (builtin make_tuple) (var first String) (var second String))
              (new-message test Pair
                (first (get-element (var tuple (Tuple String String)) 0))
                (second (get-element (var tuple (Tuple String String)) 1))))))
        """

        result = parse_and_validate(grammar_content, proto_content)
        assert result.is_valid
        assert len(result.errors) == 0
