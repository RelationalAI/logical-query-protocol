import dataclasses

from abc import ABC, abstractmethod
from typing import Union, Sequence, Dict, List, Any

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

    def LPAREN(self, ): return f"{Style.DIM}({Style.RESET_ALL}"
    def RPAREN(self, ): return f"{Style.DIM}){Style.RESET_ALL}"

    def LBRACKET(self, ): return f"{Style.DIM}[{Style.RESET_ALL}"
    def RBRACKET(self, ): return f"{Style.DIM}]{Style.RESET_ALL}"

    def indentation(self, level: int) -> str:
        return self.SIND() * level

    def kw(self, x: str) -> str:
        return f"{Fore.YELLOW}{x}{Style.RESET_ALL}"

    def uname(self, x: str) -> str:
        return f"{Fore.WHITE}{x}{Style.RESET_ALL}"

    # Styled type annotation, e.g. ::INT.
    def type_anno(self, x: str) -> str:
        return f"{Style.DIM}{x}{Style.RESET_ALL}"

class PrettyOptions(Enum):
    STYLED = 1,
    PRINT_NAMES = 2,
    PRINT_DEBUG = 3,
    PRINT_CSV_FILENAME = 4  # Useful for snapshot testing with generated CSV filenames

    def __str__(self):
        return option_to_key[self]

option_to_key = {
    PrettyOptions.STYLED: "styled",
    PrettyOptions.PRINT_NAMES: "print_names",
    PrettyOptions.PRINT_DEBUG: "print_debug",
    PrettyOptions.PRINT_CSV_FILENAME: "print_csv_filename"
}

option_to_default = {
    PrettyOptions.STYLED: False,
    PrettyOptions.PRINT_NAMES: False,
    PrettyOptions.PRINT_DEBUG: True,
    PrettyOptions.PRINT_CSV_FILENAME: True
}

# Used for precise testing
ugly_config = {
    str(PrettyOptions.STYLED): False,
    str(PrettyOptions.PRINT_NAMES): False,
    str(PrettyOptions.PRINT_DEBUG): True,
    str(PrettyOptions.PRINT_CSV_FILENAME): True
}

# Used for humans
pretty_config = {
    str(PrettyOptions.STYLED): True,
    str(PrettyOptions.PRINT_NAMES): True,
    str(PrettyOptions.PRINT_DEBUG): False,
    str(PrettyOptions.PRINT_CSV_FILENAME): True
}

def style_config(options: Dict) -> StyleConfig:
    if has_option(options, PrettyOptions.STYLED):
        return Styled()
    else:
        return Unstyled()

# Call to_str on all nodes, each of which with indent_level, separating them
# by delim.
def list_to_str(nodes: Sequence[Union[ir.LqpNode, ir.Type, ir.Value, ir.SpecializedValue, int, str, float]], indent_level: int, delim: str, options: Dict, debug_info: Dict = {}) -> str:
    return delim.join(map(lambda n: to_str(n, indent_level, options, debug_info), nodes))

# Produces "(terms term1 term2 ...)" (all on one line) indented at indent_level.
def terms_to_str(terms: Sequence[Union[ir.RelTerm, ir.SpecializedValue]], indent_level: int, options: Dict, debug_info: Dict = {}) -> str:
    # Default to true for styled.
    conf = style_config(options)

    ind = conf.indentation(indent_level)

    lqp = ""
    if len(terms) == 0:
        lqp = f"{ind}{conf.LPAREN()}{conf.kw('terms')}{conf.RPAREN()}"
    else:
        lqp = f"{ind}{conf.LPAREN()}{conf.kw('terms')} {list_to_str(terms, 0, ' ', options, debug_info)}{conf.RPAREN()}"

    return lqp

# Produces
# { :key1 value1
#   :key2 value2
#   ... }
def config_dict_to_str(config: Dict[str, Any], indent_level: int, options: Dict) -> str:
    conf = style_config(options)
    ind = conf.indentation(indent_level)

    if len(config) == 0:
        return f"{ind}{{}}"

    config_str = ind + "{" + conf.SIND()[1:]
    for i, (k, v) in enumerate(sorted(config.items())):
        if i > 0:
            config_str += f"\n{ind}{conf.SIND()}"
        config_str += f":{str(k)} {to_str(v, 0, options)}"

    config_str += "}"

    return config_str

def program_to_str(node: ir.Transaction, options: Dict = {}) -> str:
    conf = style_config(options)
    s = conf.indentation(0) + conf.LPAREN() + conf.kw("transaction")

    config_dict: Dict[str, Union[str, int]] = {}
    config = node.configure
    config_dict["semantics_version"] = config.semantics_version
    if config.ivm_config.level != ir.MaintenanceLevel.UNSPECIFIED:
        config_dict["ivm.maintenance_level"] = config.ivm_config.level.name.lower()

    s += "\n" + conf.indentation(1) + conf.LPAREN() + conf.kw("configure") + "\n"
    s += config_dict_to_str(config_dict, 2, options)
    s += conf.RPAREN()

    if node.sync is not None:
        s += "\n" + conf.indentation(1) + conf.LPAREN() + conf.kw("sync")
        if len(node.sync.fragments) != 0:
            s += " " + list_to_str(node.sync.fragments, 0, " ", options)
        s += conf.RPAREN()

    for epoch in node.epochs:
        s += "\n" + conf.indentation(1) + conf.LPAREN() + conf.kw("epoch")
        section_strs: List[str] = []
        def build_section(keyword: str, items_list: Sequence[Union[ir.LqpNode, ir.Type, ir.Value, ir.SpecializedValue]], debug_info: Dict = {}) -> Union[str, None]:
            if not items_list:
                return None
            sec_s = "\n" + conf.indentation(2) + conf.LPAREN() + conf.kw(keyword) + "\n"
            sec_s += list_to_str(items_list, 3, "\n", options, debug_info) + conf.RPAREN()
            return sec_s
        writes_s = build_section("writes", epoch.writes)
        if writes_s: section_strs.append(writes_s)
        reads_s = build_section("reads", epoch.reads, _collect_debug_infos(node))
        if reads_s: section_strs.append(reads_s)
        s += "".join(section_strs)
        s += conf.RPAREN()
    s += conf.RPAREN()

    if has_option(options, PrettyOptions.PRINT_DEBUG):
        s += _debug_str(node)
    else:
        # Debug str already contains a trailing newline, so add one if we don't print debug
        s += "\n"

    return s

def _debug_str(node: ir.LqpNode) -> str:
    debug_infos = _collect_debug_infos(node)
    if len(debug_infos) != 0:
        debug_str: str = "\n\n"
        debug_str += ";; Debug information\n"
        debug_str += ";; -----------------------\n"
        debug_str += ";; Original names\n"
        for (rid, name) in debug_infos.items():
            debug_str += f";; \t ID `{rid.id}` -> `{name}`\n"
        return debug_str
    else: return ""

def _collect_debug_infos(node: ir.LqpNode) -> Dict[ir.RelationId, str]:
    debug_infos: Dict = {}
    if isinstance(node, ir.DebugInfo):
        debug_infos = node.id_to_orig_name | debug_infos
    else:
        if isinstance(node, ir.LqpNode):
            for field_info in dataclasses.fields(type(node)):
                debug_infos = _collect_debug_infos(getattr(node, field_info.name)) | debug_infos
        elif isinstance(node, (list, tuple)):
            for elt in node:
                debug_infos = _collect_debug_infos(elt) | debug_infos
    return debug_infos

def to_str(node: Union[ir.LqpNode, ir.Type, ir.Value, ir.SpecializedValue, int, str, float], indent_level: int, options: Dict = {}, debug_info: Dict = {}) -> str:
    conf = style_config(options)

    ind = conf.indentation(indent_level)
    lqp = ""

    if isinstance(node, ir.Def):
        lqp += ind + conf.LPAREN() + conf.kw("def") + " " + to_str(node.name, 0, options, debug_info) + "\n"
        lqp += to_str(node.body, indent_level + 1, options, debug_info)
        if len(node.attrs) == 0:
            lqp += f"{conf.RPAREN()}"
        else:
            lqp += "\n"
            lqp += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("attrs") + "\n"
            lqp += list_to_str(node.attrs, indent_level + 2, "\n", options, debug_info)
            lqp += f"{conf.RPAREN()}{conf.RPAREN()}"

    elif isinstance(node, ir.Constraint):
        if isinstance(node, ir.FunctionalDependency):
            lqp += ind + conf.LPAREN() + conf.kw("functional_dependency") + "\n"
            lqp += to_str(node.guard, indent_level + 1, options, debug_info) + "\n"
            lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("keys") + " " \
                + " ".join([to_str(var, 0, options, debug_info) for var in node.keys]) \
                + conf.RPAREN() + "\n"
            lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("values") + " " \
                + " ".join([to_str(var, 0, options, debug_info) for var in node.values]) \
                + conf.RPAREN() \
                + conf.RPAREN()
        else:
            raise NotImplementedError(f"to_str not implemented for constraint type {type(node)}.")

    elif isinstance(node, ir.Algorithm):
        lqp += ind + conf.LPAREN() + conf.kw("algorithm")
        # Print global_
        if len(node.global_) > 4:
            lqp += "\n"
            lqp += ind + conf.SIND() + list_to_str(node.global_, indent_level + 2, "\n", options, debug_info)
            lqp += "\n"
        else:
            lqp += " "
            lqp += list_to_str(node.global_, 0, " ", options, debug_info) + "\n"
        lqp += to_str(node.body, indent_level + 1, options, debug_info)
        lqp += conf.RPAREN()

    elif isinstance(node, ir.RelEDB):
        lqp += ind + conf.LPAREN() + conf.kw("rel_edb") + " " + to_str(node.target_id, 0, options, debug_info)
        lqp += " " + conf.LBRACKET()
        if len(node.path) > 0:
            lqp += list_to_str(node.path, 0, " ", options, debug_info)
        lqp += conf.RBRACKET()
        lqp += " " + conf.LBRACKET()
        if len(node.types) > 0:
            lqp += list_to_str(node.types, 0, " ", options, debug_info)
        lqp += conf.RBRACKET()
        lqp += conf.RPAREN()

    elif isinstance(node, ir.BeTreeRelation):
        lqp += ind + conf.LPAREN() + conf.kw("betree_relation") + " " + to_str(node.name, 0, options, debug_info) + "\n"
        lqp += to_str(node.relation_info, indent_level + 1, options, debug_info)
        lqp += conf.RPAREN()

    elif isinstance(node, ir.BeTreeInfo):
        lqp += ind + conf.LPAREN() + conf.kw("betree_info") + "\n"
        # Print key_types
        lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("key_types")
        if len(node.key_types) > 0:
            lqp += " " + list_to_str(node.key_types, 0, " ", options, debug_info)
        lqp += conf.RPAREN() + "\n"
        # Print value_types
        lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("value_types")
        if len(node.value_types) > 0:
            lqp += " " + list_to_str(node.value_types, 0, " ", options, debug_info)
        lqp += conf.RPAREN() + "\n"
        # Print config_dict combining storage_config and relation_locator
        config_dict: dict[str, Any] = {}
        config_dict['betree_config_epsilon'] = node.storage_config.epsilon
        config_dict['betree_config_max_pivots'] = node.storage_config.max_pivots
        config_dict['betree_config_max_deltas'] = node.storage_config.max_deltas
        config_dict['betree_config_max_leaf'] = node.storage_config.max_leaf
        # Handle oneof: only print the location field that is set
        if node.relation_locator.root_pageid is not None:
            config_dict['betree_locator_root_pageid'] = node.relation_locator.root_pageid
        if node.relation_locator.inline_data is not None:
            # Convert bytes back to string for printing
            inline_data_str = node.relation_locator.inline_data.decode('utf-8')
            config_dict['betree_locator_inline_data'] = inline_data_str
        config_dict['betree_locator_element_count'] = node.relation_locator.element_count
        config_dict['betree_locator_tree_height'] = node.relation_locator.tree_height
        lqp += config_dict_to_str(config_dict, indent_level + 1, options)
        lqp += conf.RPAREN()

    elif isinstance(node, ir.CSVData):
        lqp += ind + conf.LPAREN() + conf.kw("csv_data") + "\n"
        lqp += to_str(node.locator, indent_level + 1, options, debug_info) + "\n"
        lqp += to_str(node.config, indent_level + 1, options, debug_info) + "\n"
        # Print columns
        lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("columns") + "\n"
        lqp += list_to_str(node.columns, indent_level + 2, "\n", options, debug_info)
        lqp += conf.RPAREN() + "\n"
        # Print asof
        lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("asof") + " " + to_str(node.asof, 0, options, debug_info) + conf.RPAREN()
        lqp += conf.RPAREN()

    elif isinstance(node, ir.CSVLocator):
        lqp += ind + conf.LPAREN() + conf.kw("csv_locator") + "\n"
        # Print paths or inline_data (mutually exclusive)
        if node.paths:
            lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("paths")
            if len(node.paths) > 0:
                lqp += " " + list_to_str(node.paths, 0, " ", options, debug_info)
            lqp += conf.RPAREN()
        elif node.inline_data is not None:
            # Convert bytes back to string for printing
            inline_data_str = node.inline_data.decode('utf-8')
            lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("inline_data") + " " + to_str(inline_data_str, 0, options, debug_info) + conf.RPAREN()
        lqp += conf.RPAREN()

    elif isinstance(node, ir.CSVConfig):
        config_dict: dict[str, Any] = {}
        # Always include all config values
        config_dict['csv_header_row'] = node.header_row
        config_dict['csv_skip'] = node.skip
        if node.new_line != '':
            config_dict['csv_new_line'] = node.new_line
        config_dict['csv_delimiter'] = node.delimiter
        config_dict['csv_quotechar'] = node.quotechar
        config_dict['csv_escapechar'] = node.escapechar
        if node.comment != '':
            config_dict['csv_comment'] = node.comment
        if node.missing_strings:
            # For lists, we only support single string values in config dicts for now
            # If there's only one missing string, output it as a single string
            # Otherwise, we'll need to output just the first one (this is a limitation)
            if len(node.missing_strings) == 1:
                config_dict['csv_missing_strings'] = node.missing_strings[0]
            else:
                # For multiple missing strings, join them or just use first
                # This is a temporary workaround - we may need a better solution
                config_dict['csv_missing_strings'] = node.missing_strings[0]
        config_dict['csv_decimal_separator'] = node.decimal_separator
        config_dict['csv_encoding'] = node.encoding
        config_dict['csv_compression'] = node.compression

        lqp += ind + conf.LPAREN() + conf.kw("csv_config")
        if len(config_dict) > 0:
            lqp += "\n"
        lqp += config_dict_to_str(config_dict, indent_level + 1, options)
        lqp += conf.RPAREN()

    elif isinstance(node, ir.CSVColumn):
        lqp += ind + conf.LPAREN() + conf.kw("column") + " "
        lqp += to_str(node.column_name, 0, options, debug_info) + " "
        lqp += to_str(node.target_id, 0, options, debug_info)
        lqp += " " + conf.LBRACKET()
        if len(node.types) > 0:
            lqp += list_to_str(node.types, 0, " ", options, debug_info)
        lqp += conf.RBRACKET()
        lqp += conf.RPAREN()

    elif isinstance(node, ir.Script):
        lqp += ind + conf.LPAREN() + conf.kw("script") + "\n"
        lqp += list_to_str(node.constructs, indent_level + 1, "\n", options, debug_info)
        lqp += conf.RPAREN()

    elif isinstance(node, ir.Loop):
        lqp += ind + conf.LPAREN() + conf.kw("loop") + "\n"
        lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("init")
        if len(node.init) > 0:
            lqp += "\n"
            lqp += list_to_str(node.init, indent_level + 2, "\n", options, debug_info)
        lqp += conf.RPAREN() + "\n"
        lqp += to_str(node.body, indent_level + 1, options, debug_info)
        lqp += conf.RPAREN()

    elif isinstance(node, (ir.Assign, ir.Break)):
        if isinstance(node, ir.Assign):
            s = "assign"
        elif isinstance(node, ir.Break):
            s = "break"
        lqp += ind + conf.LPAREN() + conf.kw(s) + " " + to_str(node.name, 0, options, debug_info) + "\n"
        lqp += to_str(node.body, indent_level + 1, options, debug_info)
        if len(node.attrs) == 0:
            lqp += f"{conf.RPAREN()}"
        else:
            lqp += "\n"
            lqp += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("attrs") + "\n"
            lqp += list_to_str(node.attrs, indent_level + 2, "\n", options, debug_info)
            lqp += f"{conf.RPAREN()}{conf.RPAREN()}"

    elif isinstance(node, ir.Upsert):
        lqp += ind + conf.LPAREN() + conf.kw("upsert") + " " + to_str(node.name, 0, options, debug_info) + "\n"
        body = node.body
        if node.value_arity == 0:
            lqp += to_str(body, indent_level + 1, options, debug_info)
        else: # We need a different printing mechanism
            partition = len(body.vars)-node.value_arity
            lvars, rvars = body.vars[:partition], body.vars[partition:]
            lqp += ind + conf.indentation(1) + conf.LPAREN() + conf.LBRACKET()
            lqp += " ".join(map(lambda v: conf.uname(v[0].name) \
                    + conf.type_anno("::") + to_str(v[1], indent_level + 2, options, debug_info), lvars))
            lqp += " | "
            lqp += " ".join(map(lambda v: conf.uname(v[0].name) \
                    + conf.type_anno("::") + to_str(v[1], indent_level + 2, options, debug_info), rvars))
            lqp += conf.RBRACKET() + "\n"
            lqp += f"{to_str(body.value, indent_level + 2, options, debug_info)}{conf.RPAREN()}"
        if len(node.attrs) == 0:
            lqp += f"{conf.RPAREN()}"
        else:
            lqp += "\n"
            lqp += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("attrs") + "\n"
            lqp += list_to_str(node.attrs, indent_level + 2, "\n", options, debug_info)
            lqp += f"{conf.RPAREN()}{conf.RPAREN()}"

    elif isinstance(node, (ir.MonoidDef, ir.MonusDef)):
        s = "monoid" if isinstance(node, ir.MonoidDef) else "monus"
        lqp += ind + conf.LPAREN() + conf.kw(s) + " " \
                + to_str(node.monoid, 0, options, debug_info) + " " \
                + to_str(node.name, 0, options, debug_info) + "\n"
        body = node.body
        if node.value_arity == 0:
            lqp += to_str(body, indent_level + 1, options, debug_info)
        else:
            partition = len(body.vars)-node.value_arity
            lvars, rvars = body.vars[:partition], body.vars[partition:]
            lqp += ind + conf.indentation(1) + conf.LPAREN() + conf.LBRACKET()
            lqp += " ".join(map(lambda v: conf.uname(v[0].name) \
                    + conf.type_anno("::") + to_str(v[1], indent_level + 2, options, debug_info), lvars))
            lqp += " | "
            lqp += " ".join(map(lambda v: conf.uname(v[0].name) \
                    + conf.type_anno("::") + to_str(v[1], indent_level + 2, options, debug_info), rvars))
            lqp += conf.RBRACKET() + "\n"
            lqp += f"{to_str(body.value, indent_level + 2, options, debug_info)}{conf.RPAREN()}"
        if len(node.attrs) == 0:
            lqp += f"{conf.RPAREN()}"
        else:
            lqp += "\n"
            lqp += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("attrs") + "\n"
            lqp += list_to_str(node.attrs, indent_level + 2, "\n", options, debug_info)
            lqp += f"{conf.RPAREN()}{conf.RPAREN()}"

    elif isinstance(node, ir.OrMonoid):
        lqp += "BOOL::OR"

    elif isinstance(node, ir.MinMonoid):
        lqp += to_str(node.type, 0, options, debug_info) + "::MIN"

    elif isinstance(node, ir.MaxMonoid):
        lqp += to_str(node.type, 0, options, debug_info) + "::MAX"

    elif isinstance(node, ir.SumMonoid):
        lqp += to_str(node.type, 0, options, debug_info) + "::SUM"

    elif isinstance(node, ir.Type):
        if len(node.parameters) == 0:
            lqp += conf.type_anno(str(node.type_name))
        else:
            lqp += conf.LPAREN() + conf.type_anno(str(node.type_name)) + " "
            lqp += " ".join([to_str(x, 0, options, debug_info) for x in node.parameters])
            lqp += conf.RPAREN()
    elif isinstance(node, ir.Abstraction):
        lqp += ind + conf.LPAREN() + conf.LBRACKET()
        lqp += " ".join(map(lambda v: conf.uname(v[0].name) \
                + conf.type_anno("::") + to_str(v[1], indent_level + 1, options, debug_info), node.vars))
        lqp += conf.RBRACKET() + "\n"
        lqp += f"{to_str(node.value, indent_level + 1, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Exists):
        lqp += ind + conf.LPAREN() + conf.kw("exists") + " " + conf.LBRACKET()
        lqp += " ".join(map(lambda v: conf.uname(v[0].name) \
                + conf.type_anno("::") + to_str(v[1], indent_level + 1, options, debug_info), node.body.vars))
        lqp += conf.RBRACKET() + "\n"
        lqp += to_str(node.body.value, indent_level + 1, options, debug_info) + conf.RPAREN()

    elif isinstance(node, ir.Reduce):
        lqp += ind + conf.LPAREN() + conf.kw("reduce") + "\n"
        lqp += to_str(node.op, indent_level + 1, options, debug_info) + "\n"
        lqp += to_str(node.body, indent_level + 1, options, debug_info) + "\n"
        lqp += f"{terms_to_str(node.terms, indent_level + 1, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Conjunction):
        if len(node.args) == 0:
            lqp += ind + conf.LPAREN() + conf.kw("and") + conf.RPAREN()
        else:
            lqp += ind + conf.LPAREN() + conf.kw("and") + "\n"
            lqp += list_to_str(node.args, indent_level + 1, "\n", options, debug_info) + conf.RPAREN()

    elif isinstance(node, ir.Disjunction):
        if len(node.args) == 0:
            lqp += ind + conf.LPAREN() + conf.kw("or") + conf.RPAREN()
        else:
            lqp += ind + conf.LPAREN() + conf.kw("or") + "\n"
            lqp += list_to_str(node.args, indent_level + 1, "\n", options, debug_info) + conf.RPAREN()

    elif isinstance(node, ir.Not):
        lqp += ind + conf.LPAREN() + conf.kw("not") + "\n"
        lqp += f"{to_str(node.arg, indent_level + 1, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.FFI):
        lqp += ind + conf.LPAREN() + conf.kw("ffi") + " " + ":" + node.name + "\n"
        lqp += ind + conf.SIND() + conf.LPAREN() + conf.kw("args") + "\n"
        lqp += list_to_str(node.args, indent_level + 2, "\n", options, debug_info)
        lqp += conf.RPAREN() + "\n"
        lqp += f"{terms_to_str(node.terms, indent_level + 1, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Atom):
        if len(node.terms) > 4:
            lqp += f"{ind}{conf.LPAREN()}{conf.kw('atom')} {to_str(node.name, 0, options, debug_info)}\n"
            lqp += list_to_str(node.terms, indent_level + 1, "\n", options, debug_info) + conf.RPAREN()
        else:
            lqp += f"{ind}{conf.LPAREN()}{conf.kw('atom')} {to_str(node.name, 0, options, debug_info)} {list_to_str(node.terms, 0, ' ', options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Pragma):
        terms = f"{list_to_str(node.terms, 0, ' ', options, debug_info)}"
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('pragma')} :{conf.uname(node.name)} {terms}{conf.RPAREN()}"

    elif isinstance(node, ir.Primitive):
        if len(node.terms) > 4:
            lqp += f"{ind}{conf.LPAREN()}{conf.kw('primitive')} :{conf.uname(node.name)}\n"
            lqp += list_to_str(node.terms, indent_level + 1, "\n", options, debug_info) + conf.RPAREN()
        else:
            lqp += f"{ind}{conf.LPAREN()}{conf.kw('primitive')} :{conf.uname(node.name)} {list_to_str(node.terms, 0, ' ', options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.RelAtom):
        if len(node.terms) > 4:
            lqp += f"{ind}{conf.LPAREN()}{conf.kw('relatom')} :{node.name}\n"
            lqp += list_to_str(node.terms, indent_level + 1, "\n", options, debug_info) + conf.RPAREN()
        else:
            lqp += f"{ind}{conf.LPAREN()}{conf.kw('relatom')} :{node.name} {list_to_str(node.terms, 0, ' ', options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Cast):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('cast')} {to_str(node.input, 0, options, debug_info)} {to_str(node.result, 0, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Var):
        lqp += f"{ind}{conf.uname(node.name)}"

    elif isinstance(node, ir.Value):
        lqp += to_str(node.value, indent_level, options, debug_info)

    elif isinstance(node, str):
        lqp += ind + "\"" + node.encode('unicode_escape').replace(b'"', b'\\"').decode() + "\""
    elif isinstance(node, ir.UInt128Value):
        lqp += f"{ind}{hex(node.value)}"
    elif isinstance(node, ir.Int128Value):
        lqp += f"{ind}{node.value}i128"
    elif isinstance(node, ir.MissingValue):
        lqp += f"{ind}missing"
    elif isinstance(node, ir.DecimalValue):
        _, _, exponent = node.value.as_tuple()
        assert isinstance(exponent, int)
        # Format the decimal to have the correct scale
        lqp += f"{ind}{node.value:.{node.scale}f}d{node.precision}"
    elif isinstance(node, ir.DateValue):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('date')} {node.value.year} {node.value.month} {node.value.day}{conf.RPAREN()}"
    elif isinstance(node, ir.DateTimeValue):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('datetime')} {node.value.year} {node.value.month} {node.value.day} {node.value.hour} {node.value.minute} {node.value.second} {node.value.microsecond}{conf.RPAREN()}"

    elif isinstance(node, (int, float)):
        lqp += f"{ind}{str(node)}"

    elif isinstance(node, ir.BooleanValue):
        if node.value:
            lqp += f"{ind}true"
        else:
            lqp += f"{ind}false"

    elif isinstance(node, ir.SpecializedValue):
        lqp += "#" + to_str(node.value, 0, {}, {})

    elif isinstance(node, ir.Attribute):
        args_str = list_to_str(node.args, 0, ' ', options, debug_info)
        space = " " if args_str else ""
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('attribute')} :{node.name}{space}{args_str}{conf.RPAREN()}"

    elif isinstance(node, ir.RelationId):
        name = id_to_name(options, debug_info, node)
        lqp += f"{ind}{str(conf.uname(name))}"

    elif isinstance(node, ir.Write):
        # Delegate to the specific write type
        lqp += to_str(node.write_type, indent_level, options, debug_info)

    elif isinstance(node, ir.Define):
        lqp += ind + conf.LPAREN() + conf.kw("define") + "\n" + to_str(node.fragment, indent_level + 1, options, debug_info) + conf.RPAREN()

    elif isinstance(node, ir.Undefine):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('undefine')} {to_str(node.fragment_id, 0, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Context):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('context')} {list_to_str(node.relations, 0, ' ', options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.FragmentId):
        lqp += f"{ind}:{conf.uname(node.id.decode())}"

    elif isinstance(node, ir.Read):
        # Delegate to the specific read type
        lqp += to_str(node.read_type, indent_level, options, debug_info)

    elif isinstance(node, ir.Demand):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('demand')} {to_str(node.relation_id, 0, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Output):
        name_str = f":{conf.uname(node.name)} " if node.name else ""
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('output')} {name_str}{to_str(node.relation_id, 0, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Export):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('export')}\n{to_str(node.config, indent_level + 1, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.ExportCSVConfig):
        def line(kw: str, body: str) -> str:
            return f"{ind}{conf.SIND()}{conf.LPAREN()}{conf.kw(kw)} {body}{conf.RPAREN()}"

        def line_conf_f(kw: str, field: Union[int, str]) -> str:
            return line(kw, to_str(field, 0, options, debug_info))

        lqp += f"{ind}{conf.LPAREN()}{conf.kw('export_csv_config')}\n"

        if has_option(options, PrettyOptions.PRINT_CSV_FILENAME):
            lqp += line_conf_f('path', node.path) + "\n"
        else:
            lqp += line_conf_f('path', '<hidden filename>') + "\n"
        lqp += line('columns', list_to_str(node.data_columns, 0, " ", options, debug_info)) + "\n"

        config_dict: dict[str, Any] = {}
        config_dict['partition_size'] = node.partition_size if node.partition_size is not None else 0
        config_dict['compression'] = node.compression if node.compression is not None else "" #type: ignore
        config_dict['syntax_header_row'] = node.syntax_header_row if node.syntax_header_row is not None else 1
        config_dict['syntax_missing_string'] = node.syntax_missing_string if node.syntax_missing_string is not None else "" #type: ignore
        config_dict['syntax_delim'] = node.syntax_delim if node.syntax_delim is not None else "," #type: ignore
        config_dict['syntax_quotechar'] = node.syntax_quotechar if node.syntax_quotechar is not None else '"' #type: ignore
        config_dict['syntax_escapechar'] = node.syntax_escapechar if node.syntax_escapechar is not None else '\\' #type: ignore

        lqp += config_dict_to_str(config_dict, indent_level + 1, options) #type: ignore
        lqp += f"{conf.RPAREN()}"

    elif isinstance(node, ir.ExportCSVColumn):
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('column')} {to_str(node.column_name, 0, options, debug_info)} {to_str(node.column_data, 0, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Abort):
        name_str = f":{conf.uname(node.name)} " if node.name else ""
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('abort')} {name_str}{to_str(node.relation_id, 0, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.WhatIf):
        branch_str = f":{conf.uname(node.branch)} " if node.branch else ""
        lqp += f"{ind}{conf.LPAREN()}{conf.kw('what_if')} {branch_str}{to_str(node.epoch, indent_level + 1, options, debug_info)}{conf.RPAREN()}"

    elif isinstance(node, ir.Epoch):
        # Epoch is handled within program_to_str, but might be called directly for WhatIf
        # This case should ideally not be hit directly by list_to_str for epoch.local_writes etc.
        # But if it is, it should print its contents.
        epoch_content = ""
        if len(node.writes) > 0:
            epoch_content += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("writes") + "\n"
            epoch_content += list_to_str(node.writes, indent_level + 2, "\n", options, debug_info)
            epoch_content += conf.RPAREN() + "\n"
        if len(node.reads) > 0:
            epoch_content += conf.indentation(indent_level + 1) + conf.LPAREN() + conf.kw("reads") + "\n"
            epoch_content += list_to_str(node.reads, indent_level + 2, "\n", options, debug_info)
            epoch_content += conf.RPAREN() + "\n"
        lqp += ind + conf.LPAREN() + conf.kw("epoch") + "\n" + epoch_content + conf.RPAREN()

    elif isinstance(node, ir.Fragment):
        lqp += fragment_to_str(node, indent_level, debug_info, options)

    else:
        raise NotImplementedError(f"to_str not implemented for {type(node)}.")

    return lqp

def fragment_to_str(node: ir.Fragment, indent_level: int, debug_info: Dict, options: Dict = {}) -> str:
    conf = style_config(options)
    ind = conf.indentation(indent_level)
    debug_info = node.debug_info.id_to_orig_name | debug_info
    declarations_portion = list_to_str(node.declarations, indent_level + 1, "\n", options, debug_info)
    return \
        ind + conf.LPAREN() + conf.kw("fragment") + " " + to_str(node.id, 0, options, debug_info) + "\n" + \
        declarations_portion + \
        conf.RPAREN()

def to_string(node: ir.LqpNode, options: Dict = {}) -> str:
    if isinstance(node, ir.Transaction):
        return program_to_str(node, options)
    elif isinstance(node, ir.Fragment):
        return fragment_to_str(node, 0, {}, options)
    else:
        raise NotImplementedError(f"to_string not implemented for top-level node type {type(node)}.")

def id_to_name(options: Dict, debug_info: Dict, rid: ir.RelationId) -> str:
    if not has_option(options, PrettyOptions.PRINT_NAMES):
        return f"{rid.id}"
    if len(debug_info) == 0:
        return f"{rid.id}"
    if rid not in debug_info:
        # The relation ID may be missing from the debug info if it was never defined. But it
        # is still valid and should be treated as empty.
        return f"{rid.id}"
    return ":"+debug_info.get(rid, "")

def has_option(options: Dict, opt: PrettyOptions) -> bool:
    return options.get(option_to_key[opt], option_to_default[opt])
