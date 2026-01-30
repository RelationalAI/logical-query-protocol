; Messages that are constructed imperatively by the parser, not parsed from grammar rules.
; These protobuf message types are excluded from completeness validation because they are
; built programmatically by builtin functions (like construct_betree_info, construct_csv_config)
; or by parser internals, rather than being directly produced by grammar production rules.
; Without these directives, the validator would report errors that these message types have
; no grammar rules producing them.
(ignore-completeness DebugInfo)
(ignore-completeness IVMConfig)
(ignore-completeness BeTreeConfig)
(ignore-completeness BeTreeLocator)
(ignore-completeness CSVConfig)

; Terminal declarations
(terminal COLON_SYMBOL String)
(terminal DECIMAL (Message logic DecimalValue))
(terminal FLOAT Float64)
(terminal INT Int64)
(terminal INT128 (Message logic Int128Value))
(terminal STRING String)
(terminal SYMBOL String)
(terminal UINT128 (Message logic UInt128Value))

(rule
  (lhs transaction (Message transactions Transaction))
  (rhs
    "("
    "transaction"
    (option
      configure)
    (option sync)
    (star epoch)
    ")")
  (construct
    ((configure (Option (Message transactions Configure)))
      (sync (Option (Message transactions Sync)))
      (epochs (List (Message transactions Epoch))))
    (Message transactions Transaction)
    (new-message
      transactions
      Transaction
      (epochs (var epochs (List (Message transactions Epoch))))
      (configure
        (call
          (builtin unwrap_option_or)
          (var configure (Option (Message transactions Configure)))
          (call
            (builtin construct_configure)
            (list (Tuple String (Message logic Value))))))
      (sync (var sync (Option (Message transactions Sync)))))))

(rule
  (lhs configure (Message transactions Configure))
  (rhs
    "("
    "configure"
    config_dict
    ")")
  (construct
    ((config_dict (List (Tuple String (Message logic Value)))))
    (Message transactions Configure)
    (call
      (builtin construct_configure)
      (var
        config_dict
        (List (Tuple String (Message logic Value)))))))

(rule
  (lhs
    config_dict
    (List (Tuple String (Message logic Value))))
  (rhs
    "{"
    (star
      config_key_value)
    "}")
  (construct
    ((x (List (Tuple String (Message logic Value)))))
    (List (Tuple String (Message logic Value)))
    (var x (List (Tuple String (Message logic Value))))))

(rule
  (lhs config_key_value (Tuple String (Message logic Value)))
  (rhs
    COLON_SYMBOL
    value)
  (construct
    ((symbol String) (value (Message logic Value)))
    (Tuple String (Message logic Value))
    (call
      (builtin make_tuple)
      (var symbol String)
      (var value (Message logic Value)))))

(rule
  (lhs value (Message logic Value))
  (rhs date)
  (construct
    ((value (Message logic DateValue)))
    (Message logic Value)
    (new-message
      logic
      Value
      (value
        (call
          (oneof date_value)
          (var value (Message logic DateValue)))))))

(rule
  (lhs value (Message logic Value))
  (rhs datetime)
  (construct
    ((value (Message logic DateTimeValue)))
    (Message logic Value)
    (new-message
      logic
      Value
      (value
        (call
          (oneof datetime_value)
          (var value (Message logic DateTimeValue)))))))

(rule
  (lhs value (Message logic Value))
  (rhs STRING)
  (construct
    ((value String))
    (Message logic Value)
    (new-message
      logic
      Value
      (value (call (oneof string_value) (var value String))))))

(rule
  (lhs value (Message logic Value))
  (rhs INT)
  (construct
    ((value Int64))
    (Message logic Value)
    (new-message
      logic
      Value
      (value (call (oneof int_value) (var value Int64))))))

(rule
  (lhs value (Message logic Value))
  (rhs FLOAT)
  (construct
    ((value Float64))
    (Message logic Value)
    (new-message
      logic
      Value
      (value (call (oneof float_value) (var value Float64))))))

(rule
  (lhs value (Message logic Value))
  (rhs UINT128)
  (construct
    ((value (Message logic UInt128Value)))
    (Message logic Value)
    (new-message
      logic
      Value
      (value
        (call
          (oneof uint128_value)
          (var value (Message logic UInt128Value)))))))

(rule
  (lhs value (Message logic Value))
  (rhs INT128)
  (construct
    ((value (Message logic Int128Value)))
    (Message logic Value)
    (new-message
      logic
      Value
      (value
        (call
          (oneof int128_value)
          (var value (Message logic Int128Value)))))))

(rule
  (lhs value (Message logic Value))
  (rhs DECIMAL)
  (construct
    ((value (Message logic DecimalValue)))
    (Message logic Value)
    (new-message
      logic
      Value
      (value
        (call
          (oneof decimal_value)
          (var value (Message logic DecimalValue)))))))

(rule
  (lhs value (Message logic Value))
  (rhs "missing")
  (construct
    ()
    (Message logic Value)
    (new-message
      logic
      Value
      (value
        (call
          (oneof missing_value)
          (new-message logic MissingValue))))))

(rule
  (lhs value (Message logic Value))
  (rhs boolean_value)
  (construct
    ((value Boolean))
    (Message logic Value)
    (new-message
      logic
      Value
      (value (call (oneof boolean_value) (var value Boolean))))))

(rule
  (lhs date (Message logic DateValue))
  (rhs
    "("
    "date"
    INT
    INT
    INT
    ")")
  (construct
    ((year Int64) (month Int64) (day Int64))
    (Message logic DateValue)
    (new-message
      logic
      DateValue
      (year (call (builtin int64_to_int32) (var year Int64)))
      (month (call (builtin int64_to_int32) (var month Int64)))
      (day (call (builtin int64_to_int32) (var day Int64))))))

(rule
  (lhs datetime (Message logic DateTimeValue))
  (rhs
    "("
    "datetime"
    INT
    INT
    INT
    INT
    INT
    INT
    (option INT)
    ")")
  (construct
    ((year Int64)
      (month Int64)
      (day Int64)
      (hour Int64)
      (minute Int64)
      (second Int64)
      (microsecond (Option Int64)))
    (Message logic DateTimeValue)
    (new-message
      logic
      DateTimeValue
      (year (call (builtin int64_to_int32) (var year Int64)))
      (month (call (builtin int64_to_int32) (var month Int64)))
      (day (call (builtin int64_to_int32) (var day Int64)))
      (hour (call (builtin int64_to_int32) (var hour Int64)))
      (minute (call (builtin int64_to_int32) (var minute Int64)))
      (second (call (builtin int64_to_int32) (var second Int64)))
      (microsecond
        (call
          (builtin int64_to_int32)
          (call
            (builtin unwrap_option_or)
            (var microsecond (Option Int64))
            (lit 0)))))))

(rule (lhs boolean_value Boolean) (rhs "true") (construct () Boolean (lit true)))

(rule (lhs boolean_value Boolean) (rhs "false") (construct () Boolean (lit false)))

(rule
  (lhs sync (Message transactions Sync))
  (rhs
    "("
    "sync"
    (star fragment_id)
    ")")
  (construct
    ((fragments (List (Message fragments FragmentId))))
    (Message transactions Sync)
    (new-message
      transactions
      Sync
      (fragments
        (var fragments (List (Message fragments FragmentId)))))))

(rule
  (lhs fragment_id (Message fragments FragmentId))
  (rhs COLON_SYMBOL)
  (construct
    ((symbol String))
    (Message fragments FragmentId)
    (call (builtin fragment_id_from_string) (var symbol String))))

(rule
  (lhs epoch (Message transactions Epoch))
  (rhs
    "("
    "epoch"
    (option
      epoch_writes)
    (option
      epoch_reads)
    ")")
  (construct
    ((writes (Option (List (Message transactions Write))))
      (reads (Option (List (Message transactions Read)))))
    (Message transactions Epoch)
    (new-message
      transactions
      Epoch
      (writes
        (call
          (builtin unwrap_option_or)
          (var writes (Option (List (Message transactions Write))))
          (list (Message transactions Write))))
      (reads
        (call
          (builtin unwrap_option_or)
          (var reads (Option (List (Message transactions Read))))
          (list (Message transactions Read)))))))

(rule
  (lhs epoch_writes (List (Message transactions Write)))
  (rhs
    "("
    "writes"
    (star write)
    ")")
  (construct
    ((x (List (Message transactions Write))))
    (List (Message transactions Write))
    (var x (List (Message transactions Write)))))

(rule
  (lhs write (Message transactions Write))
  (rhs define)
  (construct
    ((value (Message transactions Define)))
    (Message transactions Write)
    (new-message
      transactions
      Write
      (write_type
        (call
          (oneof define)
          (var value (Message transactions Define)))))))

(rule
  (lhs write (Message transactions Write))
  (rhs undefine)
  (construct
    ((value (Message transactions Undefine)))
    (Message transactions Write)
    (new-message
      transactions
      Write
      (write_type
        (call
          (oneof undefine)
          (var value (Message transactions Undefine)))))))

(rule
  (lhs write (Message transactions Write))
  (rhs context)
  (construct
    ((value (Message transactions Context)))
    (Message transactions Write)
    (new-message
      transactions
      Write
      (write_type
        (call
          (oneof context)
          (var value (Message transactions Context)))))))

(rule
  (lhs define (Message transactions Define))
  (rhs
    "("
    "define"
    fragment
    ")")
  (construct
    ((fragment (Message fragments Fragment)))
    (Message transactions Define)
    (new-message
      transactions
      Define
      (fragment (var fragment (Message fragments Fragment))))))

(rule
  (lhs fragment (Message fragments Fragment))
  (rhs
    "("
    "fragment"
    new_fragment_id
    (star declaration)
    ")")
  (construct
    ((fragment_id (Message fragments FragmentId))
      (declarations (List (Message logic Declaration))))
    (Message fragments Fragment)
    (call
      (builtin construct_fragment)
      (var fragment_id (Message fragments FragmentId))
      (var declarations (List (Message logic Declaration))))))

(rule
  (lhs new_fragment_id (Message fragments FragmentId))
  (rhs fragment_id)
  (construct
    ((fragment_id (Message fragments FragmentId)))
    (Message fragments FragmentId)
    (seq
      (call
        (builtin start_fragment)
        (var fragment_id (Message fragments FragmentId)))
      (var fragment_id (Message fragments FragmentId)))))

(rule
  (lhs declaration (Message logic Declaration))
  (rhs def)
  (construct
    ((value (Message logic Def)))
    (Message logic Declaration)
    (new-message
      logic
      Declaration
      (declaration_type
        (call (oneof def) (var value (Message logic Def)))))))

(rule
  (lhs declaration (Message logic Declaration))
  (rhs algorithm)
  (construct
    ((value (Message logic Algorithm)))
    (Message logic Declaration)
    (new-message
      logic
      Declaration
      (declaration_type
        (call
          (oneof algorithm)
          (var value (Message logic Algorithm)))))))

(rule
  (lhs declaration (Message logic Declaration))
  (rhs constraint)
  (construct
    ((value (Message logic Constraint)))
    (Message logic Declaration)
    (new-message
      logic
      Declaration
      (declaration_type
        (call
          (oneof constraint)
          (var value (Message logic Constraint)))))))

(rule
  (lhs declaration (Message logic Declaration))
  (rhs data)
  (construct
    ((value (Message logic Data)))
    (Message logic Declaration)
    (new-message
      logic
      Declaration
      (declaration_type
        (call (oneof data) (var value (Message logic Data)))))))

(rule
  (lhs def (Message logic Def))
  (rhs
    "("
    "def"
    relation_id
    abstraction
    (option attrs)
    ")")
  (construct
    ((name (Message logic RelationId))
      (body (Message logic Abstraction))
      (attrs (Option (List (Message logic Attribute)))))
    (Message logic Def)
    (new-message
      logic
      Def
      (name (var name (Message logic RelationId)))
      (body (var body (Message logic Abstraction)))
      (attrs
        (call
          (builtin unwrap_option_or)
          (var attrs (Option (List (Message logic Attribute))))
          (list (Message logic Attribute)))))))

(rule
  (lhs relation_id (Message logic RelationId))
  (rhs COLON_SYMBOL)
  (construct
    ((symbol String))
    (Message logic RelationId)
    (call (builtin relation_id_from_string) (var symbol String))))

(rule
  (lhs relation_id (Message logic RelationId))
  (rhs INT)
  (construct
    ((INT Int64))
    (Message logic RelationId)
    (call (builtin relation_id_from_int) (var INT Int64))))

(rule
  (lhs abstraction (Message logic Abstraction))
  (rhs
    "("
    bindings
    formula
    ")")
  (construct
    ((bindings
      (Tuple
        (List (Message logic Binding))
        (List (Message logic Binding))))
      (formula (Message logic Formula)))
    (Message logic Abstraction)
    (new-message
      logic
      Abstraction
      (vars
        (call
          (builtin list_concat)
          (get-element
            (var
              bindings
              (Tuple
                (List (Message logic Binding))
                (List (Message logic Binding))))
            0)
          (get-element
            (var
              bindings
              (Tuple
                (List (Message logic Binding))
                (List (Message logic Binding))))
            1)))
      (value (var formula (Message logic Formula))))))

(rule
  (lhs
    bindings
    (Tuple
      (List (Message logic Binding))
      (List (Message logic Binding))))
  (rhs
    "["
    (star binding)
    (option
      value_bindings)
    "]")
  (construct
    ((keys (List (Message logic Binding)))
      (values (Option (List (Message logic Binding)))))
    (Tuple
      (List (Message logic Binding))
      (List (Message logic Binding)))
    (call
      (builtin make_tuple)
      (var keys (List (Message logic Binding)))
      (call
        (builtin unwrap_option_or)
        (var values (Option (List (Message logic Binding))))
        (list (Message logic Binding))))))

(rule
  (lhs binding (Message logic Binding))
  (rhs
    SYMBOL
    "::"
    type)
  (construct
    ((symbol String) (type (Message logic Type)))
    (Message logic Binding)
    (new-message
      logic
      Binding
      (var (new-message logic Var (name (var symbol String))))
      (type (var type (Message logic Type))))))

(rule
  (lhs type (Message logic Type))
  (rhs
    unspecified_type)
  (construct
    ((value (Message logic UnspecifiedType)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call
          (oneof unspecified_type)
          (var value (Message logic UnspecifiedType)))))))

(rule
  (lhs type (Message logic Type))
  (rhs string_type)
  (construct
    ((value (Message logic StringType)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call
          (oneof string_type)
          (var value (Message logic StringType)))))))

(rule
  (lhs type (Message logic Type))
  (rhs int_type)
  (construct
    ((value (Message logic IntType)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call (oneof int_type) (var value (Message logic IntType)))))))

(rule
  (lhs type (Message logic Type))
  (rhs float_type)
  (construct
    ((value (Message logic FloatType)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call
          (oneof float_type)
          (var value (Message logic FloatType)))))))

(rule
  (lhs type (Message logic Type))
  (rhs uint128_type)
  (construct
    ((value (Message logic UInt128Type)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call
          (oneof uint128_type)
          (var value (Message logic UInt128Type)))))))

(rule
  (lhs type (Message logic Type))
  (rhs int128_type)
  (construct
    ((value (Message logic Int128Type)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call
          (oneof int128_type)
          (var value (Message logic Int128Type)))))))

(rule
  (lhs type (Message logic Type))
  (rhs date_type)
  (construct
    ((value (Message logic DateType)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call
          (oneof date_type)
          (var value (Message logic DateType)))))))

(rule
  (lhs type (Message logic Type))
  (rhs datetime_type)
  (construct
    ((value (Message logic DateTimeType)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call
          (oneof datetime_type)
          (var value (Message logic DateTimeType)))))))

(rule
  (lhs type (Message logic Type))
  (rhs missing_type)
  (construct
    ((value (Message logic MissingType)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call
          (oneof missing_type)
          (var value (Message logic MissingType)))))))

(rule
  (lhs type (Message logic Type))
  (rhs decimal_type)
  (construct
    ((value (Message logic DecimalType)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call
          (oneof decimal_type)
          (var value (Message logic DecimalType)))))))

(rule
  (lhs type (Message logic Type))
  (rhs boolean_type)
  (construct
    ((value (Message logic BooleanType)))
    (Message logic Type)
    (new-message
      logic
      Type
      (type
        (call
          (oneof boolean_type)
          (var value (Message logic BooleanType)))))))

(rule
  (lhs unspecified_type (Message logic UnspecifiedType))
  (rhs "UNKNOWN")
  (construct
    ()
    (Message logic UnspecifiedType)
    (new-message logic UnspecifiedType)))

(rule
  (lhs string_type (Message logic StringType))
  (rhs "STRING")
  (construct
    ()
    (Message logic StringType)
    (new-message logic StringType)))

(rule
  (lhs int_type (Message logic IntType))
  (rhs "INT")
  (construct
    ()
    (Message logic IntType)
    (new-message logic IntType)))

(rule
  (lhs float_type (Message logic FloatType))
  (rhs "FLOAT")
  (construct
    ()
    (Message logic FloatType)
    (new-message logic FloatType)))

(rule
  (lhs uint128_type (Message logic UInt128Type))
  (rhs "UINT128")
  (construct
    ()
    (Message logic UInt128Type)
    (new-message logic UInt128Type)))

(rule
  (lhs int128_type (Message logic Int128Type))
  (rhs "INT128")
  (construct
    ()
    (Message logic Int128Type)
    (new-message logic Int128Type)))

(rule
  (lhs date_type (Message logic DateType))
  (rhs "DATE")
  (construct
    ()
    (Message logic DateType)
    (new-message logic DateType)))

(rule
  (lhs datetime_type (Message logic DateTimeType))
  (rhs "DATETIME")
  (construct
    ()
    (Message logic DateTimeType)
    (new-message logic DateTimeType)))

(rule
  (lhs missing_type (Message logic MissingType))
  (rhs "MISSING")
  (construct
    ()
    (Message logic MissingType)
    (new-message logic MissingType)))

(rule
  (lhs decimal_type (Message logic DecimalType))
  (rhs "(" "DECIMAL" INT INT ")")
  (construct
    ((precision Int64) (scale Int64))
    (Message logic DecimalType)
    (new-message
      logic
      DecimalType
      (precision
        (call (builtin int64_to_int32) (var precision Int64)))
      (scale (call (builtin int64_to_int32) (var scale Int64))))))

(rule
  (lhs boolean_type (Message logic BooleanType))
  (rhs "BOOLEAN")
  (construct
    ()
    (Message logic BooleanType)
    (new-message logic BooleanType)))

(rule
  (lhs value_bindings (List (Message logic Binding)))
  (rhs "|" (star binding))
  (construct
    ((x (List (Message logic Binding))))
    (List (Message logic Binding))
    (var x (List (Message logic Binding)))))

(rule
  (lhs formula (Message logic Formula))
  (rhs true)
  (construct
    ((value (Message logic Conjunction)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call
          (oneof conjunction)
          (var value (Message logic Conjunction)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs false)
  (construct
    ((value (Message logic Disjunction)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call
          (oneof disjunction)
          (var value (Message logic Disjunction)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs exists)
  (construct
    ((value (Message logic Exists)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call (oneof exists) (var value (Message logic Exists)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs reduce)
  (construct
    ((value (Message logic Reduce)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call (oneof reduce) (var value (Message logic Reduce)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs conjunction)
  (construct
    ((value (Message logic Conjunction)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call
          (oneof conjunction)
          (var value (Message logic Conjunction)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs disjunction)
  (construct
    ((value (Message logic Disjunction)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call
          (oneof disjunction)
          (var value (Message logic Disjunction)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs not)
  (construct
    ((value (Message logic Not)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call (oneof not) (var value (Message logic Not)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs ffi)
  (construct
    ((value (Message logic FFI)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call (oneof ffi) (var value (Message logic FFI)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs atom)
  (construct
    ((value (Message logic Atom)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call (oneof atom) (var value (Message logic Atom)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs pragma)
  (construct
    ((value (Message logic Pragma)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call (oneof pragma) (var value (Message logic Pragma)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs primitive)
  (construct
    ((value (Message logic Primitive)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call
          (oneof primitive)
          (var value (Message logic Primitive)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs rel_atom)
  (construct
    ((value (Message logic RelAtom)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call (oneof rel_atom) (var value (Message logic RelAtom)))))))

(rule
  (lhs formula (Message logic Formula))
  (rhs cast)
  (construct
    ((value (Message logic Cast)))
    (Message logic Formula)
    (new-message
      logic
      Formula
      (formula_type
        (call (oneof cast) (var value (Message logic Cast)))))))

(rule
  (lhs true (Message logic Conjunction))
  (rhs "(" "true" ")")
  (construct
    ()
    (Message logic Conjunction)
    (new-message
      logic
      Conjunction
      (args (list (Message logic Formula))))))

(rule
  (lhs false (Message logic Disjunction))
  (rhs "(" "false" ")")
  (construct
    ()
    (Message logic Disjunction)
    (new-message
      logic
      Disjunction
      (args (list (Message logic Formula))))))

(rule
  (lhs exists (Message logic Exists))
  (rhs
    "("
    "exists"
    bindings
    formula
    ")")
  (construct
    ((bindings
      (Tuple
        (List (Message logic Binding))
        (List (Message logic Binding))))
      (formula (Message logic Formula)))
    (Message logic Exists)
    (new-message
      logic
      Exists
      (body
        (new-message
          logic
          Abstraction
          (vars
            (call
              (builtin list_concat)
              (get-element
                (var
                  bindings
                  (Tuple
                    (List (Message logic Binding))
                    (List (Message logic Binding))))
                0)
              (get-element
                (var
                  bindings
                  (Tuple
                    (List (Message logic Binding))
                    (List (Message logic Binding))))
                1)))
          (value (var formula (Message logic Formula))))))))

(rule
  (lhs reduce (Message logic Reduce))
  (rhs
    "("
    "reduce"
    abstraction
    abstraction
    terms
    ")")
  (construct
    ((op (Message logic Abstraction))
      (body (Message logic Abstraction))
      (terms (List (Message logic Term))))
    (Message logic Reduce)
    (new-message
      logic
      Reduce
      (op (var op (Message logic Abstraction)))
      (body (var body (Message logic Abstraction)))
      (terms (var terms (List (Message logic Term)))))))

(rule
  (lhs term (Message logic Term))
  (rhs var)
  (construct
    ((value (Message logic Var)))
    (Message logic Term)
    (new-message
      logic
      Term
      (term_type
        (call (oneof var) (var value (Message logic Var)))))))

(rule
  (lhs term (Message logic Term))
  (rhs constant)
  (construct
    ((value (Message logic Value)))
    (Message logic Term)
    (new-message
      logic
      Term
      (term_type
        (call (oneof constant) (var value (Message logic Value)))))))

(rule
  (lhs var (Message logic Var))
  (rhs SYMBOL)
  (construct
    ((symbol String))
    (Message logic Var)
    (new-message logic Var (name (var symbol String)))))

(rule
  (lhs constant (Message logic Value))
  (rhs value)
  (construct
    ((x (Message logic Value)))
    (Message logic Value)
    (var x (Message logic Value))))

(rule
  (lhs conjunction (Message logic Conjunction))
  (rhs
    "("
    "and"
    (star formula)
    ")")
  (construct
    ((args (List (Message logic Formula))))
    (Message logic Conjunction)
    (new-message
      logic
      Conjunction
      (args (var args (List (Message logic Formula)))))))

(rule
  (lhs disjunction (Message logic Disjunction))
  (rhs
    "("
    "or"
    (star formula)
    ")")
  (construct
    ((args (List (Message logic Formula))))
    (Message logic Disjunction)
    (new-message
      logic
      Disjunction
      (args (var args (List (Message logic Formula)))))))

(rule
  (lhs not (Message logic Not))
  (rhs
    "("
    "not"
    formula
    ")")
  (construct
    ((arg (Message logic Formula)))
    (Message logic Not)
    (new-message
      logic
      Not
      (arg (var arg (Message logic Formula))))))

(rule
  (lhs ffi (Message logic FFI))
  (rhs
    "("
    "ffi"
    name
    ffi_args
    terms
    ")")
  (construct
    ((name String)
      (args (List (Message logic Abstraction)))
      (terms (List (Message logic Term))))
    (Message logic FFI)
    (new-message
      logic
      FFI
      (name (var name String))
      (args (var args (List (Message logic Abstraction))))
      (terms (var terms (List (Message logic Term)))))))

(rule
  (lhs ffi_args (List (Message logic Abstraction)))
  (rhs
    "("
    "args"
    (star abstraction)
    ")")
  (construct
    ((x (List (Message logic Abstraction))))
    (List (Message logic Abstraction))
    (var x (List (Message logic Abstraction)))))

(rule
  (lhs terms (List (Message logic Term)))
  (rhs
    "("
    "terms"
    (star term)
    ")")
  (construct
    ((x (List (Message logic Term))))
    (List (Message logic Term))
    (var x (List (Message logic Term)))))

(rule
  (lhs name String)
  (rhs COLON_SYMBOL)
  (construct ((x String)) String (var x String)))

(rule
  (lhs atom (Message logic Atom))
  (rhs
    "("
    "atom"
    relation_id
    (star term)
    ")")
  (construct
    ((name (Message logic RelationId))
      (terms (List (Message logic Term))))
    (Message logic Atom)
    (new-message
      logic
      Atom
      (name (var name (Message logic RelationId)))
      (terms (var terms (List (Message logic Term)))))))

(rule
  (lhs pragma (Message logic Pragma))
  (rhs
    "("
    "pragma"
    name
    (star term)
    ")")
  (construct
    ((name String) (terms (List (Message logic Term))))
    (Message logic Pragma)
    (new-message
      logic
      Pragma
      (name (var name String))
      (terms (var terms (List (Message logic Term)))))))

(rule
  (lhs primitive (Message logic Primitive))
  (rhs eq)
  (construct
    ((op (Message logic Primitive)))
    (Message logic Primitive)
    (var op (Message logic Primitive))))

(rule
  (lhs primitive (Message logic Primitive))
  (rhs lt)
  (construct
    ((op (Message logic Primitive)))
    (Message logic Primitive)
    (var op (Message logic Primitive))))

(rule
  (lhs primitive (Message logic Primitive))
  (rhs lt_eq)
  (construct
    ((op (Message logic Primitive)))
    (Message logic Primitive)
    (var op (Message logic Primitive))))

(rule
  (lhs primitive (Message logic Primitive))
  (rhs gt)
  (construct
    ((op (Message logic Primitive)))
    (Message logic Primitive)
    (var op (Message logic Primitive))))

(rule
  (lhs primitive (Message logic Primitive))
  (rhs gt_eq)
  (construct
    ((op (Message logic Primitive)))
    (Message logic Primitive)
    (var op (Message logic Primitive))))

(rule
  (lhs primitive (Message logic Primitive))
  (rhs add)
  (construct
    ((op (Message logic Primitive)))
    (Message logic Primitive)
    (var op (Message logic Primitive))))

(rule
  (lhs primitive (Message logic Primitive))
  (rhs minus)
  (construct
    ((op (Message logic Primitive)))
    (Message logic Primitive)
    (var op (Message logic Primitive))))

(rule
  (lhs primitive (Message logic Primitive))
  (rhs multiply)
  (construct
    ((op (Message logic Primitive)))
    (Message logic Primitive)
    (var op (Message logic Primitive))))

(rule
  (lhs primitive (Message logic Primitive))
  (rhs divide)
  (construct
    ((op (Message logic Primitive)))
    (Message logic Primitive)
    (var op (Message logic Primitive))))

(rule
  (lhs primitive (Message logic Primitive))
  (rhs
    "("
    "primitive"
    name
    (star rel_term)
    ")")
  (construct
    ((name String) (terms (List (Message logic RelTerm))))
    (Message logic Primitive)
    (new-message
      logic
      Primitive
      (name (var name String))
      (terms (var terms (List (Message logic RelTerm)))))))

(rule
  (lhs eq (Message logic Primitive))
  (rhs
    "("
    "="
    term
    term
    ")")
  (construct
    ((left (Message logic Term)) (right (Message logic Term)))
    (Message logic Primitive)
    (new-message
      logic
      Primitive
      (name (lit "rel_primitive_eq"))
      (terms
        (list
          (Message logic RelTerm)
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var left (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var right (Message logic Term))))))))))

(rule
  (lhs lt (Message logic Primitive))
  (rhs
    "("
    "<"
    term
    term
    ")")
  (construct
    ((left (Message logic Term)) (right (Message logic Term)))
    (Message logic Primitive)
    (new-message
      logic
      Primitive
      (name (lit "rel_primitive_lt_monotype"))
      (terms
        (list
          (Message logic RelTerm)
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var left (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var right (Message logic Term))))))))))

(rule
  (lhs lt_eq (Message logic Primitive))
  (rhs
    "("
    "<="
    term
    term
    ")")
  (construct
    ((left (Message logic Term)) (right (Message logic Term)))
    (Message logic Primitive)
    (new-message
      logic
      Primitive
      (name (lit "rel_primitive_lt_eq_monotype"))
      (terms
        (list
          (Message logic RelTerm)
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var left (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var right (Message logic Term))))))))))

(rule
  (lhs gt (Message logic Primitive))
  (rhs
    "("
    ">"
    term
    term
    ")")
  (construct
    ((left (Message logic Term)) (right (Message logic Term)))
    (Message logic Primitive)
    (new-message
      logic
      Primitive
      (name (lit "rel_primitive_gt_monotype"))
      (terms
        (list
          (Message logic RelTerm)
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var left (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var right (Message logic Term))))))))))

(rule
  (lhs gt_eq (Message logic Primitive))
  (rhs
    "("
    ">="
    term
    term
    ")")
  (construct
    ((left (Message logic Term)) (right (Message logic Term)))
    (Message logic Primitive)
    (new-message
      logic
      Primitive
      (name (lit "rel_primitive_gt_eq_monotype"))
      (terms
        (list
          (Message logic RelTerm)
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var left (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var right (Message logic Term))))))))))

(rule
  (lhs add (Message logic Primitive))
  (rhs
    "("
    "+"
    term
    term
    term
    ")")
  (construct
    ((left (Message logic Term))
      (right (Message logic Term))
      (result (Message logic Term)))
    (Message logic Primitive)
    (new-message
      logic
      Primitive
      (name (lit "rel_primitive_add_monotype"))
      (terms
        (list
          (Message logic RelTerm)
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var left (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var right (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var result (Message logic Term))))))))))

(rule
  (lhs minus (Message logic Primitive))
  (rhs
    "("
    "-"
    term
    term
    term
    ")")
  (construct
    ((left (Message logic Term))
      (right (Message logic Term))
      (result (Message logic Term)))
    (Message logic Primitive)
    (new-message
      logic
      Primitive
      (name (lit "rel_primitive_subtract_monotype"))
      (terms
        (list
          (Message logic RelTerm)
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var left (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var right (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var result (Message logic Term))))))))))

(rule
  (lhs multiply (Message logic Primitive))
  (rhs
    "("
    "*"
    term
    term
    term
    ")")
  (construct
    ((left (Message logic Term))
      (right (Message logic Term))
      (result (Message logic Term)))
    (Message logic Primitive)
    (new-message
      logic
      Primitive
      (name (lit "rel_primitive_multiply_monotype"))
      (terms
        (list
          (Message logic RelTerm)
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var left (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var right (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var result (Message logic Term))))))))))

(rule
  (lhs divide (Message logic Primitive))
  (rhs
    "("
    "/"
    term
    term
    term
    ")")
  (construct
    ((left (Message logic Term))
      (right (Message logic Term))
      (result (Message logic Term)))
    (Message logic Primitive)
    (new-message
      logic
      Primitive
      (name (lit "rel_primitive_divide_monotype"))
      (terms
        (list
          (Message logic RelTerm)
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var left (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var right (Message logic Term)))))
          (new-message
            logic
            RelTerm
            (rel_term_type
              (call (oneof term) (var result (Message logic Term))))))))))

(rule
  (lhs rel_term (Message logic RelTerm))
  (rhs specialized_value)
  (construct
    ((value (Message logic Value)))
    (Message logic RelTerm)
    (new-message
      logic
      RelTerm
      (rel_term_type
        (call
          (oneof specialized_value)
          (var value (Message logic Value)))))))

(rule
  (lhs rel_term (Message logic RelTerm))
  (rhs term)
  (construct
    ((value (Message logic Term)))
    (Message logic RelTerm)
    (new-message
      logic
      RelTerm
      (rel_term_type
        (call (oneof term) (var value (Message logic Term)))))))

(rule
  (lhs specialized_value (Message logic Value))
  (rhs "#" value)
  (construct
    ((value (Message logic Value)))
    (Message logic Value)
    (var value (Message logic Value))))

(rule
  (lhs rel_atom (Message logic RelAtom))
  (rhs
    "("
    "relatom"
    name
    (star rel_term)
    ")")
  (construct
    ((name String) (terms (List (Message logic RelTerm))))
    (Message logic RelAtom)
    (new-message
      logic
      RelAtom
      (name (var name String))
      (terms (var terms (List (Message logic RelTerm)))))))

(rule
  (lhs cast (Message logic Cast))
  (rhs
    "("
    "cast"
    term
    term
    ")")
  (construct
    ((input (Message logic Term)) (result (Message logic Term)))
    (Message logic Cast)
    (new-message
      logic
      Cast
      (input (var input (Message logic Term)))
      (result (var result (Message logic Term))))))

(rule
  (lhs attrs (List (Message logic Attribute)))
  (rhs
    "("
    "attrs"
    (star attribute)
    ")")
  (construct
    ((x (List (Message logic Attribute))))
    (List (Message logic Attribute))
    (var x (List (Message logic Attribute)))))

(rule
  (lhs attribute (Message logic Attribute))
  (rhs
    "("
    "attribute"
    name
    (star value)
    ")")
  (construct
    ((name String) (args (List (Message logic Value))))
    (Message logic Attribute)
    (new-message
      logic
      Attribute
      (name (var name String))
      (args (var args (List (Message logic Value)))))))

(rule
  (lhs algorithm (Message logic Algorithm))
  (rhs
    "("
    "algorithm"
    (star relation_id)
    script
    ")")
  (construct
    ((global (List (Message logic RelationId)))
      (body (Message logic Script)))
    (Message logic Algorithm)
    (new-message
      logic
      Algorithm
      (global (var global (List (Message logic RelationId))))
      (body (var body (Message logic Script))))))

(rule
  (lhs script (Message logic Script))
  (rhs
    "("
    "script"
    (star construct)
    ")")
  (construct
    ((constructs (List (Message logic Construct))))
    (Message logic Script)
    (new-message
      logic
      Script
      (constructs
        (var constructs (List (Message logic Construct)))))))

(rule
  (lhs construct (Message logic Construct))
  (rhs loop)
  (construct
    ((value (Message logic Loop)))
    (Message logic Construct)
    (new-message
      logic
      Construct
      (construct_type
        (call (oneof loop) (var value (Message logic Loop)))))))

(rule
  (lhs construct (Message logic Construct))
  (rhs instruction)
  (construct
    ((value (Message logic Instruction)))
    (Message logic Construct)
    (new-message
      logic
      Construct
      (construct_type
        (call
          (oneof instruction)
          (var value (Message logic Instruction)))))))

(rule
  (lhs loop (Message logic Loop))
  (rhs
    "("
    "loop"
    init
    script
    ")")
  (construct
    ((init (List (Message logic Instruction)))
      (body (Message logic Script)))
    (Message logic Loop)
    (new-message
      logic
      Loop
      (init (var init (List (Message logic Instruction))))
      (body (var body (Message logic Script))))))

(rule
  (lhs init (List (Message logic Instruction)))
  (rhs
    "("
    "init"
    (star instruction)
    ")")
  (construct
    ((x (List (Message logic Instruction))))
    (List (Message logic Instruction))
    (var x (List (Message logic Instruction)))))

(rule
  (lhs instruction (Message logic Instruction))
  (rhs assign)
  (construct
    ((value (Message logic Assign)))
    (Message logic Instruction)
    (new-message
      logic
      Instruction
      (instr_type
        (call (oneof assign) (var value (Message logic Assign)))))))

(rule
  (lhs instruction (Message logic Instruction))
  (rhs upsert)
  (construct
    ((value (Message logic Upsert)))
    (Message logic Instruction)
    (new-message
      logic
      Instruction
      (instr_type
        (call (oneof upsert) (var value (Message logic Upsert)))))))

(rule
  (lhs instruction (Message logic Instruction))
  (rhs break)
  (construct
    ((value (Message logic Break)))
    (Message logic Instruction)
    (new-message
      logic
      Instruction
      (instr_type
        (call (oneof break) (var value (Message logic Break)))))))

(rule
  (lhs instruction (Message logic Instruction))
  (rhs monoid_def)
  (construct
    ((value (Message logic MonoidDef)))
    (Message logic Instruction)
    (new-message
      logic
      Instruction
      (instr_type
        (call
          (oneof monoid_def)
          (var value (Message logic MonoidDef)))))))

(rule
  (lhs instruction (Message logic Instruction))
  (rhs monus_def)
  (construct
    ((value (Message logic MonusDef)))
    (Message logic Instruction)
    (new-message
      logic
      Instruction
      (instr_type
        (call
          (oneof monus_def)
          (var value (Message logic MonusDef)))))))

(rule
  (lhs assign (Message logic Assign))
  (rhs
    "("
    "assign"
    relation_id
    abstraction
    (option attrs)
    ")")
  (construct
    ((name (Message logic RelationId))
      (body (Message logic Abstraction))
      (attrs (Option (List (Message logic Attribute)))))
    (Message logic Assign)
    (new-message
      logic
      Assign
      (name (var name (Message logic RelationId)))
      (body (var body (Message logic Abstraction)))
      (attrs
        (call
          (builtin unwrap_option_or)
          (var attrs (Option (List (Message logic Attribute))))
          (list (Message logic Attribute)))))))

(rule
  (lhs upsert (Message logic Upsert))
  (rhs
    "("
    "upsert"
    relation_id
    abstraction_with_arity
    (option attrs)
    ")")
  (construct
    ((name (Message logic RelationId))
      (abstraction_with_arity
        (Tuple (Message logic Abstraction) Int64))
      (attrs (Option (List (Message logic Attribute)))))
    (Message logic Upsert)
    (let
      (abstraction (Message logic Abstraction))
      (get-element
        (var
          abstraction_with_arity
          (Tuple (Message logic Abstraction) Int64))
        0)
      (let
        (arity Int64)
        (get-element
          (var
            abstraction_with_arity
            (Tuple (Message logic Abstraction) Int64))
          1)
        (new-message
          logic
          Upsert
          (name (var name (Message logic RelationId)))
          (body (var abstraction (Message logic Abstraction)))
          (attrs
            (call
              (builtin unwrap_option_or)
              (var attrs (Option (List (Message logic Attribute))))
              (list (Message logic Attribute))))
          (value_arity (var arity Int64)))))))

(rule
  (lhs
    abstraction_with_arity
    (Tuple (Message logic Abstraction) Int64))
  (rhs
    "("
    bindings
    formula
    ")")
  (construct
    ((bindings
      (Tuple
        (List (Message logic Binding))
        (List (Message logic Binding))))
      (formula (Message logic Formula)))
    (Tuple (Message logic Abstraction) Int64)
    (call
      (builtin make_tuple)
      (new-message
        logic
        Abstraction
        (vars
          (call
            (builtin list_concat)
            (get-element
              (var
                bindings
                (Tuple
                  (List (Message logic Binding))
                  (List (Message logic Binding))))
              0)
            (get-element
              (var
                bindings
                (Tuple
                  (List (Message logic Binding))
                  (List (Message logic Binding))))
              1)))
        (value (var formula (Message logic Formula))))
      (call
        (builtin length)
        (get-element
          (var
            bindings
            (Tuple
              (List (Message logic Binding))
              (List (Message logic Binding))))
          1)))))

(rule
  (lhs break (Message logic Break))
  (rhs
    "("
    "break"
    relation_id
    abstraction
    (option attrs)
    ")")
  (construct
    ((name (Message logic RelationId))
      (body (Message logic Abstraction))
      (attrs (Option (List (Message logic Attribute)))))
    (Message logic Break)
    (new-message
      logic
      Break
      (name (var name (Message logic RelationId)))
      (body (var body (Message logic Abstraction)))
      (attrs
        (call
          (builtin unwrap_option_or)
          (var attrs (Option (List (Message logic Attribute))))
          (list (Message logic Attribute)))))))

(rule
  (lhs monoid_def (Message logic MonoidDef))
  (rhs
    "("
    "monoid"
    monoid
    relation_id
    abstraction_with_arity
    (option attrs)
    ")")
  (construct
    ((monoid (Message logic Monoid))
      (name (Message logic RelationId))
      (abstraction_with_arity
        (Tuple (Message logic Abstraction) Int64))
      (attrs (Option (List (Message logic Attribute)))))
    (Message logic MonoidDef)
    (let
      (abstraction (Message logic Abstraction))
      (get-element
        (var
          abstraction_with_arity
          (Tuple (Message logic Abstraction) Int64))
        0)
      (let
        (arity Int64)
        (get-element
          (var
            abstraction_with_arity
            (Tuple (Message logic Abstraction) Int64))
          1)
        (new-message
          logic
          MonoidDef
          (monoid (var monoid (Message logic Monoid)))
          (name (var name (Message logic RelationId)))
          (body (var abstraction (Message logic Abstraction)))
          (attrs
            (call
              (builtin unwrap_option_or)
              (var attrs (Option (List (Message logic Attribute))))
              (list (Message logic Attribute))))
          (value_arity (var arity Int64)))))))

(rule
  (lhs monoid (Message logic Monoid))
  (rhs or_monoid)
  (construct
    ((value (Message logic OrMonoid)))
    (Message logic Monoid)
    (new-message
      logic
      Monoid
      (value
        (call
          (oneof or_monoid)
          (var value (Message logic OrMonoid)))))))

(rule
  (lhs monoid (Message logic Monoid))
  (rhs min_monoid)
  (construct
    ((value (Message logic MinMonoid)))
    (Message logic Monoid)
    (new-message
      logic
      Monoid
      (value
        (call
          (oneof min_monoid)
          (var value (Message logic MinMonoid)))))))

(rule
  (lhs monoid (Message logic Monoid))
  (rhs max_monoid)
  (construct
    ((value (Message logic MaxMonoid)))
    (Message logic Monoid)
    (new-message
      logic
      Monoid
      (value
        (call
          (oneof max_monoid)
          (var value (Message logic MaxMonoid)))))))

(rule
  (lhs monoid (Message logic Monoid))
  (rhs sum_monoid)
  (construct
    ((value (Message logic SumMonoid)))
    (Message logic Monoid)
    (new-message
      logic
      Monoid
      (value
        (call
          (oneof sum_monoid)
          (var value (Message logic SumMonoid)))))))

(rule
  (lhs or_monoid (Message logic OrMonoid))
  (rhs "(" "or" ")")
  (construct
    ()
    (Message logic OrMonoid)
    (new-message logic OrMonoid)))

(rule
  (lhs min_monoid (Message logic MinMonoid))
  (rhs "(" "min" type ")")
  (construct
    ((type (Message logic Type)))
    (Message logic MinMonoid)
    (new-message
      logic
      MinMonoid
      (type (var type (Message logic Type))))))

(rule
  (lhs max_monoid (Message logic MaxMonoid))
  (rhs "(" "max" type ")")
  (construct
    ((type (Message logic Type)))
    (Message logic MaxMonoid)
    (new-message
      logic
      MaxMonoid
      (type (var type (Message logic Type))))))

(rule
  (lhs sum_monoid (Message logic SumMonoid))
  (rhs "(" "sum" type ")")
  (construct
    ((type (Message logic Type)))
    (Message logic SumMonoid)
    (new-message
      logic
      SumMonoid
      (type (var type (Message logic Type))))))

(rule
  (lhs monus_def (Message logic MonusDef))
  (rhs
    "("
    "monus"
    monoid
    relation_id
    abstraction_with_arity
    (option attrs)
    ")")
  (construct
    ((monoid (Message logic Monoid))
      (name (Message logic RelationId))
      (abstraction_with_arity
        (Tuple (Message logic Abstraction) Int64))
      (attrs (Option (List (Message logic Attribute)))))
    (Message logic MonusDef)
    (let
      (abstraction (Message logic Abstraction))
      (get-element
        (var
          abstraction_with_arity
          (Tuple (Message logic Abstraction) Int64))
        0)
      (let
        (arity Int64)
        (get-element
          (var
            abstraction_with_arity
            (Tuple (Message logic Abstraction) Int64))
          1)
        (new-message
          logic
          MonusDef
          (monoid (var monoid (Message logic Monoid)))
          (name (var name (Message logic RelationId)))
          (body (var abstraction (Message logic Abstraction)))
          (attrs
            (call
              (builtin unwrap_option_or)
              (var attrs (Option (List (Message logic Attribute))))
              (list (Message logic Attribute))))
          (value_arity (var arity Int64)))))))

(rule
  (lhs constraint (Message logic Constraint))
  (rhs
    "("
    "functional_dependency"
    relation_id
    abstraction
    functional_dependency_keys
    functional_dependency_values
    ")")
  (construct
    ((name (Message logic RelationId))
      (guard (Message logic Abstraction))
      (keys (List (Message logic Var)))
      (values (List (Message logic Var))))
    (Message logic Constraint)
    (new-message
      logic
      Constraint
      (name (var name (Message logic RelationId)))
      (constraint_type
        (call
          (oneof functional_dependency)
          (new-message
            logic
            FunctionalDependency
            (guard (var guard (Message logic Abstraction)))
            (keys (var keys (List (Message logic Var))))
            (values (var values (List (Message logic Var))))))))))

(rule
  (lhs functional_dependency_keys (List (Message logic Var)))
  (rhs
    "("
    "keys"
    (star var)
    ")")
  (construct
    ((x (List (Message logic Var))))
    (List (Message logic Var))
    (var x (List (Message logic Var)))))

(rule
  (lhs
    functional_dependency_values
    (List (Message logic Var)))
  (rhs
    "("
    "values"
    (star var)
    ")")
  (construct
    ((x (List (Message logic Var))))
    (List (Message logic Var))
    (var x (List (Message logic Var)))))

(rule
  (lhs data (Message logic Data))
  (rhs rel_edb)
  (construct
    ((value (Message logic RelEDB)))
    (Message logic Data)
    (new-message
      logic
      Data
      (data_type
        (call (oneof rel_edb) (var value (Message logic RelEDB)))))))

(rule
  (lhs data (Message logic Data))
  (rhs
    betree_relation)
  (construct
    ((value (Message logic BeTreeRelation)))
    (Message logic Data)
    (new-message
      logic
      Data
      (data_type
        (call
          (oneof betree_relation)
          (var value (Message logic BeTreeRelation)))))))

(rule
  (lhs data (Message logic Data))
  (rhs csv_data)
  (construct
    ((value (Message logic CSVData)))
    (Message logic Data)
    (new-message
      logic
      Data
      (data_type
        (call (oneof csv_data) (var value (Message logic CSVData)))))))

(rule
  (lhs rel_edb_path (List String))
  (rhs
    "["
    (star STRING)
    "]")
  (construct
    ((x (List String)))
    (List String)
    (var x (List String))))

(rule
  (lhs rel_edb_types (List (Message logic Type)))
  (rhs
    "["
    (star type)
    "]")
  (construct
    ((x (List (Message logic Type))))
    (List (Message logic Type))
    (var x (List (Message logic Type)))))

(rule
  (lhs rel_edb (Message logic RelEDB))
  (rhs
    "("
    "rel_edb"
    relation_id
    rel_edb_path
    (option rel_edb_types)
    ")")
  (construct
    ((target_id (Message logic RelationId))
      (path (List String))
      (types (Option (List (Message logic Type)))))
    (Message logic RelEDB)
    (new-message
      logic
      RelEDB
      (target_id (var target_id (Message logic RelationId)))
      (path (var path (List String)))
      (types
        (call
          (builtin unwrap_option_or)
          (var types (Option (List (Message logic Type))))
          (list (Message logic Type)))))))

(rule
  (lhs betree_relation (Message logic BeTreeRelation))
  (rhs
    be_tree_relation)
  (construct
    ((x (Message logic BeTreeRelation)))
    (Message logic BeTreeRelation)
    (var x (Message logic BeTreeRelation))))

(rule
  (lhs be_tree_relation (Message logic BeTreeRelation))
  (rhs
    "("
    "betree_relation"
    relation_id
    be_tree_info
    ")")
  (construct
    ((name (Message logic RelationId))
      (relation_info (Message logic BeTreeInfo)))
    (Message logic BeTreeRelation)
    (new-message
      logic
      BeTreeRelation
      (name (var name (Message logic RelationId)))
      (relation_info
        (var relation_info (Message logic BeTreeInfo))))))

(rule
  (lhs be_tree_info (Message logic BeTreeInfo))
  (rhs
    "("
    "betree_info"
    (option
      be_tree_info_key_types)
    (option
      be_tree_info_value_types)
    config_dict
    ")")
  (construct
    ((key_types (Option (List (Message logic Type))))
      (value_types (Option (List (Message logic Type))))
      (config_dict (List (Tuple String (Message logic Value)))))
    (Message logic BeTreeInfo)
    (call
      (builtin construct_betree_info)
      (call
        (builtin unwrap_option_or)
        (var key_types (Option (List (Message logic Type))))
        (list (Message logic Type)))
      (call
        (builtin unwrap_option_or)
        (var value_types (Option (List (Message logic Type))))
        (list (Message logic Type)))
      (var config_dict (List (Tuple String (Message logic Value)))))))

(rule
  (lhs be_tree_info_key_types (List (Message logic Type)))
  (rhs
    "("
    "key_types"
    (star type)
    ")")
  (construct
    ((x (List (Message logic Type))))
    (List (Message logic Type))
    (var x (List (Message logic Type)))))

(rule
  (lhs be_tree_info_value_types (List (Message logic Type)))
  (rhs
    "("
    "value_types"
    (star type)
    ")")
  (construct
    ((x (List (Message logic Type))))
    (List (Message logic Type))
    (var x (List (Message logic Type)))))

(rule
  (lhs csv_data (Message logic CSVData))
  (rhs csvdata)
  (construct
    ((x (Message logic CSVData)))
    (Message logic CSVData)
    (var x (Message logic CSVData))))

(rule
  (lhs csv_columns (List (Message logic CSVColumn)))
  (rhs
    "("
    "columns"
    (star csv_column)
    ")")
  (construct
    ((x (List (Message logic CSVColumn))))
    (List (Message logic CSVColumn))
    (var x (List (Message logic CSVColumn)))))

(rule
  (lhs csv_asof String)
  (rhs
    "("
    "asof"
    STRING
    ")")
  (construct
    ((x String))
    String
    (var x String)))

(rule
  (lhs csvdata (Message logic CSVData))
  (rhs
    "("
    "csv_data"
    csvlocator
    csv_config
    csv_columns
    csv_asof
    ")")
  (construct
    ((locator (Message logic CSVLocator))
      (config (Message logic CSVConfig))
      (columns (List (Message logic CSVColumn)))
      (asof String))
    (Message logic CSVData)
    (new-message
      logic
      CSVData
      (locator (var locator (Message logic CSVLocator)))
      (config (var config (Message logic CSVConfig)))
      (columns (var columns (List (Message logic CSVColumn))))
      (asof (var asof String)))))

(rule
  (lhs csv_locator_paths (List String))
  (rhs
    "("
    "paths"
    (star STRING)
    ")")
  (construct
    ((x (List String)))
    (List String)
    (var x (List String))))

(rule
  (lhs csv_locator_inline_data String)
  (rhs
    "("
    "inline_data"
    STRING
    ")")
  (construct
    ((x String))
    String
    (var x String)))

(rule
  (lhs csvlocator (Message logic CSVLocator))
  (rhs
    "("
    "csv_locator"
    (option csv_locator_paths)
    (option csv_locator_inline_data)
    ")")
  (construct
    ((paths (Option (List String))) (inline_data (Option String)))
    (Message logic CSVLocator)
    (new-message
      logic
      CSVLocator
      (paths
        (call
          (builtin unwrap_option_or)
          (var paths (Option (List String)))
          (list String)))
      (inline_data
        (call
          (builtin encode_string)
          (call
            (builtin unwrap_option_or)
            (var inline_data (Option String))
            (lit "")))))))

(rule
  (lhs csv_config (Message logic CSVConfig))
  (rhs
    "("
    "csv_config"
    config_dict
    ")")
  (construct
    ((config_dict (List (Tuple String (Message logic Value)))))
    (Message logic CSVConfig)
    (call
      (builtin construct_csv_config)
      (var config_dict (List (Tuple String (Message logic Value)))))))

(rule
  (lhs csv_column (Message logic CSVColumn))
  (rhs
    "("
    "column"
    STRING
    relation_id
    "["
    (star type)
    "]"
    ")")
  (construct
    ((column_name String)
      (target_id (Message logic RelationId))
      (types (List (Message logic Type))))
    (Message logic CSVColumn)
    (new-message
      logic
      CSVColumn
      (column_name (var column_name String))
      (target_id (var target_id (Message logic RelationId)))
      (types (var types (List (Message logic Type)))))))

(rule
  (lhs undefine (Message transactions Undefine))
  (rhs
    "("
    "undefine"
    fragment_id
    ")")
  (construct
    ((fragment_id (Message fragments FragmentId)))
    (Message transactions Undefine)
    (new-message
      transactions
      Undefine
      (fragment_id
        (var fragment_id (Message fragments FragmentId))))))

(rule
  (lhs context (Message transactions Context))
  (rhs
    "("
    "context"
    (star relation_id)
    ")")
  (construct
    ((relations (List (Message logic RelationId))))
    (Message transactions Context)
    (new-message
      transactions
      Context
      (relations
        (var relations (List (Message logic RelationId)))))))

(rule
  (lhs epoch_reads (List (Message transactions Read)))
  (rhs
    "("
    "reads"
    (star read)
    ")")
  (construct
    ((x (List (Message transactions Read))))
    (List (Message transactions Read))
    (var x (List (Message transactions Read)))))

(rule
  (lhs read (Message transactions Read))
  (rhs demand)
  (construct
    ((value (Message transactions Demand)))
    (Message transactions Read)
    (new-message
      transactions
      Read
      (read_type
        (call
          (oneof demand)
          (var value (Message transactions Demand)))))))

(rule
  (lhs read (Message transactions Read))
  (rhs output)
  (construct
    ((value (Message transactions Output)))
    (Message transactions Read)
    (new-message
      transactions
      Read
      (read_type
        (call
          (oneof output)
          (var value (Message transactions Output)))))))

(rule
  (lhs read (Message transactions Read))
  (rhs what_if)
  (construct
    ((value (Message transactions WhatIf)))
    (Message transactions Read)
    (new-message
      transactions
      Read
      (read_type
        (call
          (oneof what_if)
          (var value (Message transactions WhatIf)))))))

(rule
  (lhs read (Message transactions Read))
  (rhs abort)
  (construct
    ((value (Message transactions Abort)))
    (Message transactions Read)
    (new-message
      transactions
      Read
      (read_type
        (call
          (oneof abort)
          (var value (Message transactions Abort)))))))

(rule
  (lhs read (Message transactions Read))
  (rhs export)
  (construct
    ((value (Message transactions Export)))
    (Message transactions Read)
    (new-message
      transactions
      Read
      (read_type
        (call
          (oneof export)
          (var value (Message transactions Export)))))))

(rule
  (lhs demand (Message transactions Demand))
  (rhs
    "("
    "demand"
    relation_id
    ")")
  (construct
    ((relation_id (Message logic RelationId)))
    (Message transactions Demand)
    (new-message
      transactions
      Demand
      (relation_id (var relation_id (Message logic RelationId))))))

(rule
  (lhs output (Message transactions Output))
  (rhs
    "("
    "output"
    (option name)
    relation_id
    ")")
  (construct
    ((name (Option String))
      (relation_id (Message logic RelationId)))
    (Message transactions Output)
    (new-message
      transactions
      Output
      (name
        (call
          (builtin unwrap_option_or)
          (var name (Option String))
          (lit "output")))
      (relation_id (var relation_id (Message logic RelationId))))))

(rule
  (lhs what_if (Message transactions WhatIf))
  (rhs
    "("
    "what_if"
    name
    epoch
    ")")
  (construct
    ((branch String) (epoch (Message transactions Epoch)))
    (Message transactions WhatIf)
    (new-message
      transactions
      WhatIf
      (branch (var branch String))
      (epoch (var epoch (Message transactions Epoch))))))

(rule
  (lhs abort (Message transactions Abort))
  (rhs
    "("
    "abort"
    (option name)
    relation_id
    ")")
  (construct
    ((name (Option String))
      (relation_id (Message logic RelationId)))
    (Message transactions Abort)
    (new-message
      transactions
      Abort
      (name
        (call
          (builtin unwrap_option_or)
          (var name (Option String))
          (lit "abort")))
      (relation_id (var relation_id (Message logic RelationId))))))

(rule
  (lhs export (Message transactions Export))
  (rhs
    "("
    "export"
    export_csv_config
    ")")
  (construct
    ((config (Message transactions ExportCSVConfig)))
    (Message transactions Export)
    (new-message
      transactions
      Export
      (export_config
        (call
          (oneof csv_config)
          (var config (Message transactions ExportCSVConfig)))))))

(rule
  (lhs
    export_csv_config
    (Message transactions ExportCSVConfig))
  (rhs
    "("
    "export_csv_config"
    export_csv_path
    export_csv_columns
    config_dict
    ")")
  (construct
    ((path String)
      (columns (List (Message transactions ExportCSVColumn)))
      (config (List (Tuple String (Message logic Value)))))
    (Message transactions ExportCSVConfig)
    (call
      (builtin export_csv_config)
      (var path String)
      (var columns (List (Message transactions ExportCSVColumn)))
      (var config (List (Tuple String (Message logic Value)))))))

(rule
  (lhs export_csv_path String)
  (rhs "(" "path" STRING ")")
  (construct ((x String)) String (var x String)))

(rule
  (lhs
    export_csv_columns
    (List (Message transactions ExportCSVColumn)))
  (rhs
    "("
    "columns"
    (star
      export_csv_column)
    ")")
  (construct
    ((x (List (Message transactions ExportCSVColumn))))
    (List (Message transactions ExportCSVColumn))
    (var x (List (Message transactions ExportCSVColumn)))))

(rule
  (lhs
    export_csv_column
    (Message transactions ExportCSVColumn))
  (rhs
    "("
    "column"
    STRING
    relation_id
    ")")
  (construct
    ((name String) (relation_id (Message logic RelationId)))
    (Message transactions ExportCSVColumn)
    (new-message
      transactions
      ExportCSVColumn
      (column_name (var name String))
      (column_data (var relation_id (Message logic RelationId))))))
