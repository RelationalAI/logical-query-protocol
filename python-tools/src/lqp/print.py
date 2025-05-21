from abc import ABC, abstractmethod
from typing import Union, Sequence, Dict

from colorama import Style, Fore
from enum import Enum

from . import ir

class StyleConfig(ABC):
    @abstractmethod
    def SIND(self, ) -> str: pass

    @abstractmethod
    def LPAREN(self, ) -> str: pass
    @abstractmethod
    def RPAREN(self, ) -> str: pass

    @abstractmethod
    def LBRACKET(self, ) -> str: pass
    @abstractmethod
    def RBRACKET(self, ) -> str: pass

    # String of level indentations for LLQP.
    @abstractmethod
    def indentation(self, level: int) -> str: pass

    # Styled keyword x.
    @abstractmethod
    def kw(self, x: str) -> str: pass

    # Styled user provided name, e.g. variables.
    @abstractmethod
    def uname(self, x: str) -> str: pass

    # Styled type annotation, e.g. ::INT.
    @abstractmethod
    def type_anno(self, x: str) -> str: pass

# Some basic components and how they are to be printed.
class Unstyled(StyleConfig):
    # Single INDentation.
    def SIND(self, ): return "    "

    def LPAREN(self, ): return "("
    def RPAREN(self, ): return ")"

    def LBRACKET(self, ): return "["
    def RBRACKET(self, ): return "]"

    # String of level indentations for LLQP.
    def indentation(self, level: int) -> str:
        return self.SIND() * level

    # Styled keyword x.
    def kw(self, x: str) -> str:
        return x

    # Styled user provided name, e.g. variables.
    def uname(self, x: str) -> str:
        return x

    # Styled type annotation, e.g. ::INT.
    def type_anno(self, x: str) -> str:
        return x

class Styled(StyleConfig):
    def SIND(self, ): return "    "

    def LPAREN(self, ): return str(Style.DIM) + "(" + str(Style.RESET_ALL)
    def RPAREN(self, ): return str(Style.DIM) + ")" + str(Style.RESET_ALL)

    def LBRACKET(self, ): return str(Style.DIM) + "[" + str(Style.RESET_ALL)
    def RBRACKET(self, ): return str(Style.DIM) + "]" + str(Style.RESET_ALL)

    def indentation(self, level: int) -> str:
        return self.SIND() * level

    def kw(self, x: str) -> str:
        return str(Fore.YELLOW) + x + str(Style.RESET_ALL)

    def uname(self, x: str) -> str:
        return str(Fore.WHITE) + x + str(Style.RESET_ALL)

    # Styled type annotation, e.g. ::INT.
    def type_anno(self, x: str) -> str:
        return str(Style.DIM) + x + str(Style.RESET_ALL)

class PrettyOptions(Enum):
    STYLED = 1,
    PRINT_NAMES = 2,

    def __str__(self):
        return option_to_key[self]

option_to_key = {
    PrettyOptions.STYLED: "styled",
    PrettyOptions.PRINT_NAMES: "print_names"
}

option_to_default = {
    PrettyOptions.STYLED: False,
    PrettyOptions.PRINT_NAMES: False
}

# Used for precise testing
ugly_config = {
    str(PrettyOptions.STYLED): False,
    str(PrettyOptions.PRINT_NAMES): False,
}

# Used for humans
pretty_config = {
    str(PrettyOptions.STYLED): True,
    str(PrettyOptions.PRINT_NAMES): True,
}

def style_config(options: Dict) -> StyleConfig:
    if has_option(options, PrettyOptions.STYLED):
        return Styled()
    else:
        return Unstyled()

# Call to_llqp on all nodes, each of which with indent_level, separating them
# by delim.
def list_to_llqp(nodes: Sequence[Union[ir.LqpNode, ir.PrimitiveType, ir.PrimitiveValue, ir.Specialized]], indent_level: int, delim: str, options: Dict) -> str:
    return delim.join(map(lambda n: to_llqp(n, indent_level, options), nodes))

# Produces "(terms term1 term2 ...)" (all on one line) indented at indent_level.
def terms_to_llqp(terms: Sequence[Union[ir.Term, ir.Specialized]], indent_level: int, options: Dict) -> str:
    # Default to true for styled.
    conf = style_config(options)

    ind = conf.indentation(indent_level)

    llqp = ""
    if len(terms) == 0:
        llqp = ind + conf.LPAREN() + conf.kw("terms") + conf.RPAREN()
    else:
        llqp = ind + conf.LPAREN() + conf.kw("terms") + " " + list_to_llqp(terms, 0, " ", options) + conf.RPAREN()

    return llqp

def program_to_llqp(node: ir.Transaction, options: Dict = {}) -> str:
    conf = style_config(options)
    epochs_portion = ""
    for epoch in node.epochs:
        epochs_portion += conf.indentation(1) + conf.LPAREN() + conf.kw("epoch") + "\n"
        if len(epoch.persistent_writes) > 0:
            epochs_portion += conf.indentation(2) + conf.LPAREN() + conf.kw("persistent_writes") + "\n"
            epochs_portion += list_to_llqp(epoch.persistent_writes, 3, "\n", options) + "\n"
            epochs_portion += conf.indentation(2) + conf.RPAREN() + "\n"

        if len(epoch.local_writes) > 0:
            epochs_portion += conf.indentation(2) + conf.LPAREN() + conf.kw("local_writes") + "\n"
            epochs_portion += list_to_llqp(epoch.local_writes, 3, "\n", options) + "\n"
            epochs_portion += conf.indentation(2) + conf.RPAREN() + "\n"
        if len(epoch.reads) > 0:
            epochs_portion += conf.indentation(2) + conf.LPAREN() + conf.kw("reads") + "\n"
            epochs_portion += list_to_llqp(epoch.reads, 3, "\n", options) + "\n"
            epochs_portion += conf.indentation(2) + conf.RPAREN() + "\n"
        epochs_portion += conf.indentation(1) + conf.RPAREN() + "\n" # Close epoch

    return\
    conf.indentation(0) + conf.LPAREN() + conf.kw("transaction") + "\n" +\
    epochs_portion +\
    conf.indentation(0) + conf.RPAREN()

def to_llqp(node: Union[ir.LqpNode, ir.PrimitiveType, ir.PrimitiveValue, ir.Specialized], indent_level: int, options: Dict = {}) -> str:
    conf = style_config(options)

    ind = conf.indentation(indent_level)
    llqp = ""

    if isinstance(node, ir.Def):
        llqp += ind + conf.LPAREN() + conf.kw("def") + " " + to_llqp(node.name, 0, options) + "\n"
        llqp += to_llqp(node.body, indent_level + 1, options) + "\n"
        if len(node.attrs) == 0:
            llqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("attrs") + conf.RPAREN() + conf.RPAREN()
        else:
            llqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("attrs") + "\n"
            llqp += list_to_llqp(node.attrs, indent_level + 2, "\n", options) + "\n"
            llqp += ind + conf.SIND() + conf.RPAREN() + conf.RPAREN()

    elif isinstance(node, ir.Loop):
        llqp += ind + conf.LPAREN() + conf.kw("loop") + "\n"
        llqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("inits") + "\n"
        llqp += list_to_llqp(node.inits, indent_level + 2, "\n", options) + "\n"
        llqp += ind + conf.SIND() + conf.RPAREN() + "\n"
        llqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("body") + "\n"
        llqp += list_to_llqp(node.body, indent_level + 2, "\n", options) + "\n"
        llqp += ind + conf.SIND() + conf.RPAREN() + conf.RPAREN()

    elif isinstance(node, ir.Abstraction):
        llqp += ind + conf.LPAREN() + conf.LBRACKET()
        llqp += " ".join(map(lambda v: conf.uname(v[0].name) + conf.type_anno("::" + type_to_llqp(v[1])), node.vars))
        llqp += conf.RBRACKET() + "\n"
        llqp += to_llqp(node.value, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Exists):
        llqp += ind + conf.LPAREN() + conf.kw("exists") + " " + conf.LBRACKET()
        llqp += " ".join(map(lambda v: conf.uname(v[0].name) + conf.type_anno("::" + type_to_llqp(v[1])), node.body.vars))
        llqp += conf.RBRACKET() + "\n"
        llqp += to_llqp(node.body.value, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Reduce):
        llqp += ind + conf.LPAREN() + conf.kw("reduce") + "\n"
        llqp += to_llqp(node.op, indent_level + 1, options) + "\n"
        llqp += to_llqp(node.body, indent_level + 1, options) + "\n"
        llqp += terms_to_llqp(node.terms, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Conjunction):
        llqp += ind + conf.LPAREN() + conf.kw("and") + "\n"
        llqp += list_to_llqp(node.args, indent_level + 1, "\n", options) + conf.RPAREN()

    elif isinstance(node, ir.Disjunction):
        llqp += ind + conf.LPAREN() + conf.kw("or") + "\n"
        llqp += list_to_llqp(node.args, indent_level + 1, "\n", options) + conf.RPAREN()

    elif isinstance(node, ir.Not):
        llqp += ind + conf.LPAREN() + conf.kw("not") + "\n"
        llqp += to_llqp(node.arg, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.FFI):
        llqp += ind + conf.LPAREN() + conf.kw("ffi") + " " + ":" + node.name + "\n"
        llqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("args") + "\n"
        llqp += list_to_llqp(node.args, indent_level + 2, "\n", options) + "\n"
        llqp += ind + conf.SIND() + conf.RPAREN() + "\n"
        llqp += terms_to_llqp(node.terms, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Atom):
        llqp += f"{ind}{conf.LPAREN()}{conf.kw('atom!')} {to_llqp(node.name, 0, options)} {list_to_llqp(node.terms, 0, ' ', options)}{conf.RPAREN()}"

    elif isinstance(node, ir.Pragma):
        llqp += f"{ind}{conf.LPAREN()}{conf.kw('pragma')} :{conf.uname(node.name)} {terms_to_llqp(node.terms, 0, options)}{conf.RPAREN()}"

    elif isinstance(node, ir.Primitive):
        llqp += f"{ind}{conf.LPAREN()}{conf.kw('primitive')} :{conf.uname(node.name)} {list_to_llqp(node.terms, 0, ' ', options)}{conf.RPAREN()}"

    elif isinstance(node, ir.RelAtom):
        llqp += f"{ind}{conf.LPAREN()}{conf.kw('relatom')} {node.name} {list_to_llqp(node.terms, 0, ' ', options)}{conf.RPAREN()}"

    elif isinstance(node, ir.Cast):
        llqp += ind + conf.LPAREN() + conf.kw("cast") + " " + type_to_llqp(node.type) + " " + to_llqp(node.input, 0, options) + " " + to_llqp(node.result, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.Var):
        llqp += ind + conf.uname(node.name)

    elif isinstance(node, str):
        llqp += f"{ind}\"{node}\""
    elif isinstance(node, ir.UInt128):
        llqp += ind + str(node.value)
    elif isinstance(node, bool):
        llqp += ind + str(node).lower()
    elif isinstance(node, (int, float)):
        llqp += ind + str(node)

    elif isinstance(node, ir.Specialized):
        val_to_print = node.value
        if isinstance(val_to_print, str):
            llqp += ind + "\"" + val_to_print + "\""
        elif isinstance(val_to_print, ir.UInt128):
            llqp += ind + str(val_to_print.value)
        elif isinstance(val_to_print, bool):
            llqp += ind + str(val_to_print).lower()
        elif isinstance(val_to_print, (int, float)):
            llqp += ind + str(val_to_print)
        else:
            llqp += ind + str(val_to_print)

    elif isinstance(node, ir.Attribute):
        llqp += ind
        llqp += conf.LPAREN() + conf.kw("attribute") + " "
        llqp += ":" + node.name + " "
        if len(node.args) == 0:
            llqp += conf.LPAREN() + conf.kw("args") + conf.RPAREN()
        else:
            llqp += conf.LPAREN() + conf.kw("args") + " "
            llqp += list_to_llqp(node.args, 0, " ", options)
            llqp += conf.RPAREN()
        llqp += conf.RPAREN()

    elif isinstance(node, ir.RelationId):
        name = id_to_name(options, node)
        llqp += f"{ind}{str(conf.uname(name))}"

    elif isinstance(node, ir.PrimitiveType):
        llqp += ind + node.name

    elif isinstance(node, ir.Write):
        # Delegate to the specific write type
        llqp += to_llqp(node.write_type, indent_level, options)

    elif isinstance(node, ir.Define):
        llqp += ind + conf.LPAREN() + conf.kw("define") + " " + to_llqp(node.fragment, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.Undefine):
        llqp += ind + conf.LPAREN() + conf.kw("undefine") + " " + to_llqp(node.fragment_id, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.Context):
        llqp += ind + conf.LPAREN() + conf.kw("context") + " " + list_to_llqp(node.relations, 0, " ", options) + conf.RPAREN()

    elif isinstance(node, ir.FragmentId):
        llqp += f"{ind}:{conf.uname(node.id.decode())}"

    elif isinstance(node, ir.Read):
        # Delegate to the specific read type
        llqp += to_llqp(node.read_type, indent_level, options)

    elif isinstance(node, ir.Demand):
        llqp += ind + conf.LPAREN() + conf.kw("demand") + " " + to_llqp(node.relation_id, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.Output):
        name_str = f":{conf.uname(node.name)} " if node.name else ""
        llqp += ind + conf.LPAREN() + conf.kw("output") + " " + name_str + to_llqp(node.relation_id, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.Abort):
        name_str = f":{conf.uname(node.name)} " if node.name else ""
        llqp += ind + conf.LPAREN() + conf.kw("abort") + " " + name_str + to_llqp(node.relation_id, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.WhatIf):
        branch_str = f":{conf.uname(node.branch)} " if node.branch else ""
        llqp += ind + conf.LPAREN() + conf.kw("what_if") + " " + branch_str + to_llqp(node.epoch, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Epoch):
        # Epoch is handled within program_to_llqp, but might be called directly for WhatIf
        # This case should ideally not be hit directly by list_to_llqp for epoch.local_writes etc.
        # But if it is, it should print its contents.
        epoch_content = ""
        if len(node.persistent_writes) > 0:
            epoch_content += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("persistent_writes") + "\n"
            epoch_content += list_to_llqp(node.persistent_writes, indent_level + 2, "\n", options) + "\n"
            epoch_content += conf.indentation(indent_level + 1) + conf.RPAREN() + "\n"

        if len(node.local_writes) > 0:
            epoch_content += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("local_writes") + "\n"
            epoch_content += list_to_llqp(node.local_writes, indent_level + 2, "\n", options) + "\n"
            epoch_content += conf.indentation(indent_level + 1) + conf.RPAREN() + "\n"

        if len(node.reads) > 0:
            epoch_content += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("reads") + "\n"
            epoch_content += list_to_llqp(node.reads, indent_level + 2, "\n", options) + "\n"
            epoch_content += conf.indentation(indent_level + 1) + conf.RPAREN() + "\n"
        llqp += ind + conf.LPAREN() + conf.kw("epoch") + "\n" + epoch_content + ind + conf.RPAREN()

    elif isinstance(node, ir.Fragment):
        llqp += fragment_to_llqp(node, options)

    else:
        raise NotImplementedError(f"to_llqp not implemented for {type(node)}.")

    return llqp

def fragment_to_llqp(node: ir.Fragment, options: Dict = {}) -> str:
    conf = style_config(options)
    declarations_portion = list_to_llqp(node.declarations, 5, "\n", options)
    return \
        conf.indentation(0) + conf.LPAREN() + conf.kw("fragment") + " " + to_llqp(node.id, 0, options) + "\n" + \
        declarations_portion + \
        conf.RPAREN()

def to_llqp_string(node: ir.LqpNode, options: Dict = {}) -> str:
    if isinstance(node, ir.Transaction):
        return program_to_llqp(node, options)
    elif isinstance(node, ir.Fragment):
        return fragment_to_llqp(node, options)
    else:
        raise NotImplementedError(f"to_llqp_string not implemented for top-level node type {type(node)}.")

def type_to_llqp(node: ir.RelType) -> str:
    return str(node.name)

def id_to_name(options: Dict, rid: ir.RelationId) -> str:
    if not has_option(options, PrettyOptions.PRINT_NAMES):
        return str(rid.id)
    debug = options.get("_debug", None)
    if debug is None:
        return str(rid.id)
    assert rid in debug.id_to_orig_name, f"ID {rid} not found in debug info."
    name = debug.id_to_orig_name[rid]
    name = ":" + name
    return name

def has_option(options: Dict, opt: PrettyOptions) -> bool:
    return options.get(option_to_key[opt], option_to_default[opt])
