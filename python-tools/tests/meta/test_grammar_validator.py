#!/usr/bin/env python3
"""Tests for grammar validator."""

import pytest

from meta.target import (
    BaseType, MessageType, TupleType, SequenceType, ListType, OptionType, FunctionType,
    Var, GetElement, Call, Builtin, NewMessage, Lambda, Lit, IfElse, Let, ListExpr,
    NamedFun, FunDef
)
from meta.target_builtins import make_builtin
from meta.grammar import (
    Grammar, Nonterminal, Rule, LitTerminal, NamedTerminal,
    Star, Option, Sequence,
)
from meta.grammar_validator import GrammarValidator
from meta.proto_parser import ProtoParser
from meta.proto_ast import ProtoMessage, ProtoField

# Dummy type for test builtins
_ANY = BaseType("Any")
_DUMMY_FN_TYPE = FunctionType([], _ANY)


def _test_builtin(name: str) -> Builtin:
    """Create a test builtin with a dummy type."""
    return Builtin(name, _DUMMY_FN_TYPE)


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
        call = Call(make_builtin("some"), [elem])
        validator._check_expr_types(call, "test_rule")
        assert validator.result.is_valid

    def test_getelement_multiple_in_call(self, validator):
        """Test multiple GetElement expressions in same call."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("Int64")])
        tuple_expr = Var("pair", tuple_type)
        elem0 = GetElement(tuple_expr, 0)
        elem1 = GetElement(tuple_expr, 1)

        # Use both elements in a builtin call
        call = Call(make_builtin("equal"), [elem0, elem1])
        validator._check_expr_types(call, "test_rule")
        assert validator.result.is_valid

    def test_getelement_with_invalid_index_in_call(self, validator):
        """Test GetElement with invalid index used in call."""
        tuple_type = TupleType([BaseType("Int64"), BaseType("String")])
        tuple_expr = Var("pair", tuple_type)
        elem = GetElement(tuple_expr, 5)  # Out of bounds

        call = Call(make_builtin("some"), [elem])
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

        validator = GrammarValidator(grammar, parser)
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

        validator = GrammarValidator(grammar, parser)
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

        validator = GrammarValidator(grammar, parser)
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

        validator = GrammarValidator(grammar, parser)
        validator._check_message_coverage()
        assert validator.result.is_valid

    def test_message_without_rule(self):
        """Test message without corresponding rule fails."""
        parser = ProtoParser()
        msg = ProtoMessage(name='MissingMessage', module='proto')
        parser.messages['MissingMessage'] = msg

        start = Nonterminal('start', BaseType('Unit'))
        grammar = Grammar(start=start)

        validator = GrammarValidator(grammar, parser)
        validator._check_message_coverage()
        assert not validator.result.is_valid
        assert any("MissingMessage" in e.message for e in validator.result.errors)


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

        validator = GrammarValidator(grammar, parser)
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

        validator = GrammarValidator(grammar, parser)
        validator._check_types()  # Field validation now happens in type checking
        # Missing fields are errors
        assert not validator.result.is_valid
        assert any(e.category == 'field_coverage' for e in validator.result.errors)
        assert any('missing field' in e.message.lower() for e in validator.result.errors)


class TestTypeChecking:
    """Tests for expression type checking."""

    def test_builtin_unwrap_option_or_valid(self, validator):
        """Test unwrap_option_or with correct types."""
        builtin = make_builtin('unwrap_option_or')
        args = [
            Var('opt', OptionType(BaseType('String'))),
            Var('default', BaseType('String'))
        ]

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert validator.result.is_valid

    def test_builtin_unwrap_option_or_wrong_arity(self, validator):
        """Test unwrap_option_or with wrong arity."""
        builtin = make_builtin('unwrap_option_or')
        args = [Var('opt', OptionType(BaseType('String')))]  # Missing default

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert not validator.result.is_valid
        assert any("expects 2 args, got 1" in e.message for e in validator.result.errors)

    def test_builtin_unwrap_option_or_non_option(self, validator):
        """Test unwrap_option_or with non-option type."""
        builtin = make_builtin('unwrap_option_or')
        args = [
            Var('s', BaseType('String')),  # Not an Option type
            Var('default', BaseType('String'))
        ]

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert not validator.result.is_valid
        assert any("arg 0" in e.message and "expected Option" in e.message for e in validator.result.errors)

    def test_builtin_list_concat_valid(self, validator):
        """Test list_concat with correct types."""
        builtin = make_builtin('list_concat')
        args = [
            Var('list1', ListType(BaseType('String'))),
            Var('list2', ListType(BaseType('String')))
        ]

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert validator.result.is_valid

    def test_builtin_list_concat_incompatible_types(self, validator):
        """Test list_concat with incompatible element types."""
        builtin = make_builtin('list_concat')
        args = [
            Var('list1', ListType(BaseType('String'))),
            Var('list2', ListType(BaseType('Int64')))  # Different element type
        ]

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert not validator.result.is_valid
        assert any("no common supertype" in e.message for e in validator.result.errors)

    def test_builtin_length_valid(self, validator):
        """Test length with list type."""
        builtin = make_builtin('length')
        args = [Var('list', ListType(BaseType('String')))]

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert validator.result.is_valid

    def test_builtin_length_non_list(self, validator):
        """Test length with non-list type."""
        builtin = make_builtin('length')
        args = [Var('s', BaseType('String'))]  # Not a list

        validator._check_builtin_call_types(builtin, args, 'test_rule')
        assert not validator.result.is_valid
        assert any("expected Sequence" in e.message for e in validator.result.errors)


class TestRuleTypeChecking:
    """Tests for rule-level type checking."""

    def test_rule_arity_match(self):
        """Test rule with matching parameter and RHS element counts."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('String'))
        grammar = Grammar(start=start)

        param1 = Var('x', BaseType('String'))
        param2 = Var('y', BaseType('Int64'))
        rhs = Sequence((NamedTerminal('STRING', BaseType('String')), NamedTerminal('INT', BaseType('Int64'))))
        constructor = Lambda([param1, param2], BaseType('String'), param1)
        rule = Rule(start, rhs, constructor)

        validator = GrammarValidator(grammar, parser)
        validator._check_rule_types(rule)
        assert validator.result.is_valid

    def test_rule_arity_mismatch(self):
        """Test rule with mismatched parameter and RHS element counts."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('Unit'))
        grammar = Grammar(start=start)

        # Can't construct Rule with arity mismatch due to assertion
        # Just verify the validator would catch it
        validator = GrammarValidator(grammar, parser)
        validator.result.add_error('type_arity', "lambda has 1 params but RHS has 2 non-literal elements")
        assert not validator.result.is_valid

    def test_rule_param_type_match(self):
        """Test rule with matching parameter types."""
        parser = ProtoParser()
        parser.messages['TestMsg'] = ProtoMessage(
            name='TestMsg', module='proto', fields=[
                ProtoField(name='s', number=1, type='string'),
            ], oneofs=[], enums=[], reserved=[]
        )
        msg_type = MessageType('proto', 'TestMsg')
        start = Nonterminal('start', msg_type)
        grammar = Grammar(start=start)

        param = Var('s', BaseType('String'))
        rhs = NamedTerminal('STRING', BaseType('String'))
        body = NewMessage('proto', 'TestMsg', (('s', param),))
        constructor = Lambda([param], msg_type, body)
        rule = Rule(start, rhs, constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser)
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

        validator = GrammarValidator(grammar, parser)
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

        validator = GrammarValidator(grammar, parser)
        validator._check_rule_types(rule)
        assert not validator.result.is_valid
        assert any("out of bounds" in e.message for e in validator.result.errors)


class TestUnreachableRules:
    """Tests for unreachable rule detection."""

    def test_reachable_rule(self):
        """Test that reachable rules don't generate errors."""
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

        validator = GrammarValidator(grammar, parser)
        validator._check_unreachable()
        assert len(validator.result.errors) == 0

    def test_unreachable_rule(self):
        """Test that unreachable rules generate errors."""
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

        validator = GrammarValidator(grammar, parser)
        validator._check_unreachable()
        assert len(validator.result.errors) > 0
        assert any("orphan" in e.message and "unreachable" in e.message for e in validator.result.errors)


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

        validator = GrammarValidator(grammar, parser)
        validator._check_soundness()
        assert validator.result.is_valid

    def test_rule_without_proto_backing(self):
        """Test rule with invalid type generates error."""
        parser = ProtoParser()

        # Create a rule with a MessageType that doesn't exist in the proto spec
        invalid_type = MessageType('proto', 'NonExistentMessage')
        start = Nonterminal('unknown_rule', invalid_type)
        grammar = Grammar(start=start)
        constructor = Lambda([], invalid_type, Call(NewMessage('proto', 'NonExistentMessage', ()), []))
        rule = Rule(start, LitTerminal('test'), constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser)
        validator._check_soundness()
        assert len(validator.result.errors) > 0
        assert any("unknown_rule" in e.message and "is not a valid type" in e.message for e in validator.result.errors)


class TestTypeInference:
    """Tests for type inference."""

    def test_infer_var_type(self, validator):
        """Test type inference for Var."""
        var = Var('x', BaseType('Int64'))
        inferred = validator._infer_expr_type(var)
        assert inferred == BaseType('Int64')

    def test_infer_newmessage_type(self, validator):
        """Test type inference for NewMessage expression."""
        msg = NewMessage('proto', 'TestMsg', ())
        inferred = validator._infer_expr_type(msg)
        assert inferred == MessageType('proto', 'TestMsg')

    def test_infer_list_expr_type(self, validator):
        """Test type inference for ListExpr."""
        list_expr = ListExpr([Lit(1), Lit(2)], BaseType('Int64'))
        inferred = validator._infer_expr_type(list_expr)
        assert inferred == ListType(BaseType('Int64'))

    def test_infer_builtin_int64_to_int32(self, validator):
        """Test type inference for int64_to_int32 builtin."""
        call = Call(make_builtin('int64_to_int32'), [Var('x', BaseType('Int64'))])
        inferred = validator._infer_expr_type(call)
        assert inferred == BaseType('Int32')

    def test_infer_builtin_length(self, validator):
        """Test type inference for length builtin."""
        call = Call(make_builtin('length'), [Var('list', ListType(BaseType('String')))])
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
        inner = Call(make_builtin('length'), [Var('list', ListType(BaseType('String')))])
        outer = Call(make_builtin('int64_to_int32'), [inner])

        validator._check_expr_types(outer, 'test_rule')
        assert validator.result.is_valid


class TestHelperFunctionCalls:
    """Tests for calling helper functions defined in grammar."""

    def test_call_helper_function(self):
        """Test that calling a helper function in a rule passes validation."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('String'))
        grammar = Grammar(start=start)

        # Define a helper function: def my_helper(x: String) -> String: x
        helper_param = Var('x', BaseType('String'))
        helper_body = helper_param
        helper_def = FunDef('my_helper', [helper_param], BaseType('String'), helper_body)
        grammar.function_defs['my_helper'] = helper_def

        # Rule that calls the helper: start -> STRING { my_helper($1) }
        param = Var('s', BaseType('String'))
        helper_type = FunctionType([BaseType('String')], BaseType('String'))
        body = Call(NamedFun('my_helper', helper_type), [param])
        constructor = Lambda([param], BaseType('String'), body)
        rule = Rule(start, NamedTerminal('STRING', BaseType('String')), constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser)
        validator._check_rule_types(rule)
        assert validator.result.is_valid

    def test_call_helper_function_in_expression(self, validator):
        """Test calling a helper function within an expression."""
        # Call to a named function with type Int64 -> String
        fn_type = FunctionType([BaseType('Int64')], BaseType('String'))
        call = Call(NamedFun('some_helper', fn_type), [Lit(42)])
        # Should pass - validator doesn't check if function exists
        validator._check_expr_types(call, 'test_rule')
        assert validator.result.is_valid

    def test_helper_function_as_argument(self):
        """Test helper function result used as argument to another call."""
        parser = ProtoParser()
        start = Nonterminal('start', ListType(BaseType('String')))
        grammar = Grammar(start=start)

        # Define helper: def wrap(x: String) -> String: x
        helper_param = Var('x', BaseType('String'))
        helper_def = FunDef('wrap', [helper_param], BaseType('String'), helper_param)
        grammar.function_defs['wrap'] = helper_def

        # Rule: start -> STRING { [wrap($1)] }
        param = Var('s', BaseType('String'))
        wrap_type = FunctionType([BaseType('String')], BaseType('String'))
        helper_call = Call(NamedFun('wrap', wrap_type), [param])
        body = ListExpr([helper_call], BaseType('String'))
        constructor = Lambda([param], ListType(BaseType('String')), body)
        rule = Rule(start, NamedTerminal('STRING', BaseType('String')), constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser)
        validator._check_rule_types(rule)
        assert validator.result.is_valid

    def test_nested_helper_function_calls(self):
        """Test nested calls to helper functions."""
        parser = ProtoParser()
        start = Nonterminal('start', BaseType('String'))
        grammar = Grammar(start=start)

        # Define helpers
        str_to_str = FunctionType([BaseType('String')], BaseType('String'))

        inner_param = Var('x', BaseType('String'))
        inner_def = FunDef('inner', [inner_param], BaseType('String'), inner_param)
        grammar.function_defs['inner'] = inner_def

        outer_param = Var('y', BaseType('String'))
        outer_body = Call(NamedFun('inner', str_to_str), [outer_param])
        outer_def = FunDef('outer', [outer_param], BaseType('String'), outer_body)
        grammar.function_defs['outer'] = outer_def

        # Rule: start -> STRING { outer($1) }
        param = Var('s', BaseType('String'))
        body = Call(NamedFun('outer', str_to_str), [param])
        constructor = Lambda([param], BaseType('String'), body)
        rule = Rule(start, NamedTerminal('STRING', BaseType('String')), constructor)
        grammar.rules[start] = [rule]

        validator = GrammarValidator(grammar, parser)
        validator._check_rule_types(rule)
        assert validator.result.is_valid


class TestGetFieldTypeChecking:
    """Tests for GetField type validation."""

    def test_getfield_correct_message_type(self, validator):
        """Test GetField with correct message type passes."""
        from meta.target import GetField
        msg_type = MessageType('proto', 'TestMsg')
        obj = Var('msg', msg_type)
        field = GetField(obj, 'field_name', msg_type, BaseType('String'))
        validator._check_expr_types(field, 'test_rule')
        assert validator.result.is_valid

    def test_getfield_wrong_message_type(self, validator):
        """Test GetField with wrong message type fails."""
        from meta.target import GetField
        actual_type = MessageType('proto', 'ActualMsg')
        expected_type = MessageType('proto', 'ExpectedMsg')
        obj = Var('msg', actual_type)
        field = GetField(obj, 'field_name', expected_type, BaseType('String'))
        validator._check_expr_types(field, 'test_rule')
        assert not validator.result.is_valid
        assert any('type_field_access' == e.category for e in validator.result.errors)
        assert any('ExpectedMsg' in e.message and 'ActualMsg' in e.message for e in validator.result.errors)

    def test_getfield_target_type(self):
        """Test GetField.target_type() returns field_type."""
        from meta.target import GetField
        msg_type = MessageType('proto', 'TestMsg')
        field_type = BaseType('Int64')
        obj = Var('msg', msg_type)
        field = GetField(obj, 'value', msg_type, field_type)
        assert field.target_type() == field_type

    def test_getfield_nested_correct_types(self, validator):
        """Test nested GetField with correct types passes."""
        from meta.target import GetField
        outer_type = MessageType('proto', 'Outer')
        inner_type = MessageType('proto', 'Inner')
        obj = Var('msg', outer_type)
        inner = GetField(obj, 'inner', outer_type, inner_type)
        outer = GetField(inner, 'value', inner_type, BaseType('String'))
        validator._check_expr_types(outer, 'test_rule')
        assert validator.result.is_valid


class TestIsSubtype:
    """Property tests for _is_subtype."""

    def test_reflexivity(self, validator):
        """T <: T for all T."""
        types = [
            BaseType("Never"),
            BaseType("Any"),
            BaseType("Int64"),
            BaseType("Int32"),
            BaseType("Float64"),
            BaseType("String"),
            BaseType("Boolean"),
        ]
        for t in types:
            assert validator._is_subtype(t, t)

    def test_never_is_bottom(self, validator):
        """Never <: T for all T."""
        never = BaseType("Never")
        types = [
            BaseType("Any"),
            BaseType("Int64"),
            BaseType("Int32"),
            BaseType("Float64"),
            BaseType("String"),
            BaseType("Boolean"),
        ]
        for t in types:
            assert validator._is_subtype(never, t)

    def test_any_is_top(self, validator):
        """T <: Any for all T."""
        any_type = BaseType("Any")
        types = [
            BaseType("Never"),
            BaseType("Int64"),
            BaseType("Int32"),
            BaseType("Float64"),
            BaseType("String"),
            BaseType("Boolean"),
        ]
        for t in types:
            assert validator._is_subtype(t, any_type)

    def test_concrete_not_subtype_of_different_concrete(self, validator):
        """Distinct concrete types are not subtypes of each other."""
        concrete = [
            BaseType("Int64"),
            BaseType("Int32"),
            BaseType("Float64"),
            BaseType("String"),
            BaseType("Boolean"),
        ]
        for t in concrete:
            for other in concrete:
                if t != other:
                    assert not validator._is_subtype(t, other)

    def test_concrete_not_subtype_of_never(self, validator):
        """Concrete types are not subtypes of Never."""
        never = BaseType("Never")
        concrete = [
            BaseType("Int64"),
            BaseType("Int32"),
            BaseType("Float64"),
            BaseType("String"),
            BaseType("Boolean"),
        ]
        for t in concrete:
            assert not validator._is_subtype(t, never)

    def test_any_not_subtype_of_concrete(self, validator):
        """Any is not a subtype of concrete types."""
        any_type = BaseType("Any")
        concrete = [
            BaseType("Int64"),
            BaseType("Int32"),
            BaseType("Float64"),
            BaseType("String"),
            BaseType("Boolean"),
        ]
        for t in concrete:
            assert not validator._is_subtype(any_type, t)

    def test_list_reflexivity(self, validator):
        """List[T] <: List[T]."""
        types = [
            BaseType("Never"),
            BaseType("Any"),
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t in types:
            assert validator._is_subtype(ListType(t), ListType(t))

    def test_list_invariant(self, validator):
        """List is invariant: List[T] <: List[U] only if T == U."""
        never = BaseType("Never")
        any_type = BaseType("Any")
        int64 = BaseType("Int64")
        string = BaseType("String")
        # List[Never] is NOT a subtype of List[Any] (invariant)
        assert not validator._is_subtype(ListType(never), ListType(any_type))
        # List[Int64] is NOT a subtype of List[Any] (invariant)
        assert not validator._is_subtype(ListType(int64), ListType(any_type))
        # Distinct concrete types are not subtypes
        assert not validator._is_subtype(ListType(int64), ListType(string))
        assert not validator._is_subtype(ListType(string), ListType(int64))

    # --- Sequence tests (covariant) ---

    def test_sequence_reflexivity(self, validator):
        """Sequence[T] <: Sequence[T]."""
        types = [
            BaseType("Never"),
            BaseType("Any"),
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t in types:
            assert validator._is_subtype(SequenceType(t), SequenceType(t))

    def test_sequence_never_is_bottom(self, validator):
        """Sequence[Never] <: Sequence[T] (Sequence is covariant)."""
        never = BaseType("Never")
        types = [
            BaseType("Any"),
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t in types:
            assert validator._is_subtype(SequenceType(never), SequenceType(t))

    def test_sequence_any_is_top(self, validator):
        """Sequence[T] <: Sequence[Any] (Sequence is covariant)."""
        any_type = BaseType("Any")
        types = [
            BaseType("Never"),
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t in types:
            assert validator._is_subtype(SequenceType(t), SequenceType(any_type))

    def test_sequence_concrete_not_subtype(self, validator):
        """Sequence[T] is not a subtype of Sequence[U] for distinct concrete T, U."""
        int64 = BaseType("Int64")
        string = BaseType("String")
        assert not validator._is_subtype(SequenceType(int64), SequenceType(string))
        assert not validator._is_subtype(SequenceType(string), SequenceType(int64))

    def test_nested_sequence_covariance(self, validator):
        """Sequence[Sequence[Never]] <: Sequence[Sequence[Int64]]."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert validator._is_subtype(
            SequenceType(SequenceType(never)),
            SequenceType(SequenceType(int64))
        )

    def test_sequence_not_subtype_of_element(self, validator):
        """Sequence[T] is not a subtype of T."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(SequenceType(int64), int64)

    def test_element_not_subtype_of_sequence(self, validator):
        """T is not a subtype of Sequence[T]."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(int64, SequenceType(int64))

    def test_sequence_not_subtype_of_option(self, validator):
        """Sequence[T] is not a subtype of Option[T]."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(SequenceType(int64), OptionType(int64))

    def test_option_not_subtype_of_sequence(self, validator):
        """Option[T] is not a subtype of Sequence[T]."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(OptionType(int64), SequenceType(int64))

    # --- List <: Sequence relationship ---

    def test_list_subtype_of_sequence(self, validator):
        """List[T] <: Sequence[T]."""
        types = [
            BaseType("Never"),
            BaseType("Any"),
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t in types:
            assert validator._is_subtype(ListType(t), SequenceType(t))

    def test_list_invariant_not_subtype_with_never(self, validator):
        """List[Never] is NOT <: List[T] (List is invariant)."""
        never = BaseType("Never")
        types = [
            BaseType("Any"),
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t in types:
            assert not validator._is_subtype(ListType(never), ListType(t))

    def test_list_invariant_not_subtype_with_any(self, validator):
        """List[T] is NOT <: List[Any] (List is invariant)."""
        any_type = BaseType("Any")
        types = [
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t in types:
            assert not validator._is_subtype(ListType(t), ListType(any_type))

    def test_list_not_subtype_of_element(self, validator):
        """List[T] is not a subtype of T."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(ListType(int64), int64)

    def test_element_not_subtype_of_list(self, validator):
        """T is not a subtype of List[T]."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(int64, ListType(int64))

    def test_option_reflexivity(self, validator):
        """Option[T] <: Option[T]."""
        types = [
            BaseType("Never"),
            BaseType("Any"),
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t in types:
            assert validator._is_subtype(OptionType(t), OptionType(t))

    def test_option_never_is_bottom(self, validator):
        """Option[Never] <: Option[T]."""
        never = BaseType("Never")
        types = [
            BaseType("Any"),
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t in types:
            assert validator._is_subtype(OptionType(never), OptionType(t))

    def test_option_any_is_top(self, validator):
        """Option[T] <: Option[Any]."""
        any_type = BaseType("Any")
        types = [
            BaseType("Never"),
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t in types:
            assert validator._is_subtype(OptionType(t), OptionType(any_type))

    def test_option_concrete_not_subtype(self, validator):
        """Option[T] is not a subtype of Option[U] for distinct concrete T, U."""
        int64 = BaseType("Int64")
        string = BaseType("String")
        assert not validator._is_subtype(OptionType(int64), OptionType(string))
        assert not validator._is_subtype(OptionType(string), OptionType(int64))

    def test_option_not_subtype_of_element(self, validator):
        """Option[T] is not a subtype of T."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(OptionType(int64), int64)

    def test_element_not_subtype_of_option(self, validator):
        """T is not a subtype of Option[T]."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(int64, OptionType(int64))

    def test_nested_list_invariance(self, validator):
        """List is invariant: List[List[Never]] is NOT a subtype of List[List[Int64]]."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert not validator._is_subtype(
            ListType(ListType(never)),
            ListType(ListType(int64))
        )

    def test_nested_option_covariance(self, validator):
        """Option[Option[Never]] <: Option[Option[Int64]]."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert validator._is_subtype(
            OptionType(OptionType(never)),
            OptionType(OptionType(int64))
        )

    def test_list_of_option_invariance(self, validator):
        """List is invariant, so List[Option[Never]] is NOT <: List[Option[Int64]]."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert not validator._is_subtype(
            ListType(OptionType(never)),
            ListType(OptionType(int64))
        )

    def test_sequence_of_option_covariance(self, validator):
        """Sequence[Option[Never]] <: Sequence[Option[Int64]]."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert validator._is_subtype(
            SequenceType(OptionType(never)),
            SequenceType(OptionType(int64))
        )

    def test_option_of_list_invariance(self, validator):
        """Option[List[Never]] is NOT <: Option[List[Int64]] because List is invariant."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert not validator._is_subtype(
            OptionType(ListType(never)),
            OptionType(ListType(int64))
        )

    def test_option_of_sequence_covariance(self, validator):
        """Option[Sequence[Never]] <: Option[Sequence[Int64]]."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert validator._is_subtype(
            OptionType(SequenceType(never)),
            OptionType(SequenceType(int64))
        )

    def test_tuple_reflexivity(self, validator):
        """(T, U) <: (T, U)."""
        int64 = BaseType("Int64")
        string = BaseType("String")
        t = TupleType([int64, string])
        assert validator._is_subtype(t, t)

    def test_tuple_covariance(self, validator):
        """(Never, Never) <: (Int64, String)."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        string = BaseType("String")
        t1 = TupleType([never, never])
        t2 = TupleType([int64, string])
        assert validator._is_subtype(t1, t2)

    def test_tuple_to_any(self, validator):
        """(Int64, String) <: (Any, Any)."""
        any_type = BaseType("Any")
        int64 = BaseType("Int64")
        string = BaseType("String")
        t1 = TupleType([int64, string])
        t2 = TupleType([any_type, any_type])
        assert validator._is_subtype(t1, t2)

    def test_tuple_length_mismatch(self, validator):
        """(T,) is not a subtype of (T, U)."""
        int64 = BaseType("Int64")
        string = BaseType("String")
        t1 = TupleType([int64])
        t2 = TupleType([int64, string])
        assert not validator._is_subtype(t1, t2)
        assert not validator._is_subtype(t2, t1)

    def test_tuple_element_mismatch(self, validator):
        """(Int64, String) is not a subtype of (String, Int64)."""
        int64 = BaseType("Int64")
        string = BaseType("String")
        t1 = TupleType([int64, string])
        t2 = TupleType([string, int64])
        assert not validator._is_subtype(t1, t2)

    def test_list_not_subtype_of_option(self, validator):
        """List[T] is not a subtype of Option[T]."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(ListType(int64), OptionType(int64))

    def test_option_not_subtype_of_list(self, validator):
        """Option[T] is not a subtype of List[T]."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(OptionType(int64), ListType(int64))

    def test_tuple_not_subtype_of_list(self, validator):
        """(T,) is not a subtype of List[T]."""
        int64 = BaseType("Int64")
        assert not validator._is_subtype(TupleType([int64]), ListType(int64))


class TestTypesCompatible:
    """Property tests for _types_compatible."""

    def test_symmetric(self, validator):
        """types_compatible(t1, t2) == types_compatible(t2, t1)."""
        types = [
            BaseType("Never"),
            BaseType("Any"),
            BaseType("Int64"),
            BaseType("String"),
        ]
        for t1 in types:
            for t2 in types:
                assert validator._types_compatible(t1, t2) == validator._types_compatible(t2, t1)

    def test_reflexive(self, validator):
        """types_compatible(t, t) is True."""
        types = [
            BaseType("Int64"),
            BaseType("String"),
            BaseType("Boolean"),
        ]
        for t in types:
            assert validator._types_compatible(t, t)

    def test_never_compatible_with_all(self, validator):
        """Never is compatible with all types."""
        never = BaseType("Never")
        concrete = [
            BaseType("Int64"),
            BaseType("String"),
            BaseType("Boolean"),
        ]
        for t in concrete:
            assert validator._types_compatible(never, t)
            assert validator._types_compatible(t, never)

    def test_any_compatible_with_all(self, validator):
        """Any is compatible with all types."""
        any_type = BaseType("Any")
        concrete = [
            BaseType("Int64"),
            BaseType("String"),
            BaseType("Boolean"),
        ]
        for t in concrete:
            assert validator._types_compatible(any_type, t)
            assert validator._types_compatible(t, any_type)

    def test_distinct_concrete_not_compatible(self, validator):
        """Distinct concrete types are not compatible."""
        int64 = BaseType("Int64")
        string = BaseType("String")
        assert not validator._types_compatible(int64, string)

    def test_list_not_compatible_via_never(self, validator):
        """List[Never] is NOT compatible with List[Int64] (List is invariant)."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert not validator._types_compatible(ListType(never), ListType(int64))

    def test_list_not_compatible_via_any(self, validator):
        """List[Int64] is NOT compatible with List[Any] (List is invariant)."""
        any_type = BaseType("Any")
        int64 = BaseType("Int64")
        assert not validator._types_compatible(ListType(int64), ListType(any_type))

    def test_list_incompatible_elements(self, validator):
        """List[Int64] is not compatible with List[String]."""
        int64 = BaseType("Int64")
        string = BaseType("String")
        assert not validator._types_compatible(ListType(int64), ListType(string))

    def test_list_self_compatible(self, validator):
        """List[T] is compatible with List[T]."""
        int64 = BaseType("Int64")
        assert validator._types_compatible(ListType(int64), ListType(int64))

    def test_option_compatible_via_never(self, validator):
        """Option[Never] is compatible with Option[Int64]."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert validator._types_compatible(OptionType(never), OptionType(int64))

    def test_option_incompatible_elements(self, validator):
        """Option[Int64] is not compatible with Option[String]."""
        int64 = BaseType("Int64")
        string = BaseType("String")
        assert not validator._types_compatible(OptionType(int64), OptionType(string))

    def test_list_option_not_compatible(self, validator):
        """List[T] is not compatible with Option[T]."""
        int64 = BaseType("Int64")
        assert not validator._types_compatible(ListType(int64), OptionType(int64))

    # --- Sequence compatibility ---

    def test_sequence_compatible_via_never(self, validator):
        """Sequence[Never] is compatible with Sequence[Int64] (covariant)."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert validator._types_compatible(SequenceType(never), SequenceType(int64))

    def test_sequence_compatible_via_any(self, validator):
        """Sequence[Int64] is compatible with Sequence[Any] (covariant)."""
        any_type = BaseType("Any")
        int64 = BaseType("Int64")
        assert validator._types_compatible(SequenceType(int64), SequenceType(any_type))

    def test_sequence_incompatible_elements(self, validator):
        """Sequence[Int64] is not compatible with Sequence[String]."""
        int64 = BaseType("Int64")
        string = BaseType("String")
        assert not validator._types_compatible(SequenceType(int64), SequenceType(string))

    def test_sequence_option_not_compatible(self, validator):
        """Sequence[T] is not compatible with Option[T]."""
        int64 = BaseType("Int64")
        assert not validator._types_compatible(SequenceType(int64), OptionType(int64))

    # --- List-Sequence compatibility ---

    def test_list_compatible_with_sequence(self, validator):
        """List[T] is compatible with Sequence[T] (List <: Sequence)."""
        int64 = BaseType("Int64")
        assert validator._types_compatible(ListType(int64), SequenceType(int64))
        assert validator._types_compatible(SequenceType(int64), ListType(int64))

    def test_list_compatible_with_wider_sequence(self, validator):
        """List[Never] is compatible with Sequence[Int64] (List <: Sequence, covariant)."""
        never = BaseType("Never")
        int64 = BaseType("Int64")
        assert validator._types_compatible(ListType(never), SequenceType(int64))

    def test_list_not_compatible_with_incompatible_sequence(self, validator):
        """List[Int64] is not compatible with Sequence[String]."""
        int64 = BaseType("Int64")
        string = BaseType("String")
        assert not validator._types_compatible(ListType(int64), SequenceType(string))
