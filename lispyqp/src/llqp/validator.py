from relationalai.lqp.v1 import logic_pb2, fragments_pb2, transactions_pb2
from google.protobuf.message import Message

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

class LQPValidator:
    """
    Validates LQP protobuf structures for variable scope and type consistency.
    """
    def __init__(self):
        # Scope: list of dictionaries mapping var_name -> var_type_enum
        # Innermost scope is at the end of the list
        self.scopes = [{}]

    def _enter_scope(self):
        self.scopes.append({})

    def _exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
        else:
            raise RuntimeError("Attempted to exit global scope")

    def _declare_var(self, var: logic_pb2.Var):
        """Declare a variable in the current innermost scope."""
        if var.name in self.scopes[-1]:
            pass # Allow shadowing for now
        self.scopes[-1][var.name] = var.type

    def _check_var_usage(self, var: logic_pb2.Var):
        """Check if a variable is declared and used with its declared type."""
        declared_type = None
        # Look up the variable starting from the innermost scope
        for scope in reversed(self.scopes):
            if var.name in scope:
                declared_type = scope[var.name]
                break

        if declared_type is None:
            raise ValidationError(f"Undeclared variable used: '{var.name}'")

        # Check type consistency: The type used must match the declared type.
        if var.type != logic_pb2.PrimitiveType.PRIMITIVE_TYPE_UNSPECIFIED and var.type != declared_type:
             type_name_declared = logic_pb2.PrimitiveType.Name(declared_type)
             type_name_used = logic_pb2.PrimitiveType.Name(var.type)
             raise ValidationError(
                 f"Type mismatch for variable '{var.name}': "
                 f"Declared as {type_name_declared}, used as {type_name_used}"
             )

    def validate(self, proto_obj: Message):
        """Public method to start validation."""
        if isinstance(proto_obj, transactions_pb2.Transaction):
            self._validate_transaction(proto_obj)
        elif isinstance(proto_obj, fragments_pb2.Fragment):
            self._validate_fragment(proto_obj)

    def _validate_transaction(self, tx: transactions_pb2.Transaction):
        for epoch in tx.epochs:
            self._validate_epoch(epoch)

    def _validate_epoch(self, epoch: transactions_pb2.Epoch):
        for write in epoch.persistent_writes:
            self._validate_write(write)
        for write in epoch.local_writes:
            self._validate_write(write)

    def _validate_write(self, write: transactions_pb2.Write):
        write_type = write.WhichOneof("write_type")
        if write_type == "define":
            self._validate_fragment(write.define.fragment)

    def _validate_fragment(self, fragment: fragments_pb2.Fragment):
        self.scopes = [{}]
        for decl in fragment.declarations:
            self._validate_declaration(decl)

    def _validate_declaration(self, decl: logic_pb2.Declaration):
        decl_type = decl.WhichOneof("declaration_type")
        if decl_type == "def":
            # Def introduces a relation, its body has variable scopes
            self._validate_def(getattr(decl, "def"))
        elif decl_type == "loop":
            self._validate_loop(decl.loop)

    def _validate_def(self, definition: logic_pb2.Def):
        self._validate_abstraction(definition.body)

    def _validate_loop(self, loop: logic_pb2.Loop):
        self._enter_scope()
        # Declare the temporal variable if it has a name (assuming it acts like a declared var)
        # Need clarity on its type - assume INT for now? Or add type to LoopIndex?
        # Let's assume it doesn't have a type specified in proto for now.
        # self._declare_var(logic_pb2.Var(name=loop.temporal_var.name, type=...?))

        # Validate initial definitions within the loop's scope
        for init_def in loop.inits:
            self._validate_def(init_def)
        # Validate body declarations within the loop's scope
        for decl in loop.body:
            self._validate_declaration(decl)
        self._exit_scope()

    def _validate_abstraction(self, abstraction: logic_pb2.Abstraction):
        self._enter_scope()
        for var in abstraction.vars:
            self._declare_var(var)
        self._validate_formula(abstraction.value)
        self._exit_scope()

    def _validate_formula(self, formula: logic_pb2.Formula):
        formula_type = formula.WhichOneof("formula_type")

        if formula_type == "exists":
            self._enter_scope()
            for var in formula.exists.vars:
                self._declare_var(var)
            self._validate_formula(formula.exists.value)
            self._exit_scope()
        elif formula_type == "reduce":
            self._validate_abstraction(formula.reduce.op)
            self._validate_abstraction(formula.reduce.body)
            for term in formula.reduce.terms:
                self._validate_term(term)
        elif formula_type == "conjunction" or formula_type == "disjunction":
            container = getattr(formula, formula_type)
            for arg_formula in container.args:
                self._validate_formula(arg_formula)
        elif formula_type == "not":
            self._validate_formula(formula.not_.arg)
        elif formula_type == "ffi":
            for arg_abs in formula.ffi.args:
                self._validate_abstraction(arg_abs)
            for term in formula.ffi.terms:
                self._validate_term(term)
        elif formula_type == "atom" or formula_type == "rel_atom" or formula_type == "pragma" or formula_type == "primitive":
            container = getattr(formula, formula_type)
            for term in container.terms:
                self._validate_term(term)

    def _validate_term(self, term: logic_pb2.Term):
        term_type = term.WhichOneof("term_type")
        if term_type == "var":
            self._check_var_usage(term.var)
        elif term_type == "constant":
            pass

# Helper function to be called from parser script
def validate_lqp(proto_obj: Message):
    """
    Validates the given LQP protobuf object.
    Raises ValidationError on failure.
    """
    validator = LQPValidator()
    validator.validate(proto_obj)
