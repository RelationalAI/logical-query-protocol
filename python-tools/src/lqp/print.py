from abc import ABC, abstractmethod
from typing import Union, Sequence, Dict, List

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
    def SIND(self, ): return "  "

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
    def SIND(self, ): return "  "

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

# Call to_lqp on all nodes, each of which with indent_level, separating them
# by delim.
def list_to_lqp(nodes: Sequence[Union[ir.LqpNode, ir.PrimitiveType, ir.PrimitiveValue, ir.Specialized]], indent_level: int, delim: str, options: Dict) -> str:
    return delim.join(map(lambda n: to_lqp(n, indent_level, options), nodes))

# Produces "(terms term1 term2 ...)" (all on one line) indented at indent_level.
def terms_to_lqp(terms: Sequence[Union[ir.Term, ir.Specialized]], indent_level: int, options: Dict) -> str:
    # Default to true for styled.
    conf = style_config(options)

    ind = conf.indentation(indent_level)

    lqp = ""
    if len(terms) == 0:
        lqp = ind + conf.LPAREN() + conf.kw("terms") + conf.RPAREN()
    else:
        lqp = ind + conf.LPAREN() + conf.kw("terms") + " " + list_to_lqp(terms, 0, " ", options) + conf.RPAREN()

    return lqp

def program_to_lqp(node: ir.Transaction, options: Dict = {}) -> str:
    conf = style_config(options)
    s = conf.indentation(0) + conf.LPAREN() + conf.kw("transaction")
    epoch_strs: List[str] = []
    for epoch in node.epochs:
        s += "\n" + conf.indentation(1) + conf.LPAREN() + conf.kw("epoch")
        section_strs: List[str] = []
        def build_section(keyword: str, items_list: Sequence[Union[ir.LqpNode, ir.PrimitiveType, ir.PrimitiveValue, ir.Specialized]]) -> Union[str, None]:
            if not items_list:
                return None
            sec_s = "\n" + conf.indentation(2) + conf.LPAREN() + conf.kw(keyword) + "\n"
            sec_s += list_to_lqp(items_list, 3, "\n", options) + conf.RPAREN()
            return sec_s
        persistent_writes_s = build_section("persistent_writes", epoch.persistent_writes)
        if persistent_writes_s: section_strs.append(persistent_writes_s)
        local_writes_s = build_section("local_writes", epoch.local_writes)
        if local_writes_s: section_strs.append(local_writes_s)
        reads_s = build_section("reads", epoch.reads)
        if reads_s: section_strs.append(reads_s)
        s += "".join(section_strs)
        s += conf.RPAREN()
    s += conf.RPAREN()
    return s

def to_lqp(node: Union[ir.LqpNode, ir.PrimitiveType, ir.PrimitiveValue, ir.Specialized], indent_level: int, options: Dict = {}) -> str:
    conf = style_config(options)

    ind = conf.indentation(indent_level)
    lqp = ""

    if isinstance(node, ir.Def):
        lqp += ind + conf.LPAREN() + conf.kw("def") + " " + to_lqp(node.name, 0, options) + "\n"
        lqp += to_lqp(node.body, indent_level + 1, options) + "\n"
        if len(node.attrs) == 0:
            lqp += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("attrs") + conf.RPAREN() + conf.RPAREN()
        else:
            lqp += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("attrs") + "\n"
            lqp += list_to_lqp(node.attrs, indent_level + 2, "\n", options)
            lqp += conf.RPAREN() + conf.RPAREN()

    elif isinstance(node, ir.Loop):
        lqp += ind + conf.LPAREN() + conf.kw("loop") + "\n"
        lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("inits") + "\n"
        lqp += list_to_lqp(node.inits, indent_level + 2, "\n", options)
        lqp += conf.RPAREN() + "\n"
        lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("body") + "\n"
        lqp += list_to_lqp(node.body, indent_level + 2, "\n", options)
        lqp += conf.RPAREN() + conf.RPAREN()

    elif isinstance(node, ir.Abstraction):
        lqp += ind + conf.LPAREN() + conf.LBRACKET()
        lqp += " ".join(map(lambda v: conf.uname(v[0].name) + conf.type_anno("::" + type_to_lqp(v[1])), node.vars))
        lqp += conf.RBRACKET() + "\n"
        lqp += to_lqp(node.value, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Exists):
        lqp += ind + conf.LPAREN() + conf.kw("exists") + " " + conf.LBRACKET()
        lqp += " ".join(map(lambda v: conf.uname(v[0].name) + conf.type_anno("::" + type_to_lqp(v[1])), node.body.vars))
        lqp += conf.RBRACKET() + "\n"
        lqp += to_lqp(node.body.value, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Reduce):
        lqp += ind + conf.LPAREN() + conf.kw("reduce") + "\n"
        lqp += to_lqp(node.op, indent_level + 1, options) + "\n"
        lqp += to_lqp(node.body, indent_level + 1, options) + "\n"
        lqp += terms_to_lqp(node.terms, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Conjunction):
        lqp += ind + conf.LPAREN() + conf.kw("and") + "\n"
        lqp += list_to_lqp(node.args, indent_level + 1, "\n", options) + conf.RPAREN()

    elif isinstance(node, ir.Disjunction):
        lqp += ind + conf.LPAREN() + conf.kw("or") + "\n"
        lqp += list_to_lqp(node.args, indent_level + 1, "\n", options) + conf.RPAREN()

    elif isinstance(node, ir.Not):
        lqp += ind + conf.LPAREN() + conf.kw("not") + "\n"
        lqp += to_lqp(node.arg, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.FFI):
        lqp += ind + conf.LPAREN() + conf.kw("ffi") + " " + ":" + node.name + "\n"
        lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("args") + "\n"
        lqp += list_to_lqp(node.args, indent_level + 2, "\n", options)
        lqp += conf.RPAREN() + "\n"
        lqp += terms_to_lqp(node.terms, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Atom):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('atom')} {to_lqp(node.name, 0, options)} {list_to_lqp(node.terms, 0, ' ', options)}{conf.RPAREN()}"

    elif isinstance(node, ir.Pragma):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('pragma')} :{conf.uname(node.name)} {terms_to_lqp(node.terms, 0, options)}{conf.RPAREN()}"

    elif isinstance(node, ir.Primitive):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('primitive')} :{conf.uname(node.name)} {list_to_lqp(node.terms, 0, ' ', options)}{conf.RPAREN()}"

    elif isinstance(node, ir.RelAtom):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('relatom')} :{node.name} {list_to_lqp(node.terms, 0, ' ', options)}{conf.RPAREN()}"

    elif isinstance(node, ir.Cast):
        lqp += ind + conf.LPAREN() + conf.kw("cast") + " " + type_to_lqp(node.type) + " " + to_lqp(node.input, 0, options) + " " + to_lqp(node.result, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.Var):
        lqp += ind + conf.uname(node.name)

    elif isinstance(node, str):
        lqp += f"{ind}\"{node}\""
    elif isinstance(node, ir.UInt128):
        lqp += f"{ind}{hex(node.value)}"
    elif isinstance(node, bool):
        lqp += ind + str(node).lower()
    elif isinstance(node, (int, float)):
        lqp += ind + str(node)

    elif isinstance(node, ir.Specialized):
        val_to_print = node.value
        if isinstance(val_to_print, str):
            lqp += f"{ind}#\"{val_to_print}\""
        elif isinstance(val_to_print, ir.UInt128):
            lqp += f"{ind}#{hex(val_to_print.value)}"
        elif isinstance(val_to_print, bool):
            lqp += f"{ind}#{str(val_to_print).lower()}"
        elif isinstance(val_to_print, (int, float)):
            lqp += f"{ind}#{val_to_print}"
        else:
            lqp += f"{ind}#{val_to_print}"

    elif isinstance(node, ir.Attribute):
        lqp += ind
        lqp += conf.LPAREN() + conf.kw("attribute") + " "
        lqp += ":" + node.name + " "
        lqp += list_to_lqp(node.args, 0, " ", options)
        lqp += conf.RPAREN()

    elif isinstance(node, ir.RelationId):
        name = id_to_name(options, node)
        lqp += f"{ind}{str(conf.uname(name))}"

    elif isinstance(node, ir.PrimitiveType):
        lqp += ind + node.name

    elif isinstance(node, ir.Write):
        # Delegate to the specific write type
        lqp += to_lqp(node.write_type, indent_level, options)

    elif isinstance(node, ir.Define):
        lqp += ind + conf.LPAREN() + conf.kw("define") + "\n" + to_lqp(node.fragment, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Undefine):
        lqp += ind + conf.LPAREN() + conf.kw("undefine") + " " + to_lqp(node.fragment_id, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.Context):
        lqp += ind + conf.LPAREN() + conf.kw("context") + " " + list_to_lqp(node.relations, 0, " ", options) + conf.RPAREN()

    elif isinstance(node, ir.FragmentId):
        lqp += f"{ind}:{conf.uname(node.id.decode())}"

    elif isinstance(node, ir.Read):
        # Delegate to the specific read type
        lqp += to_lqp(node.read_type, indent_level, options)

    elif isinstance(node, ir.Demand):
        lqp += ind + conf.LPAREN() + conf.kw("demand") + " " + to_lqp(node.relation_id, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.Output):
        name_str = f":{conf.uname(node.name)} " if node.name else ""
        lqp += ind + conf.LPAREN() + conf.kw("output") + " " + name_str + to_lqp(node.relation_id, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.Abort):
        name_str = f":{conf.uname(node.name)} " if node.name else ""
        lqp += ind + conf.LPAREN() + conf.kw("abort") + " " + name_str + to_lqp(node.relation_id, 0, options) + conf.RPAREN()

    elif isinstance(node, ir.WhatIf):
        branch_str = f":{conf.uname(node.branch)} " if node.branch else ""
        lqp += ind + conf.LPAREN() + conf.kw("what_if") + " " + branch_str + to_lqp(node.epoch, indent_level + 1, options) + conf.RPAREN()

    elif isinstance(node, ir.Epoch):
        # Epoch is handled within program_to_lqp, but might be called directly for WhatIf
        # This case should ideally not be hit directly by list_to_lqp for epoch.local_writes etc.
        # But if it is, it should print its contents.
        epoch_content = ""
        if len(node.persistent_writes) > 0:
            epoch_content += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("persistent_writes") + "\n"
            epoch_content += list_to_lqp(node.persistent_writes, indent_level + 2, "\n", options)
            epoch_content += conf.RPAREN() + "\n"

        if len(node.local_writes) > 0:
            epoch_content += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("local_writes") + "\n"
            epoch_content += list_to_lqp(node.local_writes, indent_level + 2, "\n", options)
            epoch_content += conf.RPAREN() + "\n"

        if len(node.reads) > 0:
            epoch_content += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("reads") + "\n"
            epoch_content += list_to_lqp(node.reads, indent_level + 2, "\n", options)
            epoch_content += conf.RPAREN() + "\n"
        lqp += ind + conf.LPAREN() + conf.kw("epoch") + "\n" + epoch_content + conf.RPAREN()

    elif isinstance(node, ir.Fragment):
        lqp += fragment_to_lqp(node, indent_level, options)

    else:
        raise NotImplementedError(f"to_lqp not implemented for {type(node)}.")

    return lqp

def fragment_to_lqp(node: ir.Fragment, indent_level: int, options: Dict = {}) -> str:
    conf = style_config(options)
    ind = conf.indentation(indent_level)
    declarations_portion = list_to_lqp(node.declarations, indent_level + 1, "\n", options)
    return \
        ind + conf.LPAREN() + conf.kw("fragment") + " " + to_lqp(node.id, 0, options) + "\n" + \
        declarations_portion + \
        conf.RPAREN()

def to_lqp_string(node: ir.LqpNode, options: Dict = {}) -> str:
    if isinstance(node, ir.Transaction):
        return program_to_lqp(node, options)
    elif isinstance(node, ir.Fragment):
        return fragment_to_lqp(node, 0, options)
    else:
        raise NotImplementedError(f"to_lqp_string not implemented for top-level node type {type(node)}.")

def type_to_lqp(node: ir.RelType) -> str:
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
