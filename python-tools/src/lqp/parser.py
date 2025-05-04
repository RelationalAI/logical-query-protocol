import argparse
import os
import sys

import hashlib
from lark import Lark, Transformer
from lqp.proto.v1 import logic_pb2, fragments_pb2, transactions_pb2
from lqp.validator import validate_lqp, ValidationError

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

formula: exists | reduce | conjunction | disjunction | not | ffi | atom | pragma | primitive | true | false | relatom | cast
exists: "(exists" vars formula ")"
reduce: "(reduce" abstraction abstraction terms ")"
conjunction: "(and" formula* ")"
disjunction: "(or" formula* ")"
not: "(not" formula ")"
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
raw_primitive: "(primitive" name term* ")"
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
var: SYMBOL "::" rel_type
constant: primitive_value

attrs: "(attrs" attribute* ")"
attribute: "(attribute" name constant* ")"

fragment_id: ":" SYMBOL
relation_id: ":" SYMBOL
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

def rel_type_to_proto(parsed_type):
    if parsed_type.children[0].type == "PRIMITIVE_TYPE":
        val = primitive_type_to_proto(parsed_type.children[0].value)
        return logic_pb2.RelType(primitive_type=val)
    elif parsed_type.children[0].type == "REL_VALUE_TYPE":
        val = rel_value_type_to_proto(parsed_type.children[0].value)
        return logic_pb2.RelType(value_type=val)
    else:
        raise ValueError(f"Unknown type: {parsed_type.children[0].type}")

def primitive_type_to_proto(primitive_type):
    # Map ENTITY -> HASH
    if primitive_type.upper() == "ENTITY":
        primitive_type = "UINT128"

    # Map the primitive type string to the corresponding protobuf enum value
    return getattr(logic_pb2.PrimitiveType, f"PRIMITIVE_TYPE_{primitive_type.upper()}")

def rel_value_type_to_proto(primitive_type):
    # Map the primitive type string to the corresponding protobuf enum value
    return getattr(logic_pb2.RelValueType, f"REL_VALUE_TYPE_{primitive_type.upper()}")

class LQPTransformer(Transformer):
    def start(self, items):
        return items[0]

    #
    # Transactions
    #
    def transaction(self, items):
        return transactions_pb2.Transaction(epochs=items)
    def epoch(self, items):
        kwargs = {k: v for k, v in items if v}  # Filter out None values
        return transactions_pb2.Epoch(**kwargs)

    def persistent_writes(self, items):
        return ("persistent_writes", items)
    def local_writes(self, items):
        return ("local_writes", items)
    def reads(self, items):
        return ("reads", items)
    def write(self, items):
        return self.transform(items[0])

    def define(self, items):
        return transactions_pb2.Write(define=transactions_pb2.Define(fragment=items[0]))
    def undefine(self, items):
        return transactions_pb2.Write(undefine=transactions_pb2.Undefine(fragment_id=items[0]))
    def context(self, items):
        return transactions_pb2.Write(context=transactions_pb2.Context(relations=items))

    def read(self, items):
        return self.transform(items[0])
    def demand(self, items):
        return transactions_pb2.Read(demand=transactions_pb2.Demand(relation_id=items[0]))
    def output(self, items):
        if len(items) == 1:
            return transactions_pb2.Read(output=transactions_pb2.Output(relation_id=items[0]))
        return transactions_pb2.Read(output=transactions_pb2.Output(name=items[0], relation_id=items[1]))
    def abort(self, items):
        if len(items) == 1:
            return transactions_pb2.Read(abort=transactions_pb2.Abort(relation_id=items[0]))
        return transactions_pb2.Read(abort=transactions_pb2.Abort(name=items[0], relation_id=items[1]))

    #
    # Logic
    #
    def fragment(self, items):
        return fragments_pb2.Fragment(id=items[0], declarations=items[1:])
    def fragment_id(self, items):
        return fragments_pb2.FragmentId(id=items[0].encode())

    def declaration(self, items):
        return items[0]
    def def_(self, items):
        name = items[0]
        body = items[1]
        attrs = items[2] if len(items) > 2 else []

        definition = logic_pb2.Def(name=name, body=body, attrs=attrs)
        return logic_pb2.Declaration(**{'def': definition}) # type: ignore

    def abstraction(self, items):
        return logic_pb2.Abstraction(vars=items[0], value=items[1])

    def vars(self, items):
        return [term.var for term in items]
    def attrs(self, items):
        return items

    def formula(self, items):
        return items[0]
    def true(self, _):
        return logic_pb2.Formula(conjunction=logic_pb2.Conjunction(args=[]))
    def false(self, _):
        return logic_pb2.Formula(disjunction=logic_pb2.Disjunction(args=[]))
    def exists(self, items):
        inner_abs = logic_pb2.Abstraction(vars=items[0], value=items[1])
        return logic_pb2.Formula(exists=logic_pb2.Exists(body=inner_abs))
    def reduce(self, items):
        return logic_pb2.Formula(reduce=logic_pb2.Reduce(op=items[0], body=items[1], terms=items[2]))
    def conjunction(self, items):
        return logic_pb2.Formula(conjunction=logic_pb2.Conjunction(args=items))
    def disjunction(self, items):
        return logic_pb2.Formula(disjunction=logic_pb2.Disjunction(args=items))
    def not_(self, items):
        return logic_pb2.Formula(not_=logic_pb2.Not(arg=items[0]))
    def ffi(self, items):
        return logic_pb2.Formula(ffi=logic_pb2.FFI(name=items[0], args=items[1], terms=items[2]))
    def atom(self, items):
        return logic_pb2.Formula(atom=logic_pb2.Atom(name=items[0], terms=items[1:]))
    def pragma(self, items):
        return logic_pb2.Formula(pragma=logic_pb2.Pragma(name=items[0], terms=items[1]))
    def relatom(self, items):
        return logic_pb2.Formula(rel_atom=logic_pb2.RelAtom(name=items[0], terms=items[1:]))
    def cast(self, items):
        t = rel_type_to_proto(items[0])
        return logic_pb2.Formula(cast=logic_pb2.Cast(type=t, input=items[1], result=items[2]))

    #
    # Primitives
    #
    def primitive(self, items):
        return items[0]
    def raw_primitive(self, items):
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=items[0], terms=items[1:]))
    def eq(self, items):
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=self.name(["rel_primitive_eq"]), terms=items))
    def lt(self, items):
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=self.name(["rel_primitive_lt"]), terms=items))
    def lt_eq(self, items):
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=self.name(["rel_primitive_lt_eq"]), terms=items))
    def gt(self, items):
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=self.name(["rel_primitive_gt"]), terms=items))
    def gt_eq(self, items):
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=self.name(["rel_primitive_gt_eq"]), terms=items))

    def add(self, items):
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=self.name(["rel_primitive_add"]), terms=items))
    def minus(self, items):
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=self.name(["rel_primitive_subtract"]), terms=items))
    def multiply(self, items):
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=self.name(["rel_primitive_multiply"]), terms=items))
    def divide(self, items):
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=self.name(["rel_primitive_divide"]), terms=items))

    def args(self, items):
        return items
    def terms(self, items):
        return items

    def relterm(self, items):
        inner = items[0]
        if isinstance(inner, logic_pb2.SpecializedValue):
            return logic_pb2.RelTerm(specialized_value=inner)
        else:
            return logic_pb2.RelTerm(term=inner)
    def term(self, items):
        return items[0]
    def var(self, items):
        identifier = items[0]
        primitive_type = items[1]
        type_enum = rel_type_to_proto(primitive_type)
        return logic_pb2.Term(var=logic_pb2.Var(name=identifier, type=type_enum))
    def constant(self, items):
        return logic_pb2.Term(constant=logic_pb2.Constant(value=items[0]))
    def specialized_value(self, items):
        return logic_pb2.SpecializedValue(value=items[0])

    def name(self, items):
        return items[0]
    def attribute(self, items):
        return logic_pb2.Attribute(name=items[0], args=items[1:])

    def relation_id(self, items):
        symbol = items[0][1:]  # Remove leading ':'
        hash_val = int(hashlib.sha256(symbol.encode()).hexdigest()[:16], 16)  # First 64 bits of SHA-256
        return logic_pb2.RelationId(id_low=hash_val, id_high=0)  # Simplified hashing

    #
    # Primitive values
    #
    def primitive_value(self, items):
        return items[0]
    def STRING(self, s):
        return logic_pb2.PrimitiveValue(string_value=s[1:-1])  # Strip quotes
    def NUMBER(self, n):
        return logic_pb2.PrimitiveValue(int_value=int(n))
    def FLOAT(self, f):
        return logic_pb2.PrimitiveValue(float_value=float(f))
    def SYMBOL(self, sym):
        return str(sym)
    def UINT128(self, u):
        uint128_val = int(u, 16)
        low = uint128_val & 0xFFFFFFFFFFFFFFFF
        high = (uint128_val >> 64) & 0xFFFFFFFFFFFFFFFF
        uint128_proto = logic_pb2.UInt128(low=low, high=high)
        return logic_pb2.PrimitiveValue(uint128_value=uint128_proto)

# LALR(1) is significantly faster than Earley for parsing, especially on larger inputs. It
# uses a precomputed parse table, reducing runtime complexity to O(n) (linear in input
# size), whereas Earley is O(n³) in the worst case (though often O(n²) or better for
# practical grammars). The LQP grammar is relatively complex but unambiguous, making
# LALR(1)’s speed advantage appealing for a CLI tool where quick parsing matters.
parser = Lark(grammar, parser="lalr")

def parse_lqp(text):
    tree = parser.parse(text)
    return LQPTransformer().transform(tree)

def process_file(filename, bin, json):
    with open(filename, "r") as f:
        lqp_text = f.read()

    lqp_proto = parse_lqp(lqp_text)
    validate_lqp(lqp_proto)
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
