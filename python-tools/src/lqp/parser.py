import argparse
import os
import hashlib
from dataclasses import dataclass
from lark import Lark, Transformer, v_args
import lqp.ir as ir
from lqp.emit import ir_to_proto
from lqp.validator import validate_lqp
from google.protobuf.json_format import MessageToJson
from decimal import Decimal
from datetime import date, datetime

grammar = """
start: transaction | fragment

transaction: "(transaction" epoch* ")"
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

declaration: def_ | algorithm
def_: "(def" relation_id abstraction attrs? ")"

algorithm: "(algorithm" relation_id* script ")"
script: "(script" construct* ")"

construct: loop | instruction
loop: "(loop" init script ")"
init: "(init" instruction* ")"

instruction: assign | upsert | break_ | copy | monoid_def | monus_def

assign : "(assign" relation_id abstraction attrs? ")"
upsert : "(upsert" relation_id abstraction attrs? ")"
break_ : "(break" relation_id abstraction attrs? ")"
copy : "(copy" relation_id abstraction attrs? ")"
monoid_def : "(monoid" monoid relation_id abstraction attrs? ")"
monus_def : "(monus" monoid relation_id abstraction attrs? ")"

monoid : or_monoid | min_monoid | max_monoid | sum_monoid
or_monoid : "BOOL" "::" "OR"
min_monoid : type_ "::" "MIN"
max_monoid : type_ "::" "MAX"
sum_monoid : type_ "::" "SUM"

abstraction: "(" bindings formula ")"
bindings: "[" binding* "]"
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

TYPE_NAME: "STRING" | "INT" | "FLOAT" | "UINT128" | "INT128"
         | "DATE" | "DATETIME" | "MISSING" | "DECIMAL" | "BOOLEAN"

SYMBOL: /[a-zA-Z_][a-zA-Z0-9_-]*/
MISSING.1: "missing" // Set a higher priority so so it's MISSING instead of SYMBOL
STRING: ESCAPED_STRING
NUMBER: /[-]?\\d+/
INT128: /[-]?\\d+i128/
UINT128: /0x[0-9a-fA-F]+/
FLOAT: /[-]?\\d+\\.\\d+/
DECIMAL: /[-]?\\d+\\.\\d+d\\d+/
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


def desugar_to_raw_primitive(name, terms):
    # Convert terms to relterms
    return ir.Primitive(name=name, terms=terms, meta=None)
@v_args(meta=True)
class LQPTransformer(Transformer):
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
        return ir.Transaction(epochs=items, meta=self.meta(meta))
    def epoch(self, meta, items):
        kwargs = {k: v for k, v in items if v} # Filter out None values
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
        # items is a list of ExportCSVColumn objects
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
        debug_info = ir.DebugInfo(id_to_orig_name=self.id_to_debuginfo[fragment_id], meta=self.meta(meta))
        self._current_fragment_id = None
        return ir.Fragment(id=fragment_id, declarations=items[1:], debug_info=debug_info, meta=self.meta(meta))

    def fragment_id(self, meta, items):
        fragment_id = ir.FragmentId(id=items[0].encode(), meta=self.meta(meta))
        self._current_fragment_id = fragment_id # type: ignore
        if fragment_id not in self.id_to_debuginfo:
            self.id_to_debuginfo[fragment_id] = {}
        return fragment_id

    def declaration(self, meta, items):
        return items[0]
    def def_(self, meta, items):
        name = items[0]
        body = items[1]
        attrs = items[2] if len(items) > 2 else []
        return ir.Def(name=name, body=body, attrs=attrs, meta=self.meta(meta))

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
        body = items[1]
        attrs = items[2] if len(items) > 2 else []
        return ir.Assign(name=name, body=body, attrs=attrs, meta=self.meta(meta))
    def upsert(self, meta, items):
        name = items[0]
        body = items[1]
        attrs = items[2] if len(items) > 2 else []
        return ir.Upsert(name=name, body=body, attrs=attrs, meta=self.meta(meta))
    def break_(self, meta, items):
        name = items[0]
        body = items[1]
        attrs = items[2] if len(items) > 2 else []
        return ir.Break(name=name, body=body, attrs=attrs, meta=self.meta(meta))
    def copy(self, meta, items):
        name = items[0]
        body = items[1]
        attrs = items[2] if len(items) > 2 else []
        return ir.Copy(name=name, body=body, attrs=attrs, meta=self.meta(meta))
    def monoid_def(self, meta, items):
        monoid = items[0]
        name = items[1]
        body = items[2]
        attrs = items[3] if len(items) > 3 else []
        return ir.MonoidDef(monoid=monoid, name=name, body=body, attrs=attrs, meta=self.meta(meta))
    def monus_def(self, meta, items):
        monoid = items[0]
        name = items[1]
        body = items[2]
        attrs = items[3] if len(items) > 3 else []
        return ir.MonusDef(monoid=monoid, name=name, body=body, attrs=attrs, meta=self.meta(meta))

    def monoid(self, meta, items) :
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
        return ir.Abstraction(vars=items[0], value=items[1], meta=self.meta(meta))

    def binding(self, meta, items):
        name, rel_t = items
        return (ir.Var(name=name, meta=self.meta(meta)), rel_t)

    def vars(self, meta, items):
        return items
    def bindings(self, meta, items):
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
        # Create Abstraction for body directly here
        body_abstraction = ir.Abstraction(vars=items[0], value=items[1], meta=self.meta(meta))
        return ir.Exists(body=body_abstraction, meta=self.meta(meta))

    def reduce(self, meta, items):
        return ir.Reduce(op=items[0], body=items[1], terms=items[2], meta=self.meta(meta))

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
         # Convert name symbol to string if needed, assuming self.name handles it
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
        return items
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
        ident = items[0] # Remove leading ':'
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
        return s[1:-1].encode().decode('unicode_escape') # Strip quotes and process escaping
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
        u= u[:-4]  # Remove the 'i128' suffix
        int128_val = int(u)
        return ir.Int128Value(value=int128_val, meta=None)
    def MISSING(self, m):
        return ir.MissingValue(meta=None)
    def DECIMAL(self, d):
        # Decimal is a string like "123.456d12" where the last part after `d` is the
        # precision, and the scale is the number of digits between the decimal point and `d`
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
        # Date is in the format (date YYYY MM DD)
        date_val = date(*items)
        return ir.DateValue(value=date_val, meta=None)
    def datetime(self, meta, items):
        # Date is in the format (datetime YYYY MM DD HH MM SS [MS])
        datetime_val = datetime(*items)
        return ir.DateTimeValue(value=datetime_val, meta=None)

    def config_dict(self, meta, items):
        # items is a list of key-value pairs
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
# LALR(1)’s speed advantage appealing for a CLI tool where quick parsing matters.
parser = Lark(grammar, parser="lalr", propagate_positions=True)

def parse_lqp(file, text) -> ir.LqpNode:
    """Parse LQP text and return an IR node that can be converted to protocol buffers"""
    tree = parser.parse(text)
    transformer = LQPTransformer(file)
    result = transformer.transform(tree)
    return result

def process_file(filename, bin, json):
    with open(filename, "r") as f:
        lqp_text = f.read()

    lqp = parse_lqp(filename, lqp_text)
    validate_lqp(lqp) # type: ignore
    lqp_proto = ir_to_proto(lqp)
    print(lqp_proto)

    # Write binary output to the configured directories, using the same filename.
    if bin:
        with open(bin, "wb") as f:
            f.write(lqp_proto.SerializeToString())

    # Write JSON output
    if json:
        with open(json, "w") as f:
            f.write(MessageToJson(lqp_proto, preserving_proto_field_name=True))

def main():
    arg_parser = argparse.ArgumentParser(description="Parse LQP S-expression into Protobuf binary and JSON files.")
    arg_parser.add_argument("input_directory", help="path to the input LQP S-expression files")
    arg_parser.add_argument("--bin", help="output directory for the binary encoded protobuf")
    arg_parser.add_argument("--json", help="output directory for the JSON encoded protobuf")
    args = arg_parser.parse_args()

    print(args)

    # Check if directory
    if not os.path.isdir(args.input_directory):
        filename = args.input_directory
        if not filename.endswith(".lqp"):
            print(f"Skipping file {filename} as it does not have the .lqp extension")
            return

        bin = args.bin if args.bin else None
        if bin and not bin.endswith(".bin"):
            print(f"Skipping output {bin} as it does not have the .bin extension")
            bin = None

        json = args.json if args.json else None
        if json and not json.endswith(".json"):
            print(f"Skipping output {json} as it does not have the .json extension")
            json = None
        process_file(filename, bin, json)

    else:
        # Process each file in the input directory
        for file in os.listdir(args.input_directory):
            if not file.endswith(".lqp"):
                print(f"Skipping file {file} as it does not have the .lqp extension")
                continue

            filename = os.path.join(args.input_directory, file)
            basename = os.path.splitext(file)[0]
            bin = os.path.join(args.bin, basename+".bin") if args.bin else None
            json = os.path.join(args.json, basename+".json") if args.json else None
            process_file(filename, bin, json)


if __name__ == "__main__":
    main()
