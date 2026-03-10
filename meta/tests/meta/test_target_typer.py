"""Tests for target IR type checker."""

import pytest

from meta.target import (
    Assign,
    BaseType,
    Builtin,
    Call,
    Foreach,
    ForeachEnumerated,
    FunctionType,
    FunDef,
    GetElement,
    IfElse,
    Lambda,
    Let,
    ListExpr,
    ListType,
    Lit,
    OptionType,
    TupleType,
    Var,
    VarType,
    While,
)
from meta.target_builtins import VOID
from meta.target_typer import typecheck_def, typecheck_ir

INT64 = BaseType("Int64")
STRING = BaseType("String")
BOOLEAN = BaseType("Boolean")
NEVER = BaseType("Never")


def _fn_type(params, ret):
    return FunctionType(params, ret)


def _builtin(name, params, ret):
    return Builtin(name, _fn_type(params, ret))


class TestTypecheckLet:
    def test_valid_let(self):
        defn = FunDef(
            "f",
            [],
            INT64,
            Let(Var("x", INT64), Lit(42), Var("x", INT64)),
        )
        assert typecheck_def(defn) == []

    def test_init_type_mismatch(self):
        defn = FunDef(
            "f",
            [],
            INT64,
            Let(Var("x", INT64), Lit("hello"), Var("x", INT64)),
        )
        errors = typecheck_def(defn)
        assert len(errors) == 1
        assert "init type String" in errors[0]
        assert "var type Int64" in errors[0]


class TestTypecheckAssign:
    def test_valid_assign(self):
        defn = FunDef(
            "f",
            [],
            VOID,
            Assign(Var("x", INT64), Lit(42)),
        )
        assert typecheck_def(defn) == []

    def test_assign_type_mismatch(self):
        defn = FunDef(
            "f",
            [],
            VOID,
            Assign(Var("x", INT64), Lit("hello")),
        )
        errors = typecheck_def(defn)
        assert len(errors) == 1
        assert "Assign" in errors[0]


class TestTypecheckIfElse:
    def test_valid_ifelse(self):
        defn = FunDef(
            "f",
            [],
            INT64,
            IfElse(Lit(True), Lit(1), Lit(2)),
        )
        assert typecheck_def(defn) == []

    def test_non_boolean_condition_rejected_at_construction(self):
        """IfElse.__post_init__ rejects non-Boolean conditions."""
        with pytest.raises(AssertionError, match="must be Boolean"):
            IfElse(Lit(42), Lit(1), Lit(2))

    def test_incompatible_branches(self):
        defn = FunDef(
            "f",
            [],
            INT64,
            IfElse(Lit(True), Lit(1), Lit("hello")),
        )
        errors = typecheck_def(defn)
        assert any("incompatible types" in e for e in errors)

    def test_void_branches_join(self):
        """Void and OptionType(Never) join to Void."""
        assign = Assign(Var("x", INT64), Lit(42))
        defn = FunDef(
            "f",
            [],
            VOID,
            IfElse(Lit(True), assign, Lit(None)),
        )
        assert typecheck_def(defn) == []


class TestTypecheckCall:
    def test_valid_call(self):
        add = _builtin("add", [INT64, INT64], INT64)
        defn = FunDef(
            "f",
            [],
            INT64,
            Call(add, [Lit(1), Lit(2)]),
        )
        assert typecheck_def(defn) == []

    def test_arg_type_mismatch(self):
        add = _builtin("add", [INT64, INT64], INT64)
        defn = FunDef(
            "f",
            [],
            INT64,
            Call(add, [Lit("hello"), Lit(2)]),
        )
        errors = typecheck_def(defn)
        assert any("arg 0" in e for e in errors)

    def test_arity_mismatch(self):
        add = _builtin("add", [INT64, INT64], INT64)
        defn = FunDef(
            "f",
            [],
            INT64,
            Call(add, [Lit(1)]),
        )
        errors = typecheck_def(defn)
        assert any("arity mismatch" in e for e in errors)

    def test_polymorphic_call_skipped(self):
        """Calls with VarType params should not produce errors."""
        some = _builtin("some", [VarType("T")], OptionType(VarType("T")))
        defn = FunDef(
            "f",
            [],
            OptionType(INT64),
            Call(some, [Lit(42)]),
        )
        assert typecheck_def(defn) == []


class TestTypecheckWhile:
    def test_valid_while(self):
        defn = FunDef(
            "f",
            [],
            VOID,
            While(Lit(True), Assign(Var("x", INT64), Lit(1))),
        )
        assert typecheck_def(defn) == []

    def test_non_boolean_condition(self):
        defn = FunDef(
            "f",
            [],
            VOID,
            While(Lit(42), Lit(1)),
        )
        errors = typecheck_def(defn)
        assert any("While condition" in e for e in errors)


class TestTypecheckForeach:
    def test_valid_foreach(self):
        defn = FunDef(
            "f",
            [],
            VOID,
            Foreach(
                Var("x", INT64),
                Var("items", ListType(INT64)),
                Assign(Var("y", INT64), Var("x", INT64)),
            ),
        )
        assert typecheck_def(defn) == []

    def test_non_collection(self):
        defn = FunDef(
            "f",
            [],
            VOID,
            Foreach(
                Var("x", INT64),
                Lit(42),
                Lit(1),
            ),
        )
        errors = typecheck_def(defn)
        assert any("Foreach collection" in e for e in errors)


class TestTypecheckForeachEnumerated:
    def test_non_collection(self):
        defn = FunDef(
            "f",
            [],
            VOID,
            ForeachEnumerated(
                Var("i", INT64),
                Var("x", INT64),
                Lit(42),
                Lit(1),
            ),
        )
        errors = typecheck_def(defn)
        assert any("ForeachEnumerated collection" in e for e in errors)


class TestTypecheckLambda:
    def test_valid_lambda(self):
        lam = Lambda([Var("x", INT64)], INT64, Var("x", INT64))
        defn = FunDef("f", [], FunctionType([INT64], INT64), lam)
        assert typecheck_def(defn) == []

    def test_body_type_mismatch(self):
        lam = Lambda([Var("x", INT64)], STRING, Var("x", INT64))
        defn = FunDef("f", [], FunctionType([INT64], STRING), lam)
        errors = typecheck_def(defn)
        assert any("Lambda body" in e for e in errors)


class TestTypecheckGetElement:
    def test_valid_get_element(self):
        t = TupleType([INT64, STRING])
        defn = FunDef(
            "f",
            [],
            INT64,
            GetElement(Var("pair", t), 0),
        )
        assert typecheck_def(defn) == []

    def test_out_of_bounds(self):
        t = TupleType([INT64, STRING])
        defn = FunDef(
            "f",
            [],
            INT64,
            GetElement(Var("pair", t), 5),
        )
        errors = typecheck_def(defn)
        assert any("out of bounds" in e for e in errors)

    def test_non_tuple_type(self):
        defn = FunDef(
            "f",
            [],
            INT64,
            GetElement(Lit(42), 0),
        )
        errors = typecheck_def(defn)
        assert any("non-tuple/sequence type" in e for e in errors)


class TestTypecheckListExpr:
    def test_valid_list(self):
        defn = FunDef(
            "f",
            [],
            ListType(INT64),
            ListExpr([Lit(1), Lit(2), Lit(3)], INT64),
        )
        assert typecheck_def(defn) == []

    def test_element_type_mismatch(self):
        defn = FunDef(
            "f",
            [],
            ListType(INT64),
            ListExpr([Lit(1), Lit("hello")], INT64),
        )
        errors = typecheck_def(defn)
        assert any("ListExpr element" in e for e in errors)


class TestTypecheckNullBody:
    def test_null_body_skipped(self):
        """FunDef with body=None should return no errors."""
        defn = FunDef("f", [Var("x", INT64)], INT64, None)
        assert typecheck_def(defn) == []


class TestTypecheckIR:
    def test_empty_input(self):
        assert typecheck_ir([], [], []) == []

    def test_collects_errors_from_all_defs(self):
        d1 = FunDef("f", [], INT64, Let(Var("x", INT64), Lit("wrong"), Lit(1)))
        d2 = FunDef("g", [], INT64, Let(Var("y", STRING), Lit(42), Lit(1)))
        errors = typecheck_ir([], [], [d1, d2])
        assert len(errors) == 2


class TestVoidType:
    def test_while_returns_void(self):
        w = While(Lit(True), Lit(1))
        assert w.target_type() == BaseType("Void")

    def test_foreach_returns_void(self):
        f = Foreach(Var("x", INT64), Var("xs", ListType(INT64)), Lit(1))
        assert f.target_type() == BaseType("Void")

    def test_foreach_enumerated_returns_void(self):
        f = ForeachEnumerated(
            Var("i", INT64),
            Var("x", INT64),
            Var("xs", ListType(INT64)),
            Lit(1),
        )
        assert f.target_type() == BaseType("Void")

    def test_assign_returns_void(self):
        a = Assign(Var("x", INT64), Lit(42))
        assert a.target_type() == BaseType("Void")


class TestVoidTypeJoin:
    def test_void_and_option_never(self):
        from meta.target_utils import type_join

        void = BaseType("Void")
        opt_never = OptionType(NEVER)
        assert type_join(void, opt_never) == void
        assert type_join(opt_never, void) == void

    def test_void_self_join(self):
        from meta.target_utils import type_join

        void = BaseType("Void")
        assert type_join(void, void) == void

    def test_void_and_int_fails(self):
        from meta.target_utils import type_join

        void = BaseType("Void")
        with pytest.raises(TypeError):
            type_join(void, INT64)
