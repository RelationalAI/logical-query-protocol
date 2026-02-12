# The structure of this file is similar to yacc.
#
# <tokens>
# <grammar directives>
# %%
# <rules>
# %%
# <helper functions>
#
# Actions and helper functions are written in a restricted Python.
# Type annotations are required.
# Not all expression forms are supported. Indeed, one can only call helper
# functions declared below and builtin functions via `builtin.func(...)`.
# We translate this restricted Python into actual Python, Julia, and Go.


# Start symbol
%start transaction

# Token declarations: %token NAME Type PATTERN
# PATTERN can be r'...' for regex or '...' for fixed string
%token DECIMAL logic.DecimalValue r'[-]?\d+\.\d+d\d+'
%token FLOAT Float64 r'[-]?\d+\.\d+|inf|nan'
%token INT Int64 r'[-]?\d+'
%token INT128 logic.Int128Value r'[-]?\d+i128'
%token STRING String r'"(?:[^"\\]|\\.)*"'
%token SYMBOL String r'[a-zA-Z_][a-zA-Z0-9_.-]*'
%token UINT128 logic.UInt128Value r'0x[0-9a-fA-F]+'

# Type declarations for rules
%nonterm abstraction logic.Abstraction
%nonterm abstraction_with_arity Tuple[logic.Abstraction, Int64]
%nonterm add logic.Primitive
%nonterm algorithm logic.Algorithm
%nonterm assign logic.Assign
%nonterm atom logic.Atom
%nonterm attribute logic.Attribute
%nonterm attrs List[logic.Attribute]
%nonterm betree_info logic.BeTreeInfo
%nonterm betree_info_key_types List[logic.Type]
%nonterm betree_info_value_types List[logic.Type]
%nonterm betree_relation logic.BeTreeRelation
%nonterm binding logic.Binding
%nonterm bindings Tuple[List[logic.Binding], List[logic.Binding]]
%nonterm boolean_type logic.BooleanType
%nonterm boolean_value Boolean
%nonterm break logic.Break
%nonterm cast logic.Cast
%nonterm config_dict List[Tuple[String, logic.Value]]
%nonterm config_key_value Tuple[String, logic.Value]
%nonterm configure transactions.Configure
%nonterm conjunction logic.Conjunction
%nonterm constant logic.Value
%nonterm constraint logic.Constraint
%nonterm construct logic.Construct
%nonterm context transactions.Context
%nonterm csv_asof String
%nonterm csv_column logic.CSVColumn
%nonterm csv_columns List[logic.CSVColumn]
%nonterm csv_config logic.CSVConfig
%nonterm csv_data logic.CSVData
%nonterm csv_locator_inline_data String
%nonterm csv_locator_paths List[String]
%nonterm csvlocator logic.CSVLocator
%nonterm data logic.Data
%nonterm date logic.DateValue
%nonterm date_type logic.DateType
%nonterm datetime logic.DateTimeValue
%nonterm datetime_type logic.DateTimeType
%nonterm decimal_type logic.DecimalType
%nonterm declaration logic.Declaration
%nonterm def logic.Def
%nonterm define transactions.Define
%nonterm demand transactions.Demand
%nonterm disjunction logic.Disjunction
%nonterm divide logic.Primitive
%nonterm abort transactions.Abort
%nonterm epoch transactions.Epoch
%nonterm epoch_reads List[transactions.Read]
%nonterm epoch_writes List[transactions.Write]
%nonterm eq logic.Primitive
%nonterm exists logic.Exists
%nonterm export transactions.Export
%nonterm export_csv_column transactions.ExportCSVColumn
%nonterm export_csv_columns List[transactions.ExportCSVColumn]
%nonterm export_csv_config transactions.ExportCSVConfig
%nonterm export_csv_path String
%nonterm false logic.Disjunction
%nonterm ffi logic.FFI
%nonterm ffi_args List[logic.Abstraction]
%nonterm float_type logic.FloatType
%nonterm formula logic.Formula
%nonterm fragment fragments.Fragment
%nonterm fragment_id fragments.FragmentId
%nonterm functional_dependency_keys List[logic.Var]
%nonterm functional_dependency_values List[logic.Var]
%nonterm gt logic.Primitive
%nonterm gt_eq logic.Primitive
%nonterm init List[logic.Instruction]
%nonterm instruction logic.Instruction
%nonterm int_type logic.IntType
%nonterm int128_type logic.Int128Type
%nonterm loop logic.Loop
%nonterm lt logic.Primitive
%nonterm lt_eq logic.Primitive
%nonterm max_monoid logic.MaxMonoid
%nonterm min_monoid logic.MinMonoid
%nonterm minus logic.Primitive
%nonterm missing_type logic.MissingType
%nonterm monoid logic.Monoid
%nonterm monoid_def logic.MonoidDef
%nonterm monus_def logic.MonusDef
%nonterm multiply logic.Primitive
%nonterm name String
%nonterm new_fragment_id fragments.FragmentId
%nonterm not logic.Not
%nonterm or_monoid logic.OrMonoid
%nonterm output transactions.Output
%nonterm pragma logic.Pragma
%nonterm primitive logic.Primitive
%nonterm read transactions.Read
%nonterm reduce logic.Reduce
%nonterm rel_atom logic.RelAtom
%nonterm rel_edb logic.RelEDB
%nonterm rel_edb_path List[String]
%nonterm rel_edb_types List[logic.Type]
%nonterm rel_term logic.RelTerm
%nonterm relation_id logic.RelationId
%nonterm script logic.Script
%nonterm specialized_value logic.Value
%nonterm string_type logic.StringType
%nonterm sum_monoid logic.SumMonoid
%nonterm sync transactions.Sync
%nonterm term logic.Term
%nonterm terms List[logic.Term]
%nonterm transaction transactions.Transaction
%nonterm true logic.Conjunction
%nonterm type logic.Type
%nonterm uint128_type logic.UInt128Type
%nonterm undefine transactions.Undefine
%nonterm unspecified_type logic.UnspecifiedType
%nonterm upsert logic.Upsert
%nonterm value logic.Value
%nonterm value_bindings List[logic.Binding]
%nonterm var logic.Var
%nonterm what_if transactions.WhatIf
%nonterm write transactions.Write

# Messages that are constructed imperatively by the parser, not parsed from grammar rules.
# These protobuf message types are excluded from completeness validation because they are
# built programmatically by builtin functions (like construct_betree_info, construct_csv_config)
# or by parser internals, rather than being directly produced by grammar production rules.
# Without these directives, the validator would report errors that these message types have
# no grammar rules producing them.
%validator_ignore_completeness DebugInfo
%validator_ignore_completeness IVMConfig
%validator_ignore_completeness UInt128Value
%validator_ignore_completeness Int128Value
%validator_ignore_completeness DecimalValue
%validator_ignore_completeness BeTreeLocator
%validator_ignore_completeness BeTreeConfig

%%

transaction
    : "(" "transaction" configure? sync? epoch* ")"
      construct: transactions.Transaction(epochs=$5, configure=builtin.unwrap_option_or($3, default_configure()), sync=$4)

configure
    : "(" "configure" config_dict ")"
      construct: construct_configure($3)

config_dict
    : "{" config_key_value* "}"

config_key_value
    : ":" SYMBOL value
      construct: builtin.tuple($2, $3)

value
    : date
      construct: logic.Value(date_value=$1)
    | datetime
      construct: logic.Value(datetime_value=$1)
    | STRING
      construct: logic.Value(string_value=$1)
    | INT
      construct: logic.Value(int_value=$1)
    | FLOAT
      construct: logic.Value(float_value=$1)
    | UINT128
      construct: logic.Value(uint128_value=$1)
    | INT128
      construct: logic.Value(int128_value=$1)
    | DECIMAL
      construct: logic.Value(decimal_value=$1)
    | "missing"
      construct: logic.Value(missing_value=logic.MissingValue())
    | boolean_value
      construct: logic.Value(boolean_value=$1)

date
    : "(" "date" INT INT INT ")"
      construct: logic.DateValue(year=builtin.int64_to_int32($3), month=builtin.int64_to_int32($4), day=builtin.int64_to_int32($5))

datetime
    : "(" "datetime" INT INT INT INT INT INT INT? ")"
      construct: logic.DateTimeValue(year=builtin.int64_to_int32($3), month=builtin.int64_to_int32($4), day=builtin.int64_to_int32($5), hour=builtin.int64_to_int32($6), minute=builtin.int64_to_int32($7), second=builtin.int64_to_int32($8), microsecond=builtin.int64_to_int32(builtin.unwrap_option_or($9, 0)))

boolean_value
    : "true"
      construct: True
    | "false"
      construct: False

sync
    : "(" "sync" fragment_id* ")"
      construct: transactions.Sync(fragments=$3)

fragment_id
    : ":" SYMBOL
      construct: builtin.fragment_id_from_string($2)

epoch
    : "(" "epoch" epoch_writes? epoch_reads? ")"
      construct: transactions.Epoch(writes=builtin.unwrap_option_or($3, list[transactions.Write]()), reads=builtin.unwrap_option_or($4, list[transactions.Read]()))

epoch_writes
    : "(" "writes" write* ")"

write
    : define
      construct: transactions.Write(define=$1)
    | undefine
      construct: transactions.Write(undefine=$1)
    | context
      construct: transactions.Write(context=$1)

define
    : "(" "define" fragment ")"
      construct: transactions.Define(fragment=$3)

fragment
    : "(" "fragment" new_fragment_id declaration* ")"
      construct: builtin.construct_fragment($3, $4)

new_fragment_id
    : fragment_id
      construct:
        builtin.start_fragment($1)
        $1

declaration
    : def
      construct: logic.Declaration(def=$1)
    | algorithm
      construct: logic.Declaration(algorithm=$1)
    | constraint
      construct: logic.Declaration(constraint=$1)
    | data
      construct: logic.Declaration(data=$1)

def
    : "(" "def" relation_id abstraction attrs? ")"
      construct: logic.Def(name=$3, body=$4, attrs=builtin.unwrap_option_or($5, list[logic.Attribute]()))

relation_id
    : ":" SYMBOL
      construct: builtin.relation_id_from_string($2)
    | UINT128
      construct: builtin.relation_id_from_uint128($1)

abstraction
    : "(" bindings formula ")"
      construct: logic.Abstraction(vars=builtin.list_concat($2[0], $2[1]), value=$3)

bindings
    : "[" binding* value_bindings? "]"
      construct: builtin.tuple($2, builtin.unwrap_option_or($3, list[logic.Binding]()))

binding
    : SYMBOL "::" type
      construct: logic.Binding(var=logic.Var(name=$1), type=$3)

type
    : unspecified_type
      construct: logic.Type(unspecified_type=$1)
    | string_type
      construct: logic.Type(string_type=$1)
    | int_type
      construct: logic.Type(int_type=$1)
    | float_type
      construct: logic.Type(float_type=$1)
    | uint128_type
      construct: logic.Type(uint128_type=$1)
    | int128_type
      construct: logic.Type(int128_type=$1)
    | date_type
      construct: logic.Type(date_type=$1)
    | datetime_type
      construct: logic.Type(datetime_type=$1)
    | missing_type
      construct: logic.Type(missing_type=$1)
    | decimal_type
      construct: logic.Type(decimal_type=$1)
    | boolean_type
      construct: logic.Type(boolean_type=$1)

unspecified_type
    : "UNKNOWN"
      construct: logic.UnspecifiedType()

string_type
    : "STRING"
      construct: logic.StringType()

int_type
    : "INT"
      construct: logic.IntType()

float_type
    : "FLOAT"
      construct: logic.FloatType()

uint128_type
    : "UINT128"
      construct: logic.UInt128Type()

int128_type
    : "INT128"
      construct: logic.Int128Type()

date_type
    : "DATE"
      construct: logic.DateType()

datetime_type
    : "DATETIME"
      construct: logic.DateTimeType()

missing_type
    : "MISSING"
      construct: logic.MissingType()

decimal_type
    : "(" "DECIMAL" INT INT ")"
      construct: logic.DecimalType(precision=builtin.int64_to_int32($3), scale=builtin.int64_to_int32($4))

boolean_type
    : "BOOLEAN"
      construct: logic.BooleanType()

value_bindings
    : "|" binding*

formula
    : true
      construct: logic.Formula(conjunction=$1)
    | false
      construct: logic.Formula(disjunction=$1)
    | exists
      construct: logic.Formula(exists=$1)
    | reduce
      construct: logic.Formula(reduce=$1)
    | conjunction
      construct: logic.Formula(conjunction=$1)
    | disjunction
      construct: logic.Formula(disjunction=$1)
    | not
      construct: logic.Formula(not=$1)
    | ffi
      construct: logic.Formula(ffi=$1)
    | atom
      construct: logic.Formula(atom=$1)
    | pragma
      construct: logic.Formula(pragma=$1)
    | primitive
      construct: logic.Formula(primitive=$1)
    | rel_atom
      construct: logic.Formula(rel_atom=$1)
    | cast
      construct: logic.Formula(cast=$1)

true
    : "(" "true" ")"
      construct: logic.Conjunction(args=list[logic.Formula]())

false
    : "(" "false" ")"
      construct: logic.Disjunction(args=list[logic.Formula]())

exists
    : "(" "exists" bindings formula ")"
      construct: logic.Exists(body=logic.Abstraction(vars=builtin.list_concat($3[0], $3[1]), value=$4))

reduce
    : "(" "reduce" abstraction abstraction terms ")"
      construct: logic.Reduce(op=$3, body=$4, terms=$5)

term
    : var
      construct: logic.Term(var=$1)
    | constant
      construct: logic.Term(constant=$1)

var
    : SYMBOL
      construct: logic.Var(name=$1)

constant
    : value

conjunction
    : "(" "and" formula* ")"
      construct: logic.Conjunction(args=$3)

disjunction
    : "(" "or" formula* ")"
      construct: logic.Disjunction(args=$3)

not
    : "(" "not" formula ")"
      construct: logic.Not(arg=$3)

ffi
    : "(" "ffi" name ffi_args terms ")"
      construct: logic.FFI(name=$3, args=$4, terms=$5)

ffi_args
    : "(" "args" abstraction* ")"

terms
    : "(" "terms" term* ")"

name
    : ":" SYMBOL

atom
    : "(" "atom" relation_id term* ")"
      construct: logic.Atom(name=$3, terms=$4)

pragma
    : "(" "pragma" name term* ")"
      construct: logic.Pragma(name=$3, terms=$4)

primitive
    : eq
    | lt
    | lt_eq
    | gt
    | gt_eq
    | add
    | minus
    | multiply
    | divide
    | "(" "primitive" name rel_term* ")"
      construct: logic.Primitive(name=$3, terms=$4)

eq
    : "(" "=" term term ")"
      construct: logic.Primitive(name="rel_primitive_eq", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)])

lt
    : "(" "<" term term ")"
      construct: logic.Primitive(name="rel_primitive_lt_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)])

lt_eq
    : "(" "<=" term term ")"
      construct: logic.Primitive(name="rel_primitive_lt_eq_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)])

gt
    : "(" ">" term term ")"
      construct: logic.Primitive(name="rel_primitive_gt_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)])

gt_eq
    : "(" ">=" term term ")"
      construct: logic.Primitive(name="rel_primitive_gt_eq_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)])

add
    : "(" "+" term term term ")"
      construct: logic.Primitive(name="rel_primitive_add_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)])

minus
    : "(" "-" term term term ")"
      construct: logic.Primitive(name="rel_primitive_subtract_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)])

multiply
    : "(" "*" term term term ")"
      construct: logic.Primitive(name="rel_primitive_multiply_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)])

divide
    : "(" "/" term term term ")"
      construct: logic.Primitive(name="rel_primitive_divide_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)])

rel_term
    : specialized_value
      construct: logic.RelTerm(specialized_value=$1)
    | term
      construct: logic.RelTerm(term=$1)

specialized_value
    : "#" value

rel_atom
    : "(" "relatom" name rel_term* ")"
      construct: logic.RelAtom(name=$3, terms=$4)

cast
    : "(" "cast" term term ")"
      construct: logic.Cast(input=$3, result=$4)

attrs
    : "(" "attrs" attribute* ")"

attribute
    : "(" "attribute" name value* ")"
      construct: logic.Attribute(name=$3, args=$4)

algorithm
    : "(" "algorithm" relation_id* script ")"
      construct: logic.Algorithm(global=$3, body=$4)

script
    : "(" "script" construct* ")"
      construct: logic.Script(constructs=$3)

construct
    : loop
      construct: logic.Construct(loop=$1)
    | instruction
      construct: logic.Construct(instruction=$1)

loop
    : "(" "loop" init script ")"
      construct: logic.Loop(init=$3, body=$4)

init
    : "(" "init" instruction* ")"

instruction
    : assign
      construct: logic.Instruction(assign=$1)
    | upsert
      construct: logic.Instruction(upsert=$1)
    | break
      construct: logic.Instruction(break=$1)
    | monoid_def
      construct: logic.Instruction(monoid_def=$1)
    | monus_def
      construct: logic.Instruction(monus_def=$1)

assign
    : "(" "assign" relation_id abstraction attrs? ")"
      construct: logic.Assign(name=$3, body=$4, attrs=builtin.unwrap_option_or($5, list[logic.Attribute]()))

upsert
    : "(" "upsert" relation_id abstraction_with_arity attrs? ")"
      construct: logic.Upsert(name=$3, body=$4[0], attrs=builtin.unwrap_option_or($5, list[logic.Attribute]()), value_arity=$4[1])

abstraction_with_arity
    : "(" bindings formula ")"
      construct: builtin.tuple(logic.Abstraction(vars=builtin.list_concat($2[0], $2[1]), value=$3), builtin.length($2[1]))

break
    : "(" "break" relation_id abstraction attrs? ")"
      construct: logic.Break(name=$3, body=$4, attrs=builtin.unwrap_option_or($5, list[logic.Attribute]()))

monoid_def
    : "(" "monoid" monoid relation_id abstraction_with_arity attrs? ")"
      construct: logic.MonoidDef(monoid=$3, name=$4, body=$5[0], attrs=builtin.unwrap_option_or($6, list[logic.Attribute]()), value_arity=$5[1])

monoid
    : or_monoid
      construct: logic.Monoid(or_monoid=$1)
    | min_monoid
      construct: logic.Monoid(min_monoid=$1)
    | max_monoid
      construct: logic.Monoid(max_monoid=$1)
    | sum_monoid
      construct: logic.Monoid(sum_monoid=$1)

or_monoid
    : "(" "or" ")"
      construct: logic.OrMonoid()

min_monoid
    : "(" "min" type ")"
      construct: logic.MinMonoid(type=$3)
max_monoid
    : "(" "max" type ")"
      construct: logic.MaxMonoid(type=$3)

sum_monoid
    : "(" "sum" type ")"
      construct: logic.SumMonoid(type=$3)

monus_def
    : "(" "monus" monoid relation_id abstraction_with_arity attrs? ")"
      construct: logic.MonusDef(monoid=$3, name=$4, body=$5[0], attrs=builtin.unwrap_option_or($6, list[logic.Attribute]()), value_arity=$5[1])

constraint
    : "(" "functional_dependency" relation_id abstraction functional_dependency_keys functional_dependency_values ")"
      construct: logic.Constraint(name=$3, functional_dependency=logic.FunctionalDependency(guard=$4, keys=$5, values=$6))

functional_dependency_keys
    : "(" "keys" var* ")"

functional_dependency_values
    : "(" "values" var* ")"

data
    : rel_edb
      construct: logic.Data(rel_edb=$1)
    | betree_relation
      construct: logic.Data(betree_relation=$1)
    | csv_data
      construct: logic.Data(csv_data=$1)

rel_edb_path
    : "[" STRING* "]"

rel_edb_types
    : "[" type* "]"

rel_edb
    : "(" "rel_edb" relation_id rel_edb_path rel_edb_types ")"
      construct: logic.RelEDB(target_id=$3, path=$4, types=$5)

betree_relation
    : "(" "betree_relation" relation_id betree_info ")"
      construct: logic.BeTreeRelation(name=$3, relation_info=$4)

betree_info
    : "(" "betree_info" betree_info_key_types betree_info_value_types config_dict ")"
      construct: construct_betree_info($3, $4, $5)

betree_info_key_types
    : "(" "key_types" type* ")"

betree_info_value_types
    : "(" "value_types" type* ")"

csv_columns
    : "(" "columns" csv_column* ")"

csv_asof
    : "(" "asof" STRING ")"

csv_data
    : "(" "csv_data" csvlocator csv_config csv_columns csv_asof ")"
      construct: logic.CSVData(locator=$3, config=$4, columns=$5, asof=$6)

csv_locator_paths
    : "(" "paths" STRING* ")"

csv_locator_inline_data
    : "(" "inline_data" STRING ")"

csvlocator
    : "(" "csv_locator" csv_locator_paths? csv_locator_inline_data? ")"
      construct: logic.CSVLocator(paths=builtin.unwrap_option_or($3, list[str]()), inline_data=builtin.encode_string(builtin.unwrap_option_or($4, "")))

csv_config
    : "(" "csv_config" config_dict ")"
      construct: construct_csv_config($3)

csv_column
    : "(" "column" STRING relation_id "[" type* "]" ")"
      construct: logic.CSVColumn(column_name=$3, target_id=$4, types=$6)

undefine
    : "(" "undefine" fragment_id ")"
      construct: transactions.Undefine(fragment_id=$3)

context
    : "(" "context" relation_id* ")"
      construct: transactions.Context(relations=$3)

epoch_reads
    : "(" "reads" read* ")"

read
    : demand
      construct: transactions.Read(demand=$1)
    | output
      construct: transactions.Read(output=$1)
    | what_if
      construct: transactions.Read(what_if=$1)
    | abort
      construct: transactions.Read(abort=$1)
    | export
      construct: transactions.Read(export=$1)

demand
    : "(" "demand" relation_id ")"
      construct: transactions.Demand(relation_id=$3)

output
    : "(" "output" name? relation_id ")"
      construct: transactions.Output(name=builtin.unwrap_option_or($3, "output"), relation_id=$4)

what_if
    : "(" "what_if" name epoch ")"
      construct: transactions.WhatIf(branch=$3, epoch=$4)

abort
    : "(" "abort" name? relation_id ")"
      construct: transactions.Abort(name=builtin.unwrap_option_or($3, "abort"), relation_id=$4)

export
    : "(" "export" export_csv_config ")"
      construct: transactions.Export(csv_config=$3)

export_csv_config
    : "(" "export_csv_config" export_csv_path export_csv_columns config_dict ")"
      construct: export_csv_config($3, $4, $5)

export_csv_path
    : "(" "path" STRING ")"

export_csv_columns
    : "(" "columns" export_csv_column* ")"

export_csv_column
    : "(" "column" STRING relation_id ")"
      construct: transactions.ExportCSVColumn(column_name=$3, column_data=$4)


%%


def _extract_value_int32(value: Optional[logic.Value], default: int) -> Int32:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'int_value'):
        return builtin.int64_to_int32(builtin.unwrap_option(value).int_value)
    return builtin.int64_to_int32(default)


def _extract_value_int64(value: Optional[logic.Value], default: int) -> int:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'int_value'):
        return builtin.unwrap_option(value).int_value
    return default


def _extract_value_float64(value: Optional[logic.Value], default: float) -> float:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'float_value'):
        return builtin.unwrap_option(value).float_value
    return default


def _extract_value_string(value: Optional[logic.Value], default: str) -> str:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'string_value'):
        return builtin.unwrap_option(value).string_value
    return default


def _extract_value_boolean(value: Optional[logic.Value], default: bool) -> bool:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'boolean_value'):
        return builtin.unwrap_option(value).boolean_value
    return default


def _extract_value_bytes(value: Optional[logic.Value], default: bytes) -> bytes:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'string_value'):
        return builtin.encode_string(builtin.unwrap_option(value).string_value)
    return default


def _extract_value_uint128(value: Optional[logic.Value], default: logic.UInt128Value) -> logic.UInt128Value:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'uint128_value'):
        return builtin.unwrap_option(value).uint128_value
    return default

def _extract_value_string_list(value: Optional[logic.Value], default: List[String]) -> List[String]:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'string_value'):
        return [builtin.unwrap_option(value).string_value]
    return default

def _try_extract_value_int64(value: Optional[logic.Value]) -> Optional[int]:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'int_value'):
        return builtin.unwrap_option(value).int_value
    return None


def _try_extract_value_float64(value: Optional[logic.Value]) -> Optional[float]:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'float_value'):
        return builtin.unwrap_option(value).float_value
    return None


def _try_extract_value_string(value: Optional[logic.Value]) -> Optional[str]:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'string_value'):
        return builtin.unwrap_option(value).string_value
    return None


def _try_extract_value_bytes(value: Optional[logic.Value]) -> Optional[bytes]:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'string_value'):
        return builtin.encode_string(builtin.unwrap_option(value).string_value)
    return None


def _try_extract_value_uint128(value: Optional[logic.Value]) -> Optional[logic.UInt128Value]:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'uint128_value'):
        return builtin.unwrap_option(value).uint128_value
    return None


def _try_extract_value_string_list(value: Optional[logic.Value]) -> Optional[List[String]]:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'string_value'):
        return [builtin.unwrap_option(value).string_value]
    return None


def construct_csv_config(config_dict: List[Tuple[String, logic.Value]]) -> logic.CSVConfig:
    config: Dict[String, logic.Value] = builtin.dict_from_list(config_dict)
    header_row: Int32 = _extract_value_int32(builtin.dict_get(config, "csv_header_row"), 1)
    skip: int = _extract_value_int64(builtin.dict_get(config, "csv_skip"), 0)
    new_line: str = _extract_value_string(builtin.dict_get(config, "csv_new_line"), "")
    delimiter: str = _extract_value_string(builtin.dict_get(config, "csv_delimiter"), ",")
    quotechar: str = _extract_value_string(builtin.dict_get(config, "csv_quotechar"), "\"")
    escapechar: str = _extract_value_string(builtin.dict_get(config, "csv_escapechar"), "\"")
    comment: str = _extract_value_string(builtin.dict_get(config, "csv_comment"), "")
    missing_strings: List[String] = _extract_value_string_list(builtin.dict_get(config, "csv_missing_strings"), list[str]())
    decimal_separator: str = _extract_value_string(builtin.dict_get(config, "csv_decimal_separator"), ".")
    encoding: str = _extract_value_string(builtin.dict_get(config, "csv_encoding"), "utf-8")
    compression: str = _extract_value_string(builtin.dict_get(config, "csv_compression"), "auto")
    return logic.CSVConfig(
        header_row=header_row,
        skip=skip,
        new_line=new_line,
        delimiter=delimiter,
        quotechar=quotechar,
        escapechar=escapechar,
        comment=comment,
        missing_strings=missing_strings,
        decimal_separator=decimal_separator,
        encoding=encoding,
        compression=compression,
    )


def construct_betree_info(
    key_types: List[logic.Type],
    value_types: List[logic.Type],
    config_dict: List[Tuple[String, logic.Value]],
) -> logic.BeTreeInfo:
    config: Dict[String, logic.Value] = builtin.dict_from_list(config_dict)
    epsilon: Optional[float] = _try_extract_value_float64(builtin.dict_get(config, "betree_config_epsilon"))
    max_pivots: Optional[int] = _try_extract_value_int64(builtin.dict_get(config, "betree_config_max_pivots"))
    max_deltas: Optional[int] = _try_extract_value_int64(builtin.dict_get(config, "betree_config_max_deltas"))
    max_leaf: Optional[int] = _try_extract_value_int64(builtin.dict_get(config, "betree_config_max_leaf"))
    storage_config: logic.BeTreeConfig = logic.BeTreeConfig(
        epsilon=epsilon,
        max_pivots=max_pivots,
        max_deltas=max_deltas,
        max_leaf=max_leaf,
    )
    root_pageid: Optional[logic.UInt128Value] = _try_extract_value_uint128(builtin.dict_get(config, "betree_locator_root_pageid"))
    inline_data: Optional[bytes] = _try_extract_value_bytes(builtin.dict_get(config, "betree_locator_inline_data"))
    element_count: Optional[int] = _try_extract_value_int64(builtin.dict_get(config, "betree_locator_element_count"))
    tree_height: Optional[int] = _try_extract_value_int64(builtin.dict_get(config, "betree_locator_tree_height"))
    relation_locator: logic.BeTreeLocator = logic.BeTreeLocator(
        root_pageid=root_pageid,
        inline_data=inline_data,
        element_count=element_count,
        tree_height=tree_height,
    )
    return logic.BeTreeInfo(
        key_types=key_types,
        value_types=value_types,
        storage_config=storage_config,
        relation_locator=relation_locator,
    )


def default_configure() -> transactions.Configure:
    ivm_config: transactions.IVMConfig = transactions.IVMConfig(level=transactions.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    return transactions.Configure(
        semantics_version=0,
        ivm_config=ivm_config,
    )

def construct_configure(config_dict: List[Tuple[String, logic.Value]]) -> transactions.Configure:
    config: Dict[String, logic.Value] = builtin.dict_from_list(config_dict)
    maintenance_level_val: Optional[logic.Value] = builtin.dict_get(config, "ivm.maintenance_level")
    maintenance_level: transactions.MaintenanceLevel = transactions.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
    if (maintenance_level_val is not None
            and builtin.has_proto_field(maintenance_level_val, 'string_value')):
        if maintenance_level_val.string_value == "off":
            maintenance_level = transactions.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
        elif maintenance_level_val.string_value == "auto":
            maintenance_level = transactions.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO
        elif maintenance_level_val.string_value == "all":
            maintenance_level = transactions.MaintenanceLevel.MAINTENANCE_LEVEL_ALL
        else:
            maintenance_level = transactions.MaintenanceLevel.MAINTENANCE_LEVEL_OFF
    ivm_config: transactions.IVMConfig = transactions.IVMConfig(level=maintenance_level)
    semantics_version: int = _extract_value_int64(builtin.dict_get(config, "semantics_version"), 0)
    return transactions.Configure(
        semantics_version=semantics_version,
        ivm_config=ivm_config,
    )


def export_csv_config(
    path: String,
    columns: List[transactions.ExportCSVColumn],
    config_dict: List[Tuple[String, logic.Value]],
) -> transactions.ExportCSVConfig:
    config: Dict[String, logic.Value] = builtin.dict_from_list(config_dict)
    partition_size: int = _extract_value_int64(builtin.dict_get(config, "partition_size"), 0)
    compression: str = _extract_value_string(builtin.dict_get(config, "compression"), "")
    syntax_header_row: bool = _extract_value_boolean(builtin.dict_get(config, "syntax_header_row"), True)
    syntax_missing_string: str = _extract_value_string(builtin.dict_get(config, "syntax_missing_string"), "")
    syntax_delim: str = _extract_value_string(builtin.dict_get(config, "syntax_delim"), ",")
    syntax_quotechar: str = _extract_value_string(builtin.dict_get(config, "syntax_quotechar"), '"')
    syntax_escapechar: str = _extract_value_string(builtin.dict_get(config, "syntax_escapechar"), "\\")
    return transactions.ExportCSVConfig(
        path=path,
        data_columns=columns,
        partition_size=builtin.some(partition_size),
        compression=builtin.some(compression),
        syntax_header_row=builtin.some(syntax_header_row),
        syntax_missing_string=builtin.some(syntax_missing_string),
        syntax_delim=builtin.some(syntax_delim),
        syntax_quotechar=builtin.some(syntax_quotechar),
        syntax_escapechar=builtin.some(syntax_escapechar),
    )
