(rule (lhs transaction (Message transactions Transaction)) (rhs "(" "transaction" (option (nonterm configure (Message transactions Configure))) (option (nonterm sync (Message transactions Sync))) (star (nonterm epoch (Message transactions Epoch))) ")") (lambda ((configure (Option (Message transactions Configure))) (sync (Option (Message transactions Sync))) (epochs (List (Message transactions Epoch)))) (Message transactions Transaction) (call (message transactions Transaction) (var epochs (List (Message transactions Epoch))) (call (builtin unwrap_option_or) (var configure (Option (Message transactions Configure))) (call (builtin construct_configure) (list (Tuple String (Message logic Value))))) (var sync (Option (Message transactions Sync))))))

(rule (lhs configure (Message transactions Configure)) (rhs "(" "configure" (nonterm config_dict (List (Tuple String (Message logic Value)))) ")") (lambda ((config_dict (List (Tuple String (Message logic Value))))) (Message transactions Configure) (call (builtin construct_configure) (var config_dict (List (Tuple String (Message logic Value)))))))

(rule (lhs config_dict (List (Tuple String (Message logic Value)))) (rhs "{" (star (nonterm config_key_value (Tuple String (Message logic Value)))) "}") (lambda ((x (List (Tuple String (Message logic Value))))) (List (Tuple String (Message logic Value))) (var x (List (Tuple String (Message logic Value))))))

(rule (lhs config_key_value (Tuple String (Message logic Value))) (rhs (term COLON_SYMBOL String) (nonterm value (Message logic Value))) (lambda ((symbol String) (value (Message logic Value))) (Tuple String (Message logic Value)) (call (builtin make_tuple) (var symbol String) (var value (Message logic Value)))))

(rule (lhs value (Message logic Value)) (rhs (nonterm date (Message logic DateValue))) (lambda ((value (Message logic DateValue))) (Message logic Value) (call (message logic Value) (call (oneof date_value) (var value (Message logic DateValue))))))

(rule (lhs value (Message logic Value)) (rhs (nonterm datetime (Message logic DateTimeValue))) (lambda ((value (Message logic DateTimeValue))) (Message logic Value) (call (message logic Value) (call (oneof datetime_value) (var value (Message logic DateTimeValue))))))

(rule (lhs value (Message logic Value)) (rhs (term STRING String)) (lambda ((value String)) (Message logic Value) (call (message logic Value) (call (oneof string_value) (var value String)))))

(rule (lhs value (Message logic Value)) (rhs (term INT Int64)) (lambda ((value Int64)) (Message logic Value) (call (message logic Value) (call (oneof int_value) (var value Int64)))))

(rule (lhs value (Message logic Value)) (rhs (term FLOAT Float64)) (lambda ((value Float64)) (Message logic Value) (call (message logic Value) (call (oneof float_value) (var value Float64)))))

(rule (lhs value (Message logic Value)) (rhs (term UINT128 (Message logic UInt128Value))) (lambda ((value (Message logic UInt128Value))) (Message logic Value) (call (message logic Value) (call (oneof uint128_value) (var value (Message logic UInt128Value))))))

(rule (lhs value (Message logic Value)) (rhs (term INT128 (Message logic Int128Value))) (lambda ((value (Message logic Int128Value))) (Message logic Value) (call (message logic Value) (call (oneof int128_value) (var value (Message logic Int128Value))))))

(rule (lhs value (Message logic Value)) (rhs (term DECIMAL (Message logic DecimalValue))) (lambda ((value (Message logic DecimalValue))) (Message logic Value) (call (message logic Value) (call (oneof decimal_value) (var value (Message logic DecimalValue))))))

(rule (lhs value (Message logic Value)) (rhs "missing") (lambda () (Message logic Value) (call (message logic Value) (call (oneof missing_value) (call (message logic MissingValue))))))

(rule (lhs value (Message logic Value)) (rhs (nonterm boolean_value Boolean)) (lambda ((value Boolean)) (Message logic Value) (call (message logic Value) (call (oneof boolean_value) (var value Boolean)))))

(rule (lhs date (Message logic DateValue)) (rhs "(" "date" (term INT Int64) (term INT Int64) (term INT Int64) ")") (lambda ((year Int64) (month Int64) (day Int64)) (Message logic DateValue) (call (message logic DateValue) (call (builtin int64_to_int32) (var year Int64)) (call (builtin int64_to_int32) (var month Int64)) (call (builtin int64_to_int32) (var day Int64)))))

(rule (lhs datetime (Message logic DateTimeValue)) (rhs "(" "datetime" (term INT Int64) (term INT Int64) (term INT Int64) (term INT Int64) (term INT Int64) (term INT Int64) (option (term INT Int64)) ")") (lambda ((year Int64) (month Int64) (day Int64) (hour Int64) (minute Int64) (second Int64) (microsecond (Option Int64))) (Message logic DateTimeValue) (call (message logic DateTimeValue) (call (builtin int64_to_int32) (var year Int64)) (call (builtin int64_to_int32) (var month Int64)) (call (builtin int64_to_int32) (var day Int64)) (call (builtin int64_to_int32) (var hour Int64)) (call (builtin int64_to_int32) (var minute Int64)) (call (builtin int64_to_int32) (var second Int64)) (call (builtin int64_to_int32) (call (builtin unwrap_option_or) (var microsecond (Option Int64)) (lit 0))))))

(rule (lhs boolean_value Boolean) (rhs "true") (lambda () Boolean (lit true)))

(rule (lhs boolean_value Boolean) (rhs "false") (lambda () Boolean (lit false)))

(rule (lhs sync (Message transactions Sync)) (rhs "(" "sync" (star (nonterm fragment_id (Message fragments FragmentId))) ")") (lambda ((fragments (List (Message fragments FragmentId)))) (Message transactions Sync) (call (message transactions Sync) (var fragments (List (Message fragments FragmentId))))))

(rule (lhs fragment_id (Message fragments FragmentId)) (rhs (term COLON_SYMBOL String)) (lambda ((symbol String)) (Message fragments FragmentId) (call (builtin fragment_id_from_string) (var symbol String))))

(rule (lhs epoch (Message transactions Epoch)) (rhs "(" "epoch" (option (nonterm epoch_writes (List (Message transactions Write)))) (option (nonterm epoch_reads (List (Message transactions Read)))) ")") (lambda ((writes (Option (List (Message transactions Write)))) (reads (Option (List (Message transactions Read))))) (Message transactions Epoch) (call (message transactions Epoch) (call (builtin unwrap_option_or) (var writes (Option (List (Message transactions Write)))) (list (Message transactions Write))) (call (builtin unwrap_option_or) (var reads (Option (List (Message transactions Read)))) (list (Message transactions Read))))))

(rule (lhs epoch_writes (List (Message transactions Write))) (rhs "(" "writes" (star (nonterm write (Message transactions Write))) ")") (lambda ((x (List (Message transactions Write)))) (List (Message transactions Write)) (var x (List (Message transactions Write)))))

(rule (lhs write (Message transactions Write)) (rhs (nonterm define (Message transactions Define))) (lambda ((value (Message transactions Define))) (Message transactions Write) (call (message transactions Write) (call (oneof define) (var value (Message transactions Define))))))

(rule (lhs write (Message transactions Write)) (rhs (nonterm undefine (Message transactions Undefine))) (lambda ((value (Message transactions Undefine))) (Message transactions Write) (call (message transactions Write) (call (oneof undefine) (var value (Message transactions Undefine))))))

(rule (lhs write (Message transactions Write)) (rhs (nonterm context (Message transactions Context))) (lambda ((value (Message transactions Context))) (Message transactions Write) (call (message transactions Write) (call (oneof context) (var value (Message transactions Context))))))

(rule (lhs define (Message transactions Define)) (rhs "(" "define" (nonterm fragment (Message fragments Fragment)) ")") (lambda ((fragment (Message fragments Fragment))) (Message transactions Define) (call (message transactions Define) (var fragment (Message fragments Fragment)))))

(rule (lhs fragment (Message fragments Fragment)) (rhs "(" "fragment" (nonterm new_fragment_id (Message fragments FragmentId)) (star (nonterm declaration (Message logic Declaration))) ")") (lambda ((fragment_id (Message fragments FragmentId)) (declarations (List (Message logic Declaration)))) (Message fragments Fragment) (call (builtin construct_fragment) (var fragment_id (Message fragments FragmentId)) (var declarations (List (Message logic Declaration))))))

(rule (lhs new_fragment_id (Message fragments FragmentId)) (rhs (nonterm fragment_id (Message fragments FragmentId))) (lambda ((fragment_id (Message fragments FragmentId))) (Message fragments FragmentId) (seq (call (builtin start_fragment) (var fragment_id (Message fragments FragmentId))) (var fragment_id (Message fragments FragmentId)))))

(rule (lhs declaration (Message logic Declaration)) (rhs (nonterm def (Message logic Def))) (lambda ((value (Message logic Def))) (Message logic Declaration) (call (message logic Declaration) (call (oneof def) (var value (Message logic Def))))))

(rule (lhs declaration (Message logic Declaration)) (rhs (nonterm algorithm (Message logic Algorithm))) (lambda ((value (Message logic Algorithm))) (Message logic Declaration) (call (message logic Declaration) (call (oneof algorithm) (var value (Message logic Algorithm))))))

(rule (lhs declaration (Message logic Declaration)) (rhs (nonterm constraint (Message logic Constraint))) (lambda ((value (Message logic Constraint))) (Message logic Declaration) (call (message logic Declaration) (call (oneof constraint) (var value (Message logic Constraint))))))

(rule (lhs declaration (Message logic Declaration)) (rhs (nonterm data (Message logic Data))) (lambda ((value (Message logic Data))) (Message logic Declaration) (call (message logic Declaration) (call (oneof data) (var value (Message logic Data))))))

(rule (lhs def (Message logic Def)) (rhs "(" "def" (nonterm relation_id (Message logic RelationId)) (nonterm abstraction (Message logic Abstraction)) (option (nonterm attrs (List (Message logic Attribute)))) ")") (lambda ((name (Message logic RelationId)) (body (Message logic Abstraction)) (attrs (Option (List (Message logic Attribute))))) (Message logic Def) (call (message logic Def) (var name (Message logic RelationId)) (var body (Message logic Abstraction)) (call (builtin unwrap_option_or) (var attrs (Option (List (Message logic Attribute)))) (list (Message logic Attribute))))))

(rule (lhs relation_id (Message logic RelationId)) (rhs (term COLON_SYMBOL String)) (lambda ((symbol String)) (Message logic RelationId) (call (builtin relation_id_from_string) (var symbol String))))

(rule (lhs relation_id (Message logic RelationId)) (rhs (term INT Int64)) (lambda ((INT Int64)) (Message logic RelationId) (call (builtin relation_id_from_int) (var INT Int64))))

(rule (lhs abstraction (Message logic Abstraction)) (rhs "(" (nonterm bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) (nonterm formula (Message logic Formula)) ")") (lambda ((bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) (formula (Message logic Formula))) (Message logic Abstraction) (call (message logic Abstraction) (call (builtin list_concat) (get-element (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) 0) (get-element (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) 1)) (var formula (Message logic Formula)))))

(rule (lhs bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) (rhs "[" (star (nonterm binding (Message logic Binding))) (option (nonterm value_bindings (List (Message logic Binding)))) "]") (lambda ((keys (List (Message logic Binding))) (values (Option (List (Message logic Binding))))) (Tuple (List (Message logic Binding)) (List (Message logic Binding))) (call (builtin make_tuple) (var keys (List (Message logic Binding))) (call (builtin unwrap_option_or) (var values (Option (List (Message logic Binding)))) (list (Message logic Binding))))))

(rule (lhs binding (Message logic Binding)) (rhs (term SYMBOL String) "::" (nonterm type (Message logic Type))) (lambda ((symbol String) (type (Message logic Type))) (Message logic Binding) (call (message logic Binding) (call (message logic Var) (var symbol String)) (var type (Message logic Type)))))

(rule (lhs type (Message logic Type)) (rhs (nonterm unspecified_type (Message logic UnspecifiedType))) (lambda ((value (Message logic UnspecifiedType))) (Message logic Type) (call (message logic Type) (call (oneof unspecified_type) (var value (Message logic UnspecifiedType))))))

(rule (lhs type (Message logic Type)) (rhs (nonterm string_type (Message logic StringType))) (lambda ((value (Message logic StringType))) (Message logic Type) (call (message logic Type) (call (oneof string_type) (var value (Message logic StringType))))))

(rule (lhs type (Message logic Type)) (rhs (nonterm int_type (Message logic IntType))) (lambda ((value (Message logic IntType))) (Message logic Type) (call (message logic Type) (call (oneof int_type) (var value (Message logic IntType))))))

(rule (lhs type (Message logic Type)) (rhs (nonterm float_type (Message logic FloatType))) (lambda ((value (Message logic FloatType))) (Message logic Type) (call (message logic Type) (call (oneof float_type) (var value (Message logic FloatType))))))

(rule (lhs type (Message logic Type)) (rhs (nonterm uint128_type (Message logic UInt128Type))) (lambda ((value (Message logic UInt128Type))) (Message logic Type) (call (message logic Type) (call (oneof uint128_type) (var value (Message logic UInt128Type))))))

(rule (lhs type (Message logic Type)) (rhs (nonterm int128_type (Message logic Int128Type))) (lambda ((value (Message logic Int128Type))) (Message logic Type) (call (message logic Type) (call (oneof int128_type) (var value (Message logic Int128Type))))))

(rule (lhs type (Message logic Type)) (rhs (nonterm date_type (Message logic DateType))) (lambda ((value (Message logic DateType))) (Message logic Type) (call (message logic Type) (call (oneof date_type) (var value (Message logic DateType))))))

(rule (lhs type (Message logic Type)) (rhs (nonterm datetime_type (Message logic DateTimeType))) (lambda ((value (Message logic DateTimeType))) (Message logic Type) (call (message logic Type) (call (oneof datetime_type) (var value (Message logic DateTimeType))))))

(rule (lhs type (Message logic Type)) (rhs (nonterm missing_type (Message logic MissingType))) (lambda ((value (Message logic MissingType))) (Message logic Type) (call (message logic Type) (call (oneof missing_type) (var value (Message logic MissingType))))))

(rule (lhs type (Message logic Type)) (rhs (nonterm decimal_type (Message logic DecimalType))) (lambda ((value (Message logic DecimalType))) (Message logic Type) (call (message logic Type) (call (oneof decimal_type) (var value (Message logic DecimalType))))))

(rule (lhs type (Message logic Type)) (rhs (nonterm boolean_type (Message logic BooleanType))) (lambda ((value (Message logic BooleanType))) (Message logic Type) (call (message logic Type) (call (oneof boolean_type) (var value (Message logic BooleanType))))))

(rule (lhs unspecified_type (Message logic UnspecifiedType)) (rhs "UNKNOWN") (lambda () (Message logic UnspecifiedType) (call (message logic UnspecifiedType))))

(rule (lhs string_type (Message logic StringType)) (rhs "STRING") (lambda () (Message logic StringType) (call (message logic StringType))))

(rule (lhs int_type (Message logic IntType)) (rhs "INT") (lambda () (Message logic IntType) (call (message logic IntType))))

(rule (lhs float_type (Message logic FloatType)) (rhs "FLOAT") (lambda () (Message logic FloatType) (call (message logic FloatType))))

(rule (lhs uint128_type (Message logic UInt128Type)) (rhs "UINT128") (lambda () (Message logic UInt128Type) (call (message logic UInt128Type))))

(rule (lhs int128_type (Message logic Int128Type)) (rhs "INT128") (lambda () (Message logic Int128Type) (call (message logic Int128Type))))

(rule (lhs date_type (Message logic DateType)) (rhs "DATE") (lambda () (Message logic DateType) (call (message logic DateType))))

(rule (lhs datetime_type (Message logic DateTimeType)) (rhs "DATETIME") (lambda () (Message logic DateTimeType) (call (message logic DateTimeType))))

(rule (lhs missing_type (Message logic MissingType)) (rhs "MISSING") (lambda () (Message logic MissingType) (call (message logic MissingType))))

(rule (lhs decimal_type (Message logic DecimalType)) (rhs "(" "DECIMAL" (term INT Int64) (term INT Int64) ")") (lambda ((precision Int64) (scale Int64)) (Message logic DecimalType) (call (message logic DecimalType) (call (builtin int64_to_int32) (var precision Int64)) (call (builtin int64_to_int32) (var scale Int64)))))

(rule (lhs boolean_type (Message logic BooleanType)) (rhs "BOOLEAN") (lambda () (Message logic BooleanType) (call (message logic BooleanType))))

(rule (lhs value_bindings (List (Message logic Binding))) (rhs "|" (star (nonterm binding (Message logic Binding)))) (lambda ((x (List (Message logic Binding)))) (List (Message logic Binding)) (var x (List (Message logic Binding)))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm true (Message logic Conjunction))) (lambda ((value (Message logic Conjunction))) (Message logic Formula) (call (message logic Formula) (call (oneof conjunction) (var value (Message logic Conjunction))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm false (Message logic Disjunction))) (lambda ((value (Message logic Disjunction))) (Message logic Formula) (call (message logic Formula) (call (oneof disjunction) (var value (Message logic Disjunction))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm exists (Message logic Exists))) (lambda ((value (Message logic Exists))) (Message logic Formula) (call (message logic Formula) (call (oneof exists) (var value (Message logic Exists))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm reduce (Message logic Reduce))) (lambda ((value (Message logic Reduce))) (Message logic Formula) (call (message logic Formula) (call (oneof reduce) (var value (Message logic Reduce))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm conjunction (Message logic Conjunction))) (lambda ((value (Message logic Conjunction))) (Message logic Formula) (call (message logic Formula) (call (oneof conjunction) (var value (Message logic Conjunction))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm disjunction (Message logic Disjunction))) (lambda ((value (Message logic Disjunction))) (Message logic Formula) (call (message logic Formula) (call (oneof disjunction) (var value (Message logic Disjunction))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm not (Message logic Not))) (lambda ((value (Message logic Not))) (Message logic Formula) (call (message logic Formula) (call (oneof not) (var value (Message logic Not))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm ffi (Message logic FFI))) (lambda ((value (Message logic FFI))) (Message logic Formula) (call (message logic Formula) (call (oneof ffi) (var value (Message logic FFI))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm atom (Message logic Atom))) (lambda ((value (Message logic Atom))) (Message logic Formula) (call (message logic Formula) (call (oneof atom) (var value (Message logic Atom))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm pragma (Message logic Pragma))) (lambda ((value (Message logic Pragma))) (Message logic Formula) (call (message logic Formula) (call (oneof pragma) (var value (Message logic Pragma))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm primitive (Message logic Primitive))) (lambda ((value (Message logic Primitive))) (Message logic Formula) (call (message logic Formula) (call (oneof primitive) (var value (Message logic Primitive))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm rel_atom (Message logic RelAtom))) (lambda ((value (Message logic RelAtom))) (Message logic Formula) (call (message logic Formula) (call (oneof rel_atom) (var value (Message logic RelAtom))))))

(rule (lhs formula (Message logic Formula)) (rhs (nonterm cast (Message logic Cast))) (lambda ((value (Message logic Cast))) (Message logic Formula) (call (message logic Formula) (call (oneof cast) (var value (Message logic Cast))))))

(rule (lhs true (Message logic Conjunction)) (rhs "(" "true" ")") (lambda () (Message logic Conjunction) (call (message logic Conjunction) (list (Message logic Formula)))))

(rule (lhs false (Message logic Disjunction)) (rhs "(" "false" ")") (lambda () (Message logic Disjunction) (call (message logic Disjunction) (list (Message logic Formula)))))

(rule (lhs exists (Message logic Exists)) (rhs "(" "exists" (nonterm bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) (nonterm formula (Message logic Formula)) ")") (lambda ((bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) (formula (Message logic Formula))) (Message logic Exists) (call (message logic Exists) (call (message logic Abstraction) (call (builtin list_concat) (get-element (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) 0) (get-element (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) 1)) (var formula (Message logic Formula))))))

(rule (lhs reduce (Message logic Reduce)) (rhs "(" "reduce" (nonterm abstraction (Message logic Abstraction)) (nonterm abstraction (Message logic Abstraction)) (nonterm terms (List (Message logic Term))) ")") (lambda ((op (Message logic Abstraction)) (body (Message logic Abstraction)) (terms (List (Message logic Term)))) (Message logic Reduce) (call (message logic Reduce) (var op (Message logic Abstraction)) (var body (Message logic Abstraction)) (var terms (List (Message logic Term))))))

(rule (lhs term (Message logic Term)) (rhs (nonterm var (Message logic Var))) (lambda ((value (Message logic Var))) (Message logic Term) (call (message logic Term) (call (oneof var) (var value (Message logic Var))))))

(rule (lhs term (Message logic Term)) (rhs (nonterm constant (Message logic Value))) (lambda ((value (Message logic Value))) (Message logic Term) (call (message logic Term) (call (oneof constant) (var value (Message logic Value))))))

(rule (lhs var (Message logic Var)) (rhs (term SYMBOL String)) (lambda ((symbol String)) (Message logic Var) (call (message logic Var) (var symbol String))))

(rule (lhs constant (Message logic Value)) (rhs (nonterm value (Message logic Value))) (lambda ((x (Message logic Value))) (Message logic Value) (var x (Message logic Value))))

(rule (lhs conjunction (Message logic Conjunction)) (rhs "(" "and" (star (nonterm formula (Message logic Formula))) ")") (lambda ((args (List (Message logic Formula)))) (Message logic Conjunction) (call (message logic Conjunction) (var args (List (Message logic Formula))))))

(rule (lhs disjunction (Message logic Disjunction)) (rhs "(" "or" (star (nonterm formula (Message logic Formula))) ")") (lambda ((args (List (Message logic Formula)))) (Message logic Disjunction) (call (message logic Disjunction) (var args (List (Message logic Formula))))))

(rule (lhs not (Message logic Not)) (rhs "(" "not" (nonterm formula (Message logic Formula)) ")") (lambda ((arg (Message logic Formula))) (Message logic Not) (call (message logic Not) (var arg (Message logic Formula)))))

(rule (lhs ffi (Message logic FFI)) (rhs "(" "ffi" (nonterm name String) (nonterm ffi_args (List (Message logic Abstraction))) (nonterm terms (List (Message logic Term))) ")") (lambda ((name String) (args (List (Message logic Abstraction))) (terms (List (Message logic Term)))) (Message logic FFI) (call (message logic FFI) (var name String) (var args (List (Message logic Abstraction))) (var terms (List (Message logic Term))))))

(rule (lhs ffi_args (List (Message logic Abstraction))) (rhs "(" "args" (star (nonterm abstraction (Message logic Abstraction))) ")") (lambda ((x (List (Message logic Abstraction)))) (List (Message logic Abstraction)) (var x (List (Message logic Abstraction)))))

(rule (lhs terms (List (Message logic Term))) (rhs "(" "terms" (star (nonterm term (Message logic Term))) ")") (lambda ((x (List (Message logic Term)))) (List (Message logic Term)) (var x (List (Message logic Term)))))

(rule (lhs name String) (rhs (term COLON_SYMBOL String)) (lambda ((x String)) String (var x String)))

(rule (lhs atom (Message logic Atom)) (rhs "(" "atom" (nonterm relation_id (Message logic RelationId)) (star (nonterm term (Message logic Term))) ")") (lambda ((name (Message logic RelationId)) (terms (List (Message logic Term)))) (Message logic Atom) (call (message logic Atom) (var name (Message logic RelationId)) (var terms (List (Message logic Term))))))

(rule (lhs pragma (Message logic Pragma)) (rhs "(" "pragma" (nonterm name String) (star (nonterm term (Message logic Term))) ")") (lambda ((name String) (terms (List (Message logic Term)))) (Message logic Pragma) (call (message logic Pragma) (var name String) (var terms (List (Message logic Term))))))

(rule (lhs primitive (Message logic Primitive)) (rhs (nonterm eq (Message logic Primitive))) (lambda ((op (Message logic Primitive))) (Message logic Primitive) (var op (Message logic Primitive))))

(rule (lhs primitive (Message logic Primitive)) (rhs (nonterm lt (Message logic Primitive))) (lambda ((op (Message logic Primitive))) (Message logic Primitive) (var op (Message logic Primitive))))

(rule (lhs primitive (Message logic Primitive)) (rhs (nonterm lt_eq (Message logic Primitive))) (lambda ((op (Message logic Primitive))) (Message logic Primitive) (var op (Message logic Primitive))))

(rule (lhs primitive (Message logic Primitive)) (rhs (nonterm gt (Message logic Primitive))) (lambda ((op (Message logic Primitive))) (Message logic Primitive) (var op (Message logic Primitive))))

(rule (lhs primitive (Message logic Primitive)) (rhs (nonterm gt_eq (Message logic Primitive))) (lambda ((op (Message logic Primitive))) (Message logic Primitive) (var op (Message logic Primitive))))

(rule (lhs primitive (Message logic Primitive)) (rhs (nonterm add (Message logic Primitive))) (lambda ((op (Message logic Primitive))) (Message logic Primitive) (var op (Message logic Primitive))))

(rule (lhs primitive (Message logic Primitive)) (rhs (nonterm minus (Message logic Primitive))) (lambda ((op (Message logic Primitive))) (Message logic Primitive) (var op (Message logic Primitive))))

(rule (lhs primitive (Message logic Primitive)) (rhs (nonterm multiply (Message logic Primitive))) (lambda ((op (Message logic Primitive))) (Message logic Primitive) (var op (Message logic Primitive))))

(rule (lhs primitive (Message logic Primitive)) (rhs (nonterm divide (Message logic Primitive))) (lambda ((op (Message logic Primitive))) (Message logic Primitive) (var op (Message logic Primitive))))

(rule (lhs primitive (Message logic Primitive)) (rhs "(" "primitive" (nonterm name String) (star (nonterm rel_term (Message logic RelTerm))) ")") (lambda ((name String) (terms (List (Message logic RelTerm)))) (Message logic Primitive) (call (message logic Primitive) (var name String) (var terms (List (Message logic RelTerm))))))

(rule (lhs primitive (Message logic Primitive)) (rhs "(" "primitive" (nonterm name String) (star (nonterm rel_term (Message logic RelTerm))) ")") (lambda ((name String) (terms (List (Message logic RelTerm)))) (Message logic Primitive) (call (message logic Primitive) (var name String) (var terms (List (Message logic RelTerm))))))

(rule (lhs eq (Message logic Primitive)) (rhs "(" "=" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")") (lambda ((left (Message logic Term)) (right (Message logic Term))) (Message logic Primitive) (call (message logic Primitive) (lit "rel_primitive_eq") (list (Message logic RelTerm) (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))))))

(rule (lhs lt (Message logic Primitive)) (rhs "(" "<" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")") (lambda ((left (Message logic Term)) (right (Message logic Term))) (Message logic Primitive) (call (message logic Primitive) (lit "rel_primitive_lt_monotype") (list (Message logic RelTerm) (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))))))

(rule (lhs lt_eq (Message logic Primitive)) (rhs "(" "<=" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")") (lambda ((left (Message logic Term)) (right (Message logic Term))) (Message logic Primitive) (call (message logic Primitive) (lit "rel_primitive_lt_eq_monotype") (list (Message logic RelTerm) (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))))))

(rule (lhs gt (Message logic Primitive)) (rhs "(" ">" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")") (lambda ((left (Message logic Term)) (right (Message logic Term))) (Message logic Primitive) (call (message logic Primitive) (lit "rel_primitive_gt_monotype") (list (Message logic RelTerm) (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))))))

(rule (lhs gt_eq (Message logic Primitive)) (rhs "(" ">=" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")") (lambda ((left (Message logic Term)) (right (Message logic Term))) (Message logic Primitive) (call (message logic Primitive) (lit "rel_primitive_gt_eq_monotype") (list (Message logic RelTerm) (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term))))))))

(rule (lhs add (Message logic Primitive)) (rhs "(" "+" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")") (lambda ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term))) (Message logic Primitive) (call (message logic Primitive) (lit "rel_primitive_add_monotype") (list (Message logic RelTerm) (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term))))))))

(rule (lhs minus (Message logic Primitive)) (rhs "(" "-" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")") (lambda ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term))) (Message logic Primitive) (call (message logic Primitive) (lit "rel_primitive_subtract_monotype") (list (Message logic RelTerm) (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term))))))))

(rule (lhs multiply (Message logic Primitive)) (rhs "(" "*" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")") (lambda ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term))) (Message logic Primitive) (call (message logic Primitive) (lit "rel_primitive_multiply_monotype") (list (Message logic RelTerm) (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term))))))))

(rule (lhs divide (Message logic Primitive)) (rhs "(" "/" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")") (lambda ((left (Message logic Term)) (right (Message logic Term)) (result (Message logic Term))) (Message logic Primitive) (call (message logic Primitive) (lit "rel_primitive_divide_monotype") (list (Message logic RelTerm) (call (message logic RelTerm) (call (oneof term) (var left (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var right (Message logic Term)))) (call (message logic RelTerm) (call (oneof term) (var result (Message logic Term))))))))

(rule (lhs rel_term (Message logic RelTerm)) (rhs (nonterm specialized_value (Message logic Value))) (lambda ((value (Message logic Value))) (Message logic RelTerm) (call (message logic RelTerm) (call (oneof specialized_value) (var value (Message logic Value))))))

(rule (lhs rel_term (Message logic RelTerm)) (rhs (nonterm term (Message logic Term))) (lambda ((value (Message logic Term))) (Message logic RelTerm) (call (message logic RelTerm) (call (oneof term) (var value (Message logic Term))))))

(rule (lhs specialized_value (Message logic Value)) (rhs "#" (nonterm value (Message logic Value))) (lambda ((value (Message logic Value))) (Message logic Value) (var value (Message logic Value))))

(rule (lhs rel_atom (Message logic RelAtom)) (rhs "(" "rel_atom" (nonterm name String) (star (nonterm rel_term (Message logic RelTerm))) ")") (lambda ((name String) (terms (List (Message logic RelTerm)))) (Message logic RelAtom) (call (message logic RelAtom) (var name String) (var terms (List (Message logic RelTerm))))))

(rule (lhs cast (Message logic Cast)) (rhs "(" "cast" (nonterm term (Message logic Term)) (nonterm term (Message logic Term)) ")") (lambda ((input (Message logic Term)) (result (Message logic Term))) (Message logic Cast) (call (message logic Cast) (var input (Message logic Term)) (var result (Message logic Term)))))

(rule (lhs attrs (List (Message logic Attribute))) (rhs "(" "attrs" (star (nonterm attribute (Message logic Attribute))) ")") (lambda ((x (List (Message logic Attribute)))) (List (Message logic Attribute)) (var x (List (Message logic Attribute)))))

(rule (lhs attribute (Message logic Attribute)) (rhs "(" "attribute" (nonterm name String) (star (nonterm value (Message logic Value))) ")") (lambda ((name String) (args (List (Message logic Value)))) (Message logic Attribute) (call (message logic Attribute) (var name String) (var args (List (Message logic Value))))))

(rule (lhs algorithm (Message logic Algorithm)) (rhs "(" "algorithm" (star (nonterm relation_id (Message logic RelationId))) (nonterm script (Message logic Script)) ")") (lambda ((global (List (Message logic RelationId))) (body (Message logic Script))) (Message logic Algorithm) (call (message logic Algorithm) (var global (List (Message logic RelationId))) (var body (Message logic Script)))))

(rule (lhs script (Message logic Script)) (rhs "(" "script" (star (nonterm construct (Message logic Construct))) ")") (lambda ((constructs (List (Message logic Construct)))) (Message logic Script) (call (message logic Script) (var constructs (List (Message logic Construct))))))

(rule (lhs construct (Message logic Construct)) (rhs (nonterm loop (Message logic Loop))) (lambda ((value (Message logic Loop))) (Message logic Construct) (call (message logic Construct) (call (oneof loop) (var value (Message logic Loop))))))

(rule (lhs construct (Message logic Construct)) (rhs (nonterm instruction (Message logic Instruction))) (lambda ((value (Message logic Instruction))) (Message logic Construct) (call (message logic Construct) (call (oneof instruction) (var value (Message logic Instruction))))))

(rule (lhs loop (Message logic Loop)) (rhs "(" "loop" (nonterm init (List (Message logic Instruction))) (nonterm script (Message logic Script)) ")") (lambda ((init (List (Message logic Instruction))) (body (Message logic Script))) (Message logic Loop) (call (message logic Loop) (var init (List (Message logic Instruction))) (var body (Message logic Script)))))

(rule (lhs init (List (Message logic Instruction))) (rhs "(" "init" (star (nonterm instruction (Message logic Instruction))) ")") (lambda ((x (List (Message logic Instruction)))) (List (Message logic Instruction)) (var x (List (Message logic Instruction)))))

(rule (lhs instruction (Message logic Instruction)) (rhs (nonterm assign (Message logic Assign))) (lambda ((value (Message logic Assign))) (Message logic Instruction) (call (message logic Instruction) (call (oneof assign) (var value (Message logic Assign))))))

(rule (lhs instruction (Message logic Instruction)) (rhs (nonterm upsert (Message logic Upsert))) (lambda ((value (Message logic Upsert))) (Message logic Instruction) (call (message logic Instruction) (call (oneof upsert) (var value (Message logic Upsert))))))

(rule (lhs instruction (Message logic Instruction)) (rhs (nonterm break (Message logic Break))) (lambda ((value (Message logic Break))) (Message logic Instruction) (call (message logic Instruction) (call (oneof break) (var value (Message logic Break))))))

(rule (lhs instruction (Message logic Instruction)) (rhs (nonterm monoid_def (Message logic MonoidDef))) (lambda ((value (Message logic MonoidDef))) (Message logic Instruction) (call (message logic Instruction) (call (oneof monoid_def) (var value (Message logic MonoidDef))))))

(rule (lhs instruction (Message logic Instruction)) (rhs (nonterm monus_def (Message logic MonusDef))) (lambda ((value (Message logic MonusDef))) (Message logic Instruction) (call (message logic Instruction) (call (oneof monus_def) (var value (Message logic MonusDef))))))

(rule (lhs assign (Message logic Assign)) (rhs "(" "assign" (nonterm relation_id (Message logic RelationId)) (nonterm abstraction (Message logic Abstraction)) (option (nonterm attrs (List (Message logic Attribute)))) ")") (lambda ((name (Message logic RelationId)) (body (Message logic Abstraction)) (attrs (Option (List (Message logic Attribute))))) (Message logic Assign) (call (message logic Assign) (var name (Message logic RelationId)) (var body (Message logic Abstraction)) (call (builtin unwrap_option_or) (var attrs (Option (List (Message logic Attribute)))) (list (Message logic Attribute))))))

(rule (lhs upsert (Message logic Upsert)) (rhs "(" "upsert" (nonterm relation_id (Message logic RelationId)) (nonterm abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) (option (nonterm attrs (List (Message logic Attribute)))) ")") (lambda ((name (Message logic RelationId)) (abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) (attrs (Option (List (Message logic Attribute))))) (Message logic Upsert) (let (abstraction (Message logic Abstraction)) (get-element (var abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) 0) (let (arity Int64) (get-element (var abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) 1) (call (message logic Upsert) (var name (Message logic RelationId)) (var abstraction (Message logic Abstraction)) (call (builtin unwrap_option_or) (var attrs (Option (List (Message logic Attribute)))) (list (Message logic Attribute))) (var arity Int64))))))

(rule (lhs abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) (rhs "(" (nonterm bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) (nonterm formula (Message logic Formula)) ")") (lambda ((bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) (formula (Message logic Formula))) (Tuple (Message logic Abstraction) Int64) (call (builtin make_tuple) (call (message logic Abstraction) (call (builtin list_concat) (get-element (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) 0) (get-element (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) 1)) (var formula (Message logic Formula))) (call (builtin length) (get-element (var bindings (Tuple (List (Message logic Binding)) (List (Message logic Binding)))) 1)))))

(rule (lhs break (Message logic Break)) (rhs "(" "break" (nonterm relation_id (Message logic RelationId)) (nonterm abstraction (Message logic Abstraction)) (option (nonterm attrs (List (Message logic Attribute)))) ")") (lambda ((name (Message logic RelationId)) (body (Message logic Abstraction)) (attrs (Option (List (Message logic Attribute))))) (Message logic Break) (call (message logic Break) (var name (Message logic RelationId)) (var body (Message logic Abstraction)) (call (builtin unwrap_option_or) (var attrs (Option (List (Message logic Attribute)))) (list (Message logic Attribute))))))

(rule (lhs monoid_def (Message logic MonoidDef)) (rhs "(" "monoid" (nonterm monoid (Message logic Monoid)) (nonterm relation_id (Message logic RelationId)) (nonterm abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) (option (nonterm attrs (List (Message logic Attribute)))) ")") (lambda ((monoid (Message logic Monoid)) (name (Message logic RelationId)) (abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) (attrs (Option (List (Message logic Attribute))))) (Message logic MonoidDef) (let (abstraction (Message logic Abstraction)) (get-element (var abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) 0) (let (arity Int64) (get-element (var abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) 1) (call (message logic MonoidDef) (var monoid (Message logic Monoid)) (var name (Message logic RelationId)) (var abstraction (Message logic Abstraction)) (call (builtin unwrap_option_or) (var attrs (Option (List (Message logic Attribute)))) (list (Message logic Attribute))) (var arity Int64))))))

(rule (lhs monoid (Message logic Monoid)) (rhs (nonterm or_monoid (Message logic OrMonoid))) (lambda ((value (Message logic OrMonoid))) (Message logic Monoid) (call (message logic Monoid) (call (oneof or_monoid) (var value (Message logic OrMonoid))))))

(rule (lhs monoid (Message logic Monoid)) (rhs (nonterm min_monoid (Message logic MinMonoid))) (lambda ((value (Message logic MinMonoid))) (Message logic Monoid) (call (message logic Monoid) (call (oneof min_monoid) (var value (Message logic MinMonoid))))))

(rule (lhs monoid (Message logic Monoid)) (rhs (nonterm max_monoid (Message logic MaxMonoid))) (lambda ((value (Message logic MaxMonoid))) (Message logic Monoid) (call (message logic Monoid) (call (oneof max_monoid) (var value (Message logic MaxMonoid))))))

(rule (lhs monoid (Message logic Monoid)) (rhs (nonterm sum_monoid (Message logic SumMonoid))) (lambda ((value (Message logic SumMonoid))) (Message logic Monoid) (call (message logic Monoid) (call (oneof sum_monoid) (var value (Message logic SumMonoid))))))

(rule (lhs or_monoid (Message logic OrMonoid)) (rhs "(" "or" ")") (lambda () (Message logic OrMonoid) (call (message logic OrMonoid))))

(rule (lhs min_monoid (Message logic MinMonoid)) (rhs "(" "min" (nonterm type (Message logic Type)) ")") (lambda ((type (Message logic Type))) (Message logic MinMonoid) (call (message logic MinMonoid) (var type (Message logic Type)))))

(rule (lhs max_monoid (Message logic MaxMonoid)) (rhs "(" "max" (nonterm type (Message logic Type)) ")") (lambda ((type (Message logic Type))) (Message logic MaxMonoid) (call (message logic MaxMonoid) (var type (Message logic Type)))))

(rule (lhs sum_monoid (Message logic SumMonoid)) (rhs "(" "sum" (nonterm type (Message logic Type)) ")") (lambda ((type (Message logic Type))) (Message logic SumMonoid) (call (message logic SumMonoid) (var type (Message logic Type)))))

(rule (lhs monus_def (Message logic MonusDef)) (rhs "(" "monus" (nonterm monoid (Message logic Monoid)) (nonterm relation_id (Message logic RelationId)) (nonterm abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) (option (nonterm attrs (List (Message logic Attribute)))) ")") (lambda ((monoid (Message logic Monoid)) (name (Message logic RelationId)) (abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) (attrs (Option (List (Message logic Attribute))))) (Message logic MonusDef) (let (abstraction (Message logic Abstraction)) (get-element (var abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) 0) (let (arity Int64) (get-element (var abstraction_with_arity (Tuple (Message logic Abstraction) Int64)) 1) (call (message logic MonusDef) (var monoid (Message logic Monoid)) (var name (Message logic RelationId)) (var abstraction (Message logic Abstraction)) (call (builtin unwrap_option_or) (var attrs (Option (List (Message logic Attribute)))) (list (Message logic Attribute))) (var arity Int64))))))

(rule (lhs constraint (Message logic Constraint)) (rhs (nonterm functional_dependency (Message logic FunctionalDependency))) (lambda ((value (Message logic FunctionalDependency))) (Message logic Constraint) (call (message logic Constraint) (call (oneof functional_dependency) (var value (Message logic FunctionalDependency))))))

(rule (lhs functional_dependency (Message logic FunctionalDependency)) (rhs "(" "functional_dependency" (nonterm abstraction (Message logic Abstraction)) (option (nonterm functional_dependency_keys (List (Message logic Var)))) (option (nonterm functional_dependency_values (List (Message logic Var)))) ")") (lambda ((guard (Message logic Abstraction)) (keys (Option (List (Message logic Var)))) (values (Option (List (Message logic Var))))) (Message logic FunctionalDependency) (call (message logic FunctionalDependency) (var guard (Message logic Abstraction)) (call (builtin unwrap_option_or) (var keys (Option (List (Message logic Var)))) (list (Message logic Var))) (call (builtin unwrap_option_or) (var values (Option (List (Message logic Var)))) (list (Message logic Var))))))

(rule (lhs functional_dependency_keys (List (Message logic Var))) (rhs "(" "keys" (star (nonterm var (Message logic Var))) ")") (lambda ((x (List (Message logic Var)))) (List (Message logic Var)) (var x (List (Message logic Var)))))

(rule (lhs functional_dependency_values (List (Message logic Var))) (rhs "(" "values" (star (nonterm var (Message logic Var))) ")") (lambda ((x (List (Message logic Var)))) (List (Message logic Var)) (var x (List (Message logic Var)))))

(rule (lhs data (Message logic Data)) (rhs (nonterm rel_edb (Message logic RelEDB))) (lambda ((value (Message logic RelEDB))) (Message logic Data) (call (message logic Data) (call (oneof rel_edb) (var value (Message logic RelEDB))))))

(rule (lhs data (Message logic Data)) (rhs (nonterm betree_relation (Message logic BeTreeRelation))) (lambda ((value (Message logic BeTreeRelation))) (Message logic Data) (call (message logic Data) (call (oneof betree_relation) (var value (Message logic BeTreeRelation))))))

(rule (lhs data (Message logic Data)) (rhs (nonterm csv_data (Message logic CSVData))) (lambda ((value (Message logic CSVData))) (Message logic Data) (call (message logic Data) (call (oneof csv_data) (var value (Message logic CSVData))))))

(rule (lhs rel_edb (Message logic RelEDB)) (rhs "(" "rel_edb" (nonterm relation_id (Message logic RelationId)) (star (nonterm name String)) (option (nonterm rel_edb_types (List (Message logic Type)))) ")") (lambda ((target_id (Message logic RelationId)) (path (List String)) (types (Option (List (Message logic Type))))) (Message logic RelEDB) (call (message logic RelEDB) (var target_id (Message logic RelationId)) (var path (List String)) (call (builtin unwrap_option_or) (var types (Option (List (Message logic Type)))) (list (Message logic Type))))))

(rule (lhs rel_edb_types (List (Message logic Type))) (rhs "(" "types" (star (nonterm type (Message logic Type))) ")") (lambda ((x (List (Message logic Type)))) (List (Message logic Type)) (var x (List (Message logic Type)))))

(rule (lhs betree_relation (Message logic BeTreeRelation)) (rhs (nonterm be_tree_relation (Message logic BeTreeRelation))) (lambda ((x (Message logic BeTreeRelation))) (Message logic BeTreeRelation) (var x (Message logic BeTreeRelation))))

(rule (lhs be_tree_relation (Message logic BeTreeRelation)) (rhs "(" "be_tree_relation" (nonterm relation_id (Message logic RelationId)) (nonterm be_tree_info (Message logic BeTreeInfo)) ")") (lambda ((name (Message logic RelationId)) (relation_info (Message logic BeTreeInfo))) (Message logic BeTreeRelation) (call (message logic BeTreeRelation) (var name (Message logic RelationId)) (var relation_info (Message logic BeTreeInfo)))))

(rule (lhs be_tree_info (Message logic BeTreeInfo)) (rhs "(" "be_tree_info" (option (nonterm be_tree_info_key_types (List (Message logic Type)))) (option (nonterm be_tree_info_value_types (List (Message logic Type)))) (nonterm be_tree_config (Message logic BeTreeConfig)) (nonterm be_tree_locator (Message logic BeTreeLocator)) ")") (lambda ((key_types (Option (List (Message logic Type)))) (value_types (Option (List (Message logic Type)))) (storage_config (Message logic BeTreeConfig)) (relation_locator (Message logic BeTreeLocator))) (Message logic BeTreeInfo) (call (message logic BeTreeInfo) (call (builtin unwrap_option_or) (var key_types (Option (List (Message logic Type)))) (list (Message logic Type))) (call (builtin unwrap_option_or) (var value_types (Option (List (Message logic Type)))) (list (Message logic Type))) (var storage_config (Message logic BeTreeConfig)) (var relation_locator (Message logic BeTreeLocator)))))

(rule (lhs be_tree_info_key_types (List (Message logic Type))) (rhs "(" "key_types" (star (nonterm type (Message logic Type))) ")") (lambda ((x (List (Message logic Type)))) (List (Message logic Type)) (var x (List (Message logic Type)))))

(rule (lhs be_tree_info_value_types (List (Message logic Type))) (rhs "(" "value_types" (star (nonterm type (Message logic Type))) ")") (lambda ((x (List (Message logic Type)))) (List (Message logic Type)) (var x (List (Message logic Type)))))

(rule (lhs be_tree_config (Message logic BeTreeConfig)) (rhs "(" "be_tree_config" (term FLOAT Float64) (term INT Int64) (term INT Int64) (term INT Int64) ")") (lambda ((epsilon Float64) (max_pivots Int64) (max_deltas Int64) (max_leaf Int64)) (Message logic BeTreeConfig) (call (message logic BeTreeConfig) (var epsilon Float64) (var max_pivots Int64) (var max_deltas Int64) (var max_leaf Int64))))

(rule (lhs be_tree_locator (Message logic BeTreeLocator)) (rhs "(" "be_tree_locator" (term INT Int64) (term INT Int64) ")") (lambda ((element_count Int64) (tree_height Int64)) (Message logic BeTreeLocator) (call (message logic BeTreeLocator) (var element_count Int64) (var tree_height Int64))))

(rule (lhs csv_data (Message logic CSVData)) (rhs (nonterm csvdata (Message logic CSVData))) (lambda ((x (Message logic CSVData))) (Message logic CSVData) (var x (Message logic CSVData))))

(rule (lhs csvdata (Message logic CSVData)) (rhs "(" "csvdata" (nonterm csvlocator (Message logic CSVLocator)) (nonterm csv_config (Message logic CSVConfig)) (star (nonterm csv_column (Message logic CSVColumn))) (nonterm name String) ")") (lambda ((locator (Message logic CSVLocator)) (config (Message logic CSVConfig)) (columns (List (Message logic CSVColumn))) (asof String)) (Message logic CSVData) (call (message logic CSVData) (var locator (Message logic CSVLocator)) (var config (Message logic CSVConfig)) (var columns (List (Message logic CSVColumn))) (var asof String))))

(rule (lhs csvlocator (Message logic CSVLocator)) (rhs "(" "csvlocator" (star (nonterm name String)) (nonterm name String) ")") (lambda ((paths (List String)) (inline_data String)) (Message logic CSVLocator) (call (message logic CSVLocator) (var paths (List String)) (var inline_data String))))

(rule (lhs csv_config (Message logic CSVConfig)) (rhs "(" "csv_config" (term INT Int32) (term INT Int64) (nonterm name String) (nonterm name String) (nonterm name String) (nonterm name String) (nonterm name String) (star (nonterm name String)) (nonterm name String) (nonterm name String) (nonterm name String) ")") (lambda ((header_row Int32) (skip Int64) (new_line String) (delimiter String) (quotechar String) (escapechar String) (comment String) (missing_strings (List String)) (decimal_separator String) (encoding String) (compression String)) (Message logic CSVConfig) (call (message logic CSVConfig) (var header_row Int32) (var skip Int64) (var new_line String) (var delimiter String) (var quotechar String) (var escapechar String) (var comment String) (var missing_strings (List String)) (var decimal_separator String) (var encoding String) (var compression String))))

(rule (lhs csv_column (Message logic CSVColumn)) (rhs "(" "csv_column" (nonterm name String) (nonterm relation_id (Message logic RelationId)) (star (nonterm type (Message logic Type))) ")") (lambda ((column_name String) (target_id (Message logic RelationId)) (types (List (Message logic Type)))) (Message logic CSVColumn) (call (message logic CSVColumn) (var column_name String) (var target_id (Message logic RelationId)) (var types (List (Message logic Type))))))

(rule (lhs undefine (Message transactions Undefine)) (rhs "(" "undefine" (nonterm fragment_id (Message fragments FragmentId)) ")") (lambda ((fragment_id (Message fragments FragmentId))) (Message transactions Undefine) (call (message transactions Undefine) (var fragment_id (Message fragments FragmentId)))))

(rule (lhs context (Message transactions Context)) (rhs "(" "context" (star (nonterm relation_id (Message logic RelationId))) ")") (lambda ((relations (List (Message logic RelationId)))) (Message transactions Context) (call (message transactions Context) (var relations (List (Message logic RelationId))))))

(rule (lhs epoch_reads (List (Message transactions Read))) (rhs "(" "reads" (star (nonterm read (Message transactions Read))) ")") (lambda ((x (List (Message transactions Read)))) (List (Message transactions Read)) (var x (List (Message transactions Read)))))

(rule (lhs read (Message transactions Read)) (rhs (nonterm demand (Message transactions Demand))) (lambda ((value (Message transactions Demand))) (Message transactions Read) (call (message transactions Read) (call (oneof demand) (var value (Message transactions Demand))))))

(rule (lhs read (Message transactions Read)) (rhs (nonterm output (Message transactions Output))) (lambda ((value (Message transactions Output))) (Message transactions Read) (call (message transactions Read) (call (oneof output) (var value (Message transactions Output))))))

(rule (lhs read (Message transactions Read)) (rhs (nonterm what_if (Message transactions WhatIf))) (lambda ((value (Message transactions WhatIf))) (Message transactions Read) (call (message transactions Read) (call (oneof what_if) (var value (Message transactions WhatIf))))))

(rule (lhs read (Message transactions Read)) (rhs (nonterm abort (Message transactions Abort))) (lambda ((value (Message transactions Abort))) (Message transactions Read) (call (message transactions Read) (call (oneof abort) (var value (Message transactions Abort))))))

(rule (lhs read (Message transactions Read)) (rhs (nonterm export (Message transactions Export))) (lambda ((value (Message transactions Export))) (Message transactions Read) (call (message transactions Read) (call (oneof export) (var value (Message transactions Export))))))

(rule (lhs demand (Message transactions Demand)) (rhs "(" "demand" (nonterm relation_id (Message logic RelationId)) ")") (lambda ((relation_id (Message logic RelationId))) (Message transactions Demand) (call (message transactions Demand) (var relation_id (Message logic RelationId)))))

(rule (lhs output (Message transactions Output)) (rhs "(" "output" (option (nonterm name String)) (nonterm relation_id (Message logic RelationId)) ")") (lambda ((name (Option String)) (relation_id (Message logic RelationId))) (Message transactions Output) (call (message transactions Output) (call (builtin unwrap_option_or) (var name (Option String)) (lit "output")) (var relation_id (Message logic RelationId)))))

(rule (lhs what_if (Message transactions WhatIf)) (rhs "(" "what_if" (nonterm name String) (nonterm epoch (Message transactions Epoch)) ")") (lambda ((branch String) (epoch (Message transactions Epoch))) (Message transactions WhatIf) (call (message transactions WhatIf) (var branch String) (var epoch (Message transactions Epoch)))))

(rule (lhs abort (Message transactions Abort)) (rhs "(" "abort" (option (nonterm name String)) (nonterm relation_id (Message logic RelationId)) ")") (lambda ((name (Option String)) (relation_id (Message logic RelationId))) (Message transactions Abort) (call (message transactions Abort) (call (builtin unwrap_option_or) (var name (Option String)) (lit "abort")) (var relation_id (Message logic RelationId)))))

(rule (lhs export (Message transactions Export)) (rhs "(" "export" (nonterm export_csv_config (Message transactions ExportCSVConfig)) ")") (lambda ((config (Message transactions ExportCSVConfig))) (Message transactions Export) (call (message transactions Export) (call (oneof csv_config) (var config (Message transactions ExportCSVConfig))))))

(rule (lhs export_csv_config (Message transactions ExportCSVConfig)) (rhs "(" "export_csv_config" (nonterm export_csv_path String) (nonterm export_csv_columns (List (Message transactions ExportCSVColumn))) (nonterm config_dict (List (Tuple String (Message logic Value)))) ")") (lambda ((path String) (columns (List (Message transactions ExportCSVColumn))) (config (List (Tuple String (Message logic Value))))) (Message transactions ExportCSVConfig) (call (builtin export_csv_config) (var path String) (var columns (List (Message transactions ExportCSVColumn))) (var config (List (Tuple String (Message logic Value)))))))

(rule (lhs export_csv_path String) (rhs "(" "path" (term STRING String) ")") (lambda ((x String)) String (var x String)))

(rule (lhs export_csv_columns (List (Message transactions ExportCSVColumn))) (rhs "(" "columns" (star (nonterm export_csv_column (Message transactions ExportCSVColumn))) ")") (lambda ((x (List (Message transactions ExportCSVColumn)))) (List (Message transactions ExportCSVColumn)) (var x (List (Message transactions ExportCSVColumn)))))

(rule (lhs export_csv_column (Message transactions ExportCSVColumn)) (rhs "(" "column" (term STRING String) (nonterm relation_id (Message logic RelationId)) ")") (lambda ((name String) (relation_id (Message logic RelationId))) (Message transactions ExportCSVColumn) (call (message transactions ExportCSVColumn) (var name String) (var relation_id (Message logic RelationId)))))

(mark-nonfinal boolean_value)

(mark-nonfinal construct)

(mark-nonfinal data)

(mark-nonfinal declaration)

(mark-nonfinal formula)

(mark-nonfinal instruction)

(mark-nonfinal monoid)

(mark-nonfinal primitive)

(mark-nonfinal read)

(mark-nonfinal rel_term)

(mark-nonfinal relation_id)

(mark-nonfinal term)

(mark-nonfinal type)

(mark-nonfinal value)

(mark-nonfinal write)
