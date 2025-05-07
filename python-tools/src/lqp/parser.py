import argparse
import os
import hashlib
from lark import Lark, Transformer
from typing import cast
import lqp.ir as ir
from lqp.emit import ir_to_proto
from lqp.validator import validate_lqp, fill_types
from google.protobuf.json_format import MessageToJson

grammar = """
start: transaction | fragment

transaction: "(transaction" epoch* ")"
epoch: "(epoch" persistent_writes? local_writes? reads? ")"
persistent_writes: "(persistent_writes" write* ")"
local_writes: "(local_writes" write* ")"
reads: "(reads" read* ")"

write: define | undefine | context
define: "(define" fragment ")"
undefine: "(undefine" fragment_id ")"
context: "(context" relation_id* ")"

read: demand | output | abort
demand: "(demand" relation_id ")"
output: "(output" name? relation_id ")"
abort: "(abort" name? relation_id ")"

fragment: "(fragment" fragment_id declaration* ")"

declaration: def_
def_: "(def" relation_id abstraction attrs? ")"

abstraction: "(" vars formula ")"
vars: "[" var* "]"

formula: exists | reduce | conjunction | disjunction | not_ | ffi | atom | pragma | primitive | true | false | relatom | cast
exists: "(exists" vars formula ")"
reduce: "(reduce" abstraction abstraction terms ")"
conjunction: "(and" formula* ")"
disjunction: "(or" formula* ")"
not_: "(not" formula ")"
ffi: "(ffi" name args terms ")"
atom: "(atom" relation_id term* ")"
relatom: "(relatom" name relterm* ")"
cast: "(cast" rel_type term term ")"
pragma: "(pragma" name terms ")"
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
var: SYMBOL "::" rel_type | SYMBOL
constant: primitive_value

attrs: "(attrs" attribute* ")"
attribute: "(attribute" name constant* ")"

fragment_id: ":" SYMBOL
relation_id: (":" SYMBOL) | NUMBER
name: ":" SYMBOL

specialized_value: "#" primitive_value

primitive_value: STRING | NUMBER | FLOAT | UINT128

rel_type: PRIMITIVE_TYPE | REL_VALUE_TYPE
PRIMITIVE_TYPE: "STRING" | "INT" | "FLOAT" | "UINT128" | "ENTITY"
REL_VALUE_TYPE: "DECIMAL" | "DATE" | "DATETIME"
              | "NANOSECOND" | "MICROSECOND" | "MILLISECOND" | "SECOND" | "MINUTE" | "HOUR"
              | "DAY" | "WEEK" | "MONTH" | "YEAR"

SYMBOL: /[a-zA-Z_][a-zA-Z0-9_-]*/
STRING: "\\"" /[^"]*/ "\\""
NUMBER: /\\d+/
UINT128: /0x[0-9a-fA-F]+/
FLOAT: /\\d+\\.\\d+/

COMMENT: /;;.*/  // Matches ;; followed by any characters except newline
%ignore /\\s+/
%ignore COMMENT
"""


def desugar_to_raw_primitive(name, terms):
    # Convert terms to relterms
    return ir.Primitive(name=name, terms=terms)

class LQPTransformer(Transformer):
    def start(self, items):
        return items[0]

    def PRIMITIVE_TYPE(self, s):
        # Map ENTITY -> HASH
        if s.upper() == "ENTITY":
            return ir.PrimitiveType.UINT128
        return getattr(ir.PrimitiveType, s.upper())

    def REL_VALUE_TYPE(self, s):
        return getattr(ir.RelValueType, s.upper())

    def rel_type(self, items):
        return items[0]

    #
    # Transactions
    #
    def transaction(self, items):
        return ir.Transaction(epochs=items)
    def epoch(self, items):
        kwargs = {k: v for k, v in items if v} # Filter out None values
        return ir.Epoch(**kwargs)

    def persistent_writes(self, items):
        return ("persistent_writes", items)
    def local_writes(self, items):
        return ("local_writes", items)
    def reads(self, items):
        return ("reads", items)
    def write(self, items):
        return ir.Write(write_type=items[0])

    def define(self, items):
        return ir.Define(fragment=items[0])

    def undefine(self, items):
        return ir.Undefine(fragment_id=items[0])

    def context(self, items):
        return ir.Context(relations=items)

    def read(self, items):
        return ir.Read(read_type=items[0])
    def demand(self, items):
        return ir.Demand(relation_id=items[0])

    def output(self, items):
        if len(items) == 1:
            return ir.Output(name=None, relation_id=items[0])
        return ir.Output(name=items[0], relation_id=items[1])

    def abort(self, items):
        if len(items) == 1:
            return ir.Abort(name=None, relation_id=items[0])
        return ir.Abort(name=items[0], relation_id=items[1])

    #
    # Logic
    #
    def fragment(self, items):
        return ir.Fragment(id=items[0], declarations=items[1:])

    def fragment_id(self, items):
        return ir.FragmentId(id=items[0].encode())

    def declaration(self, items):
        return items[0]
    def def_(self, items):
        name = items[0]
        body = items[1]
        attrs = items[2] if len(items) > 2 else []
        return ir.Def(name=name, body=body, attrs=attrs)

    def abstraction(self, items):
        return ir.Abstraction(vars=items[0], value=items[1])

    def vars(self, items):
        return items
    def attrs(self, items):
        return items

    def formula(self, items):
        return items[0]
    def true(self, _):
        return ir.Conjunction(args=[])

    def false(self, _):
        return ir.Disjunction(args=[])

    def exists(self, items):
        # Create Abstraction for body directly here
        body_abstraction = ir.Abstraction(vars=items[0], value=items[1])
        return ir.Exists(body=body_abstraction)

    def reduce(self, items):
        return ir.Reduce(op=items[0], body=items[1], terms=items[2])

    def conjunction(self, items):
        return ir.Conjunction(args=items)

    def disjunction(self, items):
        return ir.Disjunction(args=items)

    def not_(self, items):
        return ir.Not(arg=items[0])

    def ffi(self, items):
        return ir.FFI(name=items[0], args=items[1], terms=items[2])

    def atom(self, items):
        return ir.Atom(name=items[0], terms=items[1:])

    def pragma(self, items):
        return ir.Pragma(name=items[0], terms=items[1])

    def relatom(self, items):
        return ir.RelAtom(name=items[0], terms=items[1:])

    def cast(self, items):
        return ir.Cast(type=items[0], input=items[1], result=items[2])

    #
    # Primitives
    #
    def primitive(self, items):
        if isinstance(items[0], ir.Formula):
            return items[0]
        raise TypeError(f"Unexpected primitive type: {type(items[0])}")
    def raw_primitive(self, items):
        return ir.Primitive(name=items[0], terms=items[1:])
    def _make_primitive(self, name_symbol, terms):
         # Convert name symbol to string if needed, assuming self.name handles it
         name_str = self.name([name_symbol]) if isinstance(name_symbol, str) else name_symbol
         return ir.Primitive(name=name_str, terms=terms)
    def eq(self, items):
        return desugar_to_raw_primitive(self.name(["rel_primitive_eq_monotype"]), items)
    def lt(self, items):
        return desugar_to_raw_primitive(self.name(["rel_primitive_lt_monotype"]), items)
    def lt_eq(self, items):
        return desugar_to_raw_primitive(self.name(["rel_primitive_lt_eq_monotype"]), items)
    def gt(self, items):
        return desugar_to_raw_primitive(self.name(["rel_primitive_gt_monotype"]), items)
    def gt_eq(self, items):
        return desugar_to_raw_primitive(self.name(["rel_primitive_gt_eq_monotype"]), items)

    def add(self, items):
        return desugar_to_raw_primitive(self.name(["rel_primitive_add_monotype"]), items)
    def minus(self, items):
        return desugar_to_raw_primitive(self.name(["rel_primitive_subtract_monotype"]), items)
    def multiply(self, items):
        return desugar_to_raw_primitive(self.name(["rel_primitive_multiply_monotype"]), items)
    def divide(self, items):
        return desugar_to_raw_primitive(self.name(["rel_primitive_divide_monotype"]), items)

    def args(self, items):
        return items
    def terms(self, items):
        return items

    def relterm(self, items):
        return items[0]
    def term(self, items):
        return items[0]
    def var(self, items):
        identifier = items[0]
        if len(items) > 1:
            rel_type_obj = items[1]
            return ir.Var(name=identifier, type=rel_type_obj)
        else:
            return ir.Var(name=identifier, type=ir.PrimitiveType.UNSPECIFIED)
    def constant(self, items):
        return items[0]
    def specialized_value(self, items):
        return ir.Specialized(value=items[0])

    def name(self, items):
        return items[0] # SYMBOL string

    def attribute(self, items):
        return ir.Attribute(name=items[0], args=items[1:])

    def relation_id(self, items):
        ident = items[0] # Remove leading ':'
        print("relation id", items, ident)
        if isinstance(ident, str):
            hash_val = int(hashlib.sha256(ident.encode()).hexdigest()[:16], 16) # First 64 bits of SHA-256
            return ir.RelationId(id_low=hash_val, id_high=0) # Simplified hashing
        elif isinstance(ident, int):
            low = ident & 0xFFFFFFFFFFFFFFFF
            high = (ident >> 64) & 0xFFFFFFFFFFFFFFFF
            return ir.RelationId(id_low=low, id_high=high)

    #
    # Primitive values
    #
    def primitive_value(self, items):
        return items[0]
    def STRING(self, s):
        return s[1:-1] # Strip quotes
    def NUMBER(self, n):
        return int(n)
    def FLOAT(self, f):
        return float(f)
    def SYMBOL(self, sym):
        return str(sym)
    def UINT128(self, u):
        uint128_val = int(u, 16)
        low = uint128_val & 0xFFFFFFFFFFFFFFFF
        high = (uint128_val >> 64) & 0xFFFFFFFFFFFFFFFF
        return ir.UInt128(low=low, high=high)

# LALR(1) is significantly faster than Earley for parsing, especially on larger inputs. It
# uses a precomputed parse table, reducing runtime complexity to O(n) (linear in input
# size), whereas Earley is O(n³) in the worst case (though often O(n²) or better for
# practical grammars). The LQP grammar is relatively complex but unambiguous, making
# LALR(1)’s speed advantage appealing for a CLI tool where quick parsing matters.
parser = Lark(grammar, parser="lalr", transformer=LQPTransformer())

def parse_lqp(text) -> ir.LqpNode:
    """Parse LQP text and return an IR node that can be converted to protocol buffers"""
    lqp_node = cast(ir.LqpNode, parser.parse(text))
    fill_types(lqp_node)
    return lqp_node

def process_file(filename, bin, json):
    with open(filename, "r") as f:
        lqp_text = f.read()

    lqp = parse_lqp(lqp_text)
    validate_lqp(lqp)
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
