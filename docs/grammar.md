# LQP S-Expression Grammar

This document describes the S-expression syntax of the Logical Query Protocol.
It is auto-generated from `grammar.y` with construct/deconstruct actions removed.

## Terminals

- **DECIMAL** &mdash; `[-]?\d+\.\d+d\d+`
- **FLOAT32** &mdash; `([-]?\d+\.\d+f32|inf32|nan32)`
- **FLOAT** &mdash; `([-]?\d+\.\d+|inf|nan)`
- **INT32** &mdash; `[-]?\d+i32`
- **INT** &mdash; `[-]?\d+`
- **UINT32** &mdash; `\d+u32`
- **INT128** &mdash; `[-]?\d+i128`
- **STRING** &mdash; `"(?:[^"\\]|\\.)*"`
- **SYMBOL** &mdash; `[a-zA-Z_][a-zA-Z0-9_.#/-]*`
- **UINT128** &mdash; `0x[0-9a-fA-F]+`

### Token Aliases (formatted variants)

These are display variants used in the pretty printer; they parse identically to the base token.

- **FORMATTED_DECIMAL** &rarr; DECIMAL
- **FORMATTED_FLOAT** &rarr; FLOAT
- **FORMATTED_FLOAT32** &rarr; FLOAT32
- **FORMATTED_INT** &rarr; INT
- **FORMATTED_INT128** &rarr; INT128
- **FORMATTED_INT32** &rarr; INT32
- **FORMATTED_STRING** &rarr; STRING
- **FORMATTED_UINT128** &rarr; UINT128
- **FORMATTED_UINT32** &rarr; UINT32

## Grammar Rules

### transaction

The top-level unit of communication. Groups one or more epochs
with optional configuration and synchronization directives.

&ensp;`(` `transaction` [configure](#configure)? [sync](#sync)? [epoch](#epoch)* `)`  

### configure

Transaction-level configuration settings (e.g., IVM maintenance level, semantics version).

&ensp;`(` `configure` [config_dict](#config_dict) `)`  

### config_dict

A dictionary of key-value pairs enclosed in braces.

&ensp;`{` [config_key_value](#config_key_value)* `}`  

### config_key_value

A single key-value entry in a config dictionary. The key is a colon-prefixed symbol.

&ensp;`:` SYMBOL [raw_value](#raw_value)  

### value

A typed constant value. Uses formatted token variants for pretty-printable output.

&ensp;[date](#date)  
| [datetime](#datetime)  
| FORMATTED_STRING  
| FORMATTED_INT32  
| FORMATTED_INT  
| FORMATTED_FLOAT32  
| FORMATTED_FLOAT  
| FORMATTED_UINT32  
| FORMATTED_UINT128  
| FORMATTED_INT128  
| FORMATTED_DECIMAL  
| `missing`  
| [boolean_value](#boolean_value)  

### raw_value

A typed constant value using raw (unformatted) token variants.

&ensp;[raw_date](#raw_date)  
| [raw_datetime](#raw_datetime)  
| STRING  
| INT32  
| INT  
| FLOAT32  
| FLOAT  
| UINT32  
| UINT128  
| INT128  
| DECIMAL  
| `missing`  
| [boolean_value](#boolean_value)  

### raw_date

A date literal with year, month, day components (raw token variant).

&ensp;`(` `date` INT INT INT `)`  

### date

A date literal with year, month, day components (formatted token variant).

&ensp;`(` `date` FORMATTED_INT FORMATTED_INT FORMATTED_INT `)`  

### raw_datetime

A datetime literal with year, month, day, hour, minute, second, and optional
microsecond components (raw token variant).

&ensp;`(` `datetime` INT INT INT INT INT INT INT? `)`  

### datetime

A datetime literal with year, month, day, hour, minute, second, and optional
microsecond components (formatted token variant).

&ensp;`(` `datetime` FORMATTED_INT FORMATTED_INT FORMATTED_INT FORMATTED_INT FORMATTED_INT FORMATTED_INT FORMATTED_INT? `)`  

### boolean_value

A boolean literal: `true` or `false`.

&ensp;`true`  
| `false`  

### sync

Synchronization directive listing fragments that must be loaded before evaluation.

&ensp;`(` `sync` [fragment_id](#fragment_id)* `)`  

### fragment_id

A colon-prefixed identifier for a fragment.

&ensp;`:` SYMBOL  

### epoch

An epoch is a unit of execution within a transaction, containing optional writes and reads.

&ensp;`(` `epoch` [epoch_writes](#epoch_writes)? [epoch_reads](#epoch_reads)? `)`  

### epoch_writes

The write section of an epoch, containing zero or more write operations.

&ensp;`(` `writes` [write](#write)* `)`  

### write

A single write operation: define, undefine, context, or snapshot.

&ensp;[define](#define)  
| [undefine](#undefine)  
| [context](#context)  
| [snapshot](#snapshot)  

### define

Installs a fragment of declarations into the database.

&ensp;`(` `define` [fragment](#fragment) `)`  

### fragment

A named group of declarations (defs, algorithms, constraints, data).

&ensp;`(` `fragment` [new_fragment_id](#new_fragment_id) [declaration](#declaration)* `)`  

### new_fragment_id

&ensp;[fragment_id](#fragment_id)  

### declaration

A single declaration within a fragment.

&ensp;[def](#def)  
| [algorithm](#algorithm)  
| [constraint](#constraint)  
| [data](#data)  

### def

A rule definition: binds a relation name to an abstraction (the rule body),
with optional attributes.

&ensp;`(` `def` [relation_id](#relation_id) [abstraction](#abstraction) [attrs](#attrs)? `)`  

### relation_id

Identifies a relation, either by a colon-prefixed symbolic name or a numeric hash.

&ensp;`:` SYMBOL  
| UINT128  

### abstraction

A lambda-like construct: a list of typed variable bindings followed by a formula body.

&ensp;`(` [bindings](#bindings) [formula](#formula) `)`  

### bindings

A bracketed list of variable bindings, with an optional value-bindings section
separated by `|`.

&ensp;`[` [binding](#binding)* [value_bindings](#value_bindings)? `]`  

### binding

A single typed variable binding: `name :: type`.

&ensp;SYMBOL `::` [type](#type)  

### type

A type annotation for a variable binding.

&ensp;[unspecified_type](#unspecified_type)  
| [string_type](#string_type)  
| [int_type](#int_type)  
| [float_type](#float_type)  
| [uint128_type](#uint128_type)  
| [int128_type](#int128_type)  
| [date_type](#date_type)  
| [datetime_type](#datetime_type)  
| [missing_type](#missing_type)  
| [decimal_type](#decimal_type)  
| [boolean_type](#boolean_type)  
| [int32_type](#int32_type)  
| [float32_type](#float32_type)  
| [uint32_type](#uint32_type)  

### unspecified_type

&ensp;`UNKNOWN`  

### string_type

&ensp;`STRING`  

### int32_type

&ensp;`INT32`  

### int_type

&ensp;`INT`  

### float32_type

&ensp;`FLOAT32`  

### float_type

&ensp;`FLOAT`  

### uint32_type

&ensp;`UINT32`  

### uint128_type

&ensp;`UINT128`  

### int128_type

&ensp;`INT128`  

### date_type

&ensp;`DATE`  

### datetime_type

&ensp;`DATETIME`  

### missing_type

&ensp;`MISSING`  

### decimal_type

A fixed-point decimal type with precision and scale parameters.

&ensp;`(` `DECIMAL` INT INT `)`  

### boolean_type

&ensp;`BOOLEAN`  

### value_bindings

The value-bindings section of a bindings list, separated from key bindings by `|`.
Used to distinguish key and value variables in upsert and monoid operations.

&ensp;`|` [binding](#binding)*  

### formula

A logical formula: the body of an abstraction. Can be a conjunction, disjunction,
negation, existential quantification, reduction, atom, primitive, or other form.

&ensp;[true](#true)  
| [false](#false)  
| [exists](#exists)  
| [reduce](#reduce)  
| [conjunction](#conjunction)  
| [disjunction](#disjunction)  
| [not](#not)  
| [ffi](#ffi)  
| [atom](#atom)  
| [pragma](#pragma)  
| [primitive](#primitive)  
| [rel_atom](#rel_atom)  
| [cast](#cast)  

### true

The trivially true formula (empty conjunction).

&ensp;`(` `true` `)`  

### false

The trivially false formula (empty disjunction).

&ensp;`(` `false` `)`  

### exists

Existential quantification: introduces locally scoped variables.

&ensp;`(` `exists` [bindings](#bindings) [formula](#formula) `)`  

### reduce

Aggregation: applies a binary operator (op) over the results of a body abstraction,
with initial seed terms.

&ensp;`(` `reduce` [abstraction](#abstraction) [abstraction](#abstraction) [terms](#terms) `)`  

### term

A term is either a variable or a constant value.

&ensp;[var](#var)  
| [value](#value)  

### var

A variable reference.

&ensp;SYMBOL  

### conjunction

Logical AND of zero or more formulas.

&ensp;`(` `and` [formula](#formula)* `)`  

### disjunction

Logical OR of zero or more formulas.

&ensp;`(` `or` [formula](#formula)* `)`  

### not

Logical negation of a formula.

&ensp;`(` `not` [formula](#formula) `)`  

### ffi

A foreign function interface call with a name, abstraction arguments, and terms.

&ensp;`(` `ffi` [name](#name) [ffi_args](#ffi_args) [terms](#terms) `)`  

### ffi_args

The argument abstractions of an FFI call.

&ensp;`(` `args` [abstraction](#abstraction)* `)`  

### terms

A parenthesized list of terms.

&ensp;`(` `terms` [term](#term)* `)`  

### name

A colon-prefixed symbolic name.

&ensp;`:` SYMBOL  

### atom

A relational atom: applies a named relation to a list of terms.

&ensp;`(` `atom` [relation_id](#relation_id) [term](#term)* `)`  

### pragma

A compiler pragma: a named directive with term arguments.

&ensp;`(` `pragma` [name](#name) [term](#term)* `)`  

### primitive

A built-in primitive operation. Includes syntactic sugar for common comparisons
and arithmetic (`=`, `<`, `+`, etc.) as well as a generic named form.

&ensp;[eq](#eq)  
| [lt](#lt)  
| [lt_eq](#lt_eq)  
| [gt](#gt)  
| [gt_eq](#gt_eq)  
| [add](#add)  
| [minus](#minus)  
| [multiply](#multiply)  
| [divide](#divide)  
| `(` `primitive` [name](#name) [rel_term](#rel_term)* `)`  

### eq

&ensp;`(` `=` [term](#term) [term](#term) `)`  

### lt

&ensp;`(` `<` [term](#term) [term](#term) `)`  

### lt_eq

&ensp;`(` `<=` [term](#term) [term](#term) `)`  

### gt

&ensp;`(` `>` [term](#term) [term](#term) `)`  

### gt_eq

&ensp;`(` `>=` [term](#term) [term](#term) `)`  

### add

&ensp;`(` `+` [term](#term) [term](#term) [term](#term) `)`  

### minus

&ensp;`(` `-` [term](#term) [term](#term) [term](#term) `)`  

### multiply

&ensp;`(` `*` [term](#term) [term](#term) [term](#term) `)`  

### divide

&ensp;`(` `/` [term](#term) [term](#term) [term](#term) `)`  

### rel_term

A relational term: either a regular term or a specialized (hash-prefixed) constant value.

&ensp;[specialized_value](#specialized_value)  
| [term](#term)  

### specialized_value

A hash-prefixed constant value used for type specialization in primitives and rel_atoms.

&ensp;`#` [raw_value](#raw_value)  

### rel_atom

A relational atom with support for specialized value terms.

&ensp;`(` `relatom` [name](#name) [rel_term](#rel_term)* `)`  

### cast

A type cast from an input term to a result term.

&ensp;`(` `cast` [term](#term) [term](#term) `)`  

### attrs

A list of attributes attached to a def, algorithm, or instruction.

&ensp;`(` `attrs` [attribute](#attribute)* `)`  

### attribute

A single named attribute with zero or more value arguments.

&ensp;`(` `attribute` [name](#name) [raw_value](#raw_value)* `)`  

### algorithm

An imperative algorithm declaration with global relation references, a script body,
and optional attributes.

&ensp;`(` `algorithm` [relation_id](#relation_id)* [script](#script) [attrs](#attrs)? `)`  

### script

The body of an algorithm: a sequence of constructs (loops and instructions).

&ensp;`(` `script` [construct](#construct)* `)`  

### construct

A single construct within a script: either a loop or an instruction.

&ensp;[loop](#loop)  
| [instruction](#instruction)  

### loop

A loop construct with initialization instructions and a script body.

&ensp;`(` `loop` [init](#init) [script](#script) [attrs](#attrs)? `)`  

### init

The initialization block of a loop.

&ensp;`(` `init` [instruction](#instruction)* `)`  

### instruction

A single imperative instruction within a script or loop.

&ensp;[assign](#assign)  
| [upsert](#upsert)  
| [break](#break)  
| [monoid_def](#monoid_def)  
| [monus_def](#monus_def)  

### assign

Assigns a relation to the result of an abstraction (replaces existing tuples).

&ensp;`(` `assign` [relation_id](#relation_id) [abstraction](#abstraction) [attrs](#attrs)? `)`  

### upsert

Merges tuples into a relation using a monoid-based update (insert or update existing).

&ensp;`(` `upsert` [relation_id](#relation_id) [abstraction_with_arity](#abstraction_with_arity) [attrs](#attrs)? `)`  

### abstraction_with_arity

An abstraction that distinguishes key bindings from value bindings via the `|` separator.
The value arity is derived from the number of value bindings.

&ensp;`(` [bindings](#bindings) [formula](#formula) `)`  

### break

A loop termination condition: breaks when the relation matches the abstraction.

&ensp;`(` `break` [relation_id](#relation_id) [abstraction](#abstraction) [attrs](#attrs)? `)`  

### monoid_def

Defines an aggregation over a relation using a monoid (or, min, max, sum).

&ensp;`(` `monoid` [monoid](#monoid) [relation_id](#relation_id) [abstraction_with_arity](#abstraction_with_arity) [attrs](#attrs)? `)`  

### monoid

The type of aggregation monoid.

&ensp;[or_monoid](#or_monoid)  
| [min_monoid](#min_monoid)  
| [max_monoid](#max_monoid)  
| [sum_monoid](#sum_monoid)  

### or_monoid

&ensp;`(` `or` `)`  

### min_monoid

&ensp;`(` `min` [type](#type) `)`  

### max_monoid

&ensp;`(` `max` [type](#type) `)`  

### sum_monoid

&ensp;`(` `sum` [type](#type) `)`  

### monus_def

Defines a monus (subtraction) operation over a relation using a monoid.

&ensp;`(` `monus` [monoid](#monoid) [relation_id](#relation_id) [abstraction_with_arity](#abstraction_with_arity) [attrs](#attrs)? `)`  

### constraint

A functional dependency constraint on a relation: given the key variables,
the value variables are uniquely determined.

&ensp;`(` `functional_dependency` [relation_id](#relation_id) [abstraction](#abstraction) [functional_dependency_keys](#functional_dependency_keys) [functional_dependency_values](#functional_dependency_values) `)`  

### functional_dependency_keys

&ensp;`(` `keys` [var](#var)* `)`  

### functional_dependency_values

&ensp;`(` `values` [var](#var)* `)`  

### data

A data source declaration: external data (EDB), B-tree, CSV, or Iceberg.

&ensp;[edb](#edb)  
| [betree_relation](#betree_relation)  
| [csv_data](#csv_data)  
| [iceberg_data](#iceberg_data)  

### edb_path

&ensp;`[` STRING* `]`  

### edb_types

&ensp;`[` [type](#type)* `]`  

### edb

An extensional database (EDB) declaration: maps a relation to stored data at a given
path with specified column types.

&ensp;`(` `edb` [relation_id](#relation_id) [edb_path](#edb_path) [edb_types](#edb_types) `)`  

### betree_relation

A B-epsilon-tree backed relation with storage configuration and locator info.

&ensp;`(` `betree_relation` [relation_id](#relation_id) [betree_info](#betree_info) `)`  

### betree_info

Storage metadata for a B-tree relation: key/value types and configuration parameters.

&ensp;`(` `betree_info` [betree_info_key_types](#betree_info_key_types) [betree_info_value_types](#betree_info_value_types) [config_dict](#config_dict) `)`  

### betree_info_key_types

&ensp;`(` `key_types` [type](#type)* `)`  

### betree_info_value_types

&ensp;`(` `value_types` [type](#type)* `)`  

### gnf_columns

A list of GNF (Generalized Normal Form) column definitions.

&ensp;`(` `columns` [gnf_column](#gnf_column)* `)`  

### csv_asof

A timestamp indicating the point-in-time for the CSV data snapshot.

&ensp;`(` `asof` STRING `)`  

### csv_data

A CSV data source with locator, configuration, column definitions, and a snapshot timestamp.

&ensp;`(` `csv_data` [csvlocator](#csvlocator) [csv_config](#csv_config) [gnf_columns](#gnf_columns) [csv_asof](#csv_asof) `)`  

### csv_locator_paths

&ensp;`(` `paths` STRING* `)`  

### csv_locator_inline_data

&ensp;`(` `inline_data` STRING `)`  

### csvlocator

Locates CSV data: either by file paths, inline data, or both.

&ensp;`(` `csv_locator` [csv_locator_paths](#csv_locator_paths)? [csv_locator_inline_data](#csv_locator_inline_data)? `)`  

### csv_config

CSV parsing configuration (delimiter, quotechar, escapechar, encoding, etc.).

&ensp;`(` `csv_config` [config_dict](#config_dict) `)`  

### gnf_column_path

The path identifying a column: a single string or a bracketed list of strings for nested paths.

&ensp;STRING  
| `[` STRING* `]`  

### gnf_column

A single GNF column definition with a path, optional target relation, and column types.

&ensp;`(` `column` [gnf_column_path](#gnf_column_path) [relation_id](#relation_id)? `[` [type](#type)* `]` `)`  

### iceberg_property_entry

&ensp;`(` `prop` STRING STRING `)`  

### iceberg_masked_property_entry

&ensp;`(` `prop` STRING STRING `)`  

### iceberg_from_snapshot

&ensp;`(` `from_snapshot` STRING `)`  

### iceberg_locator_table_name

&ensp;`(` `table_name` STRING `)`  

### iceberg_locator_namespace

&ensp;`(` `namespace` STRING* `)`  

### iceberg_locator_warehouse

&ensp;`(` `warehouse` STRING `)`  

### iceberg_locator

Identifies an Iceberg table by its name, namespace, and warehouse.

&ensp;`(` `iceberg_locator` [iceberg_locator_table_name](#iceberg_locator_table_name) [iceberg_locator_namespace](#iceberg_locator_namespace) [iceberg_locator_warehouse](#iceberg_locator_warehouse) `)`  

### iceberg_catalog_config_scope

&ensp;`(` `scope` STRING `)`  

### iceberg_catalog_uri

&ensp;`(` `catalog_uri` STRING `)`  

### iceberg_properties

&ensp;`(` `properties` [iceberg_property_entry](#iceberg_property_entry)* `)`  

### iceberg_auth_properties

&ensp;`(` `auth_properties` [iceberg_masked_property_entry](#iceberg_masked_property_entry)* `)`  

### iceberg_catalog_config

Configuration for an Iceberg catalog: URI, optional scope, properties, and auth properties.

&ensp;`(` `iceberg_catalog_config` [iceberg_catalog_uri](#iceberg_catalog_uri) [iceberg_catalog_config_scope](#iceberg_catalog_config_scope)? [iceberg_properties](#iceberg_properties) [iceberg_auth_properties](#iceberg_auth_properties) `)`  

### iceberg_to_snapshot

&ensp;`(` `to_snapshot` STRING `)`  

### iceberg_data

An Iceberg data source with locator, catalog config, columns, optional snapshot range,
and a flag indicating whether it returns delta data.

&ensp;`(` `iceberg_data` [iceberg_locator](#iceberg_locator) [iceberg_catalog_config](#iceberg_catalog_config) [gnf_columns](#gnf_columns) [iceberg_from_snapshot](#iceberg_from_snapshot)? [iceberg_to_snapshot](#iceberg_to_snapshot)? [boolean_value](#boolean_value) `)`  

### undefine

Removes a previously defined fragment from the database.

&ensp;`(` `undefine` [fragment_id](#fragment_id) `)`  

### context

Declares the context relations that are visible for the current epoch.

&ensp;`(` `context` [relation_id](#relation_id)* `)`  

### snapshot_mapping

Maps a destination EDB path to a source relation for snapshotting.

&ensp;[edb_path](#edb_path) [relation_id](#relation_id)  

### snapshot

Snapshots relations into EDB storage at a given prefix path.

&ensp;`(` `snapshot` [edb_path](#edb_path) [snapshot_mapping](#snapshot_mapping)* `)`  

### epoch_reads

The read section of an epoch, containing zero or more read operations.

&ensp;`(` `reads` [read](#read)* `)`  

### read

A single read operation: demand, output, what-if, abort, or export.

&ensp;[demand](#demand)  
| [output](#output)  
| [what_if](#what_if)  
| [abort](#abort)  
| [export](#export)  

### demand

Requests evaluation of a relation without naming the output.

&ensp;`(` `demand` [relation_id](#relation_id) `)`  

### output

Requests evaluation of a relation and assigns a name to the output.

&ensp;`(` `output` [name](#name) [relation_id](#relation_id) `)`  

### what_if

A hypothetical branch: evaluates an epoch in a named sandbox without committing writes.

&ensp;`(` `what_if` [name](#name) [epoch](#epoch) `)`  

### abort

Aborts the transaction if the given relation is non-empty, with an optional name.

&ensp;`(` `abort` [name](#name)? [relation_id](#relation_id) `)`  

### export

Exports data to an external format (CSV or Iceberg).

&ensp;`(` `export` [export_csv_config](#export_csv_config) `)`  
| `(` `export_iceberg` [export_iceberg_config](#export_iceberg_config) `)`  

### export_csv_config

Configuration for CSV export. The v2 variant uses a source specification and csv_config;
the legacy variant uses explicit column list and config dict.

&ensp;`(` `export_csv_config_v2` [export_csv_path](#export_csv_path) [export_csv_source](#export_csv_source) [csv_config](#csv_config) `)`  
| `(` `export_csv_config` [export_csv_path](#export_csv_path) [export_csv_columns_list](#export_csv_columns_list) [config_dict](#config_dict) `)`  

### export_csv_path

&ensp;`(` `path` STRING `)`  

### export_csv_columns_list

&ensp;`(` `columns` [export_csv_column](#export_csv_column)* `)`  

### export_csv_column

&ensp;`(` `column` STRING [relation_id](#relation_id) `)`  

### export_csv_source

The data source for a v2 CSV export: either explicit GNF columns or a table definition.

&ensp;`(` `gnf_columns` [export_csv_column](#export_csv_column)* `)`  
| `(` `table_def` [relation_id](#relation_id) `)`  

### export_iceberg_table_def

&ensp;`(` `table_def` [relation_id](#relation_id) `)`  

### iceberg_table_properties

&ensp;`(` `table_properties` [iceberg_property_entry](#iceberg_property_entry)* `)`  

### export_iceberg_config

Configuration for Iceberg export: locator, catalog config, table definition,
table properties, and optional additional config.

&ensp;`(` `export_iceberg_config` [iceberg_locator](#iceberg_locator) [iceberg_catalog_config](#iceberg_catalog_config) [export_iceberg_table_def](#export_iceberg_table_def) [iceberg_table_properties](#iceberg_table_properties) [config_dict](#config_dict)? `)`  
