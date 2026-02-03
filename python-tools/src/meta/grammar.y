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
# Not all expression forms are supported.
# We translate this restricted Python into actual Python, Julia, and Go.


# Token declarations
%token DECIMAL logic.DecimalValue
%token FLOAT Float64
%token INT Int64
%token INT128 logic.Int128Value
%token STRING String
%token SYMBOL String
%token UINT128 logic.UInt128Value

# Type declarations for rules
%type abstraction logic.Abstraction
%type abstraction_with_arity Tuple[logic.Abstraction, Int64]
%type add logic.Primitive
%type algorithm logic.Algorithm
%type assign logic.Assign
%type atom logic.Atom
%type attribute logic.Attribute
%type attrs List[logic.Attribute]
%type be_tree_info logic.BeTreeInfo
%type be_tree_info_key_types List[logic.Type]
%type be_tree_info_value_types List[logic.Type]
%type be_tree_relation logic.BeTreeRelation
%type betree_relation logic.BeTreeRelation
%type binding logic.Binding
%type bindings Tuple[List[logic.Binding], List[logic.Binding]]
%type boolean_type logic.BooleanType
%type boolean_value Boolean
%type break logic.Break
%type cast logic.Cast
%type config_dict List[Tuple[String, logic.Value]]
%type config_key_value Tuple[String, logic.Value]
%type configure transactions.Configure
%type conjunction logic.Conjunction
%type constant logic.Value
%type constraint logic.Constraint
%type construct logic.Construct
%type context transactions.Context
%type csv_asof String
%type csv_column logic.CSVColumn
%type csv_columns List[logic.CSVColumn]
%type csv_config logic.CSVConfig
%type csv_data logic.CSVData
%type csv_locator_inline_data String
%type csv_locator_paths List[String]
%type csvdata logic.CSVData
%type csvlocator logic.CSVLocator
%type data logic.Data
%type date logic.DateValue
%type date_type logic.DateType
%type datetime logic.DateTimeValue
%type datetime_type logic.DateTimeType
%type decimal_type logic.DecimalType
%type declaration logic.Declaration
%type def logic.Def
%type define transactions.Define
%type demand transactions.Demand
%type disjunction logic.Disjunction
%type divide logic.Primitive
%type abort transactions.Abort
%type epoch transactions.Epoch
%type epoch_reads List[transactions.Read]
%type epoch_writes List[transactions.Write]
%type eq logic.Primitive
%type exists logic.Exists
%type export transactions.Export
%type export_csv_column transactions.ExportCSVColumn
%type export_csv_columns List[transactions.ExportCSVColumn]
%type export_csv_config transactions.ExportCSVConfig
%type export_csv_path String
%type false logic.Disjunction
%type ffi logic.FFI
%type ffi_args List[logic.Abstraction]
%type float_type logic.FloatType
%type formula logic.Formula
%type fragment fragments.Fragment
%type fragment_id fragments.FragmentId
%type functional_dependency_keys List[logic.Var]
%type functional_dependency_values List[logic.Var]
%type gt logic.Primitive
%type gt_eq logic.Primitive
%type init List[logic.Instruction]
%type instruction logic.Instruction
%type int_type logic.IntType
%type int128_type logic.Int128Type
%type loop logic.Loop
%type lt logic.Primitive
%type lt_eq logic.Primitive
%type max_monoid logic.MaxMonoid
%type min_monoid logic.MinMonoid
%type minus logic.Primitive
%type missing_type logic.MissingType
%type monoid logic.Monoid
%type monoid_def logic.MonoidDef
%type monus_def logic.MonusDef
%type multiply logic.Primitive
%type name String
%type new_fragment_id fragments.FragmentId
%type not logic.Not
%type or_monoid logic.OrMonoid
%type output transactions.Output
%type pragma logic.Pragma
%type primitive logic.Primitive
%type read transactions.Read
%type reduce logic.Reduce
%type rel_atom logic.RelAtom
%type rel_edb logic.RelEDB
%type rel_edb_path List[String]
%type rel_edb_types List[logic.Type]
%type rel_term logic.RelTerm
%type relation_id logic.RelationId
%type script logic.Script
%type specialized_value logic.Value
%type string_type logic.StringType
%type sum_monoid logic.SumMonoid
%type sync transactions.Sync
%type term logic.Term
%type terms List[logic.Term]
%type transaction transactions.Transaction
%type true logic.Conjunction
%type type logic.Type
%type uint128_type logic.UInt128Type
%type undefine transactions.Undefine
%type unspecified_type logic.UnspecifiedType
%type upsert logic.Upsert
%type value logic.Value
%type value_bindings List[logic.Binding]
%type var logic.Var
%type what_if transactions.WhatIf
%type write transactions.Write

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
    { transactions.Transaction(epochs=$5, configure=unwrap_option_or($3, construct_configure([])), sync=$4) }

configure
    : "(" "configure" config_dict ")"
    { construct_configure($3) }

config_dict
    : "{" config_key_value* "}"
    { $2 }

config_key_value
    : ":" SYMBOL value
    { make_tuple($2, $3) }

value
    : date { logic.Value(date_value=$1) }
    | datetime { logic.Value(datetime_value=$1) }
    | STRING { logic.Value(string_value=$1) }
    | INT { logic.Value(int_value=$1) }
    | FLOAT { logic.Value(float_value=$1) }
    | UINT128 { logic.Value(uint128_value=$1) }
    | INT128 { logic.Value(int128_value=$1) }
    | DECIMAL { logic.Value(decimal_value=$1) }
    | "missing" { logic.Value(missing_value=logic.MissingValue()) }
    | boolean_value { logic.Value(boolean_value=$1) }

date
    : "(" "date" INT INT INT ")"
    { logic.DateValue(year=int64_to_int32($3), month=int64_to_int32($4), day=int64_to_int32($5)) }

datetime
    : "(" "datetime" INT INT INT INT INT INT INT? ")"
    { logic.DateTimeValue(year=int64_to_int32($3), month=int64_to_int32($4), day=int64_to_int32($5), hour=int64_to_int32($6), minute=int64_to_int32($7), second=int64_to_int32($8), microsecond=int64_to_int32(unwrap_option_or($9, 0))) }

boolean_value
    : "true" { true }
    | "false" { false }

sync
    : "(" "sync" fragment_id* ")"
    { transactions.Sync(fragments=$3) }

fragment_id
    : ":" SYMBOL
    { fragment_id_from_string($2) }

epoch
    : "(" "epoch" epoch_writes? epoch_reads? ")"
    { transactions.Epoch(writes=unwrap_option_or($3, []), reads=unwrap_option_or($4, [])) }

epoch_writes
    : "(" "writes" write* ")"
    { $3 }

write
    : define { transactions.Write(define=$1) }
    | undefine { transactions.Write(undefine=$1) }
    | context { transactions.Write(context=$1) }

define
    : "(" "define" fragment ")"
    { transactions.Define(fragment=$3) }

fragment
    : "(" "fragment" new_fragment_id declaration* ")"
    { construct_fragment($3, $4) }

new_fragment_id
    : fragment_id
    { seq(start_fragment($1), $1) }

declaration
    : def { logic.Declaration(def=$1) }
    | algorithm { logic.Declaration(algorithm=$1) }
    | constraint { logic.Declaration(constraint=$1) }
    | data { logic.Declaration(data=$1) }

def
    : "(" "def" relation_id abstraction attrs? ")"
    { logic.Def(name=$3, body=$4, attrs=unwrap_option_or($5, [])) }

relation_id
    : ":" SYMBOL { relation_id_from_string($2) }
    | INT { relation_id_from_int($1) }

abstraction
    : "(" bindings formula ")"
    { logic.Abstraction(vars=list_concat($2[0], $2[1]), value=$3) }

bindings
    : "[" binding* value_bindings? "]"
    { make_tuple($2, unwrap_option_or($3, [])) }

binding
    : SYMBOL "::" type
    { logic.Binding(var=logic.Var(name=$1), type=$3) }

type
    : unspecified_type { logic.Type(unspecified_type=$1) }
    | string_type { logic.Type(string_type=$1) }
    | int_type { logic.Type(int_type=$1) }
    | float_type { logic.Type(float_type=$1) }
    | uint128_type { logic.Type(uint128_type=$1) }
    | int128_type { logic.Type(int128_type=$1) }
    | date_type { logic.Type(date_type=$1) }
    | datetime_type { logic.Type(datetime_type=$1) }
    | missing_type { logic.Type(missing_type=$1) }
    | decimal_type { logic.Type(decimal_type=$1) }
    | boolean_type { logic.Type(boolean_type=$1) }

unspecified_type : "UNKNOWN" { logic.UnspecifiedType() }
string_type : "STRING" { logic.StringType() }
int_type : "INT" { logic.IntType() }
float_type : "FLOAT" { logic.FloatType() }
uint128_type : "UINT128" { logic.UInt128Type() }
int128_type : "INT128" { logic.Int128Type() }
date_type : "DATE" { logic.DateType() }
datetime_type : "DATETIME" { logic.DateTimeType() }
missing_type : "MISSING" { logic.MissingType() }

decimal_type
    : "(" "DECIMAL" INT INT ")"
    { logic.DecimalType(precision=int64_to_int32($3), scale=int64_to_int32($4)) }

boolean_type : "BOOLEAN" { logic.BooleanType() }

value_bindings
    : "|" binding*
    { $2 }

formula
    : true { logic.Formula(conjunction=$1) }
    | false { logic.Formula(disjunction=$1) }
    | exists { logic.Formula(exists=$1) }
    | reduce { logic.Formula(reduce=$1) }
    | conjunction { logic.Formula(conjunction=$1) }
    | disjunction { logic.Formula(disjunction=$1) }
    | not { logic.Formula(not=$1) }
    | ffi { logic.Formula(ffi=$1) }
    | atom { logic.Formula(atom=$1) }
    | pragma { logic.Formula(pragma=$1) }
    | primitive { logic.Formula(primitive=$1) }
    | rel_atom { logic.Formula(rel_atom=$1) }
    | cast { logic.Formula(cast=$1) }

true : "(" "true" ")" { logic.Conjunction(args=[]) }
false : "(" "false" ")" { logic.Disjunction(args=[]) }

exists
    : "(" "exists" bindings formula ")"
    { logic.Exists(body=logic.Abstraction(vars=list_concat($3[0], $3[1]), value=$4)) }

reduce
    : "(" "reduce" abstraction abstraction terms ")"
    { logic.Reduce(op=$3, body=$4, terms=$5) }

term
    : var { logic.Term(var=$1) }
    | constant { logic.Term(constant=$1) }

var : SYMBOL { logic.Var(name=$1) }
constant : value { $1 }

conjunction : "(" "and" formula* ")" { logic.Conjunction(args=$3) }
disjunction : "(" "or" formula* ")" { logic.Disjunction(args=$3) }
not : "(" "not" formula ")" { logic.Not(arg=$3) }

ffi
    : "(" "ffi" name ffi_args terms ")"
    { logic.FFI(name=$3, args=$4, terms=$5) }

ffi_args : "(" "args" abstraction* ")" { $3 }
terms : "(" "terms" term* ")" { $3 }
name : ":" SYMBOL { $2 }

atom
    : "(" "atom" relation_id term* ")"
    { logic.Atom(name=$3, terms=$4) }

pragma
    : "(" "pragma" name term* ")"
    { logic.Pragma(name=$3, terms=$4) }

primitive
    : eq { $1 }
    | lt { $1 }
    | lt_eq { $1 }
    | gt { $1 }
    | gt_eq { $1 }
    | add { $1 }
    | minus { $1 }
    | multiply { $1 }
    | divide { $1 }
    | "(" "primitive" name rel_term* ")"
    { logic.Primitive(name=$3, terms=$4) }

eq
    : "(" "=" term term ")"
    { logic.Primitive(name="rel_primitive_eq", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)]) }

lt
    : "(" "<" term term ")"
    { logic.Primitive(name="rel_primitive_lt_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)]) }

lt_eq
    : "(" "<=" term term ")"
    { logic.Primitive(name="rel_primitive_lt_eq_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)]) }

gt
    : "(" ">" term term ")"
    { logic.Primitive(name="rel_primitive_gt_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)]) }

gt_eq
    : "(" ">=" term term ")"
    { logic.Primitive(name="rel_primitive_gt_eq_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)]) }

add
    : "(" "+" term term term ")"
    { logic.Primitive(name="rel_primitive_add_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)]) }

minus
    : "(" "-" term term term ")"
    { logic.Primitive(name="rel_primitive_subtract_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)]) }

multiply
    : "(" "*" term term term ")"
    { logic.Primitive(name="rel_primitive_multiply_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)]) }

divide
    : "(" "/" term term term ")"
    { logic.Primitive(name="rel_primitive_divide_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)]) }

rel_term
    : specialized_value { logic.RelTerm(specialized_value=$1) }
    | term { logic.RelTerm(term=$1) }

specialized_value : "#" value { $2 }

rel_atom
    : "(" "relatom" name rel_term* ")"
    { logic.RelAtom(name=$3, terms=$4) }

cast
    : "(" "cast" term term ")"
    { logic.Cast(input=$3, result=$4) }

attrs : "(" "attrs" attribute* ")" { $3 }

attribute
    : "(" "attribute" name value* ")"
    { logic.Attribute(name=$3, args=$4) }

algorithm
    : "(" "algorithm" relation_id* script ")"
    { logic.Algorithm(global=$3, body=$4) }

script : "(" "script" construct* ")" { logic.Script(constructs=$3) }

construct
    : loop { logic.Construct(loop=$1) }
    | instruction { logic.Construct(instruction=$1) }

loop
    : "(" "loop" init script ")"
    { logic.Loop(init=$3, body=$4) }

init : "(" "init" instruction* ")" { $3 }

instruction
    : assign { logic.Instruction(assign=$1) }
    | upsert { logic.Instruction(upsert=$1) }
    | break { logic.Instruction(break=$1) }
    | monoid_def { logic.Instruction(monoid_def=$1) }
    | monus_def { logic.Instruction(monus_def=$1) }

assign
    : "(" "assign" relation_id abstraction attrs? ")"
    { logic.Assign(name=$3, body=$4, attrs=unwrap_option_or($5, [])) }

upsert
    : "(" "upsert" relation_id abstraction_with_arity attrs? ")"
    { let abstraction = $4[0] in let arity = $4[1] in logic.Upsert(name=$3, body=abstraction, attrs=unwrap_option_or($5, []), value_arity=arity) }

abstraction_with_arity
    : "(" bindings formula ")"
    { make_tuple(logic.Abstraction(vars=list_concat($2[0], $2[1]), value=$3), length($2[1])) }

break
    : "(" "break" relation_id abstraction attrs? ")"
    { logic.Break(name=$3, body=$4, attrs=unwrap_option_or($5, [])) }

monoid_def
    : "(" "monoid" monoid relation_id abstraction_with_arity attrs? ")"
    { let abstraction = $5[0] in let arity = $5[1] in logic.MonoidDef(monoid=$3, name=$4, body=abstraction, attrs=unwrap_option_or($6, []), value_arity=arity) }

monoid
    : or_monoid { logic.Monoid(or_monoid=$1) }
    | min_monoid { logic.Monoid(min_monoid=$1) }
    | max_monoid { logic.Monoid(max_monoid=$1) }
    | sum_monoid { logic.Monoid(sum_monoid=$1) }

or_monoid : "(" "or" ")" { logic.OrMonoid() }
min_monoid : "(" "min" type ")" { logic.MinMonoid(type=$3) }
max_monoid : "(" "max" type ")" { logic.MaxMonoid(type=$3) }
sum_monoid : "(" "sum" type ")" { logic.SumMonoid(type=$3) }

monus_def
    : "(" "monus" monoid relation_id abstraction_with_arity attrs? ")"
    { let abstraction = $5[0] in let arity = $5[1] in logic.MonusDef(monoid=$3, name=$4, body=abstraction, attrs=unwrap_option_or($6, []), value_arity=arity) }

constraint
    : "(" "functional_dependency" relation_id abstraction functional_dependency_keys functional_dependency_values ")"
    { logic.Constraint(name=$3, functional_dependency=logic.FunctionalDependency(guard=$4, keys=$5, values=$6)) }

functional_dependency_keys : "(" "keys" var* ")" { $3 }
functional_dependency_values : "(" "values" var* ")" { $3 }

data
    : rel_edb { logic.Data(rel_edb=$1) }
    | betree_relation { logic.Data(betree_relation=$1) }
    | csv_data { logic.Data(csv_data=$1) }

rel_edb_path : "[" STRING* "]" { $2 }
rel_edb_types : "[" type* "]" { $2 }

rel_edb
    : "(" "rel_edb" relation_id rel_edb_path rel_edb_types? ")"
    { logic.RelEDB(target_id=$3, path=$4, types=unwrap_option_or($5, [])) }

betree_relation : be_tree_relation { $1 }

be_tree_relation
    : "(" "betree_relation" relation_id be_tree_info ")"
    { logic.BeTreeRelation(name=$3, relation_info=$4) }

be_tree_info
    : "(" "betree_info" be_tree_info_key_types? be_tree_info_value_types? config_dict ")"
    { construct_betree_info(unwrap_option_or($3, []), unwrap_option_or($4, []), $5) }

be_tree_info_key_types : "(" "key_types" type* ")" { $3 }
be_tree_info_value_types : "(" "value_types" type* ")" { $3 }

csv_data : csvdata { $1 }
csv_columns : "(" "columns" csv_column* ")" { $3 }
csv_asof : "(" "asof" STRING ")" { $3 }

csvdata
    : "(" "csv_data" csvlocator csv_config csv_columns csv_asof ")"
    { logic.CSVData(locator=$3, config=$4, columns=$5, asof=$6) }

csv_locator_paths : "(" "paths" STRING* ")" { $3 }
csv_locator_inline_data : "(" "inline_data" STRING ")" { $3 }

csvlocator
    : "(" "csv_locator" csv_locator_paths? csv_locator_inline_data? ")"
    { logic.CSVLocator(paths=unwrap_option_or($3, []), inline_data=encode_string(unwrap_option_or($4, ""))) }

csv_config
    : "(" "csv_config" config_dict ")"
    { construct_csv_config($3) }

csv_column
    : "(" "column" STRING relation_id "[" type* "]" ")"
    { logic.CSVColumn(column_name=$3, target_id=$4, types=$6) }

undefine
    : "(" "undefine" fragment_id ")"
    { transactions.Undefine(fragment_id=$3) }

context
    : "(" "context" relation_id* ")"
    { transactions.Context(relations=$3) }

epoch_reads : "(" "reads" read* ")" { $3 }

read
    : demand { transactions.Read(demand=$1) }
    | output { transactions.Read(output=$1) }
    | what_if { transactions.Read(what_if=$1) }
    | abort { transactions.Read(abort=$1) }
    | export { transactions.Read(export=$1) }

demand
    : "(" "demand" relation_id ")"
    { transactions.Demand(relation_id=$3) }

output
    : "(" "output" name? relation_id ")"
    { transactions.Output(name=unwrap_option_or($3, "output"), relation_id=$4) }

what_if
    : "(" "what_if" name epoch ")"
    { transactions.WhatIf(branch=$3, epoch=$4) }

abort
    : "(" "abort" name? relation_id ")"
    { transactions.Abort(name=unwrap_option_or($3, "abort"), relation_id=$4) }

export
    : "(" "export" export_csv_config ")"
    { transactions.Export(csv_config=$3) }

export_csv_config
    : "(" "export_csv_config" export_csv_path export_csv_columns config_dict ")"
    { export_csv_config($3, $4, $5) }

export_csv_path : "(" "path" STRING ")" { $3 }
export_csv_columns : "(" "columns" export_csv_column* ")" { $3 }

export_csv_column
    : "(" "column" STRING relation_id ")"
    { transactions.ExportCSVColumn(column_name=$3, column_data=$4) }


%%


def _extract_value_int64(value: Optional[Value], default: int) -> int:
    if value is None:
        return default
    if value.HasField('int_value'):
        return value.int_value
    return default


def _extract_value_float64(value: Optional[Value], default: float) -> float:
    if value is None:
        return default
    if value.HasField('float_value'):
        return value.float_value
    return default


def _extract_value_string(value: Optional[Value], default: str) -> str:
    if value is None:
        return default
    if value.HasField('string_value'):
        return value.string_value
    return default


def _extract_value_boolean(value: Optional[Value], default: bool) -> bool:
    if value is None:
        return default
    if value.HasField('boolean_value'):
        return value.boolean_value
    return default


def _extract_value_bytes(value: Optional[Value], default: bytes) -> bytes:
    if value is None:
        return default
    if value.HasField('string_value'):
        return value.string_value.encode()
    return default


def _extract_value_uint128(value: Optional[Value], default: UInt128Value) -> UInt128Value:
    if value is None:
        return default
    if value.HasField('uint128_value'):
        return value.uint128_value
    return default


def _extract_value_string_list(value: Optional[Value], default: list[str]) -> list[str]:
    if value is None:
        return default
    if value.HasField('string_value'):
        return [value.string_value]
    return default


def construct_csv_config(config_dict: list[tuple[str, Value]]) -> CSVConfig:
    config = dict(config_dict)
    header_row = _extract_value_int64(config.get("csv_header_row"), 1)
    skip = _extract_value_int64(config.get("csv_skip"), 0)
    new_line = _extract_value_string(config.get("csv_new_line"), "")
    delimiter = _extract_value_string(config.get("csv_delimiter"), ",")
    quotechar = _extract_value_string(config.get("csv_quotechar"), '"')
    escapechar = _extract_value_string(config.get("csv_escapechar"), '"')
    comment = _extract_value_string(config.get("csv_comment"), "")
    missing_strings = _extract_value_string_list(config.get("csv_missing_strings"), [])
    decimal_separator = _extract_value_string(config.get("csv_decimal_separator"), ".")
    encoding = _extract_value_string(config.get("csv_encoding"), "utf-8")
    compression = _extract_value_string(config.get("csv_compression"), "auto")
    return CSVConfig(
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
    key_types: list[Type],
    value_types: list[Type],
    config_dict: list[tuple[str, Value]],
) -> BeTreeInfo:
    config = dict(config_dict)
    epsilon = _extract_value_float64(config.get("betree_config_epsilon"), 0.5)
    max_pivots = _extract_value_int64(config.get("betree_config_max_pivots"), 4)
    max_deltas = _extract_value_int64(config.get("betree_config_max_deltas"), 16)
    max_leaf = _extract_value_int64(config.get("betree_config_max_leaf"), 16)
    storage_config = BeTreeConfig(
        epsilon=epsilon,
        max_pivots=max_pivots,
        max_deltas=max_deltas,
        max_leaf=max_leaf,
    )
    root_pageid_val = config.get("betree_locator_root_pageid")
    root_pageid: Optional[UInt128Value] = None
    if root_pageid_val is not None:
        root_pageid = _extract_value_uint128(
            root_pageid_val,
            UInt128Value(low=0, high=0),
        )
    inline_data_val = config.get("betree_locator_inline_data")
    inline_data: Optional[bytes] = None
    if inline_data_val is not None:
        inline_data = _extract_value_bytes(inline_data_val, b"")
    element_count = _extract_value_int64(config.get("betree_locator_element_count"), 0)
    tree_height = _extract_value_int64(config.get("betree_locator_tree_height"), 0)
    relation_locator = BeTreeLocator(
        root_pageid=root_pageid,
        inline_data=inline_data,
        element_count=element_count,
        tree_height=tree_height,
    )
    return BeTreeInfo(
        key_types=key_types,
        value_types=value_types,
        storage_config=storage_config,
        relation_locator=relation_locator,
    )


def construct_configure(config_dict: list[tuple[str, Value]]) -> Configure:
    config = dict(config_dict)
    maintenance_level_val = config.get("ivm.maintenance_level")
    maintenance_level: str
    if (maintenance_level_val is not None
            and maintenance_level_val.HasField('string_value')):
        level_str = maintenance_level_val.string_value.upper()
        if level_str in ["OFF", "AUTO", "ALL"]:
            maintenance_level = "MAINTENANCE_LEVEL_" + level_str
        else:
            maintenance_level = level_str
    else:
        maintenance_level = "MAINTENANCE_LEVEL_OFF"
    ivm_config = IVMConfig(level=maintenance_level)
    semantics_version = _extract_value_int64(config.get("semantics_version"), 0)
    return Configure(
        semantics_version=semantics_version,
        ivm_config=ivm_config,
    )


def export_csv_config(
    path: str,
    columns: list[ExportCSVColumn],
    config_dict: list[tuple[str, Value]],
) -> ExportCSVConfig:
    config = dict(config_dict)
    partition_size = _extract_value_int64(config.get("partition_size"), 0)
    compression = _extract_value_string(config.get("compression"), "")
    syntax_header_row = _extract_value_boolean(config.get("syntax_header_row"), True)
    syntax_missing_string = _extract_value_string(config.get("syntax_missing_string"), "")
    syntax_delim = _extract_value_string(config.get("syntax_delim"), ",")
    syntax_quotechar = _extract_value_string(config.get("syntax_quotechar"), '"')
    syntax_escapechar = _extract_value_string(config.get("syntax_escapechar"), "\\")
    return ExportCSVConfig(
        path=path,
        data_columns=columns,
        partition_size=partition_size,
        compression=compression,
        syntax_header_row=syntax_header_row,
        syntax_missing_string=syntax_missing_string,
        syntax_delim=syntax_delim,
        syntax_quotechar=syntax_quotechar,
        syntax_escapechar=syntax_escapechar,
    )
