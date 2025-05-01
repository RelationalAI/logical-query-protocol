import lqp.ir as ir
from typing import Union, Dict, Any, Generic, TypeVar

T = TypeVar('T')

class ValidationError(Exception):
    pass

class LqpVisitor(Generic[T]):
    def visit(self, node: ir.LqpNode, *args: Any) -> T:
        method_name = f'visit_{node.__class__.__name__}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node, *args)

    def generic_visit(self, node: ir.LqpNode, *args: Any) -> T:
        for field_name, field_value in node.__dataclass_fields__.items():
            value = getattr(node, field_name)
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

class VariableScopeVisitor(LqpVisitor[None]):
    def __init__(self):
        self.scopes: list[Dict[str, ir.RelType]] = [{}]

    def _enter_scope(self):
        self.scopes.append({})

    def _exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
        else:
            raise RuntimeError("Attempted to exit global scope")

    def _declare_var(self, var: ir.Var):
        if var.name in self.scopes[-1]:
            pass # Allow shadowing
        self.scopes[-1][var.name] = var.type

    def _get_type_name(self, rel_type: ir.RelType) -> str:
        if isinstance(rel_type, (ir.PrimitiveType, ir.RelValueType)):
            return rel_type.name
        return "UNKNOWN"

    def _check_var_usage(self, var: ir.Var):
        declared_type: Union[ir.RelType, None] = None
        for scope in reversed(self.scopes):
            if var.name in scope:
                declared_type = scope[var.name]
                break

        if declared_type is None:
            raise ValidationError(f"Undeclared variable used: '{var.name}'")

        if var.type != declared_type:
            type_name_declared = self._get_type_name(declared_type)
            type_name_used = self._get_type_name(var.type)
            raise ValidationError(
                f"Type mismatch for variable '{var.name}': "
                f"Declared as {type_name_declared}, used as {type_name_used}"
            )

    def visit_Fragment(self, node: ir.Fragment):
        self.scopes = [{}] # Reset scope for each fragment
        self.generic_visit(node)

    def visit_Abstraction(self, node: ir.Abstraction):
        self._enter_scope()
        for var in node.vars:
            self._declare_var(var)
        self.visit(node.value)
        self._exit_scope()

    def visit_Var(self, node: ir.Var):
        self._check_var_usage(node)

def validate_lqp(lqp: ir.LqpNode):
    validator = VariableScopeVisitor()
    validator.visit(lqp)
