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
#
# Each rule has a construct action and a deconstruct action.
#
# Construct actions use `$$ = expr` to build the LHS value from the RHS
# elements ($1, $2, ...). If omitted, the default is `$$ = $N` when there
# is exactly one non-literal RHS element.
#
# Deconstruct actions use `$N = expr` assignments to extract RHS element
# values from the LHS value ($$). If omitted, the default is the identity
# deconstruct. Use `deconstruct if COND:` to guard the deconstructor: if the
# condition fails, the deconstructor returns None, signaling that this rule
# does not match the LHS value.
#
# The pretty printer uses the deconstruct actions. For nonterminals with
# multiple alternatives, it tries the rules in declaration order, choosing
# the first whose deconstructor returns a non-None value.


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
%nonterm attrs Sequence[logic.Attribute]
%nonterm betree_info logic.BeTreeInfo
%nonterm betree_info_key_types Sequence[logic.Type]
%nonterm betree_info_value_types Sequence[logic.Type]
%nonterm betree_relation logic.BeTreeRelation
%nonterm binding logic.Binding
%nonterm bindings Tuple[Sequence[logic.Binding], Sequence[logic.Binding]]
%nonterm boolean_type logic.BooleanType
%nonterm boolean_value Boolean
%nonterm break logic.Break
%nonterm cast logic.Cast
%nonterm config_dict Sequence[Tuple[String, logic.Value]]
%nonterm config_key_value Tuple[String, logic.Value]
%nonterm configure transactions.Configure
%nonterm conjunction logic.Conjunction
%nonterm constant logic.Value
%nonterm constraint logic.Constraint
%nonterm construct logic.Construct
%nonterm context transactions.Context
%nonterm csv_asof String
%nonterm csv_column logic.CSVColumn
%nonterm csv_columns Sequence[logic.CSVColumn]
%nonterm csv_config logic.CSVConfig
%nonterm csv_data logic.CSVData
%nonterm csv_locator_inline_data String
%nonterm csv_locator_paths Sequence[String]
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
%nonterm epoch_reads Sequence[transactions.Read]
%nonterm epoch_writes Sequence[transactions.Write]
%nonterm eq logic.Primitive
%nonterm exists logic.Exists
%nonterm export transactions.Export
%nonterm export_csv_column transactions.ExportCSVColumn
%nonterm export_csv_columns Sequence[transactions.ExportCSVColumn]
%nonterm export_csv_config transactions.ExportCSVConfig
%nonterm export_csv_path String
%nonterm export_csv_source transactions.ExportCSVSource
%nonterm false logic.Disjunction
%nonterm ffi logic.FFI
%nonterm ffi_args Sequence[logic.Abstraction]
%nonterm float_type logic.FloatType
%nonterm formula logic.Formula
%nonterm fragment fragments.Fragment
%nonterm fragment_id fragments.FragmentId
%nonterm functional_dependency_keys Sequence[logic.Var]
%nonterm functional_dependency_values Sequence[logic.Var]
%nonterm gt logic.Primitive
%nonterm gt_eq logic.Primitive
%nonterm init Sequence[logic.Instruction]
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
%nonterm rel_edb_path Sequence[String]
%nonterm rel_edb_types Sequence[logic.Type]
%nonterm rel_term logic.RelTerm
%nonterm relation_id logic.RelationId
%nonterm script logic.Script
%nonterm specialized_value logic.Value
%nonterm string_type logic.StringType
%nonterm sum_monoid logic.SumMonoid
%nonterm sync transactions.Sync
%nonterm term logic.Term
%nonterm terms Sequence[logic.Term]
%nonterm transaction transactions.Transaction
%nonterm true logic.Conjunction
%nonterm type logic.Type
%nonterm uint128_type logic.UInt128Type
%nonterm undefine transactions.Undefine
%nonterm unspecified_type logic.UnspecifiedType
%nonterm upsert logic.Upsert
%nonterm value logic.Value
%nonterm value_bindings Sequence[logic.Binding]
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
%validator_ignore_completeness ExportCSVColumns
%validator_ignore_completeness ExportCSVSource
%validator_ignore_completeness CSVConfig

%%

transaction
    : "(" "transaction" configure? sync? epoch* ")"
      construct: $$ = transactions.Transaction(epochs=$5, configure=builtin.unwrap_option_or($3, default_configure()), sync=$4)
      deconstruct:
        $3: Optional[transactions.Configure] = $$.configure if builtin.has_proto_field($$, "configure") else None
        $4: Optional[transactions.Sync] = $$.sync if builtin.has_proto_field($$, "sync") else None
        $5: Sequence[transactions.Epoch] = $$.epochs

configure
    : "(" "configure" config_dict ")"
      construct: $$ = construct_configure($3)
      deconstruct: $3: Sequence[Tuple[String, logic.Value]] = deconstruct_configure($$)

config_dict
    : "{" config_key_value* "}"

config_key_value
    : ":" SYMBOL value
      construct: $$ = builtin.tuple($2, $3)
      deconstruct:
        $2: String = $$[0]
        $3: logic.Value = $$[1]

value
    : date
      construct: $$ = logic.Value(date_value=$1)
      deconstruct if builtin.has_proto_field($$, 'date_value'):
        $1: logic.DateValue = $$.date_value
    | datetime
      construct: $$ = logic.Value(datetime_value=$1)
      deconstruct if builtin.has_proto_field($$, 'datetime_value'):
        $1: logic.DateTimeValue = $$.datetime_value
    | STRING
      construct: $$ = logic.Value(string_value=$1)
      deconstruct if builtin.has_proto_field($$, 'string_value'):
        $1: String = $$.string_value
    | INT
      construct: $$ = logic.Value(int_value=$1)
      deconstruct if builtin.has_proto_field($$, 'int_value'):
        $1: Int64 = $$.int_value
    | FLOAT
      construct: $$ = logic.Value(float_value=$1)
      deconstruct if builtin.has_proto_field($$, 'float_value'):
        $1: Float64 = $$.float_value
    | UINT128
      construct: $$ = logic.Value(uint128_value=$1)
      deconstruct if builtin.has_proto_field($$, 'uint128_value'):
        $1: logic.UInt128Value = $$.uint128_value
    | INT128
      construct: $$ = logic.Value(int128_value=$1)
      deconstruct if builtin.has_proto_field($$, 'int128_value'):
        $1: logic.Int128Value = $$.int128_value
    | DECIMAL
      construct: $$ = logic.Value(decimal_value=$1)
      deconstruct if builtin.has_proto_field($$, 'decimal_value'):
        $1: logic.DecimalValue = $$.decimal_value
    | "missing"
      construct: $$ = logic.Value(missing_value=logic.MissingValue())
    | boolean_value
      construct: $$ = logic.Value(boolean_value=$1)
      deconstruct if builtin.has_proto_field($$, 'boolean_value'):
        $1: Boolean = $$.boolean_value

date
    : "(" "date" INT INT INT ")"
      construct: $$ = logic.DateValue(year=builtin.int64_to_int32($3), month=builtin.int64_to_int32($4), day=builtin.int64_to_int32($5))
      deconstruct:
        $3: Int64 = builtin.int32_to_int64($$.year)
        $4: Int64 = builtin.int32_to_int64($$.month)
        $5: Int64 = builtin.int32_to_int64($$.day)

datetime
    : "(" "datetime" INT INT INT INT INT INT INT? ")"
      construct: $$ = logic.DateTimeValue(year=builtin.int64_to_int32($3), month=builtin.int64_to_int32($4), day=builtin.int64_to_int32($5), hour=builtin.int64_to_int32($6), minute=builtin.int64_to_int32($7), second=builtin.int64_to_int32($8), microsecond=builtin.int64_to_int32(builtin.unwrap_option_or($9, 0)))
      deconstruct:
        $3: Int64 = builtin.int32_to_int64($$.year)
        $4: Int64 = builtin.int32_to_int64($$.month)
        $5: Int64 = builtin.int32_to_int64($$.day)
        $6: Int64 = builtin.int32_to_int64($$.hour)
        $7: Int64 = builtin.int32_to_int64($$.minute)
        $8: Int64 = builtin.int32_to_int64($$.second)
        $9: Optional[Int64] = builtin.some(builtin.int32_to_int64($$.microsecond))

boolean_value
    : "true"
      construct: $$ = True
      deconstruct if $$:
        pass
    | "false"
      construct: $$ = False
      deconstruct if not $$:
        pass

sync
    : "(" "sync" fragment_id* ")"
      construct: $$ = transactions.Sync(fragments=$3)
      deconstruct: $3: Sequence[fragments.FragmentId] = $$.fragments

fragment_id
    : ":" SYMBOL
      construct: $$ = builtin.fragment_id_from_string($2)
      deconstruct: $2: String = builtin.fragment_id_to_string($$)

epoch
    : "(" "epoch" epoch_writes? epoch_reads? ")"
      construct: $$ = transactions.Epoch(writes=builtin.unwrap_option_or($3, list[transactions.Write]()), reads=builtin.unwrap_option_or($4, list[transactions.Read]()))
      deconstruct:
        $3: Optional[Sequence[transactions.Write]] = $$.writes if not builtin.is_empty($$.writes) else None
        $4: Optional[Sequence[transactions.Read]] = $$.reads if not builtin.is_empty($$.reads) else None

epoch_writes
    : "(" "writes" write* ")"

write
    : define
      construct: $$ = transactions.Write(define=$1)
      deconstruct if builtin.has_proto_field($$, 'define'):
        $1: transactions.Define = $$.define
    | undefine
      construct: $$ = transactions.Write(undefine=$1)
      deconstruct if builtin.has_proto_field($$, 'undefine'):
        $1: transactions.Undefine = $$.undefine
    | context
      construct: $$ = transactions.Write(context=$1)
      deconstruct if builtin.has_proto_field($$, 'context'):
        $1: transactions.Context = $$.context

define
    : "(" "define" fragment ")"
      construct: $$ = transactions.Define(fragment=$3)
      deconstruct: $3: fragments.Fragment = $$.fragment

fragment
    : "(" "fragment" new_fragment_id declaration* ")"
      construct: $$ = builtin.construct_fragment($3, $4)
      deconstruct:
        builtin.start_pretty_fragment($$)
        $3: fragments.FragmentId = $$.id
        $4: Sequence[logic.Declaration] = $$.declarations

new_fragment_id
    : fragment_id
      construct:
        builtin.start_fragment($1)
        $$ = $1

declaration
    : def
      construct: $$ = logic.Declaration(def=$1)
      deconstruct if builtin.has_proto_field($$, 'def'):
        $1: logic.Def = $$.def
    | algorithm
      construct: $$ = logic.Declaration(algorithm=$1)
      deconstruct if builtin.has_proto_field($$, 'algorithm'):
        $1: logic.Algorithm = $$.algorithm
    | constraint
      construct: $$ = logic.Declaration(constraint=$1)
      deconstruct if builtin.has_proto_field($$, 'constraint'):
        $1: logic.Constraint = $$.constraint
    | data
      construct: $$ = logic.Declaration(data=$1)
      deconstruct if builtin.has_proto_field($$, 'data'):
        $1: logic.Data = $$.data

def
    : "(" "def" relation_id abstraction attrs? ")"
      construct: $$ = logic.Def(name=$3, body=$4, attrs=builtin.unwrap_option_or($5, list[logic.Attribute]()))
      deconstruct:
        $3: logic.RelationId = $$.name
        $4: logic.Abstraction = $$.body
        $5: Optional[Sequence[logic.Attribute]] = $$.attrs if not builtin.is_empty($$.attrs) else None

relation_id
    : ":" SYMBOL
      construct: $$ = builtin.relation_id_from_string($2)
      deconstruct: $2: String = deconstruct_relation_id_string($$)
    | UINT128
      construct: $$ = builtin.relation_id_from_uint128($1)
      deconstruct: $1: logic.UInt128Value = deconstruct_relation_id_uint128($$)

abstraction
    : "(" bindings formula ")"
      construct: $$ = logic.Abstraction(vars=builtin.list_concat($2[0], $2[1]), value=$3)
      deconstruct:
        $2: Tuple[Sequence[logic.Binding], Sequence[logic.Binding]] = deconstruct_bindings($$)
        $3: logic.Formula = $$.value

bindings
    : "[" binding* value_bindings? "]"
      construct: $$ = builtin.tuple($2, builtin.unwrap_option_or($3, list[logic.Binding]()))
      deconstruct:
        $2: Sequence[logic.Binding] = $$[0]
        $3: Optional[Sequence[logic.Binding]] = $$[1] if not builtin.is_empty($$[1]) else None

binding
    : SYMBOL "::" type
      construct: $$ = logic.Binding(var=logic.Var(name=$1), type=$3)
      deconstruct:
        $1: String = $$.var.name
        $3: logic.Type = $$.type

type
    : unspecified_type
      construct: $$ = logic.Type(unspecified_type=$1)
      deconstruct if builtin.has_proto_field($$, 'unspecified_type'):
        $1: logic.UnspecifiedType = $$.unspecified_type
    | string_type
      construct: $$ = logic.Type(string_type=$1)
      deconstruct if builtin.has_proto_field($$, 'string_type'):
        $1: logic.StringType = $$.string_type
    | int_type
      construct: $$ = logic.Type(int_type=$1)
      deconstruct if builtin.has_proto_field($$, 'int_type'):
        $1: logic.IntType = $$.int_type
    | float_type
      construct: $$ = logic.Type(float_type=$1)
      deconstruct if builtin.has_proto_field($$, 'float_type'):
        $1: logic.FloatType = $$.float_type
    | uint128_type
      construct: $$ = logic.Type(uint128_type=$1)
      deconstruct if builtin.has_proto_field($$, 'uint128_type'):
        $1: logic.UInt128Type = $$.uint128_type
    | int128_type
      construct: $$ = logic.Type(int128_type=$1)
      deconstruct if builtin.has_proto_field($$, 'int128_type'):
        $1: logic.Int128Type = $$.int128_type
    | date_type
      construct: $$ = logic.Type(date_type=$1)
      deconstruct if builtin.has_proto_field($$, 'date_type'):
        $1: logic.DateType = $$.date_type
    | datetime_type
      construct: $$ = logic.Type(datetime_type=$1)
      deconstruct if builtin.has_proto_field($$, 'datetime_type'):
        $1: logic.DateTimeType = $$.datetime_type
    | missing_type
      construct: $$ = logic.Type(missing_type=$1)
      deconstruct if builtin.has_proto_field($$, 'missing_type'):
        $1: logic.MissingType = $$.missing_type
    | decimal_type
      construct: $$ = logic.Type(decimal_type=$1)
      deconstruct if builtin.has_proto_field($$, 'decimal_type'):
        $1: logic.DecimalType = $$.decimal_type
    | boolean_type
      construct: $$ = logic.Type(boolean_type=$1)
      deconstruct if builtin.has_proto_field($$, 'boolean_type'):
        $1: logic.BooleanType = $$.boolean_type

unspecified_type
    : "UNKNOWN"
      construct: $$ = logic.UnspecifiedType()

string_type
    : "STRING"
      construct: $$ = logic.StringType()

int_type
    : "INT"
      construct: $$ = logic.IntType()

float_type
    : "FLOAT"
      construct: $$ = logic.FloatType()

uint128_type
    : "UINT128"
      construct: $$ = logic.UInt128Type()

int128_type
    : "INT128"
      construct: $$ = logic.Int128Type()

date_type
    : "DATE"
      construct: $$ = logic.DateType()

datetime_type
    : "DATETIME"
      construct: $$ = logic.DateTimeType()

missing_type
    : "MISSING"
      construct: $$ = logic.MissingType()

decimal_type
    : "(" "DECIMAL" INT INT ")"
      construct: $$ = logic.DecimalType(precision=builtin.int64_to_int32($3), scale=builtin.int64_to_int32($4))
      deconstruct:
        $3: Int64 = builtin.int32_to_int64($$.precision)
        $4: Int64 = builtin.int32_to_int64($$.scale)

boolean_type
    : "BOOLEAN"
      construct: $$ = logic.BooleanType()

value_bindings
    : "|" binding*

formula
    : true
      construct: $$ = logic.Formula(conjunction=$1)
      deconstruct if builtin.has_proto_field($$, 'conjunction') and builtin.is_empty($$.conjunction.args):
        $1: logic.Conjunction = $$.conjunction
    | false
      construct: $$ = logic.Formula(disjunction=$1)
      deconstruct if builtin.has_proto_field($$, 'disjunction') and builtin.is_empty($$.disjunction.args):
        $1: logic.Disjunction = $$.disjunction
    | exists
      construct: $$ = logic.Formula(exists=$1)
      deconstruct if builtin.has_proto_field($$, 'exists'):
        $1: logic.Exists = $$.exists
    | reduce
      construct: $$ = logic.Formula(reduce=$1)
      deconstruct if builtin.has_proto_field($$, 'reduce'):
        $1: logic.Reduce = $$.reduce
    | conjunction
      construct: $$ = logic.Formula(conjunction=$1)
      deconstruct if builtin.has_proto_field($$, 'conjunction'):
        $1: logic.Conjunction = $$.conjunction
    | disjunction
      construct: $$ = logic.Formula(disjunction=$1)
      deconstruct if builtin.has_proto_field($$, 'disjunction'):
        $1: logic.Disjunction = $$.disjunction
    | not
      construct: $$ = logic.Formula(not=$1)
      deconstruct if builtin.has_proto_field($$, 'not'):
        $1: logic.Not = $$.not
    | ffi
      construct: $$ = logic.Formula(ffi=$1)
      deconstruct if builtin.has_proto_field($$, 'ffi'):
        $1: logic.FFI = $$.ffi
    | atom
      construct: $$ = logic.Formula(atom=$1)
      deconstruct if builtin.has_proto_field($$, 'atom'):
        $1: logic.Atom = $$.atom
    | pragma
      construct: $$ = logic.Formula(pragma=$1)
      deconstruct if builtin.has_proto_field($$, 'pragma'):
        $1: logic.Pragma = $$.pragma
    | primitive
      construct: $$ = logic.Formula(primitive=$1)
      deconstruct if builtin.has_proto_field($$, 'primitive'):
        $1: logic.Primitive = $$.primitive
    | rel_atom
      construct: $$ = logic.Formula(rel_atom=$1)
      deconstruct if builtin.has_proto_field($$, 'rel_atom'):
        $1: logic.RelAtom = $$.rel_atom
    | cast
      construct: $$ = logic.Formula(cast=$1)
      deconstruct if builtin.has_proto_field($$, 'cast'):
        $1: logic.Cast = $$.cast

true
    : "(" "true" ")"
      construct: $$ = logic.Conjunction(args=list[logic.Formula]())

false
    : "(" "false" ")"
      construct: $$ = logic.Disjunction(args=list[logic.Formula]())

exists
    : "(" "exists" bindings formula ")"
      construct: $$ = logic.Exists(body=logic.Abstraction(vars=builtin.list_concat($3[0], $3[1]), value=$4))
      deconstruct:
        $3: Tuple[Sequence[logic.Binding], Sequence[logic.Binding]] = deconstruct_bindings($$.body)
        $4: logic.Formula = $$.body.value

reduce
    : "(" "reduce" abstraction abstraction terms ")"
      construct: $$ = logic.Reduce(op=$3, body=$4, terms=$5)
      deconstruct:
        $3: logic.Abstraction = $$.op
        $4: logic.Abstraction = $$.body
        $5: Sequence[logic.Term] = $$.terms

term
    : var
      construct: $$ = logic.Term(var=$1)
      deconstruct if builtin.has_proto_field($$, 'var'):
        $1: logic.Var = $$.var
    | constant
      construct: $$ = logic.Term(constant=$1)
      deconstruct if builtin.has_proto_field($$, 'constant'):
        $1: logic.Value = $$.constant

var
    : SYMBOL
      construct: $$ = logic.Var(name=$1)
      deconstruct: $1: String = $$.name

constant
    : value

conjunction
    : "(" "and" formula* ")"
      construct: $$ = logic.Conjunction(args=$3)
      deconstruct: $3: Sequence[logic.Formula] = $$.args

disjunction
    : "(" "or" formula* ")"
      construct: $$ = logic.Disjunction(args=$3)
      deconstruct: $3: Sequence[logic.Formula] = $$.args

not
    : "(" "not" formula ")"
      construct: $$ = logic.Not(arg=$3)
      deconstruct: $3: logic.Formula = $$.arg

ffi
    : "(" "ffi" name ffi_args terms ")"
      construct: $$ = logic.FFI(name=$3, args=$4, terms=$5)
      deconstruct:
        $3: String = $$.name
        $4: Sequence[logic.Abstraction] = $$.args
        $5: Sequence[logic.Term] = $$.terms

ffi_args
    : "(" "args" abstraction* ")"

terms
    : "(" "terms" term* ")"

name
    : ":" SYMBOL

atom
    : "(" "atom" relation_id term* ")"
      construct: $$ = logic.Atom(name=$3, terms=$4)
      deconstruct:
        $3: logic.RelationId = $$.name
        $4: Sequence[logic.Term] = $$.terms

pragma
    : "(" "pragma" name term* ")"
      construct: $$ = logic.Pragma(name=$3, terms=$4)
      deconstruct:
        $3: String = $$.name
        $4: Sequence[logic.Term] = $$.terms

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
      construct: $$ = logic.Primitive(name=$3, terms=$4)
      deconstruct:
        $3: String = $$.name
        $4: Sequence[logic.RelTerm] = $$.terms

eq
    : "(" "=" term term ")"
      construct: $$ = logic.Primitive(name="rel_primitive_eq", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)])
      deconstruct if $$.name == "rel_primitive_eq":
        $3: logic.Term = $$.terms[0].term
        $4: logic.Term = $$.terms[1].term

lt
    : "(" "<" term term ")"
      construct: $$ = logic.Primitive(name="rel_primitive_lt_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)])
      deconstruct if $$.name == "rel_primitive_lt_monotype":
        $3: logic.Term = $$.terms[0].term
        $4: logic.Term = $$.terms[1].term

lt_eq
    : "(" "<=" term term ")"
      construct: $$ = logic.Primitive(name="rel_primitive_lt_eq_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)])
      deconstruct if $$.name == "rel_primitive_lt_eq_monotype":
        $3: logic.Term = $$.terms[0].term
        $4: logic.Term = $$.terms[1].term

gt
    : "(" ">" term term ")"
      construct: $$ = logic.Primitive(name="rel_primitive_gt_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)])
      deconstruct if $$.name == "rel_primitive_gt_monotype":
        $3: logic.Term = $$.terms[0].term
        $4: logic.Term = $$.terms[1].term

gt_eq
    : "(" ">=" term term ")"
      construct: $$ = logic.Primitive(name="rel_primitive_gt_eq_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4)])
      deconstruct if $$.name == "rel_primitive_gt_eq_monotype":
        $3: logic.Term = $$.terms[0].term
        $4: logic.Term = $$.terms[1].term

add
    : "(" "+" term term term ")"
      construct: $$ = logic.Primitive(name="rel_primitive_add_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)])
      deconstruct if $$.name == "rel_primitive_add_monotype":
        $3: logic.Term = $$.terms[0].term
        $4: logic.Term = $$.terms[1].term
        $5: logic.Term = $$.terms[2].term

minus
    : "(" "-" term term term ")"
      construct: $$ = logic.Primitive(name="rel_primitive_subtract_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)])
      deconstruct if $$.name == "rel_primitive_subtract_monotype":
        $3: logic.Term = $$.terms[0].term
        $4: logic.Term = $$.terms[1].term
        $5: logic.Term = $$.terms[2].term

multiply
    : "(" "*" term term term ")"
      construct: $$ = logic.Primitive(name="rel_primitive_multiply_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)])
      deconstruct if $$.name == "rel_primitive_multiply_monotype":
        $3: logic.Term = $$.terms[0].term
        $4: logic.Term = $$.terms[1].term
        $5: logic.Term = $$.terms[2].term

divide
    : "(" "/" term term term ")"
      construct: $$ = logic.Primitive(name="rel_primitive_divide_monotype", terms=[logic.RelTerm(term=$3), logic.RelTerm(term=$4), logic.RelTerm(term=$5)])
      deconstruct if $$.name == "rel_primitive_divide_monotype":
        $3: logic.Term = $$.terms[0].term
        $4: logic.Term = $$.terms[1].term
        $5: logic.Term = $$.terms[2].term

rel_term
    : specialized_value
      construct: $$ = logic.RelTerm(specialized_value=$1)
      deconstruct if builtin.has_proto_field($$, 'specialized_value'):
        $1: logic.Value = $$.specialized_value
    | term
      construct: $$ = logic.RelTerm(term=$1)
      deconstruct if builtin.has_proto_field($$, 'term'):
        $1: logic.Term = $$.term

specialized_value
    : "#" value

rel_atom
    : "(" "relatom" name rel_term* ")"
      construct: $$ = logic.RelAtom(name=$3, terms=$4)
      deconstruct:
        $3: String = $$.name
        $4: Sequence[logic.RelTerm] = $$.terms

cast
    : "(" "cast" term term ")"
      construct: $$ = logic.Cast(input=$3, result=$4)
      deconstruct:
        $3: logic.Term = $$.input
        $4: logic.Term = $$.result

attrs
    : "(" "attrs" attribute* ")"

attribute
    : "(" "attribute" name value* ")"
      construct: $$ = logic.Attribute(name=$3, args=$4)
      deconstruct:
        $3: String = $$.name
        $4: Sequence[logic.Value] = $$.args

algorithm
    : "(" "algorithm" relation_id* script ")"
      construct: $$ = logic.Algorithm(global=$3, body=$4)
      deconstruct:
        $3: Sequence[logic.RelationId] = $$.global
        $4: logic.Script = $$.body

script
    : "(" "script" construct* ")"
      construct: $$ = logic.Script(constructs=$3)
      deconstruct: $3: Sequence[logic.Construct] = $$.constructs

construct
    : loop
      construct: $$ = logic.Construct(loop=$1)
      deconstruct if builtin.has_proto_field($$, 'loop'):
        $1: logic.Loop = $$.loop
    | instruction
      construct: $$ = logic.Construct(instruction=$1)
      deconstruct if builtin.has_proto_field($$, 'instruction'):
        $1: logic.Instruction = $$.instruction

loop
    : "(" "loop" init script ")"
      construct: $$ = logic.Loop(init=$3, body=$4)
      deconstruct:
        $3: Sequence[logic.Instruction] = $$.init
        $4: logic.Script = $$.body

init
    : "(" "init" instruction* ")"

instruction
    : assign
      construct: $$ = logic.Instruction(assign=$1)
      deconstruct if builtin.has_proto_field($$, 'assign'):
        $1: logic.Assign = $$.assign
    | upsert
      construct: $$ = logic.Instruction(upsert=$1)
      deconstruct if builtin.has_proto_field($$, 'upsert'):
        $1: logic.Upsert = $$.upsert
    | break
      construct: $$ = logic.Instruction(break=$1)
      deconstruct if builtin.has_proto_field($$, 'break'):
        $1: logic.Break = $$.break
    | monoid_def
      construct: $$ = logic.Instruction(monoid_def=$1)
      deconstruct if builtin.has_proto_field($$, 'monoid_def'):
        $1: logic.MonoidDef = $$.monoid_def
    | monus_def
      construct: $$ = logic.Instruction(monus_def=$1)
      deconstruct if builtin.has_proto_field($$, 'monus_def'):
        $1: logic.MonusDef = $$.monus_def

assign
    : "(" "assign" relation_id abstraction attrs? ")"
      construct: $$ = logic.Assign(name=$3, body=$4, attrs=builtin.unwrap_option_or($5, list[logic.Attribute]()))
      deconstruct:
        $3: logic.RelationId = $$.name
        $4: logic.Abstraction = $$.body
        $5: Optional[Sequence[logic.Attribute]] = $$.attrs if not builtin.is_empty($$.attrs) else None

upsert
    : "(" "upsert" relation_id abstraction_with_arity attrs? ")"
      construct: $$ = logic.Upsert(name=$3, body=$4[0], attrs=builtin.unwrap_option_or($5, list[logic.Attribute]()), value_arity=$4[1])
      deconstruct:
        $3: logic.RelationId = $$.name
        $4: Tuple[logic.Abstraction, Int64] = builtin.tuple($$.body, $$.value_arity)
        $5: Optional[Sequence[logic.Attribute]] = $$.attrs if not builtin.is_empty($$.attrs) else None

abstraction_with_arity
    : "(" bindings formula ")"
      construct: $$ = builtin.tuple(logic.Abstraction(vars=builtin.list_concat($2[0], $2[1]), value=$3), builtin.length($2[1]))
      deconstruct:
        $2: Tuple[Sequence[logic.Binding], Sequence[logic.Binding]] = deconstruct_bindings_with_arity($$[0], $$[1])
        $3: logic.Formula = $$[0].value

break
    : "(" "break" relation_id abstraction attrs? ")"
      construct: $$ = logic.Break(name=$3, body=$4, attrs=builtin.unwrap_option_or($5, list[logic.Attribute]()))
      deconstruct:
        $3: logic.RelationId = $$.name
        $4: logic.Abstraction = $$.body
        $5: Optional[Sequence[logic.Attribute]] = $$.attrs if not builtin.is_empty($$.attrs) else None

monoid_def
    : "(" "monoid" monoid relation_id abstraction_with_arity attrs? ")"
      construct: $$ = logic.MonoidDef(monoid=$3, name=$4, body=$5[0], attrs=builtin.unwrap_option_or($6, list[logic.Attribute]()), value_arity=$5[1])
      deconstruct:
        $3: logic.Monoid = $$.monoid
        $4: logic.RelationId = $$.name
        $5: Tuple[logic.Abstraction, Int64] = builtin.tuple($$.body, $$.value_arity)
        $6: Optional[Sequence[logic.Attribute]] = $$.attrs if not builtin.is_empty($$.attrs) else None

monoid
    : or_monoid
      construct: $$ = logic.Monoid(or_monoid=$1)
      deconstruct if builtin.has_proto_field($$, 'or_monoid'):
        $1: logic.OrMonoid = $$.or_monoid
    | min_monoid
      construct: $$ = logic.Monoid(min_monoid=$1)
      deconstruct if builtin.has_proto_field($$, 'min_monoid'):
        $1: logic.MinMonoid = $$.min_monoid
    | max_monoid
      construct: $$ = logic.Monoid(max_monoid=$1)
      deconstruct if builtin.has_proto_field($$, 'max_monoid'):
        $1: logic.MaxMonoid = $$.max_monoid
    | sum_monoid
      construct: $$ = logic.Monoid(sum_monoid=$1)
      deconstruct if builtin.has_proto_field($$, 'sum_monoid'):
        $1: logic.SumMonoid = $$.sum_monoid

or_monoid
    : "(" "or" ")"
      construct: $$ = logic.OrMonoid()

min_monoid
    : "(" "min" type ")"
      construct: $$ = logic.MinMonoid(type=$3)
      deconstruct: $3: logic.Type = $$.type

max_monoid
    : "(" "max" type ")"
      construct: $$ = logic.MaxMonoid(type=$3)
      deconstruct: $3: logic.Type = $$.type

sum_monoid
    : "(" "sum" type ")"
      construct: $$ = logic.SumMonoid(type=$3)
      deconstruct: $3: logic.Type = $$.type

monus_def
    : "(" "monus" monoid relation_id abstraction_with_arity attrs? ")"
      construct: $$ = logic.MonusDef(monoid=$3, name=$4, body=$5[0], attrs=builtin.unwrap_option_or($6, list[logic.Attribute]()), value_arity=$5[1])
      deconstruct:
        $3: logic.Monoid = $$.monoid
        $4: logic.RelationId = $$.name
        $5: Tuple[logic.Abstraction, Int64] = builtin.tuple($$.body, $$.value_arity)
        $6: Optional[Sequence[logic.Attribute]] = $$.attrs if not builtin.is_empty($$.attrs) else None

constraint
    : "(" "functional_dependency" relation_id abstraction functional_dependency_keys functional_dependency_values ")"
      construct: $$ = logic.Constraint(name=$3, functional_dependency=logic.FunctionalDependency(guard=$4, keys=$5, values=$6))
      deconstruct:
        $3: logic.RelationId = $$.name
        $4: logic.Abstraction = $$.functional_dependency.guard
        $5: Sequence[logic.Var] = $$.functional_dependency.keys
        $6: Sequence[logic.Var] = $$.functional_dependency.values

functional_dependency_keys
    : "(" "keys" var* ")"

functional_dependency_values
    : "(" "values" var* ")"

data
    : rel_edb
      construct: $$ = logic.Data(rel_edb=$1)
      deconstruct if builtin.has_proto_field($$, 'rel_edb'):
        $1: logic.RelEDB = $$.rel_edb
    | betree_relation
      construct: $$ = logic.Data(betree_relation=$1)
      deconstruct if builtin.has_proto_field($$, 'betree_relation'):
        $1: logic.BeTreeRelation = $$.betree_relation
    | csv_data
      construct: $$ = logic.Data(csv_data=$1)
      deconstruct if builtin.has_proto_field($$, 'csv_data'):
        $1: logic.CSVData = $$.csv_data

rel_edb_path
    : "[" STRING* "]"

rel_edb_types
    : "[" type* "]"

rel_edb
    : "(" "rel_edb" relation_id rel_edb_path rel_edb_types ")"
      construct: $$ = logic.RelEDB(target_id=$3, path=$4, types=$5)
      deconstruct:
        $3: logic.RelationId = $$.target_id
        $4: Sequence[String] = $$.path
        $5: Sequence[logic.Type] = $$.types

betree_relation
    : "(" "betree_relation" relation_id betree_info ")"
      construct: $$ = logic.BeTreeRelation(name=$3, relation_info=$4)
      deconstruct:
        $3: logic.RelationId = $$.name
        $4: logic.BeTreeInfo = $$.relation_info

betree_info
    : "(" "betree_info" betree_info_key_types betree_info_value_types config_dict ")"
      construct: $$ = construct_betree_info($3, $4, $5)
      deconstruct:
        $3: Sequence[logic.Type] = $$.key_types
        $4: Sequence[logic.Type] = $$.value_types
        $5: Sequence[Tuple[String, logic.Value]] = deconstruct_betree_info_config($$)

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
      construct: $$ = logic.CSVData(locator=$3, config=$4, columns=$5, asof=$6)
      deconstruct:
        $3: logic.CSVLocator = $$.locator
        $4: logic.CSVConfig = $$.config
        $5: Sequence[logic.CSVColumn] = $$.columns
        $6: String = $$.asof

csv_locator_paths
    : "(" "paths" STRING* ")"

csv_locator_inline_data
    : "(" "inline_data" STRING ")"

csvlocator
    : "(" "csv_locator" csv_locator_paths? csv_locator_inline_data? ")"
      construct: $$ = logic.CSVLocator(paths=builtin.unwrap_option_or($3, list[str]()), inline_data=builtin.encode_string(builtin.unwrap_option_or($4, "")))
      deconstruct:
        $3: Optional[Sequence[String]] = $$.paths if not builtin.is_empty($$.paths) else None
        $4: Optional[String] = builtin.decode_string($$.inline_data) if builtin.decode_string($$.inline_data) != "" else None

csv_config
    : "(" "csv_config" config_dict ")"
      construct: $$ = construct_csv_config($3)
      deconstruct: $3: Sequence[Tuple[String, logic.Value]] = deconstruct_csv_config($$)

csv_column
    : "(" "column" STRING relation_id "[" type* "]" ")"
      construct: $$ = logic.CSVColumn(column_name=$3, target_id=$4, types=$6)
      deconstruct:
        $3: String = $$.column_name
        $4: logic.RelationId = $$.target_id
        $6: Sequence[logic.Type] = $$.types

undefine
    : "(" "undefine" fragment_id ")"
      construct: $$ = transactions.Undefine(fragment_id=$3)
      deconstruct: $3: fragments.FragmentId = $$.fragment_id

context
    : "(" "context" relation_id* ")"
      construct: $$ = transactions.Context(relations=$3)
      deconstruct: $3: Sequence[logic.RelationId] = $$.relations

epoch_reads
    : "(" "reads" read* ")"

read
    : demand
      construct: $$ = transactions.Read(demand=$1)
      deconstruct if builtin.has_proto_field($$, 'demand'):
        $1: transactions.Demand = $$.demand
    | output
      construct: $$ = transactions.Read(output=$1)
      deconstruct if builtin.has_proto_field($$, 'output'):
        $1: transactions.Output = $$.output
    | what_if
      construct: $$ = transactions.Read(what_if=$1)
      deconstruct if builtin.has_proto_field($$, 'what_if'):
        $1: transactions.WhatIf = $$.what_if
    | abort
      construct: $$ = transactions.Read(abort=$1)
      deconstruct if builtin.has_proto_field($$, 'abort'):
        $1: transactions.Abort = $$.abort
    | export
      construct: $$ = transactions.Read(export=$1)
      deconstruct if builtin.has_proto_field($$, 'export'):
        $1: transactions.Export = $$.export

demand
    : "(" "demand" relation_id ")"
      construct: $$ = transactions.Demand(relation_id=$3)
      deconstruct: $3: logic.RelationId = $$.relation_id

output
    : "(" "output" name relation_id ")"
      construct: $$ = transactions.Output(name=$3, relation_id=$4)
      deconstruct:
        $3: String = $$.name
        $4: logic.RelationId = $$.relation_id

what_if
    : "(" "what_if" name epoch ")"
      construct: $$ = transactions.WhatIf(branch=$3, epoch=$4)
      deconstruct:
        $3: String = $$.branch
        $4: transactions.Epoch = $$.epoch

abort
    : "(" "abort" name? relation_id ")"
      construct: $$ = transactions.Abort(name=builtin.unwrap_option_or($3, "abort"), relation_id=$4)
      deconstruct:
        $3: Optional[String] = $$.name if $$.name != "abort" else None
        $4: logic.RelationId = $$.relation_id

export
    : "(" "export" export_csv_config ")"
      construct: $$ = transactions.Export(csv_config=$3)
      deconstruct: $3: transactions.ExportCSVConfig = $$.csv_config

export_csv_config
    : "(" "export_csv_config_v2" export_csv_path export_csv_source csv_config ")"
      construct: $$ = construct_export_csv_config_with_source($3, $4, $5)
      deconstruct:
        $3: String = $$.path
        $4: transactions.ExportCSVSource = $$.csv_source
        $5: logic.CSVConfig = $$.csv_config
    | "(" "export_csv_config" export_csv_path "(" "columns" export_csv_column* ")" config_dict ")"
      construct: $$ = construct_export_csv_config($3, $6, $8)
      deconstruct if not builtin.has_proto_field($$, 'csv_source'):
        $3: String = $$.path
        $6: Sequence[transactions.ExportCSVColumn] = $$.data_columns
        $8: Sequence[Tuple[String, logic.Value]] = deconstruct_export_csv_config($$)

export_csv_path
    : "(" "path" STRING ")"

export_csv_column
    : "(" "column" STRING relation_id ")"
      construct: $$ = transactions.ExportCSVColumn(column_name=$3, column_data=$4)
      deconstruct:
        $3: String = $$.column_name
        $4: logic.RelationId = $$.column_data

export_csv_source
    : "(" "gnf_columns" export_csv_column* ")"
      construct: $$ = transactions.ExportCSVSource(gnf_columns=transactions.ExportCSVColumns(columns=$3))
      deconstruct if builtin.has_proto_field($$, 'gnf_columns'):
        $3: Sequence[transactions.ExportCSVColumn] = $$.gnf_columns.columns
    | "(" "table_def" relation_id ")"
      construct: $$ = transactions.ExportCSVSource(table_def=$3)
      deconstruct if builtin.has_proto_field($$, 'table_def'):
        $3: logic.RelationId = $$.table_def


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

def _extract_value_string_list(value: Optional[logic.Value], default: Sequence[String]) -> Sequence[String]:
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


def _try_extract_value_string_list(value: Optional[logic.Value]) -> Optional[Sequence[String]]:
    if value is not None and builtin.has_proto_field(builtin.unwrap_option(value), 'string_value'):
        return [builtin.unwrap_option(value).string_value]
    return None


def construct_csv_config(config_dict: Sequence[Tuple[String, logic.Value]]) -> logic.CSVConfig:
    config: Dict[String, logic.Value] = builtin.dict_from_list(config_dict)
    header_row: Int32 = _extract_value_int32(builtin.dict_get(config, "csv_header_row"), 1)
    skip: int = _extract_value_int64(builtin.dict_get(config, "csv_skip"), 0)
    new_line: str = _extract_value_string(builtin.dict_get(config, "csv_new_line"), "")
    delimiter: str = _extract_value_string(builtin.dict_get(config, "csv_delimiter"), ",")
    quotechar: str = _extract_value_string(builtin.dict_get(config, "csv_quotechar"), "\"")
    escapechar: str = _extract_value_string(builtin.dict_get(config, "csv_escapechar"), "\"")
    comment: str = _extract_value_string(builtin.dict_get(config, "csv_comment"), "")
    missing_strings: Sequence[String] = _extract_value_string_list(builtin.dict_get(config, "csv_missing_strings"), list[str]())
    decimal_separator: str = _extract_value_string(builtin.dict_get(config, "csv_decimal_separator"), ".")
    encoding: str = _extract_value_string(builtin.dict_get(config, "csv_encoding"), "utf-8")
    compression: str = _extract_value_string(builtin.dict_get(config, "csv_compression"), "auto")
    partition_size: int = _extract_value_int64(builtin.dict_get(config, "partition_size"), 0)
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
        partition_size=partition_size,
    )


def construct_betree_info(
    key_types: Sequence[logic.Type],
    value_types: Sequence[logic.Type],
    config_dict: Sequence[Tuple[String, logic.Value]],
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

def construct_configure(config_dict: Sequence[Tuple[String, logic.Value]]) -> transactions.Configure:
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

def construct_export_csv_config(
    path: String,
    columns: Sequence[transactions.ExportCSVColumn],
    config_dict: Sequence[Tuple[String, logic.Value]],
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

def construct_export_csv_config_with_source(
    path: String,
    csv_source: Any,
    csv_config: Optional[logic.CSVConfig],
) -> transactions.ExportCSVConfig:
    return transactions.ExportCSVConfig(
        path=path,
        csv_source=csv_source,
        csv_config=csv_config,
    )


def _make_value_int32(v: Int32) -> logic.Value:
    return logic.Value(int_value=builtin.int32_to_int64(v))


def _make_value_int64(v: int) -> logic.Value:
    return logic.Value(int_value=v)


def _make_value_float64(v: float) -> logic.Value:
    return logic.Value(float_value=v)


def _make_value_string(v: str) -> logic.Value:
    return logic.Value(string_value=v)


def _make_value_boolean(v: bool) -> logic.Value:
    return logic.Value(boolean_value=v)


def _make_value_uint128(v: logic.UInt128Value) -> logic.Value:
    return logic.Value(uint128_value=v)


def is_default_configure(cfg: transactions.Configure) -> bool:
    if cfg.semantics_version != 0:
        return False
    if cfg.ivm_config.level != transactions.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
        return False
    return True


def deconstruct_configure(msg: transactions.Configure) -> List[Tuple[String, logic.Value]]:
    result: List[Tuple[String, logic.Value]] = list[Tuple[String, logic.Value]]()
    if msg.ivm_config.level == transactions.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO:
        builtin.list_push(result, builtin.tuple("ivm.maintenance_level", _make_value_string("auto")))
    elif msg.ivm_config.level == transactions.MaintenanceLevel.MAINTENANCE_LEVEL_ALL:
        builtin.list_push(result, builtin.tuple("ivm.maintenance_level", _make_value_string("all")))
    elif msg.ivm_config.level == transactions.MaintenanceLevel.MAINTENANCE_LEVEL_OFF:
        builtin.list_push(result, builtin.tuple("ivm.maintenance_level", _make_value_string("off")))
    builtin.list_push(result, builtin.tuple("semantics_version", _make_value_int64(msg.semantics_version)))
    return builtin.list_sort(result)


def deconstruct_csv_config(msg: logic.CSVConfig) -> List[Tuple[String, logic.Value]]:
    result: List[Tuple[String, logic.Value]] = list[Tuple[String, logic.Value]]()
    builtin.list_push(result, builtin.tuple("csv_header_row", _make_value_int32(msg.header_row)))
    builtin.list_push(result, builtin.tuple("csv_skip", _make_value_int64(msg.skip)))
    if msg.new_line != "":
        builtin.list_push(result, builtin.tuple("csv_new_line", _make_value_string(msg.new_line)))
    builtin.list_push(result, builtin.tuple("csv_delimiter", _make_value_string(msg.delimiter)))
    builtin.list_push(result, builtin.tuple("csv_quotechar", _make_value_string(msg.quotechar)))
    builtin.list_push(result, builtin.tuple("csv_escapechar", _make_value_string(msg.escapechar)))
    if msg.comment != "":
        builtin.list_push(result, builtin.tuple("csv_comment", _make_value_string(msg.comment)))
    for missing_string in msg.missing_strings:
        builtin.list_push(result, builtin.tuple("csv_missing_strings", _make_value_string(missing_string)))
    builtin.list_push(result, builtin.tuple("csv_decimal_separator", _make_value_string(msg.decimal_separator)))
    builtin.list_push(result, builtin.tuple("csv_encoding", _make_value_string(msg.encoding)))
    builtin.list_push(result, builtin.tuple("csv_compression", _make_value_string(msg.compression)))
    if msg.partition_size != 0:
      builtin.list_push(result, builtin.tuple("csv_partition_size", _make_value_int64(msg.partition_size)))
    return builtin.list_sort(result)



def deconstruct_betree_info_config(msg: logic.BeTreeInfo) -> List[Tuple[String, logic.Value]]:
    result: List[Tuple[String, logic.Value]] = list[Tuple[String, logic.Value]]()
    builtin.list_push(result, builtin.tuple("betree_config_epsilon", _make_value_float64(msg.storage_config.epsilon)))
    builtin.list_push(result, builtin.tuple("betree_config_max_pivots", _make_value_int64(msg.storage_config.max_pivots)))
    builtin.list_push(result, builtin.tuple("betree_config_max_deltas", _make_value_int64(msg.storage_config.max_deltas)))
    builtin.list_push(result, builtin.tuple("betree_config_max_leaf", _make_value_int64(msg.storage_config.max_leaf)))
    if builtin.has_proto_field(msg.relation_locator, "root_pageid"):
        if msg.relation_locator.root_pageid is not None:
            builtin.list_push(result, builtin.tuple("betree_locator_root_pageid", _make_value_uint128(builtin.unwrap_option(msg.relation_locator.root_pageid))))
    if builtin.has_proto_field(msg.relation_locator, "inline_data"):
        if msg.relation_locator.inline_data is not None:
            builtin.list_push(result, builtin.tuple("betree_locator_inline_data", _make_value_string(builtin.decode_string(builtin.unwrap_option(msg.relation_locator.inline_data)))))
    builtin.list_push(result, builtin.tuple("betree_locator_element_count", _make_value_int64(msg.relation_locator.element_count)))
    builtin.list_push(result, builtin.tuple("betree_locator_tree_height", _make_value_int64(msg.relation_locator.tree_height)))
    return builtin.list_sort(result)


def deconstruct_export_csv_config(msg: transactions.ExportCSVConfig) -> List[Tuple[String, logic.Value]]:
    result: List[Tuple[String, logic.Value]] = list[Tuple[String, logic.Value]]()
    if msg.partition_size is not None:
        builtin.list_push(result, builtin.tuple("partition_size", _make_value_int64(builtin.unwrap_option(msg.partition_size))))
    if msg.compression is not None:
        builtin.list_push(result, builtin.tuple("compression", _make_value_string(builtin.unwrap_option(msg.compression))))
    if msg.syntax_header_row is not None:
        builtin.list_push(result, builtin.tuple("syntax_header_row", _make_value_boolean(builtin.unwrap_option(msg.syntax_header_row))))
    if msg.syntax_missing_string is not None:
        builtin.list_push(result, builtin.tuple("syntax_missing_string", _make_value_string(builtin.unwrap_option(msg.syntax_missing_string))))
    if msg.syntax_delim is not None:
        builtin.list_push(result, builtin.tuple("syntax_delim", _make_value_string(builtin.unwrap_option(msg.syntax_delim))))
    if msg.syntax_quotechar is not None:
        builtin.list_push(result, builtin.tuple("syntax_quotechar", _make_value_string(builtin.unwrap_option(msg.syntax_quotechar))))
    if msg.syntax_escapechar is not None:
        builtin.list_push(result, builtin.tuple("syntax_escapechar", _make_value_string(builtin.unwrap_option(msg.syntax_escapechar))))
    return builtin.list_sort(result)


def deconstruct_relation_id_string(msg: logic.RelationId) -> Optional[String]:
    name: String = builtin.relation_id_to_string(msg)
    if name != "":
        return name
    return None


def deconstruct_relation_id_uint128(msg: logic.RelationId) -> Optional[logic.UInt128Value]:
    name: String = builtin.relation_id_to_string(msg)
    if name == "":
        return builtin.relation_id_to_uint128(msg)
    return None


def deconstruct_bindings(abs: logic.Abstraction) -> Tuple[Sequence[logic.Binding], Sequence[logic.Binding]]:
    n: int = builtin.length(abs.vars)
    return builtin.tuple(builtin.list_slice(abs.vars, 0, n), list[logic.Binding]())


def deconstruct_bindings_with_arity(abs: logic.Abstraction, value_arity: int) -> Tuple[Sequence[logic.Binding], Sequence[logic.Binding]]:
    n: int = builtin.length(abs.vars)
    key_end: int = n - value_arity
    return builtin.tuple(builtin.list_slice(abs.vars, 0, key_end), builtin.list_slice(abs.vars, key_end, n))
