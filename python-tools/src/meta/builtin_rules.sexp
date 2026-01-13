;; Builtin grammar rules for LQP
;;
;; These rules define constructs that cannot be auto-generated from protobuf
;; definitions, including value literals, date/datetime parsing, configuration
;; syntax, bindings, abstractions, type literals, and operators.

;; ============================================================================
;; Value Rules
;; ============================================================================

;; value <- date (DateValue -> Value via date_value oneof)
(rule (lhs value (Message logic Value))
  (rhs (nonterm date (Message logic DateValue)))
  (lambda
    ((value (Message logic DateValue)))
    (call (message logic Value) (call (oneof date_value) (var value (Message logic DateValue))))))

;; value <- datetime (DateTimeValue -> Value via datetime_value oneof)
(rule (lhs value (Message logic Value))
  (rhs (nonterm datetime (Message logic DateTimeValue)))
  (lambda
    ((value (Message logic DateTimeValue)))
    (call (message logic Value) (call (oneof datetime_value) (var value (Message logic DateTimeValue))))))

;; value <- STRING
(rule (lhs value (Message logic Value))
  (rhs (term STRING String))
  (lambda
    ((value String))
    (call (message logic Value) (call (oneof string_value) (var value String)))))

;; value <- INT
(rule (lhs value (Message logic Value))
  (rhs (term INT Int64))
  (lambda ((value Int64)) (call (message logic Value) (call (oneof int_value) (var value Int64)))))

;; value <- FLOAT
(rule (lhs value (Message logic Value))
  (rhs (term FLOAT Float64))
  (lambda
    ((value Float64))
    (call (message logic Value) (call (oneof float_value) (var value Float64)))))

;; value <- UINT128
(rule (lhs value (Message logic Value))
  (rhs (term UINT128 (Message logic UInt128Value)))
  (lambda
    ((value (Message logic UInt128Value)))
    (call (message logic Value) (call (oneof uint128_value) (var value (Message logic UInt128Value))))))

;; value <- INT128
(rule (lhs value (Message logic Value))
  (rhs (term INT128 (Message logic Int128Value)))
  (lambda
    ((value (Message logic Int128Value)))
    (call (message logic Value) (call (oneof int128_value) (var value (Message logic Int128Value))))))

;; value <- DECIMAL
(rule (lhs value (Message logic Value))
  (rhs (term DECIMAL (Message logic DecimalValue)))
  (lambda
    ((value (Message logic DecimalValue)))
    (call (message logic Value) (call (oneof decimal_value) (var value (Message logic DecimalValue))))))

;; value <- "missing"
(rule (lhs value (Message logic Value))
  (rhs "missing")
  (lambda
    ()
    (call (message logic Value) (call (oneof missing_value) (call (message logic MissingValue))))))

;; boolean_value <- "true"
(rule (lhs boolean_value Boolean)
  (rhs "true")
  (lambda () (lit true)))

;; boolean_value <- "false"
(rule (lhs boolean_value Boolean)
  (rhs "false")
  (lambda () (lit false)))

;; value <- boolean_value
(rule (lhs value (Message logic Value))
  (rhs (nonterm boolean_value Boolean))
  (lambda
    ((value Boolean))
    (call (message logic Value) (call (oneof boolean_value) (var value Boolean)))))

;; date <- "(" "date" INT INT INT ")"
(rule (lhs date (Message logic DateValue))
  (rhs "(" "date" (term INT Int64) (term INT Int64) (term INT Int64) ")")
  (lambda
    ((year Int64) (month Int64) (day Int64))
    (call (message logic DateValue) (var year Int64) (var month Int64) (var day Int64))))

;; datetime <- "(" "datetime" INT INT INT INT INT INT INT? ")"
(rule (lhs datetime (Message logic DateTimeValue))
  (rhs
    "("
    "datetime"
    (term INT Int64)
    (term INT Int64)
    (term INT Int64)
    (term INT Int64)
    (term INT Int64)
    (term INT Int64)
    (option (term INT Int64))
    ")")
  (lambda
    ((year Int64)
    (month Int64)
    (day Int64)
    (hour Int64)
    (minute Int64)
    (second Int64)
    (microsecond (Option Int64)))
    (call
    (message logic DateTimeValue)
    (var year Int64)
    (var month Int64)
    (var day Int64)
    (var hour Int64)
    (var minute Int64)
    (var second Int64)
    (call (builtin unwrap_option_or) (var microsecond (Option Int64)) (lit 0)))))

;; ============================================================================
;; Transaction Rules
;; ============================================================================

;; config_dict <- "{" config_key_value* "}"
(rule (lhs config_dict (List (Tuple String (Message logic Value))))
  (rhs "{" (star (nonterm config_key_value (Tuple String (Message logic Value)))) "}")
  (lambda
    ((x (List (Tuple String (Message logic Value)))))
    (var x (List (Tuple String (Message logic Value))))))

;; config_key_value <- COLON_SYMBOL value
(rule (lhs config_key_value (Tuple String (Message logic Value)))
  (rhs (term COLON_SYMBOL String) (nonterm value (Message logic Value)))
  (lambda
    ((symbol String) (value (Message logic Value)))
    (call (builtin make_tuple) (var symbol String) (var value (Message logic Value)))))

;; transaction <- "(" "transaction" configure? sync? epoch* ")"
(rule (lhs transaction (Message transactions Transaction))
  (rhs
    "("
    "transaction"
    (option (nonterm configure (Message transactions Configure)))
    (option (nonterm sync (Message transactions Sync)))
    (star (nonterm epoch (Message transactions Epoch)))
    ")")
  (lambda
    ((configure (Option (Message transactions Configure)))
    (sync (Option (Message transactions Sync)))
    (epochs (List (Message transactions Epoch))))
    (call
    (message transactions Transaction)
    (var epochs (List (Message transactions Epoch)))
    (call
    (builtin unwrap_option_or)
    (var configure (Option (Message transactions Configure)))
    (call (builtin construct_configure) (list (Tuple String (Message logic Value)))))
    (var sync (Option (Message transactions Sync))))))

;; configure <- "(" "configure" config_dict ")"
(rule (lhs configure (Message transactions Configure))
  (rhs "(" "configure" (nonterm config_dict (List (Tuple String (Message logic Value)))) ")")
  (lambda
    ((config_dict (List (Tuple String (Message logic Value)))))
    (call (builtin construct_configure) (var config_dict (List (Tuple String (Message logic Value)))))))

;; ============================================================================
;; Bindings Rules
;; ============================================================================

;; bindings <- "[" binding* value_bindings? "]"
(rule (lhs bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
  (rhs
    "["
    (star (nonterm binding (Message logic Binding)))
    (option (nonterm value_bindings (List (Message logic Binding))))
    "]")
  (lambda
    ((keys (List (Message logic Binding))) (values (Option (List (Message logic Binding)))))
    (call
    (builtin make_tuple)
    (var keys (List (Message logic Binding)))
    (call
    (builtin unwrap_option_or)
    (var values (Option (List (Message logic Binding))))
    (list (Message logic Binding))))))

;; value_bindings <- "|" binding*
(rule (lhs value_bindings (List (Message logic Binding)))
  (rhs "|" (star (nonterm binding (Message logic Binding))))
  (lambda ((x (List (Message logic Binding)))) (var x (List (Message logic Binding)))))

;; binding <- SYMBOL "::" type
(rule (lhs binding (Message logic Binding))
  (rhs (term SYMBOL String) "::" (nonterm type (Message logic Type)))
  (lambda
    ((symbol String) (type (Message logic Type)))
    (call
    (message logic Binding)
    (call (message logic Var) (var symbol String))
    (var type (Message logic Type)))))

;; abstraction_with_arity <- "(" bindings formula ")"
(rule (lhs abstraction_with_arity (Tuple (Message logic Abstraction) Int64))
  (rhs
    "("
    (nonterm bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
    (nonterm formula (Message logic Formula))
    ")")
  (lambda
    ((bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
    (formula (Message logic Formula)))
    (call
    (builtin make_tuple)
    (call
    (message logic Abstraction)
    (call
    (builtin list_concat)
    (call
    (builtin fst)
    (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))))
    (call
    (builtin snd)
    (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))))
    (var formula (Message logic Formula)))
    (call
    (builtin length)
    (call
    (builtin snd)
    (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))))))))

;; abstraction <- "(" bindings formula ")"
(rule (lhs abstraction (Message logic Abstraction))
  (rhs
    "("
    (nonterm bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
    (nonterm formula (Message logic Formula))
    ")")
  (lambda
    ((bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
    (formula (Message logic Formula)))
    (call
    (message logic Abstraction)
    (call
    (builtin list_concat)
    (call
    (builtin fst)
    (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))))
    (call
    (builtin snd)
    (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))))
    (var formula (Message logic Formula)))))

;; ============================================================================
;; Formula Rules
;; ============================================================================

;; true <- "(" "true" ")"
(rule (lhs true (Message logic Conjunction))
  (rhs "(" "true" ")")
  (lambda () (call (message logic Conjunction) (list (Message logic Formula)))))

;; false <- "(" "false" ")"
(rule (lhs false (Message logic Disjunction))
  (rhs "(" "false" ")")
  (lambda () (call (message logic Disjunction) (list (Message logic Formula)))))

;; formula <- true
(rule (lhs formula (Message logic Formula))
  (rhs (nonterm true (Message logic Conjunction)))
  (lambda
    ((value (Message logic Conjunction)))
    (call (message logic Formula) (call (oneof conjunction) (var value (Message logic Conjunction))))))

;; formula <- false
(rule (lhs formula (Message logic Formula))
  (rhs (nonterm false (Message logic Disjunction)))
  (lambda
    ((value (Message logic Disjunction)))
    (call (message logic Formula) (call (oneof disjunction) (var value (Message logic Disjunction))))))

(mark-nonfinal formula)

;; ============================================================================
;; Export Rules
;; ============================================================================

;; export <- "(" "export" export_csvconfig ")"
(rule (lhs export (Message transactions Export))
  (rhs "(" "export" (nonterm export_csvconfig (Message transactions ExportCSVConfig)) ")")
  (lambda
    ((config (Message transactions ExportCSVConfig)))
    (call
    (message transactions Export)
    (call (oneof csv_config) (var config (Message transactions ExportCSVConfig))))))

;; export_csv_path <- "(" "path" STRING ")"
(rule (lhs export_csvpath String)
  (rhs "(" "path" (term STRING String) ")")
  (lambda ((x String)) (var x String)))

;; export_csvconfig <- "(" "export_csv_config" export_csv_path export_csv_columns config_dict ")"
(rule (lhs export_csvconfig (Message transactions ExportCSVConfig))
  (rhs
    "("
    "export_csv_config"
    (nonterm export_csvpath String)
    (nonterm export_csvcolumns (List (Message transactions ExportCSVColumn)))
    (nonterm config_dict (List (Tuple String (Message logic Value))))
    ")")
  (lambda
    ((path String)
    (columns (List (Message transactions ExportCSVColumn)))
    (config (List (Tuple String (Message logic Value)))))
    (call
    (builtin export_csv_config)
    (var path String)
    (var columns (List (Message transactions ExportCSVColumn)))
    (var config (List (Tuple String (Message logic Value)))))))

;; export_csv_columns <- "(" "columns" export_csv_column* ")"
(rule (lhs export_csvcolumns (List (Message transactions ExportCSVColumn)))
  (rhs "(" "columns" (star (nonterm export_csvcolumn (Message transactions ExportCSVColumn))) ")")
  (lambda
    ((x (List (Message transactions ExportCSVColumn))))
    (var x (List (Message transactions ExportCSVColumn)))))

;; export_csv_column <- "(" "column" STRING relation_id ")"
(rule (lhs export_csvcolumn (Message transactions ExportCSVColumn))
  (rhs "(" "column" (term STRING String) (nonterm relation_id (Message logic RelationId)) ")")
  (lambda
    ((name String) (relation_id (Message logic RelationId)))
    (call
    (message transactions ExportCSVColumn)
    (var name String)
    (var relation_id (Message logic RelationId)))))

;; ============================================================================
;; ID Rules
;; ============================================================================

;; name <- COLON_SYMBOL
(rule (lhs name String)
  (rhs (term COLON_SYMBOL String))
  (lambda ((x String)) (var x String)))

;; var <- SYMBOL
(rule (lhs var (Message logic Var))
  (rhs (term SYMBOL String))
  (lambda ((symbol String)) (call (message logic Var) (var symbol String))))

;; fragment_id <- COLON_SYMBOL
(rule (lhs fragment_id (Message fragments FragmentId))
  (rhs (term COLON_SYMBOL String))
  (lambda ((symbol String)) (call (builtin fragment_id_from_string) (var symbol String))))

;; relation_id <- COLON_SYMBOL
(rule (lhs relation_id (Message logic RelationId))
  (rhs (term COLON_SYMBOL String))
  (lambda ((symbol String)) (call (builtin relation_id_from_string) (var symbol String))))

;; relation_id <- INT
(rule (lhs relation_id (Message logic RelationId))
  (rhs (term INT Int64))
  (lambda ((INT Int64)) (call (builtin relation_id_from_int) (var INT Int64))))

;; specialized_value <- "#" value
(rule (lhs specialized_value (Message logic Value))
  (rhs "#" (nonterm value (Message logic Value)))
  (lambda ((value (Message logic Value))) (var value (Message logic Value))))

;; ============================================================================
;; Type Rules
;; ============================================================================

;; unspecified_type <- "UNKNOWN"
(rule (lhs unspecified_type (Message logic UnspecifiedType))
  (rhs "UNKNOWN")
  (lambda () (call (message logic UnspecifiedType))))

;; string_type <- "STRING"
(rule (lhs string_type (Message logic StringType))
  (rhs "STRING")
  (lambda () (call (message logic StringType))))

;; int_type <- "INT"
(rule (lhs int_type (Message logic IntType))
  (rhs "INT")
  (lambda () (call (message logic IntType))))

;; float_type <- "FLOAT"
(rule (lhs float_type (Message logic FloatType))
  (rhs "FLOAT")
  (lambda () (call (message logic FloatType))))

;; uint128_type <- "UINT128"
(rule (lhs uint128_type (Message logic UInt128Type))
  (rhs "UINT128")
  (lambda () (call (message logic UInt128Type))))

;; int128_type <- "INT128"
(rule (lhs int128_type (Message logic Int128Type))
  (rhs "INT128")
  (lambda () (call (message logic Int128Type))))

;; boolean_type <- "BOOLEAN"
(rule (lhs boolean_type (Message logic BooleanType))
  (rhs "BOOLEAN")
  (lambda () (call (message logic BooleanType))))

;; date_type <- "DATE"
(rule (lhs date_type (Message logic DateType))
  (rhs "DATE")
  (lambda () (call (message logic DateType))))

;; datetime_type <- "DATETIME"
(rule (lhs datetime_type (Message logic DateTimeType))
  (rhs "DATETIME")
  (lambda () (call (message logic DateTimeType))))

;; missing_type <- "MISSING"
(rule (lhs missing_type (Message logic MissingType))
  (rhs "MISSING")
  (lambda () (call (message logic MissingType))))

;; decimal_type <- "(" "DECIMAL" INT INT ")"
(rule (lhs decimal_type (Message logic DecimalType))
  (rhs "(" "DECIMAL" (term INT Int64) (term INT Int64) ")")
  (lambda
    ((precision Int64) (scale Int64))
    (call (message logic DecimalType) (var precision Int64) (var scale Int64))))

;; ============================================================================
;; Operator Rules
;; ============================================================================

;; eq <- "(" "=" term term ")"
(rule (lhs eq (Message logic Primitive))
  (rhs "(" "=" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")")
  (lambda
    ((left (Message logic Term)) (right (Message logic Term)))
    (call
    (message logic Primitive)
    (lit "rel_primitive_eq")
    (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))))))

;; primitive <- eq
(rule (lhs primitive (Message logic Primitive))
  (rhs (nonterm eq (Message logic Primitive)))
  (lambda ((op (Message logic Primitive))) (var op (Message logic Primitive))))

;; lt <- "(" "<" term term ")"
(rule (lhs lt (Message logic Primitive))
  (rhs "(" "<" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")")
  (lambda
    ((left (Message logic Term)) (right (Message logic Term)))
    (call
    (message logic Primitive)
    (lit "rel_primitive_lt_monotype")
    (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))))))

;; primitive <- lt
(rule (lhs primitive (Message logic Primitive))
  (rhs (nonterm lt (Message logic Primitive)))
  (lambda ((op (Message logic Primitive))) (var op (Message logic Primitive))))

;; lt_eq <- "(" "<=" term term ")"
(rule (lhs lt_eq (Message logic Primitive))
  (rhs "(" "<=" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")")
  (lambda
    ((left (Message logic Term)) (right (Message logic Term)))
    (call
    (message logic Primitive)
    (lit "rel_primitive_lt_eq_monotype")
    (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))))))

;; primitive <- lt_eq
(rule (lhs primitive (Message logic Primitive))
  (rhs (nonterm lt_eq (Message logic Primitive)))
  (lambda ((op (Message logic Primitive))) (var op (Message logic Primitive))))

;; gt <- "(" ">" term term ")"
(rule (lhs gt (Message logic Primitive))
  (rhs "(" ">" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")")
  (lambda
    ((left (Message logic Term)) (right (Message logic Term)))
    (call
    (message logic Primitive)
    (lit "rel_primitive_gt_monotype")
    (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))))))

;; primitive <- gt
(rule (lhs primitive (Message logic Primitive))
  (rhs (nonterm gt (Message logic Primitive)))
  (lambda ((op (Message logic Primitive))) (var op (Message logic Primitive))))

;; gt_eq <- "(" ">=" term term ")"
(rule (lhs gt_eq (Message logic Primitive))
  (rhs "(" ">=" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")")
  (lambda
    ((left (Message logic Term)) (right (Message logic Term)))
    (call
    (message logic Primitive)
    (lit "rel_primitive_gt_eq_monotype")
    (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))))))

;; primitive <- gt_eq
(rule (lhs primitive (Message logic Primitive))
  (rhs (nonterm gt_eq (Message logic Primitive)))
  (lambda ((op (Message logic Primitive))) (var op (Message logic Primitive))))

;; add <- "(" "+" term term term ")"
(rule (lhs add (Message logic Primitive))
  (rhs
    "("
    "+"
    (nonterm term (Message logic Term))
    (nonterm term (Message logic Term))
    (nonterm term (Message logic Term))
    ")")
  (lambda
    ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term)))
    (call
    (message logic Primitive)
    (lit "rel_primitive_add_monotype")
    (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term)))))))

;; primitive <- add
(rule (lhs primitive (Message logic Primitive))
  (rhs (nonterm add (Message logic Primitive)))
  (lambda ((op (Message logic Primitive))) (var op (Message logic Primitive))))

;; minus <- "(" "-" term term term ")"
(rule (lhs minus (Message logic Primitive))
  (rhs
    "("
    "-"
    (nonterm term (Message logic Term))
    (nonterm term (Message logic Term))
    (nonterm term (Message logic Term))
    ")")
  (lambda
    ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term)))
    (call
    (message logic Primitive)
    (lit "rel_primitive_subtract_monotype")
    (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term)))))))

;; primitive <- minus
(rule (lhs primitive (Message logic Primitive))
  (rhs (nonterm minus (Message logic Primitive)))
  (lambda ((op (Message logic Primitive))) (var op (Message logic Primitive))))

;; multiply <- "(" "*" term term term ")"
(rule (lhs multiply (Message logic Primitive))
  (rhs
    "("
    "*"
    (nonterm term (Message logic Term))
    (nonterm term (Message logic Term))
    (nonterm term (Message logic Term))
    ")")
  (lambda
    ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term)))
    (call
    (message logic Primitive)
    (lit "rel_primitive_multiply_monotype")
    (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term)))))))

;; primitive <- multiply
(rule (lhs primitive (Message logic Primitive))
  (rhs (nonterm multiply (Message logic Primitive)))
  (lambda ((op (Message logic Primitive))) (var op (Message logic Primitive))))

;; divide <- "(" "/" term term term ")"
(rule (lhs divide (Message logic Primitive))
  (rhs
    "("
    "/"
    (nonterm term (Message logic Term))
    (nonterm term (Message logic Term))
    (nonterm term (Message logic Term))
    ")")
  (lambda
    ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term)))
    (call
    (message logic Primitive)
    (lit "rel_primitive_divide_monotype")
    (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))
    (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term)))))))

;; primitive <- divide
(rule (lhs primitive (Message logic Primitive))
  (rhs (nonterm divide (Message logic Primitive)))
  (lambda ((op (Message logic Primitive))) (var op (Message logic Primitive))))

(mark-nonfinal primitive)

;; ============================================================================
;; Fragment Rules
;; ============================================================================

;; new_fragment_id <- fragment_id (calls start_fragment side effect)
(rule (lhs new_fragment_id (Message fragments FragmentId))
  (rhs (nonterm fragment_id (Message fragments FragmentId)))
  (lambda
    ((fragment_id (Message fragments FragmentId)))
    (seq
    (call (builtin start_fragment) (var fragment_id (Message fragments FragmentId)))
    (var fragment_id (Message fragments FragmentId)))))

;; fragment <- "(" "fragment" new_fragment_id declaration* ")"
(rule (lhs fragment (Message fragments Fragment))
  (rhs
    "("
    "fragment"
    (nonterm new_fragment_id (Message fragments FragmentId))
    (star (nonterm declaration (Message logic Declaration)))
    ")")
  (lambda
    ((fragment_id (Message fragments FragmentId)) (declarations (List (Message logic Declaration))))
    (call
    (builtin construct_fragment)
    (var fragment_id (Message fragments FragmentId))
    (var declarations (List (Message logic Declaration))))))

;; ============================================================================
;; Epoch Rules
;; ============================================================================

;; output <- "(" "output" name? relation_id ")"
(rule (lhs output (Message transactions Output))
  (rhs
    "("
    "output"
    (option (nonterm name String))
    (nonterm relation_id (Message logic RelationId))
    ")")
  (lambda
    ((name (Option String)) (relation_id (Message logic RelationId)))
    (call
    (message transactions Output)
    (call (builtin unwrap_option_or) (var name (Option String)) (lit "output"))
    (var relation_id (Message logic RelationId)))))

;; abort <- "(" "abort" name? relation_id ")"
(rule (lhs abort (Message transactions Abort))
  (rhs
    "("
    "abort"
    (option (nonterm name String))
    (nonterm relation_id (Message logic RelationId))
    ")")
  (lambda
    ((name (Option String)) (relation_id (Message logic RelationId)))
    (call
    (message transactions Abort)
    (call (builtin unwrap_option_or) (var name (Option String)) (lit "abort"))
    (var relation_id (Message logic RelationId)))))

;; ============================================================================
;; Logic Rules
;; ============================================================================

;; ffi <- "(" "ffi" name abstraction* term* ")"
(rule (lhs ffi (Message logic FFI))
  (rhs
    "("
    "ffi"
    (nonterm name String)
    (star (nonterm abstraction (Message logic Abstraction)))
    (star (nonterm term (Message logic Term)))
    ")")
  (lambda
    ((name String) (args (List (Message logic Abstraction))) (terms (List (Message logic Term))))
    (call
    (message logic FFI)
    (var name String)
    (var args (List (Message logic Abstraction)))
    (var terms (List (Message logic Term))))))

;; rel_atom <- "(" "rel_atom" name rel_term* ")"
(rule (lhs rel_atom (Message logic RelAtom))
  (rhs "(" "rel_atom" (nonterm name String) (star (nonterm rel_term (Message logic RelTerm))) ")")
  (lambda
    ((name String) (terms (List (Message logic RelTerm))))
    (call (message logic RelAtom) (var name String) (var terms (List (Message logic RelTerm))))))

;; primitive <- "(" "primitive" name rel_term* ")"
(rule (lhs primitive (Message logic Primitive))
  (rhs "(" "primitive" (nonterm name String) (star (nonterm rel_term (Message logic RelTerm))) ")")
  (lambda
    ((name String) (terms (List (Message logic RelTerm))))
    (call (message logic Primitive) (var name String) (var terms (List (Message logic RelTerm))))))

;; exists <- "(" "exists" bindings formula ")"
(rule (lhs exists (Message logic Exists))
  (rhs
    "("
    "exists"
    (nonterm bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
    (nonterm formula (Message logic Formula))
    ")")
  (lambda
    ((bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
    (formula (Message logic Formula)))
    (call
    (message logic Exists)
    (call
    (message logic Abstraction)
    (call
    (builtin list_concat)
    (call
    (builtin fst)
    (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))))
    (call
    (builtin snd)
    (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))))
    (var formula (Message logic Formula))))))
