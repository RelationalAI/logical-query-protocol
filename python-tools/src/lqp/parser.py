import argparse
import os
import sys

import hashlib
from lark import Lark
from lark.visitors import Transformer, Interpreter
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

abstraction: "(" bindings formula ")"
bindings: "[" binding* "]"
binding: SYMBOL "::" rel_type

formula: exists | reduce | conjunction | disjunction | not | ffi | atom | pragma | primitive | true | false | relatom | cast
exists: "(exists" bindings formula ")"
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
var: SYMBOL
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
    if parsed_type[0].type == "PRIMITIVE_TYPE":
        val = primitive_type_to_proto(parsed_type[0].value)
        return logic_pb2.RelType(primitive_type=val)
    elif parsed_type[0].type == "REL_VALUE_TYPE":
        val = rel_value_type_to_proto(parsed_type[0].value)
        return logic_pb2.RelType(value_type=val)
    else:
        raise ValueError(f"Unknown type: {parsed_type[0].type}")

def primitive_type_to_proto(primitive_type):
    # Map ENTITY -> HASH
    if primitive_type.upper() == "ENTITY":
        primitive_type = "UINT128"

    # Map the primitive type string to the corresponding protobuf enum value
    return getattr(logic_pb2.PrimitiveType, f"PRIMITIVE_TYPE_{primitive_type.upper()}")

def rel_value_type_to_proto(primitive_type):
    # Map the primitive type string to the corresponding protobuf enum value
    return getattr(logic_pb2.RelValueType, f"REL_VALUE_TYPE_{primitive_type.upper()}")

def desugar_to_raw_primitive(name, terms):
    # Convert terms to relterms
    relterms = [logic_pb2.RelTerm(term=term) for term in terms]
    return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=name, terms=relterms))

class LQPTransformer(Interpreter):
    def __init__(self):
        self.var_map = {}

    def start(self, tree):
        return self.visit_children(tree)[0]

    # Transactions
    def transaction(self, tree):
        _epochs = self.visit_children(tree)
        return transactions_pb2.Transaction(epochs=_epochs)

    def epoch(self, tree):
        items = self.visit_children(tree)
        kwargs = {k: v for k, v in items if v}  # Filter out None values
        return transactions_pb2.Epoch(**kwargs)

    def persistent_writes(self, tree):
        return ("persistent_writes", self.visit_children(tree))
    def local_writes(self, tree):
        return ("local_writes", self.visit_children(tree))
    def reads(self, tree):
        return ("reads", self.visit_children(tree))
    def write(self, tree):
        return self.visit_children(tree)[0]

    def define(self, tree):
        items = self.visit_children(tree)
        return transactions_pb2.Write(define=transactions_pb2.Define(fragment=items[0]))
    def undefine(self, tree):
        items = self.visit_children(tree)
        return transactions_pb2.Write(undefine=transactions_pb2.Undefine(fragment_id=items[0]))
    def context(self, tree):
        items = self.visit_children(tree)
        return transactions_pb2.Write(context=transactions_pb2.Context(relations=items))

    def read(self, tree):
        return self.visit_children(tree)[0]
    def demand(self, tree):
        items = self.visit_children(tree)
        return transactions_pb2.Read(demand=transactions_pb2.Demand(relation_id=items[0]))
    def output(self, tree):
        items = self.visit_children(tree)
        if len(items) == 1:
            return transactions_pb2.Read(output=transactions_pb2.Output(relation_id=items[0]))
        return transactions_pb2.Read(output=transactions_pb2.Output(name=items[0], relation_id=items[1]))
    def abort(self, tree):
        items = self.visit_children(tree)
        if len(items) == 1:
            return transactions_pb2.Read(abort=transactions_pb2.Abort(relation_id=items[0]))
        return transactions_pb2.Read(abort=transactions_pb2.Abort(name=items[0], relation_id=items[1]))

    # Logic
    def fragment(self, tree):
        items = self.visit_children(tree)
        return fragments_pb2.Fragment(id=items[0], declarations=items[1:])
    def fragment_id(self, tree):
        items = self.visit_children(tree)
        return fragments_pb2.FragmentId(id=items[0].encode())

    def declaration(self, tree):
        items = self.visit_children(tree)
        return items[0]
    def def_(self, tree):
        items = self.visit_children(tree)
        name = items[0]
        body = items[1]
        attrs = items[2] if len(items) > 2 else []

        definition = logic_pb2.Def(name=name, body=body, attrs=attrs)
        return logic_pb2.Declaration(**{'def': definition})
    def abstraction(self, tree):
        vars = self.visit(tree.children[0])

        for var in vars:
            if var.name in self.var_map:
                raise ValidationError(f"Duplicate variable name: {var.name}")
            self.var_map[var.name] = var.type

        body = self.visit(tree.children[1])

        # Clean up var_map so that it doesn't affect other branches
        for var in vars:
            del self.var_map[var.name]

        return logic_pb2.Abstraction(vars=vars, value=body)
    def bindings(self, tree):
        items = self.visit_children(tree)
        return [term.var for term in items]
    def binding(self, tree):
        items = self.visit_children(tree)
        identifier = items[0]
        primitive_type = items[1]
        type_enum = rel_type_to_proto(primitive_type)
        return logic_pb2.Term(var=logic_pb2.Var(name=identifier, type=type_enum))


    def attrs(self, tree):
        return self.visit_children(tree)
    def formula(self, tree):
        return self.visit_children(tree)[0]
    def true(self, tree):
        return logic_pb2.Formula(conjunction=logic_pb2.Conjunction(args=[]))
    def false(self, tree):
        return logic_pb2.Formula(disjunction=logic_pb2.Disjunction(args=[]))
    def exists(self, tree):
        vars = self.visit(tree.children[0])

        for var in vars:
            if var.name in self.var_map:
                raise ValidationError(f"Duplicate variable name: {var.name}")
            self.var_map[var.name] = var.type

        body = self.visit(tree.children[1])

        # Clean up var_map so that it doesn't affect other branches
        for var in vars:
            del self.var_map[var.name]

        inner_abs = logic_pb2.Abstraction(vars=vars, value=body)
        return logic_pb2.Formula(exists=logic_pb2.Exists(body=inner_abs))
    def reduce(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Formula(reduce=logic_pb2.Reduce(op=items[0], body=items[1], terms=items[2]))
    def conjunction(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Formula(conjunction=logic_pb2.Conjunction(args=items))
    def disjunction(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Formula(disjunction=logic_pb2.Disjunction(args=items))
    def not_(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Formula(not_=logic_pb2.Not(arg=items[0]))
    def ffi(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Formula(ffi=logic_pb2.FFI(name=items[0], args=items[1], terms=items[2]))
    def atom(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Formula(atom=logic_pb2.Atom(name=items[0], terms=items[1:]))
    def pragma(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Formula(pragma=logic_pb2.Pragma(name=items[0], terms=items[1]))
    def relatom(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Formula(rel_atom=logic_pb2.RelAtom(name=items[0], terms=items[1:]))
    def cast(self, tree):
        items = self.visit_children(tree)
        t = rel_type_to_proto(items[0])
        return logic_pb2.Formula(cast=logic_pb2.Cast(type=t, input=items[1], result=items[2]))


    # Primitives
    def primitive(self, tree):
        items = self.visit_children(tree)
        return items[0]
    def raw_primitive(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Formula(primitive=logic_pb2.Primitive(name=items[0], terms=items[1:]))
    def eq(self, tree):
        items = self.visit_children(tree)
        return desugar_to_raw_primitive("rel_primitive_eq", items)
    def lt(self, tree):
        items = self.visit_children(tree)
        return desugar_to_raw_primitive("rel_primitive_lt", items)
    def lt_eq(self, tree):
        items = self.visit_children(tree)
        return desugar_to_raw_primitive("rel_primitive_lt_eq", items)
    def gt(self, tree):
        items = self.visit_children(tree)
        return desugar_to_raw_primitive("rel_primitive_gt", items)
    def gt_eq(self, tree):
        items = self.visit_children(tree)
        return desugar_to_raw_primitive("rel_primitive_gt_eq", items)
    def add(self, tree):
        items = self.visit_children(tree)
        return desugar_to_raw_primitive("rel_primitive_add", items)
    def minus(self, tree):
        items = self.visit_children(tree)
        return desugar_to_raw_primitive("rel_primitive_subtract", items)
    def multiply(self, tree):
        items = self.visit_children(tree)
        return desugar_to_raw_primitive("rel_primitive_multiply", items)
    def divide(self, tree):
        items = self.visit_children(tree)
        return desugar_to_raw_primitive("rel_primitive_divide", items)

    def args(self, tree):
        return self.visit_children(tree)
    def terms(self, tree):
        return self.visit_children(tree)

    def relterm(self, tree):
        inner = self.visit_children(tree)[0]
        if isinstance(inner, logic_pb2.SpecializedValue):
            return logic_pb2.RelTerm(specialized_value=inner)
        else:
            return logic_pb2.RelTerm(term=inner)
    def term(self, tree):
        return self.visit_children(tree)[0]
    def var(self, tree):
        item = self.visit_children(tree)[0]

        if item not in self.var_map:
            raise ValidationError(f"Variable '{item}' not found in the variable map.")
        var_type = self.var_map[item]
        return logic_pb2.Term(var=logic_pb2.Var(name=item, type=var_type))

    def constant(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Term(constant=logic_pb2.Constant(value=items[0]))
    def specialized_value(self, tree):
        items = self.visit_children(tree)
        print("specialized_value", "\n", tree, "\n", items, "\n", type(items[0]))
        return logic_pb2.SpecializedValue(value=items[0])
    def name(self, tree):
        items = self.visit_children(tree)
        return items[0]
    def attribute(self, tree):
        items = self.visit_children(tree)
        return logic_pb2.Attribute(name=items[0], args=items[1:])

    def relation_id(self, tree):
        items = self.visit_children(tree)
        symbol = items[0][1:]
        hash_val = int(hashlib.sha256(symbol.encode()).hexdigest()[:16], 16)  # First 64 bits of SHA-256
        result = logic_pb2.RelationId(id_low=hash_val, id_high=0)  # Simplified hashing
        return result

    # Primitive values
    def primitive_value(self, tree):
        item = self.visit_children(tree)[0]

        if item.type == "STRING":
            return logic_pb2.PrimitiveValue(string_value=item[1:-1])
        elif item.type == "NUMBER":
            return logic_pb2.PrimitiveValue(int_value=int(item))
        elif item.type == "FLOAT":
            return logic_pb2.PrimitiveValue(float_value=float(item))
        elif item.type == "UINT128":
            uint128_val = int(item, 16)
            low = uint128_val & 0xFFFFFFFFFFFFFFFF
            high = (uint128_val >> 64) & 0xFFFFFFFFFFFFFFFF
            uint128_proto = logic_pb2.UInt128(low=low, high=high)
            return logic_pb2.PrimitiveValue(uint128_value=uint128_proto)

def parse_lqp(text):
    # LALR(1) is significantly faster than Earley for parsing, especially on larger inputs. It
    # uses a precomputed parse table, reducing runtime complexity to O(n) (linear in input
    # size), whereas Earley is O(n³) in the worst case (though often O(n²) or better for
    # practical grammars). The LQP grammar is relatively complex but unambiguous, making
    # LALR(1)’s speed advantage appealing for a CLI tool where quick parsing matters.
    parser = Lark(grammar, parser="lalr")
    tree = parser.parse(text)
    result = LQPTransformer().visit(tree)
    return result

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
