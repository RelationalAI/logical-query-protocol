import lqp.ir as ir
from typing import Union, Dict, Any, List, Tuple, Set, cast

class ValidationError(Exception):
    pass

class LqpVisitor:
    def visit(self, node: ir.LqpNode, *args: Any) -> None:
        method_name = f'visit_{node.__class__.__name__}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node, *args)

    def generic_visit(self, node: ir.LqpNode, *args: Any) -> None:
        for name, _ in node.__dataclass_fields__.items():
            value = getattr(node, name)
            if isinstance(value, ir.LqpNode):
                self.visit(value, *args)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if isinstance(item, ir.LqpNode):
                        self.visit(item, *args)
            elif isinstance(value, dict):
                 for key, item in value.items():
                    if isinstance(item, ir.LqpNode):
                        self.visit(item, *args)

class VariableScopeVisitor(LqpVisitor):
    def __init__(self, fill_types=False):
        self.scopes: list[Dict[str, ir.RelType]] = []
        self.fill_types = fill_types

    def _declare_var(self, var: ir.Var):
        if var.name in self.scopes[-1]:
            pass # Allow shadowing
        self.scopes[-1][var.name] = var.type

    def _get_type_name(self, rel_type: ir.RelType) -> str:
        if isinstance(rel_type, (ir.PrimitiveType, ir.RelValueType)):
            return rel_type.name
        return "UNKNOWN"

    def _get_type(self, var: str) -> Union[ir.RelType, None]:
        for scope in reversed(self.scopes):
            if var in scope:
                return scope[var]

    def _check_var_usage(self, var: ir.Var):
        declared_type: Union[ir.RelType, None] = self._get_type(var.name)
        if declared_type is None and not self.fill_types:
            raise ValidationError(f"Undeclared variable used at {var.meta}: '{var.name}'")
        if var.type == ir.PrimitiveType.UNSPECIFIED and self.fill_types:
            object.__setattr__(var, 'type', declared_type)
        elif var.type != declared_type and not self.fill_types:
            type_name_declared = self._get_type_name(cast(ir.RelType, declared_type))
            type_name_used = self._get_type_name(var.type)
            raise ValidationError(
                f"Type mismatch for variable '{var.name}' at {var.meta}: "
                f"Declared as {type_name_declared}, used as {type_name_used}"
            )

    def visit_Abstraction(self, node: ir.Abstraction):
        self.scopes.append({})
        for var in node.vars:
            self._declare_var(var)
        self.visit(node.value)
        self.scopes.pop()

    def visit_Var(self, node: ir.Var):
        self._check_var_usage(node)

class UnusedVariableVisitor(LqpVisitor):
    def __init__(self):
        self.scopes: List[Tuple[Set[str], Set[str]]] = []

    def _declare_var(self, var_name: str):
        if self.scopes:
            self.scopes[-1][0].add(var_name)

    def _mark_var_used(self, var_name: str):
        for declared, used in reversed(self.scopes):
            if var_name in declared:
                used.add(var_name)
                break

    def visit_Abstraction(self, node: ir.Abstraction):
        self.scopes.append((set(), set()))
        for var in node.vars:
            self._declare_var(var.name)
        self.visit(node.value)
        declared, used = self.scopes.pop()
        unused = declared - used
        if unused:
            for var_name in unused:
                raise ValidationError(f"Unused variable declared: '{var_name}'")

    def visit_Var(self, node: ir.Var, *args: Any):
        self._mark_var_used(node.name)

def validate_lqp(lqp: ir.LqpNode):
    VariableScopeVisitor(fill_types=False).visit(lqp)
    UnusedVariableVisitor().visit(lqp)

def fill_types(lqp: ir.LqpNode):
    VariableScopeVisitor(fill_types=True).visit(lqp)
