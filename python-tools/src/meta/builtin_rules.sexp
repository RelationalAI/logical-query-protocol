;; Builtin grammar rules for LQP
;;
;; These rules define constructs that cannot be auto-generated from protobuf
;; definitions, including value literals, date/datetime parsing, configuration
;; syntax, bindings, abstractions, type literals, and operators.

;; ============================================================================
;; Value Rules
;; ============================================================================

;; value <- date (DateValue -> Value via date_value oneof)
(rule value (Message logic Value)
  (nt date (Message logic DateValue))
  (lambda ((value (Message logic DateValue)))
    (call (message logic Value)
      (call (oneof date_value) (var value (Message logic DateValue))))))

;; value <- datetime (DateTimeValue -> Value via datetime_value oneof)
(rule value (Message logic Value)
  (nt datetime (Message logic DateTimeValue))
  (lambda ((value (Message logic DateTimeValue)))
    (call (message logic Value)
      (call (oneof datetime_value) (var value (Message logic DateTimeValue))))))

;; value <- STRING
(rule value (Message logic Value)
  (term STRING String)
  (lambda ((value String))
    (call (message logic Value)
      (call (oneof string_value) (var value String)))))

;; value <- INT
(rule value (Message logic Value)
  (term INT Int64)
  (lambda ((value Int64))
    (call (message logic Value)
      (call (oneof int_value) (var value Int64)))))

;; value <- FLOAT
(rule value (Message logic Value)
  (term FLOAT Float64)
  (lambda ((value Float64))
    (call (message logic Value)
      (call (oneof float_value) (var value Float64)))))

;; value <- UINT128
(rule value (Message logic Value)
  (term UINT128 (Message logic UInt128Value))
  (lambda ((value (Message logic UInt128Value)))
    (call (message logic Value)
      (call (oneof uint128_value) (var value (Message logic UInt128Value))))))

;; value <- INT128
(rule value (Message logic Value)
  (term INT128 (Message logic Int128Value))
  (lambda ((value (Message logic Int128Value)))
    (call (message logic Value)
      (call (oneof int128_value) (var value (Message logic Int128Value))))))

;; value <- DECIMAL
(rule value (Message logic Value)
  (term DECIMAL (Message logic DecimalValue))
  (lambda ((value (Message logic DecimalValue)))
    (call (message logic Value)
      (call (oneof decimal_value) (var value (Message logic DecimalValue))))))

;; value <- "missing"
(rule value (Message logic Value)
  "missing"
  (lambda ()
    (call (message logic Value)
      (call (oneof missing_value) (call (message logic MissingValue))))))

;; boolean_value <- "true"
(rule boolean_value Boolean
  "true"
  (lambda () (lit true)))

;; boolean_value <- "false"
(rule boolean_value Boolean
  "false"
  (lambda () (lit false)))

;; value <- boolean_value
(rule value (Message logic Value)
  (nt boolean_value Boolean)
  (lambda ((value Boolean))
    (call (message logic Value)
      (call (oneof boolean_value) (var value Boolean)))))

;; date <- "(" "date" INT INT INT ")"
(rule date (Message logic DateValue)
  (seq "(" "date" (term INT Int64) (term INT Int64) (term INT Int64) ")")
  (lambda ((year Int64) (month Int64) (day Int64))
    (call (message logic DateValue)
      (var year Int64) (var month Int64) (var day Int64))))

;; datetime <- "(" "datetime" INT INT INT INT INT INT INT? ")"
(rule datetime (Message logic DateTimeValue)
  (seq "(" "datetime"
       (term INT Int64) (term INT Int64) (term INT Int64)
       (term INT Int64) (term INT Int64) (term INT Int64)
       (option (term INT Int64))
       ")")
  (lambda ((year Int64) (month Int64) (day Int64)
           (hour Int64) (minute Int64) (second Int64)
           (microsecond (Option Int64)))
    (call (message logic DateTimeValue)
      (var year Int64) (var month Int64) (var day Int64)
      (var hour Int64) (var minute Int64) (var second Int64)
      (call (builtin unwrap_option_or)
        (var microsecond (Option Int64))
        (lit 0)))))

;; ============================================================================
;; Transaction Rules
;; ============================================================================

;; config_dict <- "{" config_key_value* "}"
(rule config_dict (List (Tuple String (Message logic Value)))
  (seq "{" (star (nt config_key_value (Tuple String (Message logic Value)))) "}")
  (lambda ((x (List (Tuple String (Message logic Value)))))
    (var x (List (Tuple String (Message logic Value))))))

;; config_key_value <- COLON_SYMBOL value
(rule config_key_value (Tuple String (Message logic Value))
  (seq (term COLON_SYMBOL String) (nt value (Message logic Value)))
  (lambda ((symbol String) (value (Message logic Value)))
    (call (builtin make_tuple)
      (var symbol String)
      (var value (Message logic Value)))))

;; transaction <- "(" "transaction" configure? sync? epoch* ")"
(rule transaction (Message transactions Transaction)
  (seq "(" "transaction"
       (option (nt configure (Message transactions Configure)))
       (option (nt sync (Message transactions Sync)))
       (star (nt epoch (Message transactions Epoch)))
       ")")
  (lambda ((configure (Option (Message transactions Configure)))
           (sync (Option (Message transactions Sync)))
           (epochs (List (Message transactions Epoch))))
    (call (message transactions Transaction)
      (var epochs (List (Message transactions Epoch)))
      (call (builtin unwrap_option_or)
        (var configure (Option (Message transactions Configure)))
        (call (builtin construct_configure)
          (list (Tuple String (Message logic Value)))))
      (var sync (Option (Message transactions Sync))))))

;; configure <- "(" "configure" config_dict ")"
(rule configure (Message transactions Configure)
  (seq "(" "configure" (nt config_dict (List (Tuple String (Message logic Value)))) ")")
  (lambda ((config_dict (List (Tuple String (Message logic Value)))))
    (call (builtin construct_configure)
      (var config_dict (List (Tuple String (Message logic Value)))))))

;; ============================================================================
;; Bindings Rules
;; ============================================================================

;; bindings <- "[" binding* value_bindings? "]"
(rule bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))
  (seq "[" (star (nt binding (Message logic Binding)))
           (option (nt value_bindings (List (Message logic Binding)))) "]")
  (lambda ((keys (List (Message logic Binding)))
           (values (Option (List (Message logic Binding)))))
    (call (builtin make_tuple)
      (var keys (List (Message logic Binding)))
      (call (builtin unwrap_option_or)
        (var values (Option (List (Message logic Binding))))
        (list (Message logic Binding))))))

;; value_bindings <- "|" binding*
(rule value_bindings (List (Message logic Binding))
  (seq "|" (star (nt binding (Message logic Binding))))
  (lambda ((x (List (Message logic Binding))))
    (var x (List (Message logic Binding)))))

;; binding <- SYMBOL "::" type
(rule binding (Message logic Binding)
  (seq (term SYMBOL String) "::" (nt type (Message logic Type)))
  (lambda ((symbol String) (type (Message logic Type)))
    (call (message logic Binding)
      (call (message logic Var) (var symbol String))
      (var type (Message logic Type)))))

;; abstraction_with_arity <- "(" bindings formula ")"
(rule abstraction_with_arity (Tuple (Message logic Abstraction) Int64)
  (seq "(" (nt bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
           (nt formula (Message logic Formula)) ")")
  (lambda ((bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
           (formula (Message logic Formula)))
    (call (builtin make_tuple)
      (call (message logic Abstraction)
        (call (builtin list_concat)
          (call (builtin fst) (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))))
          (call (builtin snd) (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))))
        (var formula (Message logic Formula)))
      (call (builtin length)
        (call (builtin snd) (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))))))))

;; abstraction <- "(" bindings formula ")"
(rule abstraction (Message logic Abstraction)
  (seq "(" (nt bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
           (nt formula (Message logic Formula)) ")")
  (lambda ((bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
           (formula (Message logic Formula)))
    (call (message logic Abstraction)
      (call (builtin list_concat)
        (call (builtin fst) (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))))
        (call (builtin snd) (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))))
      (var formula (Message logic Formula)))))

;; ============================================================================
;; Formula Rules
;; ============================================================================

;; true <- "(" "true" ")"
(rule true (Message logic Conjunction)
  (seq "(" "true" ")")
  (lambda ()
    (call (message logic Conjunction) (list (Message logic Formula)))))

;; false <- "(" "false" ")"
(rule false (Message logic Disjunction)
  (seq "(" "false" ")")
  (lambda ()
    (call (message logic Disjunction) (list (Message logic Formula)))))

;; formula <- true
(rule formula (Message logic Formula)
  (nt true (Message logic Conjunction))
  (lambda ((value (Message logic Conjunction)))
    (call (message logic Formula)
      (call (oneof conjunction) (var value (Message logic Conjunction))))))

;; formula <- false
(rule formula (Message logic Formula)
  (nt false (Message logic Disjunction))
  (lambda ((value (Message logic Disjunction)))
    (call (message logic Formula)
      (call (oneof disjunction) (var value (Message logic Disjunction))))))

(mark-nonfinal formula)

;; ============================================================================
;; Export Rules
;; ============================================================================

;; export <- "(" "export" export_csvconfig ")"
(rule export (Message transactions Export)
  (seq "(" "export" (nt export_csvconfig (Message transactions ExportCSVConfig)) ")")
  (lambda ((config (Message transactions ExportCSVConfig)))
    (call (message transactions Export)
      (call (oneof csv_config) (var config (Message transactions ExportCSVConfig))))))

;; export_csv_path <- "(" "path" STRING ")"
(rule export_csvpath String
  (seq "(" "path" (term STRING String) ")")
  (lambda ((x String))
    (var x String)))

;; export_csvconfig <- "(" "export_csv_config" export_csv_path export_csv_columns config_dict ")"
(rule export_csvconfig (Message transactions ExportCSVConfig)
  (seq "(" "export_csv_config"
       (nt export_csvpath String)
       (nt export_csvcolumns (List (Message transactions ExportCSVColumn)))
       (nt config_dict (List (Tuple String (Message logic Value))))
       ")")
  (lambda ((path String)
           (columns (List (Message transactions ExportCSVColumn)))
           (config (List (Tuple String (Message logic Value)))))
    (call (builtin export_csv_config)
      (var path String)
      (var columns (List (Message transactions ExportCSVColumn)))
      (var config (List (Tuple String (Message logic Value)))))))

;; export_csv_columns <- "(" "columns" export_csv_column* ")"
(rule export_csvcolumns (List (Message transactions ExportCSVColumn))
  (seq "(" "columns" (star (nt export_csvcolumn (Message transactions ExportCSVColumn))) ")")
  (lambda ((x (List (Message transactions ExportCSVColumn))))
    (var x (List (Message transactions ExportCSVColumn)))))

;; export_csv_column <- "(" "column" STRING relation_id ")"
(rule export_csvcolumn (Message transactions ExportCSVColumn)
  (seq "(" "column" (term STRING String) (nt relation_id (Message logic RelationId)) ")")
  (lambda ((name String) (relation_id (Message logic RelationId)))
    (call (message transactions ExportCSVColumn)
      (var name String) (var relation_id (Message logic RelationId)))))

;; ============================================================================
;; ID Rules
;; ============================================================================

;; name <- COLON_SYMBOL
(rule name String
  (term COLON_SYMBOL String)
  (lambda ((x String))
    (var x String)))

;; var <- SYMBOL
(rule var (Message logic Var)
  (term SYMBOL String)
  (lambda ((symbol String))
    (call (message logic Var) (var symbol String))))

;; fragment_id <- COLON_SYMBOL
(rule fragment_id (Message fragments FragmentId)
  (term COLON_SYMBOL String)
  (lambda ((symbol String))
    (call (builtin fragment_id_from_string) (var symbol String))))

;; relation_id <- COLON_SYMBOL
(rule relation_id (Message logic RelationId)
  (term COLON_SYMBOL String)
  (lambda ((symbol String))
    (call (builtin relation_id_from_string) (var symbol String))))

;; relation_id <- INT
(rule relation_id (Message logic RelationId)
  (term INT Int64)
  (lambda ((INT Int64))
    (call (builtin relation_id_from_int) (var INT Int64))))

;; specialized_value <- "#" value
(rule specialized_value (Message logic Value)
  (seq "#" (nt value (Message logic Value)))
  (lambda ((value (Message logic Value)))
    (var value (Message logic Value))))

;; ============================================================================
;; Type Rules
;; ============================================================================

;; unspecified_type <- "UNKNOWN"
(rule unspecified_type (Message logic UnspecifiedType)
  "UNKNOWN"
  (lambda ()
    (call (message logic UnspecifiedType))))

;; string_type <- "STRING"
(rule string_type (Message logic StringType)
  "STRING"
  (lambda ()
    (call (message logic StringType))))

;; int_type <- "INT"
(rule int_type (Message logic IntType)
  "INT"
  (lambda ()
    (call (message logic IntType))))

;; float_type <- "FLOAT"
(rule float_type (Message logic FloatType)
  "FLOAT"
  (lambda ()
    (call (message logic FloatType))))

;; uint128_type <- "UINT128"
(rule uint128_type (Message logic UInt128Type)
  "UINT128"
  (lambda ()
    (call (message logic UInt128Type))))

;; int128_type <- "INT128"
(rule int128_type (Message logic Int128Type)
  "INT128"
  (lambda ()
    (call (message logic Int128Type))))

;; boolean_type <- "BOOLEAN"
(rule boolean_type (Message logic BooleanType)
  "BOOLEAN"
  (lambda ()
    (call (message logic BooleanType))))

;; date_type <- "DATE"
(rule date_type (Message logic DateType)
  "DATE"
  (lambda ()
    (call (message logic DateType))))

;; datetime_type <- "DATETIME"
(rule datetime_type (Message logic DateTimeType)
  "DATETIME"
  (lambda ()
    (call (message logic DateTimeType))))

;; missing_type <- "MISSING"
(rule missing_type (Message logic MissingType)
  "MISSING"
  (lambda ()
    (call (message logic MissingType))))

;; decimal_type <- "(" "DECIMAL" INT INT ")"
(rule decimal_type (Message logic DecimalType)
  (seq "(" "DECIMAL" (term INT Int64) (term INT Int64) ")")
  (lambda ((precision Int64) (scale Int64))
    (call (message logic DecimalType)
      (var precision Int64) (var scale Int64))))

;; ============================================================================
;; Operator Rules
;; ============================================================================

;; eq <- "(" "=" term term ")"
(rule eq (Message logic Primitive)
  (seq "(" "=" (nt term (Message logic Term)) (nt term (Message logic Term)) ")")
  (lambda ((left (Message logic Term)) (right (Message logic Term)))
    (call (message logic Primitive)
      (lit "rel_primitive_eq")
      (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))))))

;; primitive <- eq
(rule primitive (Message logic Primitive)
  (nt eq (Message logic Primitive))
  (lambda ((op (Message logic Primitive)))
    (var op (Message logic Primitive))))

;; lt <- "(" "<" term term ")"
(rule lt (Message logic Primitive)
  (seq "(" "<" (nt term (Message logic Term)) (nt term (Message logic Term)) ")")
  (lambda ((left (Message logic Term)) (right (Message logic Term)))
    (call (message logic Primitive)
      (lit "rel_primitive_lt_monotype")
      (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))))))

;; primitive <- lt
(rule primitive (Message logic Primitive)
  (nt lt (Message logic Primitive))
  (lambda ((op (Message logic Primitive)))
    (var op (Message logic Primitive))))

;; lt_eq <- "(" "<=" term term ")"
(rule lt_eq (Message logic Primitive)
  (seq "(" "<=" (nt term (Message logic Term)) (nt term (Message logic Term)) ")")
  (lambda ((left (Message logic Term)) (right (Message logic Term)))
    (call (message logic Primitive)
      (lit "rel_primitive_lt_eq_monotype")
      (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))))))

;; primitive <- lt_eq
(rule primitive (Message logic Primitive)
  (nt lt_eq (Message logic Primitive))
  (lambda ((op (Message logic Primitive)))
    (var op (Message logic Primitive))))

;; gt <- "(" ">" term term ")"
(rule gt (Message logic Primitive)
  (seq "(" ">" (nt term (Message logic Term)) (nt term (Message logic Term)) ")")
  (lambda ((left (Message logic Term)) (right (Message logic Term)))
    (call (message logic Primitive)
      (lit "rel_primitive_gt_monotype")
      (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))))))

;; primitive <- gt
(rule primitive (Message logic Primitive)
  (nt gt (Message logic Primitive))
  (lambda ((op (Message logic Primitive)))
    (var op (Message logic Primitive))))

;; gt_eq <- "(" ">=" term term ")"
(rule gt_eq (Message logic Primitive)
  (seq "(" ">=" (nt term (Message logic Term)) (nt term (Message logic Term)) ")")
  (lambda ((left (Message logic Term)) (right (Message logic Term)))
    (call (message logic Primitive)
      (lit "rel_primitive_gt_eq_monotype")
      (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))))))

;; primitive <- gt_eq
(rule primitive (Message logic Primitive)
  (nt gt_eq (Message logic Primitive))
  (lambda ((op (Message logic Primitive)))
    (var op (Message logic Primitive))))

;; add <- "(" "+" term term term ")"
(rule add (Message logic Primitive)
  (seq "(" "+" (nt term (Message logic Term)) (nt term (Message logic Term)) (nt term (Message logic Term)) ")")
  (lambda ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term)))
    (call (message logic Primitive)
      (lit "rel_primitive_add_monotype")
      (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term)))))))

;; primitive <- add
(rule primitive (Message logic Primitive)
  (nt add (Message logic Primitive))
  (lambda ((op (Message logic Primitive)))
    (var op (Message logic Primitive))))

;; minus <- "(" "-" term term term ")"
(rule minus (Message logic Primitive)
  (seq "(" "-" (nt term (Message logic Term)) (nt term (Message logic Term)) (nt term (Message logic Term)) ")")
  (lambda ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term)))
    (call (message logic Primitive)
      (lit "rel_primitive_subtract_monotype")
      (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term)))))))

;; primitive <- minus
(rule primitive (Message logic Primitive)
  (nt minus (Message logic Primitive))
  (lambda ((op (Message logic Primitive)))
    (var op (Message logic Primitive))))

;; multiply <- "(" "*" term term term ")"
(rule multiply (Message logic Primitive)
  (seq "(" "*" (nt term (Message logic Term)) (nt term (Message logic Term)) (nt term (Message logic Term)) ")")
  (lambda ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term)))
    (call (message logic Primitive)
      (lit "rel_primitive_multiply_monotype")
      (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term)))))))

;; primitive <- multiply
(rule primitive (Message logic Primitive)
  (nt multiply (Message logic Primitive))
  (lambda ((op (Message logic Primitive)))
    (var op (Message logic Primitive))))

;; divide <- "(" "/" term term term ")"
(rule divide (Message logic Primitive)
  (seq "(" "/" (nt term (Message logic Term)) (nt term (Message logic Term)) (nt term (Message logic Term)) ")")
  (lambda ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term)))
    (call (message logic Primitive)
      (lit "rel_primitive_divide_monotype")
      (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))
      (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term)))))))

;; primitive <- divide
(rule primitive (Message logic Primitive)
  (nt divide (Message logic Primitive))
  (lambda ((op (Message logic Primitive)))
    (var op (Message logic Primitive))))

(mark-nonfinal primitive)

;; ============================================================================
;; Fragment Rules
;; ============================================================================

;; new_fragment_id <- fragment_id (calls start_fragment side effect)
(rule new_fragment_id (Message fragments FragmentId)
  (nt fragment_id (Message fragments FragmentId))
  (lambda ((fragment_id (Message fragments FragmentId)))
    (seq
      (call (builtin start_fragment) (var fragment_id (Message fragments FragmentId)))
      (var fragment_id (Message fragments FragmentId)))))

;; fragment <- "(" "fragment" new_fragment_id declaration* ")"
(rule fragment (Message fragments Fragment)
  (seq "(" "fragment"
       (nt new_fragment_id (Message fragments FragmentId))
       (star (nt declaration (Message logic Declaration)))
       ")")
  (lambda ((fragment_id (Message fragments FragmentId))
           (declarations (List (Message logic Declaration))))
    (call (builtin construct_fragment)
      (var fragment_id (Message fragments FragmentId))
      (var declarations (List (Message logic Declaration))))))

;; ============================================================================
;; Epoch Rules
;; ============================================================================

;; output <- "(" "output" name? relation_id ")"
(rule output (Message transactions Output)
  (seq "(" "output" (option (nt name String)) (nt relation_id (Message logic RelationId)) ")")
  (lambda ((name (Option String)) (relation_id (Message logic RelationId)))
    (call (message transactions Output)
      (call (builtin unwrap_option_or) (var name (Option String)) (lit "output"))
      (var relation_id (Message logic RelationId)))))

;; abort <- "(" "abort" name? relation_id ")"
(rule abort (Message transactions Abort)
  (seq "(" "abort" (option (nt name String)) (nt relation_id (Message logic RelationId)) ")")
  (lambda ((name (Option String)) (relation_id (Message logic RelationId)))
    (call (message transactions Abort)
      (call (builtin unwrap_option_or) (var name (Option String)) (lit "abort"))
      (var relation_id (Message logic RelationId)))))

;; ============================================================================
;; Logic Rules
;; ============================================================================

;; ffi <- "(" "ffi" name abstraction* term* ")"
(rule ffi (Message logic FFI)
  (seq "(" "ffi"
       (nt name String)
       (star (nt abstraction (Message logic Abstraction)))
       (star (nt term (Message logic Term)))
       ")")
  (lambda ((name String)
           (args (List (Message logic Abstraction)))
           (terms (List (Message logic Term))))
    (call (message logic FFI)
      (var name String)
      (var args (List (Message logic Abstraction)))
      (var terms (List (Message logic Term))))))

;; rel_atom <- "(" "rel_atom" name rel_term* ")"
(rule rel_atom (Message logic RelAtom)
  (seq "(" "rel_atom"
       (nt name String)
       (star (nt rel_term (Message logic RelTerm)))
       ")")
  (lambda ((name String) (terms (List (Message logic RelTerm))))
    (call (message logic RelAtom)
      (var name String)
      (var terms (List (Message logic RelTerm))))))

;; primitive <- "(" "primitive" name rel_term* ")"
(rule primitive (Message logic Primitive)
  (seq "(" "primitive"
       (nt name String)
       (star (nt rel_term (Message logic RelTerm)))
       ")")
  (lambda ((name String) (terms (List (Message logic RelTerm))))
    (call (message logic Primitive)
      (var name String)
      (var terms (List (Message logic RelTerm))))))

;; exists <- "(" "exists" bindings formula ")"
(rule exists (Message logic Exists)
  (seq "(" "exists"
       (nt bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
       (nt formula (Message logic Formula))
       ")")
  (lambda ((bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))
           (formula (Message logic Formula)))
    (call (message logic Exists)
      (call (message logic Abstraction)
        (call (builtin list_concat)
          (call (builtin fst) (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))))
          (call (builtin snd) (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding))))))
        (var formula (Message logic Formula))))))
