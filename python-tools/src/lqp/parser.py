"""
Lark-based parser for LQP S-expressions.

This module contains the grammar, parser, and transformer that converts
parse trees to IR nodes.
"""

import hashlib
from lark import Lark, Transformer, v_args
import lqp.ir as ir
from decimal import Decimal
from datetime import date, datetime

grammar = """
start: transaction | fragment

transaction: "(transaction" configure? sync? epoch* ")"
configure: "(configure" config_dict ")"
sync: "(sync" fragment_id* ")"
epoch: "(epoch" writes? reads? ")"
writes: "(writes" write* ")"
reads: "(reads" read* ")"

write: define | undefine | context
define: "(define" fragment ")"
undefine: "(undefine" fragment_id ")"
context: "(context" relation_id* ")"

read: demand | output | export | abort
demand: "(demand" relation_id ")"
output: "(output" name? relation_id ")"
export: "(export" export_csv_config ")"
abort: "(abort" name? relation_id ")"

export_csv_config: "(export_csv_config" export_path export_columns config_dict ")"

export_columns: "(columns" export_column* ")"
export_column: "(column" STRING relation_id ")"
export_path: "(path" STRING ")"

fragment: "(fragment" fragment_id declaration* ")"

declaration: def_ | algorithm | constraint | data

data: csv_data | betree_relation | rel_edb

// CSV Data
csv_data: "(csv_data" csv_locator csv_config csv_columns csv_asof ")"
csv_locator: "(csv_locator" csv_locator_content ")"
csv_locator_content: csv_paths | csv_inline_data
csv_paths: "(paths" STRING* ")"
csv_inline_data: "(inline_data" STRING ")"
csv_config: "(csv_config" config_dict ")"
csv_columns: "(columns" csv_column* ")"
csv_column: "(column" STRING relation_id type_list ")"
csv_asof: "(asof" STRING ")"
type_list: "[" type_* "]"

// BeTree Relation
betree_relation: "(betree_relation" relation_id betree_info ")"
betree_info: "(betree_info" betree_key_types betree_value_types config_dict ")"
betree_key_types: "(key_types" type_* ")"
betree_value_types: "(value_types" type_* ")"

// Rel EDB (Base Relation Path)
rel_edb: "(rel_edb" relation_id string_list type_list ")"
string_list: "[" STRING* "]"
def_: "(def" relation_id abstraction attrs? ")"

constraint: functional_dependency
functional_dependency: "(functional_dependency" abstraction fd_keys fd_values ")"
fd_keys: "(keys" var* ")"
fd_values: "(values" var* ")"

algorithm: "(algorithm" relation_id* script ")"
script: "(script" construct* ")"

construct: loop | instruction
loop: "(loop" init script ")"
init: "(init" instruction* ")"

instruction: assign | upsert | break_ | monoid_def | monus_def

assign : "(assign" relation_id abstraction attrs? ")"
upsert : "(upsert" relation_id abstraction attrs? ")"
break_ : "(break" relation_id abstraction attrs? ")"
monoid_def : "(monoid" monoid relation_id abstraction attrs? ")"
monus_def : "(monus" monoid relation_id abstraction attrs? ")"

monoid : or_monoid | min_monoid | max_monoid | sum_monoid
or_monoid : "(or)"
min_monoid : "(min" type_ ")"
max_monoid : "(max" type_ ")"
sum_monoid : "(sum" type_ ")"

abstraction: "(" bindings formula ")"
bindings: "[" left_bindings ("|" right_bindings)? "]"
left_bindings: binding*
right_bindings: binding*
binding: SYMBOL "::" type_

formula: exists | reduce | conjunction | disjunction | not_ | ffi | atom | pragma | primitive | true | false | relatom | cast
exists: "(exists" bindings formula ")"
reduce: "(reduce" abstraction abstraction terms ")"
conjunction: "(and" formula* ")"
disjunction: "(or" formula* ")"
not_: "(not" formula ")"
ffi: "(ffi" name args terms ")"
atom: "(atom" relation_id term* ")"
relatom: "(relatom" name relterm* ")"
cast: "(cast" term term ")"
pragma: "(pragma" name  term* ")"
true: "(true)"
false: "(false)"

args: "(args" abstraction* ")"
terms: "(terms" term* ")"

primitive: raw_primitive | eq | lt | lt_eq | gt | gt_eq | add | minus | multiply | divide
raw_primitive: "(primitive" name relterm* ")"
eq: "(=" term term ")"
lt: "(<" term term ")"
lt_eq: "(<=" term term ")"
gt: "(>" term term ")"
gt_eq: "(>=" term term ")"

add: "(+" term term term ")"
minus: "(-" term term term ")"
multiply: "(*" term term term ")"
divide: "(/" term term term ")"

relterm: specialized_value | term
term: var | constant
specialized_value: "#" value
var: SYMBOL
constant: value

attrs: "(attrs" attribute* ")"
attribute: "(attribute" name constant* ")"

fragment_id: ":" SYMBOL
relation_id: (":" SYMBOL) | NUMBER
name: ":" SYMBOL

value: STRING | NUMBER | FLOAT | UINT128 | INT128
     | date | datetime | MISSING | DECIMAL | BOOLEAN

type_ : TYPE_NAME | "(" TYPE_NAME value* ")"

TYPE_NAME.3: "STRING" | "INT" | "FLOAT" | "UINT128" | "INT128"
           | "DATE" | "DATETIME" | "MISSING" | "DECIMAL" | "BOOLEAN"

SYMBOL: /[a-zA-Z_][a-zA-Z0-9_.-]*/
MISSING.1: "missing" // Set a higher priority so so it's MISSING instead of SYMBOL
STRING: ESCAPED_STRING
NUMBER: /[-]?\\d+/
INT128: /[-]?\\d+i128/
UINT128: /0x[0-9a-fA-F]+/
FLOAT.1: /[-]?\\d+\\.\\d+/ | "inf" | "nan"
DECIMAL.2: /[-]?\\d+\\.\\d+d\\d+/
BOOLEAN.1: "true" | "false" // Set a higher priority so it's BOOLEAN instead of SYMBOL
date: "(date" NUMBER NUMBER NUMBER ")"
datetime: "(datetime" NUMBER NUMBER NUMBER NUMBER NUMBER NUMBER NUMBER? ")"

config_dict: "{" config_key_value* "}"
config_key_value: ":" SYMBOL value

COMMENT: /;;.*/  // Matches ;; followed by any characters except newline
%ignore /\\s+/
%ignore COMMENT
%import common.ESCAPED_STRING -> ESCAPED_STRING
"""

def construct_configure(config_dict, meta):
    """Construct a Configure IR node from config dictionary."""
    # Construct IVMConfig
    maintenance_level_value = config_dict.get("ivm.maintenance_level")
    if maintenance_level_value:
        maintenance_level = getattr(ir.MaintenanceLevel, maintenance_level_value.value.upper())
    else:
        maintenance_level = ir.MaintenanceLevel.OFF
    ivm_config = ir.IVMConfig(level=maintenance_level, meta=meta)

    # Construct Configure
    semantics_version_value = config_dict.get("semantics_version")
    if semantics_version_value:
        semantics_version = semantics_version_value.value
    else:
        semantics_version = 0

    return ir.Configure(
        semantics_version=semantics_version,
        ivm_config=ivm_config,
        meta=meta,
    )

def desugar_to_raw_primitive(name, terms):
    """Convert primitive operators to raw primitive IR nodes."""
    return ir.Primitive(name=name, terms=terms, meta=None)


@v_args(meta=True)
class LQPTransformer(Transformer):
    """Transformer that converts Lark parse tree to LQP IR nodes."""

    def __init__(self, file: str):
        self.file = file
        self.id_to_debuginfo = {}
        self._current_fragment_id = None

    def meta(self, meta):
        return ir.SourceInfo(file=self.file, line=meta.line, column=meta.column)

    def start(self, meta, items):
        return items[0]

    def TYPE_NAME(self, s):
        return getattr(ir.TypeName, s.upper())

    def type_(self, meta, items):
        return ir.Type(type_name=items[0], parameters=items[1:],  meta=self.meta(meta))

    #
    # Transactions
    #
    def transaction(self, meta, items):
        if isinstance(items[0], ir.Configure):
            configure = items[0]
            if isinstance(items[1], ir.Sync):
                sync = items[1]
                epochs = items[2:]
            else:
                sync = None
                epochs = items[1:]
        elif isinstance(items[0], ir.Sync):
            configure = construct_configure({}, self.meta(meta))
            sync = items[0]
            epochs = items[1:]
        else:
            configure = construct_configure({}, self.meta(meta))
            sync = None
            epochs = items

        return ir.Transaction(configure=configure, epochs=epochs, sync=sync, meta=self.meta(meta))

    def configure(self, meta, items):
        return construct_configure(items[0], self.meta(meta))

    def epoch(self, meta, items):
        kwargs = {k: v for k, v in items if v}
        return ir.Epoch(**kwargs, meta=self.meta(meta))

    def writes(self, meta, items):
        return ("writes", items)

    def reads(self, meta, items):
        return ("reads", items)

    def write(self, meta, items):
        return ir.Write(write_type=items[0], meta=self.meta(meta))

    def define(self, meta, items):
        return ir.Define(fragment=items[0], meta=self.meta(meta))

    def undefine(self, meta, items):
        return ir.Undefine(fragment_id=items[0], meta=self.meta(meta))

    def context(self, meta, items):
        return ir.Context(relations=items, meta=self.meta(meta))

    def sync(self, meta, items):
        return ir.Sync(fragments=items, meta=self.meta(meta))

    def read(self, meta, items):
        return ir.Read(read_type=items[0], meta=self.meta(meta))

    def demand(self, meta, items):
        return ir.Demand(relation_id=items[0], meta=self.meta(meta))

    def output(self, meta, items):
        if len(items) == 1:
            return ir.Output(name=None, relation_id=items[0], meta=self.meta(meta))
        return ir.Output(name=items[0], relation_id=items[1], meta=self.meta(meta))

    def export(self, meta, items):
        return ir.Export(config=items[0], meta=self.meta(meta))

    def export_csv_config(self, meta, items):
        assert len(items) >= 2, "Export config must have at least columns and path"

        export_fields = {}
        for i in items[2:]:
            assert isinstance(i, dict)
            for k, v in i.items():
                export_fields[k] = v.value

        return ir.ExportCSVConfig(
            path=items[0],
            data_columns=items[1],
            **export_fields,
            meta=self.meta(meta)
        )

    def export_columns(self, meta, items):
        return items

    def export_column(self, meta, items):
        return ir.ExportCSVColumn(
            column_name=items[0],
            column_data=items[1],
            meta=self.meta(meta)
        )

    def export_path(self, meta, items):
        return items[0]

    def abort(self, meta, items):
        if len(items) == 1:
            return ir.Abort(name=None, relation_id=items[0], meta=self.meta(meta))
        return ir.Abort(name=items[0], relation_id=items[1], meta=self.meta(meta))

    #
    # Logic
    #
    def fragment(self, meta, items):
        fragment_id = items[0]
        debug_info = ir.DebugInfo(id_to_orig_name=dict(self.id_to_debuginfo[fragment_id]), meta=self.meta(meta))
        self._current_fragment_id = None
        return ir.Fragment(id=fragment_id, declarations=items[1:], debug_info=debug_info, meta=self.meta(meta))

    def fragment_id(self, meta, items):
        fragment_id = ir.FragmentId(id=items[0].encode(), meta=self.meta(meta))
        self._current_fragment_id = fragment_id
        if fragment_id not in self.id_to_debuginfo:
            self.id_to_debuginfo[fragment_id] = {}
        return fragment_id

    def declaration(self, meta, items):
        return items[0]

    def def_(self, meta, items):
        name = items[0]
        body, value_arity = items[1]
        assert value_arity == 0, f"Defs should not have a value arity"
        attrs = items[2] if len(items) > 2 else []
        return ir.Def(name=name, body=body, attrs=attrs, meta=self.meta(meta))

    def constraint(self, meta, items):
        return items[0]

    def functional_dependency(self, meta, items):
        guard, _ = items[0]
        keys = items[1]
        values = items[2]
        return ir.FunctionalDependency(
            guard=guard,
            keys=keys,
            values=values,
            meta=self.meta(meta)
        )

    def fd_keys(self, meta, items):
        return items

    def fd_values(self, meta, items):
        return items

    #
    # Data declarations
    #
    def data(self, meta, items):
        return items[0]

    def csv_data(self, meta, items):
        locator = items[0]
        config = items[1]
        columns = items[2]
        asof = items[3]
        return ir.CSVData(locator=locator, config=config, columns=columns, asof=asof, meta=self.meta(meta))

    def csv_locator(self, meta, items):
        return items[0]

    def csv_locator_content(self, meta, items):
        return items[0]

    def csv_paths(self, meta, items):
        return ir.CSVLocator(paths=items, inline_data=None, meta=self.meta(meta))

    def csv_inline_data(self, meta, items):
        return ir.CSVLocator(paths=[], inline_data=items[0].encode(), meta=self.meta(meta))

    def csv_config(self, meta, items):
        config_dict = items[0] if items else {}
        return ir.CSVConfig(
            header_row=config_dict.get('csv_header_row', ir.Value(value=1, meta=None)).value if 'csv_header_row' in config_dict else 1,
            skip=config_dict.get('csv_skip', ir.Value(value=0, meta=None)).value if 'csv_skip' in config_dict else 0,
            new_line=config_dict.get('csv_new_line', ir.Value(value='', meta=None)).value if 'csv_new_line' in config_dict else '',
            delimiter=config_dict.get('csv_delimiter', ir.Value(value=',', meta=None)).value if 'csv_delimiter' in config_dict else ',',
            quotechar=config_dict.get('csv_quotechar', ir.Value(value='"', meta=None)).value if 'csv_quotechar' in config_dict else '"',
            escapechar=config_dict.get('csv_escapechar', ir.Value(value='"', meta=None)).value if 'csv_escapechar' in config_dict else '"',
            comment=config_dict.get('csv_comment', ir.Value(value='', meta=None)).value if 'csv_comment' in config_dict else '',
            missing_strings=[config_dict['csv_missing_strings'].value] if 'csv_missing_strings' in config_dict else [],
            decimal_separator=config_dict.get('csv_decimal_separator', ir.Value(value='.', meta=None)).value if 'csv_decimal_separator' in config_dict else '.',
            encoding=config_dict.get('csv_encoding', ir.Value(value='utf-8', meta=None)).value if 'csv_encoding' in config_dict else 'utf-8',
            compression=config_dict.get('csv_compression', ir.Value(value='auto', meta=None)).value if 'csv_compression' in config_dict else 'auto',
            meta=self.meta(meta)
        )

    def csv_columns(self, meta, items):
        return items

    def csv_column(self, meta, items):
        column_name = items[0]
        target_id = items[1]
        types = items[2]
        return ir.CSVColumn(column_name=column_name, target_id=target_id, types=types, meta=self.meta(meta))

    def csv_asof(self, meta, items):
        return items[0]

    def type_list(self, meta, items):
        return items

    def betree_relation(self, meta, items):
        name = items[0]
        relation_info = items[1]
        return ir.BeTreeRelation(name=name, relation_info=relation_info, meta=self.meta(meta))

    def betree_info(self, meta, items):
        key_types = items[0]
        value_types = items[1]
        config_dict = items[2] if len(items) > 2 else {}

        # Parse BeTreeConfig
        epsilon = config_dict.get('betree_config_epsilon', ir.Value(value=0.5, meta=None)).value if 'betree_config_epsilon' in config_dict else 0.5
        max_pivots = config_dict.get('betree_config_max_pivots', ir.Value(value=4, meta=None)).value if 'betree_config_max_pivots' in config_dict else 4
        max_deltas = config_dict.get('betree_config_max_deltas', ir.Value(value=16, meta=None)).value if 'betree_config_max_deltas' in config_dict else 16
        max_leaf = config_dict.get('betree_config_max_leaf', ir.Value(value=16, meta=None)).value if 'betree_config_max_leaf' in config_dict else 16

        storage_config = ir.BeTreeConfig(
            epsilon=epsilon,
            max_pivots=max_pivots,
            max_deltas=max_deltas,
            max_leaf=max_leaf,
            meta=self.meta(meta)
        )

        # Parse BeTreeLocator
        root_pageid = None
        inline_data = None
        if 'betree_locator_root_pageid' in config_dict:
            pageid_val = config_dict['betree_locator_root_pageid'].value
            if isinstance(pageid_val, ir.UInt128Value):
                root_pageid = pageid_val
            else:
                root_pageid = ir.UInt128Value(value=pageid_val, meta=None)
        if 'betree_locator_inline_data' in config_dict:
            inline_data = config_dict['betree_locator_inline_data'].value.encode() if isinstance(config_dict['betree_locator_inline_data'].value, str) else config_dict['betree_locator_inline_data'].value

        element_count = config_dict.get('betree_locator_element_count', ir.Value(value=0, meta=None)).value if 'betree_locator_element_count' in config_dict else 0
        tree_height = config_dict.get('betree_locator_tree_height', ir.Value(value=0, meta=None)).value if 'betree_locator_tree_height' in config_dict else 0

        relation_locator = ir.BeTreeLocator(
            root_pageid=root_pageid,
            inline_data=inline_data,
            element_count=element_count,
            tree_height=tree_height,
            meta=self.meta(meta)
        )

        return ir.BeTreeInfo(
            key_types=key_types,
            value_types=value_types,
            storage_config=storage_config,
            relation_locator=relation_locator,
            meta=self.meta(meta)
        )

    def betree_key_types(self, meta, items):
        return items

    def betree_value_types(self, meta, items):
        return items

    def rel_edb(self, meta, items):
        target_id = items[0]
        path = items[1]
        types = items[2]
        return ir.RelEDB(target_id=target_id, path=path, types=types, meta=self.meta(meta))

    def string_list(self, meta, items):
        return items

    def algorithm(self, meta, items):
        return ir.Algorithm(global_=items[:-1], body=items[-1], meta=self.meta(meta))

    def script(self, meta, items):
        return ir.Script(constructs=items, meta=self.meta(meta))

    def construct(self, meta, items):
        return items[0]

    def loop(self, meta, items):
        init = items[0]
        script = items[1]
        return ir.Loop(init=init, body=script, meta=self.meta(meta))

    def init(self, meta, items):
        return items

    def instruction(self, meta, items):
        return items[0]

    def assign(self, meta, items):
        name = items[0]
        body, value_arity = items[1]
        assert value_arity == 0, f"Assigns should not have a value arity"
        attrs = items[2] if len(items) > 2 else []
        return ir.Assign(name=name, body=body, attrs=attrs, meta=self.meta(meta))

    def upsert(self, meta, items):
        name = items[0]
        body, value_arity = items[1]
        attrs = items[2] if len(items) > 2 else []
        return ir.Upsert(value_arity=value_arity, name=name, body=body, attrs=attrs, meta=self.meta(meta))

    def break_(self, meta, items):
        name = items[0]
        body, value_arity = items[1]
        assert value_arity == 0, f"Breaks should not have a value arity"
        attrs = items[2] if len(items) > 2 else []
        return ir.Break(name=name, body=body, attrs=attrs, meta=self.meta(meta))

    def monoid_def(self, meta, items):
        monoid = items[0]
        name = items[1]
        body, value_arity = items[2]
        attrs = items[3] if len(items) > 3 else []
        return ir.MonoidDef(value_arity=value_arity, monoid=monoid, name=name, body=body, attrs=attrs, meta=self.meta(meta))

    def monus_def(self, meta, items):
        monoid = items[0]
        name = items[1]
        body, value_arity = items[2]
        attrs = items[3] if len(items) > 3 else []
        return ir.MonusDef(value_arity=value_arity, monoid=monoid, name=name, body=body, attrs=attrs, meta=self.meta(meta))

    def monoid(self, meta, items):
        return items[0]

    def or_monoid(self, meta, items):
        return ir.OrMonoid(meta=meta)

    def min_monoid(self, meta, items):
        return ir.MinMonoid(type=items[0], meta=meta)

    def max_monoid(self, meta, items):
        return ir.MaxMonoid(type=items[0], meta=meta)

    def sum_monoid(self, meta, items):
        return ir.SumMonoid(type=items[0], meta=meta)

    def abstraction(self, meta, items):
        vars, arity = items[0]
        return ir.Abstraction(vars=vars, value=items[1], meta=self.meta(meta)), arity

    def binding(self, meta, items):
        name, rel_t = items
        return (ir.Var(name=name, meta=self.meta(meta)), rel_t)

    def vars(self, meta, items):
        return items

    def bindings(self, meta, items):
        if len(items) == 1:
            return items[0], 0
        else:
            left = items[0]
            right = items[1]
            return left+right, len(right)

    def left_bindings(self, meta, items):
        return items

    def right_bindings(self, meta, items):
        return items

    def attrs(self, meta, items):
        return items

    def formula(self, meta, items):
        return items[0]

    def true(self, _, meta):
        return ir.Conjunction(args=[], meta=self.meta(meta))

    def false(self, _, meta):
        return ir.Disjunction(args=[], meta=self.meta(meta))

    def exists(self, meta, items):
        vars, arity = items[0]
        assert arity == 0, f"Exists should not have a value_arity"
        body_abstraction = ir.Abstraction(vars=vars, value=items[1], meta=self.meta(meta))
        return ir.Exists(body=body_abstraction, meta=self.meta(meta))

    def reduce(self, meta, items):
        op, x = items[0]
        body, y = items[1]
        assert x == y == 0, f"Abstractions in Reduce should not have value arities"
        return ir.Reduce(op=op, body=body, terms=items[2], meta=self.meta(meta))

    def conjunction(self, meta, items):
        return ir.Conjunction(args=items, meta=self.meta(meta))

    def disjunction(self, meta, items):
        return ir.Disjunction(args=items, meta=self.meta(meta))

    def not_(self, meta, items):
        return ir.Not(arg=items[0], meta=self.meta(meta))

    def ffi(self, meta, items):
        return ir.FFI(name=items[0], args=items[1], terms=items[2], meta=self.meta(meta))

    def atom(self, meta, items):
        return ir.Atom(name=items[0], terms=items[1:], meta=self.meta(meta))

    def pragma(self, meta, items):
        return ir.Pragma(name=items[0], terms=items[1:], meta=self.meta(meta))

    def relatom(self, meta, items):
        return ir.RelAtom(name=items[0], terms=items[1:], meta=self.meta(meta))

    def cast(self, meta, items):
        return ir.Cast(input=items[0], result=items[1], meta=self.meta(meta))

    #
    # Primitives
    #
    def primitive(self, meta, items):
        if isinstance(items[0], ir.Formula):
            return items[0]
        raise TypeError(f"Unexpected primitive type: {type(items[0])}")

    def raw_primitive(self, meta, items):
        return ir.Primitive(name=items[0], terms=items[1:], meta=self.meta(meta))

    def _make_primitive(self, name_symbol, terms, meta):
        name_str = self.name([name_symbol], meta) if isinstance(name_symbol, str) else name_symbol
        return ir.Primitive(name=name_str, terms=terms, meta=self.meta(meta))

    def eq(self, meta, items):
        return desugar_to_raw_primitive(self.name(meta, ["rel_primitive_eq"]), items)

    def lt(self, meta, items):
        return desugar_to_raw_primitive(self.name(meta, ["rel_primitive_lt_monotype"]), items)

    def lt_eq(self, meta, items):
        return desugar_to_raw_primitive(self.name(meta, ["rel_primitive_lt_eq_monotype"]), items)

    def gt(self, meta, items):
        return desugar_to_raw_primitive(self.name(meta, ["rel_primitive_gt_monotype"]), items)

    def gt_eq(self, meta, items):
        return desugar_to_raw_primitive(self.name(meta, ["rel_primitive_gt_eq_monotype"]), items)

    def add(self, meta, items):
        return desugar_to_raw_primitive(self.name(meta, ["rel_primitive_add_monotype"]), items)

    def minus(self, meta, items):
        return desugar_to_raw_primitive(self.name(meta, ["rel_primitive_subtract_monotype"]), items)

    def multiply(self, meta, items):
        return desugar_to_raw_primitive(self.name(meta, ["rel_primitive_multiply_monotype"]), items)

    def divide(self, meta, items):
        return desugar_to_raw_primitive(self.name(meta, ["rel_primitive_divide_monotype"]), items)

    def args(self, meta, items):
        return [item[0] for item in items]

    def terms(self, meta, items):
        return items

    def relterm(self, meta, items):
        return items[0]

    def term(self, meta, items):
        return items[0]

    def var(self, meta, items):
        return ir.Var(name=items[0], meta=self.meta(meta))

    def constant(self, meta, items):
        return items[0]

    def specialized_value(self, meta, items):
        return ir.SpecializedValue(value=items[0], meta=self.meta(meta))

    def name(self, meta, items):
        return items[0]

    def attribute(self, meta, items):
        return ir.Attribute(name=items[0], args=items[1:], meta=self.meta(meta))

    def relation_id(self, meta, items):
        ident = items[0]
        if isinstance(ident, str):
            # First 64 bits of SHA-256 as the id
            id_val = int(hashlib.sha256(ident.encode()).hexdigest()[:16], 16)
            result = ir.RelationId(id=id_val, meta=self.meta(meta))

            # Store mapping in the current fragment's debug info
            if self._current_fragment_id is not None:
                self.id_to_debuginfo[self._current_fragment_id][result] = ident
            return result

        elif isinstance(ident, int):
            return ir.RelationId(id=ident, meta=self.meta(meta))

    #
    # Primitive values
    #
    def value(self, meta, items):
        return ir.Value(value=items[0], meta=self.meta(meta))

    def STRING(self, s):
        return s[1:-1].encode().decode('unicode_escape')

    def NUMBER(self, n):
        return int(n)

    def FLOAT(self, f):
        return float(f)

    def SYMBOL(self, sym):
        return str(sym)

    def UINT128(self, u):
        uint128_val = int(u, 16)
        return ir.UInt128Value(value=uint128_val, meta=None)

    def INT128(self, u):
        u = u[:-4]
        int128_val = int(u)
        return ir.Int128Value(value=int128_val, meta=None)

    def MISSING(self, m):
        return ir.MissingValue(meta=None)

    def DECIMAL(self, d):
        parts = d.split('d')
        if len(parts) != 2:
            raise ValueError(f"Invalid decimal format: {d}")
        scale = len(parts[0].split('.')[1])
        precision = int(parts[1])
        value = Decimal(parts[0])

        return ir.DecimalValue(precision=precision, scale=scale, value=value, meta=None)

    def BOOLEAN(self, b):
        return ir.BooleanValue(value=bool(b == "true"), meta=None)

    def date(self, meta, items):
        date_val = date(*items)
        return ir.DateValue(value=date_val, meta=None)

    def datetime(self, meta, items):
        datetime_val = datetime(*items)
        return ir.DateTimeValue(value=datetime_val, meta=None)

    def config_dict(self, meta, items):
        config = {}
        for (k, v) in items:
            config[k] = v
        return config

    def config_key_value(self, meta, items):
        assert len(items) == 2
        return (items[0], items[1])


# LALR(1) is significantly faster than Earley for parsing, especially on larger inputs. It
# uses a precomputed parse table, reducing runtime complexity to O(n) (linear in input
# size), whereas Earley is O(n³) in the worst case (though often O(n²) or better for
# practical grammars). The LQP grammar is relatively complex but unambiguous, making
# LALR(1)'s speed advantage appealing for a CLI tool where quick parsing matters.
lark_parser = Lark(grammar, parser="lalr", propagate_positions=True)


def parse_lqp(file: str, text: str) -> ir.LqpNode:
    """Parse LQP text and return an IR node that can be converted to protocol buffers."""
    tree = lark_parser.parse(text)
    transformer = LQPTransformer(file)
    result = transformer.transform(tree)
    return result
