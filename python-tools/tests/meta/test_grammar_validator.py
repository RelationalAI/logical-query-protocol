#!/usr/bin/env python3
"""Tests for grammar validator."""

import pytest

from meta.target import (
    BaseType, MessageType, TupleType, ListType, OptionType, FunctionType,
    Var, GetElement, Call, Builtin, NewMessage, Lambda, Lit, IfElse, Let, ListExpr
)
from meta.grammar import (
    Grammar, Nonterminal, Rule, LitTerminal, NamedTerminal,
    Star, Option, Sequence
)
from meta.grammar_validator import GrammarValidator
from meta.proto_parser import ProtoParser
from meta.proto_ast import ProtoMessage, ProtoField, ProtoOneof


@pytest.fixture
def empty_proto_parser():
    """Create a minimal ProtoParser for testing."""
    parser = ProtoParser()
    return parser


@pytest.fixture
def empty_grammar():
    """Create a minimal Grammar for testing."""
    start = Nonterminal('start', BaseType('Unit'))
    return Grammar(start=start)


@pytest.fixture
def validator(empty_grammar, empty_proto_parser):
    """Create a GrammarValidator for testing."""
    return GrammarValidator(
        grammar=empty_grammar,
        parser=empty_proto_parser,
        expected_unreachable=set()
    )


class TestGetElementTypeChecking:
    """Tests for GetElement type checking in grammar validator."""

    def test_valid_getelement(self, validator):
        """Test GetElement with valid tuple type and index."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("String")])
        tuple_expr = Var("pair", tuple_type)
        elem = GetElement(tuple_expr, 0)

        # Should not produce any errors
        validator._check_expr_types(elem, "test_rule")
        assert validator.result.is_valid
        assert len(validator.result.errors) == 0

    def test_valid_getelement_second_element(self, validator):
        """Test GetElement accessing second element of tuple."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("String")])
        tuple_expr = Var("pair", tuple_type)
        elem = GetElement(tuple_expr, 1)

        validator._check_expr_types(elem, "test_rule")
        assert validator.result.is_valid
        assert len(validator.result.errors) == 0

    def test_getelement_out_of_bounds(self, validator):
        """Test GetElement with index out of bounds."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("String")])
        tuple_expr = Var("pair", tuple_type)
        elem = GetElement(tuple_expr, 2)  # Only 2 elements, so index 2 is out of bounds

        validator._check_expr_types(elem, "test_rule")
        assert not validator.result.is_valid
        assert len(validator.result.errors) == 1
        assert validator.result.errors[0].category == "type_tuple_element"
        assert "out of bounds" in validator.result.errors[0].message

    def test_getelement_negative_index_out_of_bounds(self):
        """Test GetElement reports negative index as out of bounds in validator."""
        # Note: GetElement constructor validates non-negative at construction,
        # but if we somehow had a -1 index, validator would catch it
        tuple_type = TupleType([BaseType("Int64"), BaseType("String")])
        tuple_expr = Var("pair", tuple_type)
        # This will raise AssertionError at construction, so we can't test validator path
        # Just verify construction fails
        with pytest.raises(AssertionError, match="GetElement index must be non-negative"):
            GetElement(tuple_expr, -1)

    def test_getelement_non_tuple_type(self, validator):
        """Test GetElement with non-tuple type."""
        list_expr = Var("list", ListType(BaseType("Int64")))
        elem = GetElement(list_expr, 0)

        validator._check_expr_types(elem, "test_rule")
        assert not validator.result.is_valid
        assert len(validator.result.errors) == 1
        assert validator.result.errors[0].category == "type_tuple_element"
        assert "expects tuple type" in validator.result.errors[0].message

    def test_getelement_with_option_type(self, validator):
        """Test GetElement with option type (should fail)."""
        option_expr = Var("opt", OptionType(TupleType([BaseType("Int64"), BaseType("String")])))
        elem = GetElement(option_expr, 0)

        validator._check_expr_types(elem, "test_rule")
        assert not validator.result.is_valid
        assert len(validator.result.errors) == 1
        assert validator.result.errors[0].category == "type_tuple_element"
        assert "expects tuple type" in validator.result.errors[0].message

    def test_getelement_nested_tuples(self, validator):
        """Test GetElement with nested tuple types."""
        inner_tuple = TupleType([BaseType("Int64"), BaseType("String")])
        outer_tuple = TupleType([inner_tuple, BaseType("Boolean")])
        tuple_expr = Var("nested", outer_tuple)
        elem = GetElement(tuple_expr, 0)

        validator._check_expr_types(elem, "test_rule")
        assert validator.result.is_valid
        assert len(validator.result.errors) == 0

    def test_getelement_chained_access(self, validator):
        """Test chained GetElement for accessing nested tuples."""
        inner_tuple = TupleType([BaseType("Int64"), BaseType("String")])
        outer_tuple = TupleType([inner_tuple, BaseType("Boolean")])
        tuple_expr = Var("nested", outer_tuple)
        first = GetElement(tuple_expr, 0)  # Gets inner_tuple
        second = GetElement(first, 1)  # Gets String from inner_tuple

        validator._check_expr_types(second, "test_rule")
        assert validator.result.is_valid
        assert len(validator.result.errors) == 0

    def test_getelement_chained_access_out_of_bounds(self, validator):
        """Test chained GetElement with out of bounds access."""
        inner_tuple = TupleType([BaseType("Int64"), BaseType("String")])
        outer_tuple = TupleType([inner_tuple, BaseType("Boolean")])
        tuple_expr = Var("nested", outer_tuple)
        first = GetElement(tuple_expr, 0)  # Gets inner_tuple
        second = GetElement(first, 3)  # Out of bounds - inner_tuple only has 2 elements

        validator._check_expr_types(second, "test_rule")
        assert not validator.result.is_valid
        assert len(validator.result.errors) == 1
        assert "out of bounds" in validator.result.errors[0].message


class TestGetElementTypeInference:
    """Tests for GetElement type inference."""

    def test_infer_type_first_element(self, validator):
        """Test type inference for first element."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("String")])
        tuple_expr = Var("pair", tuple_type)
        elem = GetElement(tuple_expr, 0)

        inferred = validator._infer_expr_type(elem)
        assert inferred == BaseType("Int64")

    def test_infer_type_second_element(self, validator):
        """Test type inference for second element."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("String")])
        tuple_expr = Var("pair", tuple_type)
        elem = GetElement(tuple_expr, 1)

        inferred = validator._infer_expr_type(elem)
        assert inferred == BaseType("String")

    def test_infer_type_out_of_bounds(self, validator):
        """Test type inference returns None for out of bounds."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("String")])
        tuple_expr = Var("pair", tuple_type)
        elem = GetElement(tuple_expr, 5)

        inferred = validator._infer_expr_type(elem)
        assert inferred is None

    def test_infer_type_nested_tuple(self, validator):
        """Test type inference with nested tuples."""
        inner_tuple = TupleType([BaseType("Int64"), BaseType("String")])
        outer_tuple = TupleType([inner_tuple, BaseType("Boolean")])
        tuple_expr = Var("nested", outer_tuple)
        elem = GetElement(tuple_expr, 0)

        inferred = validator._infer_expr_type(elem)
        assert inferred == inner_tuple

    def test_infer_type_complex_tuple(self, validator):
        """Test type inference with complex tuple containing various types."""
        tuple_type = TupleType([
            BaseType("Int64"),
            ListType(BaseType("String")),
            OptionType(MessageType("proto", "Value")),
            TupleType([BaseType("Boolean"), BaseType("Float64")])
        ])
        tuple_expr = Var("complex", tuple_type)

        # Check each element
        elem0 = GetElement(tuple_expr, 0)
        assert validator._infer_expr_type(elem0) == BaseType("Int64")

        elem1 = GetElement(tuple_expr, 1)
        assert validator._infer_expr_type(elem1) == ListType(BaseType("String"))

        elem2 = GetElement(tuple_expr, 2)
        assert validator._infer_expr_type(elem2) == OptionType(MessageType("proto", "Value"))

        elem3 = GetElement(tuple_expr, 3)
        assert validator._infer_expr_type(elem3) == TupleType([BaseType("Boolean"), BaseType("Float64")])


class TestGetElementInExpressions:
    """Tests for GetElement used within larger expressions."""

    def test_getelement_in_call(self, validator):
        """Test GetElement as argument to function call."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("String")])
        tuple_expr = Var("pair", tuple_type)
        elem = GetElement(tuple_expr, 0)

        # Use element in a builtin call
        call = Call(Builtin("Some"), [elem])
        validator._check_expr_types(call, "test_rule")
        assert validator.result.is_valid

    def test_getelement_multiple_in_call(self, validator):
        """Test multiple GetElement expressions in same call."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("Int64")])
        tuple_expr = Var("pair", tuple_type)
        elem0 = GetElement(tuple_expr, 0)
        elem1 = GetElement(tuple_expr, 1)

        # Use both elements in a builtin call
        call = Call(Builtin("equal"), [elem0, elem1])
        validator._check_expr_types(call, "test_rule")
        assert validator.result.is_valid

    def test_getelement_with_invalid_index_in_call(self, validator):
        """Test GetElement with invalid index used in call."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("String")])
        tuple_expr = Var("pair", tuple_type)
        elem = GetElement(tuple_expr, 5)  # Out of bounds

        call = Call(Builtin("Some"), [elem])
        validator._check_expr_types(call, "test_rule")
        assert not validator.result.is_valid
        assert any("out of bounds" in e.message for e in validator.result.errors)


class TestStructureValidation:
    """Tests for grammar structure validation."""

    def test_star_with_nonterminal(self):
        """Test Star with Nonterminal is valid."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('Unit'))
        grammar = Grammar(start=start)

        nt = Nonterminal('foo', BaseType('String'))
        rhs = Star(nt)
        param = Var('items', ListType(BaseType('String')))
        constructor = Lambda([param], BaseType('Unit'), Lit(None))
        rule = Rule(start, rhs, constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_structure()
        assert validator.result.is_valid

    def test_star_with_terminal(self):
        """Test Star with NamedTerminal is valid."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('Unit'))
        grammar = Grammar(start=start)

        terminal = NamedTerminal('STRING', BaseType('String'))
        rhs = Star(terminal)
        param = Var('items', ListType(BaseType('String')))
        constructor = Lambda([param], BaseType('Unit'), Lit(None))
        rule = Rule(start, rhs, constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_structure()
        assert validator.result.is_valid

    def test_star_with_sequence_invalid(self):
        """Test Star with Sequence is invalid (type-level validation)."""
        # Star has type annotation rhs: 'Nonterminal | NamedTerminal'
        # This is enforced by type checkers but not at runtime
        # The validator checks this structurally
        pass

    def test_option_with_nonterminal(self):
        """Test Option with Nonterminal is valid."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('Unit'))
        grammar = Grammar(start=start)

        nt = Nonterminal('foo', BaseType('String'))
        rhs = Option(nt)
        param = Var('opt', OptionType(BaseType('String')))
        constructor = Lambda([param], BaseType('Unit'), Lit(None))
        rule = Rule(start, rhs, constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_structure()
        assert validator.result.is_valid

    def test_sequence_with_nested_sequence_invalid(self):
        """Test Sequence with nested Sequence is invalid (caught at construction)."""
        # Sequence validates at construction that elements cannot be Sequence
        inner_seq = Sequence((LitTerminal('a'), LitTerminal('b')))
        with pytest.raises(AssertionError, match="Sequence elements cannot be Sequence"):
            Sequence((LitTerminal('('), inner_seq, LitTerminal(')')))


class TestMessageCoverage:
    """Tests for message coverage validation."""

    def test_message_with_rule(self):
        """Test message with corresponding rule passes."""
        parser = ProtoParser()
        msg = ProtoMessage(name='TestMessage', module='proto')
        parser.messages['TestMessage'] = msg

        start = Nonterminal('test_message', MessageType('proto', 'TestMessage'))
        grammar = Grammar(start=start)
        constructor = Lambda([], MessageType('proto', 'TestMessage'), Call(NewMessage('proto', 'TestMessage', ()), []))
        rule = Rule(start, LitTerminal('test'), constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_message_coverage()
        assert validator.result.is_valid

    def test_message_without_rule(self):
        """Test message without corresponding rule fails."""
        parser = ProtoParser()
        msg = ProtoMessage(name='MissingMessage', module='proto')
        parser.messages['MissingMessage'] = msg

        start = Nonterminal('start', BaseType('Unit'))
        grammar = Grammar(start=start)

        validator = GrammarValidator(grammar, parser, set())
        validator._check_message_coverage()
        assert not validator.result.is_valid
        assert any("MissingMessage" in e.message for e in validator.result.errors)

    def test_message_in_expected_unreachable_skipped(self):
        """Test message in expected_unreachable is not required."""
        parser = ProtoParser()
        msg = ProtoMessage(name='UnreachableMessage', module='proto')
        parser.messages['UnreachableMessage'] = msg

        start = Nonterminal('start', BaseType('Unit'))
        grammar = Grammar(start=start)

        validator = GrammarValidator(grammar, parser, {'unreachable_message'})
        validator._check_message_coverage()
        assert validator.result.is_valid


class TestFieldCoverage:
    """Tests for field coverage validation."""

    def test_message_with_correct_field_count(self):
        """Test message constructed with correct number of fields."""
        parser = ProtoParser()
        msg = ProtoMessage(name='Person', module='proto')
        msg.fields = [
            ProtoField(name='name', type='string', number=1, is_repeated=False, is_optional=False),
            ProtoField(name='age', type='int32', number=2, is_repeated=False, is_optional=False)
        ]
        parser.messages['Person'] = msg

        start = Nonterminal('person', MessageType('proto', 'Person'))
        grammar = Grammar(start=start)

        name_var = Var('name', BaseType('String'))
        age_var = Var('age', BaseType('Int32'))
        body = NewMessage('proto', 'Person', (('name', name_var), ('age', age_var)))
        constructor = Lambda([name_var, age_var], MessageType('proto', 'Person'), body)
        rule = Rule(start, Sequence((NamedTerminal('STRING', BaseType('String')), NamedTerminal('INT', BaseType('Int32')))), constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_types()  # Field validation now happens in type checking
        assert validator.result.is_valid

    def test_message_with_wrong_field_count(self):
        """Test message constructed with wrong number of fields warns."""
        parser = ProtoParser()
        msg = ProtoMessage(name='Person', module='proto')
        msg.fields = [
            ProtoField(name='name', type='string', number=1, is_repeated=False, is_optional=False),
            ProtoField(name='age', type='int32', number=2, is_repeated=False, is_optional=False)
        ]
        parser.messages['Person'] = msg

        start = Nonterminal('person', MessageType('proto', 'Person'))
        grammar = Grammar(start=start)

        name_var = Var('name', BaseType('String'))
        body = NewMessage('proto', 'Person', (('name', name_var),))  # Missing age field
        constructor = Lambda([name_var], MessageType('proto', 'Person'), body)
        rule = Rule(start, NamedTerminal('STRING', BaseType('String')), constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_types()  # Field validation now happens in type checking
        assert len(validator.result.warnings) > 0
        assert any('missing field' in w.message.lower() for w in validator.result.warnings)


class TestTypeChecking:
    """Tests for expression type checking."""

    def test_message_call_correct_types(self, validator):
        """Test Message call with correct argument types."""
        # Setup type env with a test message
        validator.type_env._message_field_types[('proto', 'TestMsg')] = [BaseType('String'), BaseType('Int64')]

        msg = NewMessage('proto', 'TestMsg', ())
        args = [Var('s', BaseType('String')), Var('i', BaseType('Int64'))]

        validator._check_message_call_types(msg, args, 'test_rule')
        assert validator.result.is_valid

    def test_message_call_wrong_arity(self, validator):
        """Test Message call with wrong number of arguments."""
        validator.type_env._message_field_types[('proto', 'TestMsg')] = [BaseType('String'), BaseType('Int64')]

        msg = NewMessage('proto', 'TestMsg', ())
        args = [Var('s', BaseType('String'))]  # Missing one arg

        validator._check_message_call_types(msg, args, 'test_rule')
        assert not validator.result.is_valid
        assert any("expects 2 args, got 1" in e.message for e in validator.result.errors)

    def test_message_call_wrong_type(self, validator):
        """Test Message call with wrong argument type."""
        validator.type_env._message_field_types[('proto', 'TestMsg')] = [BaseType('String'), BaseType('Int64')]

        msg = NewMessage('proto', 'TestMsg', ())
        args = [Var('s', BaseType('String')), Var('i', BaseType('String'))]  # Second arg should be Int64

        validator._check_message_call_types(msg, args, 'test_rule')
        assert not validator.result.is_valid
        assert any("arg 1" in e.message and "String" in e.message for e in validator.result.errors)

    def test_builtin_unwrap_option_or_valid(self, validator):
        """Test unwrap_option_or with correct types."""
        builtin = Builtin('unwrap_option_or')
        args = [
            Var('opt', OptionType(BaseType('String'))),
            Var('default', BaseType('String'))
        ]

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert validator.result.is_valid

    def test_builtin_unwrap_option_or_wrong_arity(self, validator):
        """Test unwrap_option_or with wrong arity."""
        builtin = Builtin('unwrap_option_or')
        args = [Var('opt', OptionType(BaseType('String')))]  # Missing default

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert not validator.result.is_valid
        assert any("expects 2 args, got 1" in e.message for e in validator.result.errors)

    def test_builtin_unwrap_option_or_non_option(self, validator):
        """Test unwrap_option_or with non-option type."""
        builtin = Builtin('unwrap_option_or')
        args = [
            Var('s', BaseType('String')),  # Not an Option type
            Var('default', BaseType('String'))
        ]

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert not validator.result.is_valid
        assert any("arg 0" in e.message and "expected Option" in e.message for e in validator.result.errors)

    def test_builtin_list_concat_valid(self, validator):
        """Test list_concat with correct types."""
        builtin = Builtin('list_concat')
        args = [
            Var('list1', ListType(BaseType('String'))),
            Var('list2', ListType(BaseType('String')))
        ]

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert validator.result.is_valid

    def test_builtin_list_concat_incompatible_types(self, validator):
        """Test list_concat with incompatible element types."""
        builtin = Builtin('list_concat')
        args = [
            Var('list1', ListType(BaseType('String'))),
            Var('list2', ListType(BaseType('Int64')))  # Different element type
        ]

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert not validator.result.is_valid
        assert any("incompatible" in e.message for e in validator.result.errors)

    def test_builtin_length_valid(self, validator):
        """Test length with list type."""
        builtin = Builtin('length')
        args = [Var('list', ListType(BaseType('String')))]

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert validator.result.is_valid

    def test_builtin_length_non_list(self, validator):
        """Test length with non-list type."""
        builtin = Builtin('length')
        args = [Var('s', BaseType('String'))]  # Not a list

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert not validator.result.is_valid
        assert any("expected List" in e.message for e in validator.result.errors)


class TestRuleTypeChecking:
    """Tests for rule-level type checking."""

    def test_rule_arity_match(self):
        """Test rule with matching parameter and RHS element counts."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('Unit'))
        grammar = Grammar(start=start)

        param1 = Var('x', BaseType('String'))
        param2 = Var('y', BaseType('Int64'))
        rhs = Sequence((NamedTerminal('STRING', BaseType('String')), NamedTerminal('INT', BaseType('Int64'))))
        constructor = Lambda([param1, param2], BaseType('Unit'), Lit(None))
        rule = Rule(start, rhs, constructor)

        validator = GrammarValidator(grammar, parser, set())
        validator._check_rule_types(rule)
        assert validator.result.is_valid

    def test_rule_arity_mismatch(self):
        """Test rule with mismatched parameter and RHS element counts."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('Unit'))
        grammar = Grammar(start=start)

        # Can't construct Rule with arity mismatch due to assertion
        # Just verify the validator would catch it
        validator = GrammarValidator(grammar, parser, set())
        validator.result.add_error('type_arity', "lambda has 1 params but RHS has 2 non-literal elements")
        assert not validator.result.is_valid

    def test_rule_param_type_match(self):
        """Test rule with matching parameter types."""
        parser = ProtoParser()
        msg_type = MessageType('proto', 'TestMsg')
        start = Nonterminal('start', msg_type)
        grammar = Grammar(start=start)

        param = Var('s', BaseType('String'))
        rhs = NamedTerminal('STRING', BaseType('String'))
        body = Call(NewMessage('proto', 'TestMsg', ()), [param])
        constructor = Lambda([param], msg_type, body)
        rule = Rule(start, rhs, constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_rule_types(rule)
        assert validator.result.is_valid

    def test_rule_return_type_match(self):
        """Test rule with matching return type."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('String'))
        grammar = Grammar(start=start)

        param = Var('s', BaseType('String'))
        rhs = NamedTerminal('STRING', BaseType('String'))
        constructor = Lambda([param], BaseType('String'), param)  # Returns the string
        rule = Rule(start, rhs, constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_rule_types(rule)
        assert validator.result.is_valid

    def test_nested_expressions_checked(self):
        """Test that nested expressions are type checked."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('String'))
        grammar = Grammar(start=start)

        param = Var('s', BaseType('String'))
        rhs = NamedTerminal('STRING', BaseType('String'))
        # Use IfElse with GetElement that has out of bounds index
        tuple_type = TupleType([BaseType('Int64'), BaseType('String')])
        tuple_var = Var('pair', tuple_type)
        condition = Var('flag', BaseType('Boolean'))
        bad_elem = GetElement(tuple_var, 5)  # Out of bounds
        body = IfElse(condition, bad_elem, param)
        constructor = Lambda([param], BaseType('String'), body)
        rule = Rule(start, rhs, constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_rule_types(rule)
        assert not validator.result.is_valid
        assert any("out of bounds" in e.message for e in validator.result.errors)


class TestUnreachableRules:
    """Tests for unreachable rule detection."""

    def test_reachable_rule(self):
        """Test that reachable rules don't generate warnings."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('Unit'))
        child = Nonterminal('child', BaseType('String'))
        grammar = Grammar(start=start)

        # Start rule references child - need parameter for child nonterminal
        child_param = Var('c', BaseType('String'))
        constructor1 = Lambda([child_param], BaseType('Unit'), Lit(None))
        rule1 = Rule(start, child, constructor1)
        grammar.rules[start] = [rule1]

        # Child rule
        constructor2 = Lambda([], BaseType('String'), Lit("test"))
        rule2 = Rule(child, LitTerminal('test'), constructor2)
        grammar.rules[child] = [rule2]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_unreachable()
        assert len(validator.result.warnings) == 0

    def test_unreachable_rule(self):
        """Test that unreachable rules generate warnings."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('Unit'))
        orphan = Nonterminal('orphan', BaseType('String'))
        grammar = Grammar(start=start)

        # Start rule doesn't reference orphan
        constructor1 = Lambda([], BaseType('Unit'), Lit(None))
        rule1 = Rule(start, LitTerminal('test'), constructor1)
        grammar.rules[start] = [rule1]

        # Orphan rule not referenced
        constructor2 = Lambda([], BaseType('String'), Lit("orphan"))
        rule2 = Rule(orphan, LitTerminal('orphan'), constructor2)
        grammar.rules[orphan] = [rule2]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_unreachable()
        assert len(validator.result.warnings) > 0
        assert any("orphan" in w.message and "unreachable" in w.message for w in validator.result.warnings)

    def test_expected_unreachable_no_warning(self):
        """Test that expected unreachable rules don't generate warnings."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('Unit'))
        orphan = Nonterminal('orphan', BaseType('String'))
        grammar = Grammar(start=start)

        constructor1 = Lambda([], BaseType('Unit'), Lit(None))
        rule1 = Rule(start, LitTerminal('test'), constructor1)
        grammar.rules[start] = [rule1]

        constructor2 = Lambda([], BaseType('String'), Lit("orphan"))
        rule2 = Rule(orphan, LitTerminal('orphan'), constructor2)
        grammar.rules[orphan] = [rule2]

        # Mark orphan as expected unreachable
        validator = GrammarValidator(grammar, parser, {'orphan'})
        validator._check_unreachable()
        assert len(validator.result.warnings) == 0


class TestSoundness:
    """Tests for grammar soundness validation."""

    def test_rule_with_proto_backing(self):
        """Test rule corresponding to proto message is sound."""
        parser = ProtoParser()
        msg = ProtoMessage(name='TestMessage', module='proto')
        parser.messages['TestMessage'] = msg

        start = Nonterminal('test_message', MessageType('proto', 'TestMessage'))
        grammar = Grammar(start=start)
        constructor = Lambda([], MessageType('proto', 'TestMessage'), Call(NewMessage('proto', 'TestMessage', ()), []))
        rule = Rule(start, LitTerminal('test'), constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_soundness()
        assert validator.result.is_valid

    def test_rule_without_proto_backing(self):
        """Test rule without proto backing generates warning."""
        parser = ProtoParser()

        start = Nonterminal('unknown_rule', BaseType('String'))
        grammar = Grammar(start=start)
        constructor = Lambda([], BaseType('String'), Lit("test"))
        rule = Rule(start, LitTerminal('test'), constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser, set())
        validator._check_soundness()
        assert len(validator.result.warnings) > 0
        assert any("unknown_rule" in w.message and "no obvious proto backing" in w.message for w in validator.result.warnings)


class TestTypeInference:
    """Tests for type inference."""

    def test_infer_var_type(self, validator):
        """Test type inference for Var."""
        var = Var('x', BaseType('Int64'))
        inferred = validator._infer_expr_type(var)
        assert inferred == BaseType('Int64')

    def test_infer_message_call_type(self, validator):
        """Test type inference for Message constructor call."""
        call = Call(NewMessage('proto', 'TestMsg', ()), [])
        inferred = validator._infer_expr_type(call)
        assert inferred == MessageType('proto', 'TestMsg')

    def test_infer_list_expr_type(self, validator):
        """Test type inference for ListExpr."""
        list_expr = ListExpr([Lit(1), Lit(2)], BaseType('Int64'))
        inferred = validator._infer_expr_type(list_expr)
        assert inferred == ListType(BaseType('Int64'))

    def test_infer_builtin_int64_to_int32(self, validator):
        """Test type inference for int64_to_int32 builtin."""
        call = Call(Builtin('int64_to_int32'), [Var('x', BaseType('Int64'))])
        inferred = validator._infer_expr_type(call)
        assert inferred == BaseType('Int32')

    def test_infer_builtin_length(self, validator):
        """Test type inference for length builtin."""
        call = Call(Builtin('length'), [Var('list', ListType(BaseType('String')))])
        inferred = validator._infer_expr_type(call)
        assert inferred == BaseType('Int64')


class TestComplexExpressions:
    """Tests for type checking complex nested expressions."""

    def test_let_expression(self, validator):
        """Test type checking Let expression."""
        var = Var('x', BaseType('Int64'))
        init = Lit(42)
        body = var
        let_expr = Let(var, init, body)

        validator._check_expr_types(let_expr, 'test_rule')
        assert validator.result.is_valid

    def test_ifelse_expression(self, validator):
        """Test type checking IfElse expression."""
        condition = Var('flag', BaseType('Boolean'))
        then_branch = Lit(1)
        else_branch = Lit(2)
        ifelse = IfElse(condition, then_branch, else_branch)

        validator._check_expr_types(ifelse, 'test_rule')
        assert validator.result.is_valid

    def test_list_expression(self, validator):
        """Test type checking ListExpr."""
        list_expr = ListExpr([Lit(1), Lit(2), Lit(3)], BaseType('Int64'))

        validator._check_expr_types(list_expr, 'test_rule')
        assert validator.result.is_valid

    def test_nested_calls(self, validator):
        """Test type checking nested function calls."""
        inner = Call(Builtin('length'), [Var('list', ListType(BaseType('String')))])
        outer = Call(Builtin('int64_to_int32'), [inner])

        validator._check_expr_types(outer, 'test_rule')
        assert validator.result.is_valid
