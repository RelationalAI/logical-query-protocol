#!/usr/bin/env python3
"""End-to-end tests for grammar validation.

These tests validate complete grammar files against protobuf specifications,
testing all validation error cases.
"""

from pathlib import Path
import tempfile
from textwrap import dedent

from meta.proto_parser import ProtoParser
from meta.grammar_validator import validate_grammar
from meta.validation_result import ValidationResult
from meta.yacc_parser import load_yacc_grammar_file
from meta.grammar import Grammar


def create_temp_file(content: str, suffix: str = ".txt") -> Path:
    """Create a temporary file with given content."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    with open(fd, 'w') as f:
        f.write(dedent(content))
    return Path(path)


def parse_and_validate(grammar_content: str, proto_content: str) -> ValidationResult:
    """Parse grammar and proto files and run validation."""
    import shutil
    import tempfile

    # Create temporary files with consistent names
    # Use "test" as the module name by using test.proto as the filename
    temp_dir = tempfile.mkdtemp()
    grammar_file = Path(temp_dir) / "grammar.y"
    proto_file = Path(temp_dir) / "test.proto"

    grammar_file.write_text(dedent(grammar_content))
    proto_file.write_text(dedent(proto_content))

    result: ValidationResult
    try:
        # Load grammar
        grammar_config = load_yacc_grammar_file(grammar_file)

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
        result = validate_grammar(grammar, proto_parser)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return result


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

        grammar_content = """\
%start person
%token STRING String r'"[^"]*"'

%nonterm person test.Person

%%

person
    : STRING
      construct: $$ = test.Person(name=$1)

%%
"""

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        assert any("Address" in e.message for e in result.errors)
        assert any(e.category == "completeness" for e in result.errors)

    def test_rule_name_can_be_anything(self):
        """Test that rule name doesn't matter - only the type matters."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Person {
            string name = 1;
        }
        """

        grammar_content = """\
%start my_custom_person_rule
%token STRING String r'"[^"]*"'

%nonterm my_custom_person_rule test.Person

%%

my_custom_person_rule
    : STRING
      construct: $$ = test.Person(name=$1)

%%
"""

        result = parse_and_validate(grammar_content, proto_content)
        # Should pass completeness check even though rule name is not 'person'
        assert not any(e.category == "completeness" for e in result.errors)
        # May have other warnings/errors (like soundness), but not completeness


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

        grammar_content = """\
%start record
%token STRING String r'"[^"]*"'

%nonterm record test.Record

%%

record
    : STRING
      construct: $$ = $1

%%
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

        grammar_content = """\
%start pair
%token STRING String r'"[^"]*"'

%nonterm pair test.Pair

%%

pair
    : STRING STRING
      construct: $$ = test.Pair(first=builtin.tuple($1, $2)[5], second=$2)

%%
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

        grammar_content = """\
%start record
%token STRING String r'"[^"]*"'

%nonterm record test.Record

%%

record
    : STRING
      construct: $$ = test.Record(value=$1[0])

%%
"""

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        assert any(e.category == "type_tuple_element" for e in result.errors)
        assert any("expects tuple type" in e.message for e in result.errors)

    def test_message_constructor_arity_error(self):
        """Test message constructor with missing fields generates error."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Person {
            string name = 1;
            int32 age = 2;
        }
        """

        grammar_content = """\
%start person
%token STRING String r'"[^"]*"'

%nonterm person test.Person

%%

person
    : STRING
      construct: $$ = test.Person(name=$1)

%%
"""

        result = parse_and_validate(grammar_content, proto_content)
        # Missing fields are errors
        assert not result.is_valid
        assert any(e.category == "field_coverage" for e in result.errors)
        assert any("age" in e.message for e in result.errors)

    def test_builtin_unwrap_option_or_non_option_arg(self):
        """Test unwrap_option_or with non-option argument."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Record {
            string value = 1;
        }
        """

        grammar_content = """\
%start record
%token STRING String r'"[^"]*"'

%nonterm record test.Record

%%

record
    : STRING
      construct: $$ = test.Record(value=builtin.unwrap_option_or($1, "default"))

%%
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

        grammar_content = """\
%start record
%token STRING String r'"[^"]*"'

%nonterm record test.Record

%%

record
    : STRING
      construct: $$ = test.Record(count=builtin.length($1))

%%
"""

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        assert any(e.category == "type_builtin_arg" for e in result.errors)
        assert any("expected Sequence" in e.message for e in result.errors)


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

        grammar_content = """\
%start value
%token STRING String r'"[^"]*"'

%nonterm value test.Value

%%

value
    : STRING
      construct: $$ = test.Value(kind=oneof_text($1))

%%
"""

        result = parse_and_validate(grammar_content, proto_content)
        assert not result.is_valid
        assert any(e.category == "oneof_coverage" for e in result.errors)
        assert any("number" in e.message for e in result.errors)


class TestSoundnessErrors:
    """Tests for soundness errors (rules without proto backing)."""

    def test_rule_without_proto_backing(self):
        """Test error for rule with type that doesn't correspond to a proto message."""
        proto_content = """
        syntax = "proto3";
        package test;

        message Person {
            string name = 1;
        }
        """

        grammar_content = """\
%start person
%token STRING String r'"[^"]*"'

%nonterm person test.Person
%nonterm unknown_rule test.NonExistentMessage

%%

person
    : STRING
      construct: $$ = test.Person(name=$1)

unknown_rule
    : STRING
      construct: $$ = test.NonExistentMessage(name=$1)

%%
"""

        result = parse_and_validate(grammar_content, proto_content)
        assert any(e.category == "soundness" for e in result.errors)
        assert any("unknown_rule" in e.message and "is not a valid type" in e.message for e in result.errors)


class TestUnreachableRules:
    """Tests for unreachable rule detection."""

    def test_unreachable_rule_error(self):
        """Test error for unreachable rule."""
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

        grammar_content = """\
%start start
%token STRING String r'"[^"]*"'

%nonterm start test.Start
%nonterm orphan test.Orphan

%%

start
    : STRING
      construct: $$ = test.Start(value=$1)

orphan
    : STRING
      construct: $$ = test.Orphan(data=$1)

%%
"""

        result = parse_and_validate(grammar_content, proto_content)
        assert any(e.category == "unreachable" for e in result.errors)
        assert any("orphan" in e.message for e in result.errors)


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

        grammar_content = """\
%start person
%token STRING String r'"[^"]*"'
%token INT Int64 r'[-]?\\d+'

%nonterm person test.Person

%%

person
    : STRING INT
      construct: $$ = test.Person(name=$1, age=builtin.int64_to_int32($2))

%%
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

        grammar_content = """\
%start value
%token STRING String r'"[^"]*"'
%token INT Int64 r'[-]?\\d+'

%nonterm value test.Value

%%

value
    : STRING
      construct: $$ = test.Value(kind=oneof_text($1))
    | INT
      construct: $$ = test.Value(kind=oneof_number($1))

%%
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

        grammar_content = """\
%start record
%token STRING String r'"[^"]*"'

%nonterm record test.Record

%%

record
    : STRING*
      construct: $$ = test.Record(values=$1)

%%
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

        grammar_content = """\
%start record
%token STRING String r'"[^"]*"'

%nonterm record test.Record

%%

record
    : STRING?
      construct: $$ = test.Record(value=$1)

%%
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

        grammar_content = """\
%start person
%token STRING String r'"[^"]*"'

%nonterm person test.Person
%nonterm address test.Address

%%

person
    : STRING address
      construct: $$ = test.Person(name=$1, address=$2)

address
    : STRING
      construct: $$ = test.Address(street=$1)

%%
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

        grammar_content = """\
%start person
%token STRING String r'"[^"]*"'
%token INT Int64 r'[-]?\\d+'

%nonterm person test.Person

%%

person
    : STRING INT
      construct: $$ = $1

%%
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

        grammar_content = """\
%start pair
%token STRING String r'"[^"]*"'

%nonterm pair test.Pair

%%

pair
    : STRING STRING
      construct: $$ = test.Pair(first=builtin.tuple($1, $2)[0], second=builtin.tuple($1, $2)[1])

%%
"""

        result = parse_and_validate(grammar_content, proto_content)
        assert result.is_valid
        assert len(result.errors) == 0
