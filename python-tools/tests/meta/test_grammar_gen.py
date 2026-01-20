#!/usr/bin/env python3
"""Tests for grammar generation from protobuf messages.

This module tests the grammar generation logic including builtin rules
and rule rewrites by creating protobuf AST structures programmatically
and verifying the generated grammar rules.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meta.proto_ast import ProtoMessage, ProtoField, ProtoOneof, ProtoEnum
from meta.proto_parser import ProtoParser
from meta.grammar_gen import GrammarGenerator
from meta.grammar import Nonterminal, LitTerminal, NamedTerminal, Sequence, Star, Option
from meta.target import MessageType, BaseType, ListType, OptionType


class TestGrammarGenBuiltins:
    """Tests for builtin grammar rule generation."""

    def test_simple_message_with_basic_fields(self):
        """Test grammar generation for a message with basic scalar fields."""
        # Create proto AST: message Point { int64 x = 1; int64 y = 2; }
        msg = ProtoMessage(
            name="Point",
            module="test",
            fields=[
                ProtoField(name="x", type="int64", number=1),
                ProtoField(name="y", type="int64", number=2),
            ]
        )

        parser = ProtoParser()
        parser.messages["Point"] = msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Check that point nonterminal exists (lowercase)
        point_nt = Nonterminal("point", MessageType("test", "Point"))
        assert grammar.has_rule(point_nt)

        # Get the rule for Point
        rules = grammar.get_rules(point_nt)
        assert len(rules) == 1

        rule = rules[0]
        assert rule.lhs == point_nt

        # The RHS should be: "(" "point" INT INT ")"
        assert isinstance(rule.rhs, Sequence)
        elements = rule.rhs.elements
        assert len(elements) == 5
        assert isinstance(elements[0], LitTerminal) and elements[0].name == "("
        assert isinstance(elements[1], LitTerminal) and elements[1].name == "point"
        assert isinstance(elements[2], NamedTerminal) and elements[2].name == "INT"
        assert isinstance(elements[3], NamedTerminal) and elements[3].name == "INT"
        assert isinstance(elements[4], LitTerminal) and elements[4].name == ")"

        # Check constructor has correct parameters
        assert len(rule.constructor.params) == 2
        assert rule.constructor.params[0].name == "x"
        assert rule.constructor.params[1].name == "y"

    def test_message_with_repeated_field(self):
        """Test grammar generation for a message with a repeated field."""
        # Create proto AST: message List { repeated int64 items = 1; }
        msg = ProtoMessage(
            name="List",
            module="test",
            fields=[
                ProtoField(name="items", type="int64", number=1, is_repeated=True),
            ]
        )

        parser = ProtoParser()
        parser.messages["List"] = msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Check that list nonterminal exists
        list_nt = Nonterminal("list", MessageType("test", "List"))
        assert grammar.has_rule(list_nt)

        rules = grammar.get_rules(list_nt)
        assert len(rules) == 1

        rule = rules[0]

        # The RHS should be: "(" "list" INT* ")"
        assert isinstance(rule.rhs, Sequence)
        elements = rule.rhs.elements
        assert len(elements) == 4
        assert isinstance(elements[0], LitTerminal) and elements[0].name == "("
        assert isinstance(elements[1], LitTerminal) and elements[1].name == "list"
        assert isinstance(elements[2], Star)
        assert isinstance(elements[2].rhs, NamedTerminal)
        assert elements[2].rhs.name == "INT"
        assert isinstance(elements[3], LitTerminal) and elements[3].name == ")"

        # Check constructor parameter
        assert len(rule.constructor.params) == 1
        assert rule.constructor.params[0].name == "items"
        assert isinstance(rule.constructor.params[0].type, ListType)

    def test_message_with_optional_field(self):
        """Test grammar generation for a message with an optional field."""
        # Create proto AST: message Optional { optional int64 value = 1; }
        msg = ProtoMessage(
            name="Optional",
            module="test",
            fields=[
                ProtoField(name="value", type="int64", number=1, is_optional=True),
            ]
        )

        parser = ProtoParser()
        parser.messages["Optional"] = msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Check that optional nonterminal exists
        opt_nt = Nonterminal("optional", MessageType("test", "Optional"))
        assert grammar.has_rule(opt_nt)

        rules = grammar.get_rules(opt_nt)
        assert len(rules) == 1

        rule = rules[0]

        # The RHS should be: "(" "optional" INT? ")"
        assert isinstance(rule.rhs, Sequence)
        elements = rule.rhs.elements
        assert len(elements) == 4
        assert isinstance(elements[0], LitTerminal) and elements[0].name == "("
        assert isinstance(elements[1], LitTerminal) and elements[1].name == "optional"
        assert isinstance(elements[2], Option)
        assert isinstance(elements[2].rhs, NamedTerminal)
        assert elements[2].rhs.name == "INT"
        assert isinstance(elements[3], LitTerminal) and elements[3].name == ")"

        # Check constructor parameter
        assert len(rule.constructor.params) == 1
        assert rule.constructor.params[0].name == "value"
        assert isinstance(rule.constructor.params[0].type, OptionType)

    def test_message_with_string_field(self):
        """Test grammar generation for a message with a string field."""
        # Create proto AST: message StringHolder { string value = 1; }
        msg = ProtoMessage(
            name="StringHolder",
            module="test",
            fields=[
                ProtoField(name="value", type="string", number=1),
            ]
        )

        parser = ProtoParser()
        parser.messages["StringHolder"] = msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Check that string_holder nonterminal exists
        string_holder_nt = Nonterminal("string_holder", MessageType("test", "StringHolder"))
        assert grammar.has_rule(string_holder_nt)

        rules = grammar.get_rules(string_holder_nt)
        assert len(rules) == 1

        rule = rules[0]

        # The RHS should be: "(" "string_holder" name ")" where name is a nonterminal for strings
        assert isinstance(rule.rhs, Sequence)
        elements = rule.rhs.elements
        assert len(elements) == 4
        assert isinstance(elements[0], LitTerminal) and elements[0].name == "("
        assert isinstance(elements[1], LitTerminal) and elements[1].name == "string_holder"
        assert isinstance(elements[2], Nonterminal) and elements[2].name == "name"
        assert isinstance(elements[3], LitTerminal) and elements[3].name == ")"

    def test_message_with_oneof(self):
        """Test grammar generation for a message with a oneof field."""
        # Create proto AST:
        # message Container {
        #   oneof content_type {
        #     int64 int_value = 1;
        #     string str_value = 2;
        #   }
        # }
        msg = ProtoMessage(
            name="Container",
            module="test",
            oneofs=[
                ProtoOneof(
                    name="content_type",
                    fields=[
                        ProtoField(name="int_value", type="int64", number=1),
                        ProtoField(name="str_value", type="string", number=2),
                    ]
                )
            ]
        )

        parser = ProtoParser()
        parser.messages["Container"] = msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Expected grammar:
        # container -> int_value | str_value
        # int_value -> INT64
        # str_value -> STRING

        # Check that container nonterminal exists
        container_nt = Nonterminal("container", MessageType("test", "Container"))
        assert grammar.has_rule(container_nt)

        rules = grammar.get_rules(container_nt)
        # Should have 2 rules: one for int_value, one for str_value
        assert len(rules) == 2

        # Check first alternative: int_value nonterminal
        rule1 = rules[0]
        assert isinstance(rule1.rhs, Nonterminal)
        assert rule1.rhs.name == "int_value"

        # Check second alternative: str_value nonterminal
        rule2 = rules[1]
        assert isinstance(rule2.rhs, Nonterminal)
        assert rule2.rhs.name == "str_value"

    def test_message_with_nested_message_field(self):
        """Test grammar generation for a message with a nested message field."""
        # Create proto AST:
        # message Inner { int64 value = 1; }
        # message Outer { Inner inner = 1; }
        inner_msg = ProtoMessage(
            name="Inner",
            module="test",
            fields=[
                ProtoField(name="value", type="int64", number=1),
            ]
        )

        outer_msg = ProtoMessage(
            name="Outer",
            module="test",
            fields=[
                ProtoField(name="inner", type="Inner", number=1),
            ]
        )

        parser = ProtoParser()
        parser.messages["Inner"] = inner_msg
        parser.messages["Outer"] = outer_msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Check that both nonterminals exist
        inner_nt = Nonterminal("inner", MessageType("test", "Inner"))
        outer_nt = Nonterminal("outer", MessageType("test", "Outer"))

        assert grammar.has_rule(inner_nt)
        assert grammar.has_rule(outer_nt)

        # Check Outer rule
        outer_rules = grammar.get_rules(outer_nt)
        assert len(outer_rules) == 1

        outer_rule = outer_rules[0]

        # The RHS should be: "(" "Outer" Inner ")"
        assert isinstance(outer_rule.rhs, Sequence)
        elements = outer_rule.rhs.elements
        assert len(elements) == 4
        assert isinstance(elements[0], LitTerminal) and elements[0].name == "("
        assert isinstance(elements[1], LitTerminal) and elements[1].name == "outer"
        assert isinstance(elements[2], Nonterminal) and elements[2].name == "inner"
        assert isinstance(elements[3], LitTerminal) and elements[3].name == ")"

    def test_message_with_enum(self):
        """Test grammar generation for a message with an enum field.

        Note: Enum fields are currently not fully supported and are skipped during
        grammar generation. This test verifies that messages with enum fields can
        still be processed without error, even though the enum field is omitted.
        """
        # Create proto AST:
        # message Status {
        #   enum State {
        #     UNKNOWN = 0;
        #     ACTIVE = 1;
        #     INACTIVE = 2;
        #   }
        #   State state = 1;
        # }
        msg = ProtoMessage(
            name="Status",
            module="test",
            enums=[
                ProtoEnum(
                    name="State",
                    values=[
                        ("UNKNOWN", 0),
                        ("ACTIVE", 1),
                        ("INACTIVE", 2),
                    ]
                )
            ],
            fields=[
                ProtoField(name="state", type="State", number=1),
            ]
        )

        parser = ProtoParser()
        parser.messages["Status"] = msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Check that status nonterminal exists
        status_nt = Nonterminal("status", MessageType("test", "Status"))
        assert grammar.has_rule(status_nt)

        # The rule should be: "(" "status" ")" with the enum field omitted
        rules = grammar.get_rules(status_nt)
        assert len(rules) == 1

        rule = rules[0]
        assert isinstance(rule.rhs, Sequence)
        elements = rule.rhs.elements
        assert len(elements) == 3
        assert isinstance(elements[0], LitTerminal) and elements[0].name == "("
        assert isinstance(elements[1], LitTerminal) and elements[1].name == "status"
        assert isinstance(elements[2], LitTerminal) and elements[2].name == ")"


class TestGrammarGenRewrites:
    """Tests for grammar rule rewrites."""

    def test_oneof_message(self):
        """Test grammar generation for a message with oneof field.

        Creates multiple grammar rules, one for each oneof alternative.
        Note: The grammar generator does NOT perform left-factoring.
        """
        # Create proto AST:
        # message Choice {
        #   oneof choice_type {
        #     int64 choice_a = 1;
        #     int64 choice_b = 2;
        #   }
        # }
        msg = ProtoMessage(
            name="Choice",
            module="test",
            oneofs=[
                ProtoOneof(
                    name="choice_type",
                    fields=[
                        ProtoField(name="choice_a", type="int64", number=1),
                        ProtoField(name="choice_b", type="int64", number=2),
                    ]
                )
            ]
        )

        parser = ProtoParser()
        parser.messages["Choice"] = msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        choice_nt = Nonterminal("choice", MessageType("test", "Choice"))
        assert grammar.has_rule(choice_nt)

        # Should have one rule per oneof alternative
        rules = grammar.get_rules(choice_nt)
        assert len(rules) == 2

        # Verify all rules are well-formed
        for rule in rules:
            assert rule.lhs == choice_nt
            assert rule.rhs is not None
            assert rule.constructor is not None

    def test_empty_message(self):
        """Test grammar generation for an empty message."""
        # Create proto AST: message Empty { }
        msg = ProtoMessage(
            name="Empty",
            module="test",
            fields=[]
        )

        parser = ProtoParser()
        parser.messages["Empty"] = msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Check that empty nonterminal exists
        empty_nt = Nonterminal("empty", MessageType("test", "Empty"))
        assert grammar.has_rule(empty_nt)

        rules = grammar.get_rules(empty_nt)
        assert len(rules) == 1

        rule = rules[0]

        # The RHS should be: "(" "empty" ")"
        assert isinstance(rule.rhs, Sequence)
        elements = rule.rhs.elements
        assert len(elements) == 3
        assert isinstance(elements[0], LitTerminal) and elements[0].name == "("
        assert isinstance(elements[1], LitTerminal) and elements[1].name == "empty"
        assert isinstance(elements[2], LitTerminal) and elements[2].name == ")"

        # Constructor should have no parameters
        assert len(rule.constructor.params) == 0


    def test_transaction_message(self):
        """Test grammar generation for Transaction message from transactions.proto.

        This tests the actual Transaction message structure:
        message Transaction {
          repeated Epoch epochs = 1;
          Configure configure = 2;
          optional Sync sync = 3;
        }

        This test validates grammar generation for:
        - repeated fields (epochs)
        - required nested messages (configure)
        - optional nested messages (sync)
        """
        # Create proto AST for supporting messages
        epoch_msg = ProtoMessage(name="Epoch", module="transactions", fields=[])
        configure_msg = ProtoMessage(name="Configure", module="transactions", fields=[])
        sync_msg = ProtoMessage(name="Sync", module="transactions", fields=[])

        # Create Transaction message
        transaction_msg = ProtoMessage(
            name="Transaction",
            module="transactions",
            fields=[
                ProtoField(name="epochs", type="Epoch", number=1, is_repeated=True),
                ProtoField(name="configure", type="Configure", number=2),
                ProtoField(name="sync", type="Sync", number=3, is_optional=True),
            ]
        )

        parser = ProtoParser()
        parser.messages["Epoch"] = epoch_msg
        parser.messages["Configure"] = configure_msg
        parser.messages["Sync"] = sync_msg
        parser.messages["Transaction"] = transaction_msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Check that transaction nonterminal exists
        transaction_nt = Nonterminal("transaction", MessageType("transactions", "Transaction"))
        assert grammar.has_rule(transaction_nt)

        rules = grammar.get_rules(transaction_nt)
        assert len(rules) == 1

        rule = rules[0]

        # The RHS should be: "(" "transaction" configure? sync? epoch* ")"
        # This matches the builtin rule from grammar_gen_builtins.py
        assert isinstance(rule.rhs, Sequence)
        elements = rule.rhs.elements
        assert len(elements) == 6
        assert isinstance(elements[0], LitTerminal) and elements[0].name == "("
        assert isinstance(elements[1], LitTerminal) and elements[1].name == "transaction"

        # configure is optional (builtin makes it optional with default constructor)
        assert isinstance(elements[2], Option)
        assert isinstance(elements[2].rhs, Nonterminal)
        assert elements[2].rhs.name == "configure"

        # sync is optional
        assert isinstance(elements[3], Option)
        assert isinstance(elements[3].rhs, Nonterminal)
        assert elements[3].rhs.name == "sync"

        # epochs is repeated (comes last in builtin rule)
        assert isinstance(elements[4], Star)
        assert isinstance(elements[4].rhs, Nonterminal)
        assert elements[4].rhs.name == "epoch"

        assert isinstance(elements[5], LitTerminal) and elements[5].name == ")"

        # Check constructor parameters (order: configure, sync, epochs)
        assert len(rule.constructor.params) == 3
        assert rule.constructor.params[0].name == "configure"
        assert isinstance(rule.constructor.params[0].type, OptionType)
        assert rule.constructor.params[1].name == "sync"
        assert isinstance(rule.constructor.params[1].type, OptionType)
        assert rule.constructor.params[2].name == "epochs"
        assert isinstance(rule.constructor.params[2].type, ListType)


    def test_upsert_message(self):
        """Test grammar generation for Upsert message from logic.proto.

        This tests the actual Upsert message structure:
        message Upsert {
          RelationId name = 1;
          Abstraction body = 2;
          repeated Attribute attrs = 3;
          int64 value_arity = 4;
        }

        Expected grammar:
        upsert
          : "(" "upsert" relation_id abstraction_with_arity attrs? ")"
        """
        # Create proto AST for supporting messages
        relation_id_msg = ProtoMessage(name="RelationId", module="logic", fields=[])
        abstraction_msg = ProtoMessage(name="Abstraction", module="logic", fields=[])
        attribute_msg = ProtoMessage(name="Attribute", module="logic", fields=[])

        # Create Upsert message
        upsert_msg = ProtoMessage(
            name="Upsert",
            module="logic",
            fields=[
                ProtoField(name="name", type="RelationId", number=1),
                ProtoField(name="body", type="Abstraction", number=2),
                ProtoField(name="attrs", type="Attribute", number=3, is_repeated=True),
                ProtoField(name="value_arity", type="int64", number=4),
            ]
        )

        parser = ProtoParser()
        parser.messages["RelationId"] = relation_id_msg
        parser.messages["Abstraction"] = abstraction_msg
        parser.messages["Attribute"] = attribute_msg
        parser.messages["Upsert"] = upsert_msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Check that upsert nonterminal exists
        upsert_nt = Nonterminal("upsert", MessageType("logic", "Upsert"))
        assert grammar.has_rule(upsert_nt)

        rules = grammar.get_rules(upsert_nt)
        assert len(rules) == 1

        rule = rules[0]

        # The RHS should be: "(" "upsert" relation_id abstraction_with_arity attrs? ")"
        # This matches the builtin rule from grammar_gen_builtins.py
        assert isinstance(rule.rhs, Sequence)
        elements = rule.rhs.elements
        assert len(elements) == 6
        assert isinstance(elements[0], LitTerminal) and elements[0].name == "("
        assert isinstance(elements[1], LitTerminal) and elements[1].name == "upsert"

        # name -> relation_id
        assert isinstance(elements[2], Nonterminal)
        assert elements[2].name == "relation_id"

        # body (Abstraction) and value_arity (int64) are combined into abstraction_with_arity
        assert isinstance(elements[3], Nonterminal)
        assert elements[3].name == "abstraction_with_arity"

        # attrs is optional (repeated field gets prefixed with message name)
        assert isinstance(elements[4], Option)
        assert isinstance(elements[4].rhs, Nonterminal)
        assert elements[4].rhs.name == "upsert_attrs"

        assert isinstance(elements[5], LitTerminal) and elements[5].name == ")"

    def test_abort_message(self):
        """Test grammar generation for Abort message from transactions.proto.

        This tests the actual Abort message structure:
        message Abort {
          string name = 1;
          RelationId relation_id = 2;
        }

        Expected grammar:
        abort
          : "(" "abort" name? relation_id ")"
        """
        # Create proto AST for supporting messages
        relation_id_msg = ProtoMessage(name="RelationId", module="logic", fields=[])

        # Create Abort message
        abort_msg = ProtoMessage(
            name="Abort",
            module="transactions",
            fields=[
                ProtoField(name="name", type="string", number=1),
                ProtoField(name="relation_id", type="RelationId", number=2),
            ]
        )

        parser = ProtoParser()
        parser.messages["RelationId"] = relation_id_msg
        parser.messages["Abort"] = abort_msg

        generator = GrammarGenerator(parser, verbose=False)
        grammar = generator.generate()

        # Check that abort nonterminal exists
        abort_nt = Nonterminal("abort", MessageType("transactions", "Abort"))
        assert grammar.has_rule(abort_nt)

        rules = grammar.get_rules(abort_nt)
        assert len(rules) == 1

        rule = rules[0]

        # The RHS should be: "(" "abort" name? relation_id ")"
        # This matches the builtin rule from grammar_gen_builtins.py
        assert isinstance(rule.rhs, Sequence)
        elements = rule.rhs.elements
        assert len(elements) == 5
        assert isinstance(elements[0], LitTerminal) and elements[0].name == "("
        assert isinstance(elements[1], LitTerminal) and elements[1].name == "abort"

        # name is optional (builtin makes string fields optional with default)
        assert isinstance(elements[2], Option)
        assert isinstance(elements[2].rhs, Nonterminal)
        assert elements[2].rhs.name == "name"

        # relation_id is required
        assert isinstance(elements[3], Nonterminal)
        assert elements[3].name == "relation_id"

        assert isinstance(elements[4], LitTerminal) and elements[4].name == ")"

        # Check constructor parameters (order: name, relation_id)
        assert len(rule.constructor.params) == 2
        assert rule.constructor.params[0].name == "name"
        assert isinstance(rule.constructor.params[0].type, OptionType)
        assert rule.constructor.params[1].name == "relation_id"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
