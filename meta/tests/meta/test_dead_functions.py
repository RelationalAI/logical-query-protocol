"""Tests for dead function elimination."""

from meta.dead_functions import collect_named_fun_refs, live_functions
from meta.target import (
    Assign,
    BaseType,
    Call,
    Foreach,
    ForeachEnumerated,
    FunctionType,
    FunDef,
    GetElement,
    GetField,
    IfElse,
    Lambda,
    Let,
    ListExpr,
    Lit,
    MessageType,
    NamedFun,
    NewMessage,
    Return,
    Seq,
    Var,
    While,
)
from meta.target_builtins import make_builtin

_INT = BaseType("Int64")
_FN = FunctionType([], _INT)


def _named(name: str) -> NamedFun:
    return NamedFun(name, _FN)


def _var(name: str = "x") -> Var:
    return Var(name, _INT)


def _fundef(name: str, body) -> FunDef:
    return FunDef(name, [_var("x")], _INT, body)


# ---------- collect_named_fun_refs ----------


class TestCollectNamedFunRefs:
    def test_named_fun(self):
        assert collect_named_fun_refs(_named("f")) == {"f"}

    def test_var(self):
        assert collect_named_fun_refs(_var()) == set()

    def test_lit(self):
        assert collect_named_fun_refs(Lit(42)) == set()

    def test_call_func_and_args(self):
        expr = Call(_named("f"), [_named("g"), _var()])
        assert collect_named_fun_refs(expr) == {"f", "g"}

    def test_call_builtin(self):
        expr = Call(make_builtin("equal"), [_var(), Lit(1)])
        assert collect_named_fun_refs(expr) == set()

    def test_let(self):
        expr = Let(_var(), _named("f"), _named("g"))
        assert collect_named_fun_refs(expr) == {"f", "g"}

    def test_assign(self):
        expr = Assign(_var(), _named("f"))
        assert collect_named_fun_refs(expr) == {"f"}

    def test_seq(self):
        expr = Seq([_named("a"), _named("b")])
        assert collect_named_fun_refs(expr) == {"a", "b"}

    def test_if_else(self):
        expr = IfElse(Lit(True), _named("then"), _named("else_"))
        assert collect_named_fun_refs(expr) == {"then", "else_"}

    def test_while(self):
        expr = While(_named("cond"), _named("body"))
        assert collect_named_fun_refs(expr) == {"cond", "body"}

    def test_foreach(self):
        expr = Foreach(_var("i"), _named("coll"), _named("body"))
        assert collect_named_fun_refs(expr) == {"coll", "body"}

    def test_foreach_enumerated(self):
        expr = ForeachEnumerated(_var("i"), _var("v"), _named("coll"), _named("body"))
        assert collect_named_fun_refs(expr) == {"coll", "body"}

    def test_return(self):
        expr = Return(_named("f"))
        assert collect_named_fun_refs(expr) == {"f"}

    def test_lambda(self):
        expr = Lambda([_var("p")], _INT, _named("f"))
        assert collect_named_fun_refs(expr) == {"f"}

    def test_new_message(self):
        expr = NewMessage("mod", "Msg", [("a", _named("f")), ("b", _named("g"))])
        assert collect_named_fun_refs(expr) == {"f", "g"}

    def test_new_message_no_fields(self):
        expr = NewMessage("mod", "Msg", [])
        assert collect_named_fun_refs(expr) == set()

    def test_get_field(self):
        msg_type = MessageType("mod", "Msg")
        expr = GetField(_named("f"), "x", msg_type, _INT)
        assert collect_named_fun_refs(expr) == {"f"}

    def test_get_element(self):
        expr = GetElement(_named("f"), 0)
        assert collect_named_fun_refs(expr) == {"f"}

    def test_list_expr(self):
        expr = ListExpr([_named("a"), _named("b")], _INT)
        assert collect_named_fun_refs(expr) == {"a", "b"}

    def test_list_expr_empty(self):
        expr = ListExpr([], _INT)
        assert collect_named_fun_refs(expr) == set()

    def test_nested(self):
        """Deeply nested expression collects refs at all levels."""
        inner = Call(_named("deep"), [Lit(1)])
        mid = Let(_var(), inner, _named("mid"))
        outer = Seq([mid, Return(_named("top"))])
        assert collect_named_fun_refs(outer) == {"deep", "mid", "top"}

    def test_duplicate_refs(self):
        """Same name appearing multiple times yields a single entry."""
        expr = Seq([_named("f"), _named("f")])
        assert collect_named_fun_refs(expr) == {"f"}


# ---------- live_functions ----------


class TestLiveFunctions:
    def test_empty(self):
        result = live_functions([], {})
        assert result == {}

    def test_no_refs_in_roots(self):
        result = live_functions([_var()], {"f": _fundef("f", _var())})
        assert result == {}

    def test_direct_ref(self):
        defs = {"f": _fundef("f", _var())}
        result = live_functions([Call(_named("f"), [])], defs)
        assert set(result.keys()) == {"f"}

    def test_dead_function_excluded(self):
        defs = {
            "live": _fundef("live", _var()),
            "dead": _fundef("dead", _var()),
        }
        result = live_functions([Call(_named("live"), [])], defs)
        assert set(result.keys()) == {"live"}

    def test_transitive(self):
        """f calls g, g calls h — all three are live."""
        defs = {
            "f": _fundef("f", Call(_named("g"), [])),
            "g": _fundef("g", Call(_named("h"), [])),
            "h": _fundef("h", _var()),
        }
        result = live_functions([Call(_named("f"), [])], defs)
        assert set(result.keys()) == {"f", "g", "h"}

    def test_transitive_dead(self):
        """f calls g, but h is unreachable."""
        defs = {
            "f": _fundef("f", Call(_named("g"), [])),
            "g": _fundef("g", _var()),
            "h": _fundef("h", _var()),
        }
        result = live_functions([Call(_named("f"), [])], defs)
        assert set(result.keys()) == {"f", "g"}

    def test_cycle(self):
        """f calls g, g calls f — both live, no infinite loop."""
        defs = {
            "f": _fundef("f", Call(_named("g"), [])),
            "g": _fundef("g", Call(_named("f"), [])),
        }
        result = live_functions([Call(_named("f"), [])], defs)
        assert set(result.keys()) == {"f", "g"}

    def test_multiple_roots(self):
        defs = {
            "a": _fundef("a", _var()),
            "b": _fundef("b", _var()),
            "dead": _fundef("dead", _var()),
        }
        roots = [Call(_named("a"), []), Call(_named("b"), [])]
        result = live_functions(roots, defs)
        assert set(result.keys()) == {"a", "b"}

    def test_ref_not_in_defs(self):
        """Reference to a name not in function_defs is ignored."""
        result = live_functions([Call(_named("missing"), [])], {})
        assert result == {}

    def test_fundef_with_none_body(self):
        """Builtin signatures (body=None) are included but not traversed."""
        defs = {
            "builtin": FunDef("builtin", [], _INT, None),
        }
        result = live_functions([Call(_named("builtin"), [])], defs)
        assert set(result.keys()) == {"builtin"}

    def test_all_dead(self):
        defs = {
            "a": _fundef("a", _var()),
            "b": _fundef("b", _var()),
        }
        result = live_functions([_var()], defs)
        assert result == {}

    def test_diamond(self):
        """Diamond dependency: root -> {a, b}, a -> c, b -> c."""
        defs = {
            "a": _fundef("a", Call(_named("c"), [])),
            "b": _fundef("b", Call(_named("c"), [])),
            "c": _fundef("c", _var()),
        }
        root = Seq([Call(_named("a"), []), Call(_named("b"), [])])
        result = live_functions([root], defs)
        assert set(result.keys()) == {"a", "b", "c"}
