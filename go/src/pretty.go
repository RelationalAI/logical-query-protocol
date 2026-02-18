// Auto-generated pretty printer.
//
// Generated from protobuf specifications.
// Do not modify this file! If you need to modify the pretty printer, edit the generator code
// in `python-tools/src/meta` or edit the protobuf specification in `proto/v1`.
//
// Command: python -m meta.cli ../proto/relationalai/lqp/v1/fragments.proto ../proto/relationalai/lqp/v1/logic.proto ../proto/relationalai/lqp/v1/transactions.proto --grammar src/meta/grammar.y --printer go

package lqp

import (
	"bytes"
	"fmt"
	"math/big"
	"strings"

	pb "logical-query-protocol/src/lqp/v1"
)

// PrettyPrinter holds state for pretty printing protobuf messages.
type PrettyPrinter struct {
	w           *bytes.Buffer
	indentLevel int
	atLineStart bool
	debugInfo   map[[2]uint64]string
}

func (p *PrettyPrinter) write(s string) {
	if p.atLineStart && strings.TrimSpace(s) != "" {
		p.w.WriteString(strings.Repeat("  ", p.indentLevel))
		p.atLineStart = false
	}
	p.w.WriteString(s)
}

func (p *PrettyPrinter) newline() {
	p.w.WriteString("\n")
	p.atLineStart = true
}

func (p *PrettyPrinter) indent() {
	p.indentLevel++
}

func (p *PrettyPrinter) dedent() {
	if p.indentLevel > 0 {
		p.indentLevel--
	}
}

func (p *PrettyPrinter) getOutput() string {
	return p.w.String()
}

// formatDecimal formats a DecimalValue as "<digits>d<precision>".
func (p *PrettyPrinter) formatDecimal(msg *pb.DecimalValue) string {
	low := msg.GetValue().GetLow()
	high := msg.GetValue().GetHigh()

	// Compute 128-bit signed integer from high/low
	intVal := new(big.Int).SetUint64(high)
	intVal.Lsh(intVal, 64)
	intVal.Add(intVal, new(big.Int).SetUint64(low))
	if high&(1<<63) != 0 {
		// Negative: subtract 2^128
		twoTo128 := new(big.Int).Lsh(big.NewInt(1), 128)
		intVal.Sub(intVal, twoTo128)
	}

	sign := ""
	if intVal.Sign() < 0 {
		sign = "-"
		intVal.Neg(intVal)
	}

	digits := intVal.String()
	scale := int(msg.GetScale())
	precision := msg.GetPrecision()

	var decimalStr string
	if scale <= 0 {
		decimalStr = digits + "." + strings.Repeat("0", -scale)
	} else if scale >= len(digits) {
		decimalStr = "0." + strings.Repeat("0", scale-len(digits)) + digits
	} else {
		decimalStr = digits[:len(digits)-scale] + "." + digits[len(digits)-scale:]
	}

	return fmt.Sprintf("%s%sd%d", sign, decimalStr, precision)
}

// formatInt128 formats an Int128Value as "<value>i128".
func (p *PrettyPrinter) formatInt128(msg *pb.Int128Value) string {
	return int128ToString(msg.GetLow(), msg.GetHigh()) + "i128"
}

// formatUint128 formats a UInt128Value as "0x<hex>".
func (p *PrettyPrinter) formatUint128(msg *pb.UInt128Value) string {
	return "0x" + uint128ToHexString(msg.GetLow(), msg.GetHigh())
}

// formatStringValue escapes and quotes a string for LQP output.
func (p *PrettyPrinter) formatStringValue(s string) string {
	escaped := strings.ReplaceAll(s, "\\", "\\\\")
	escaped = strings.ReplaceAll(escaped, "\"", "\\\"")
	escaped = strings.ReplaceAll(escaped, "\n", "\\n")
	escaped = strings.ReplaceAll(escaped, "\r", "\\r")
	escaped = strings.ReplaceAll(escaped, "\t", "\\t")
	return "\"" + escaped + "\""
}

// fragmentIdToString decodes a FragmentId's bytes to a string.
func (p *PrettyPrinter) fragmentIdToString(msg *pb.FragmentId) string {
	if msg.GetId() == nil {
		return ""
	}
	return string(msg.GetId())
}

// startPrettyFragment extracts debug info from a Fragment for relation ID lookup.
func (p *PrettyPrinter) startPrettyFragment(msg *pb.Fragment) {
	debugInfo := msg.GetDebugInfo()
	if debugInfo == nil {
		return
	}
	ids := debugInfo.GetIds()
	names := debugInfo.GetOrigNames()
	for i, rid := range ids {
		if i < len(names) {
			key := [2]uint64{rid.GetIdLow(), rid.GetIdHigh()}
			p.debugInfo[key] = names[i]
		}
	}
}

// relationIdToString looks up a RelationId in the debug info map.
func (p *PrettyPrinter) relationIdToString(msg *pb.RelationId) string {
	key := [2]uint64{msg.GetIdLow(), msg.GetIdHigh()}
	if name, ok := p.debugInfo[key]; ok {
		return name
	}
	return ""
}

// relationIdToInt returns a pointer to int64 if the RelationId fits in
// signed 64-bit range, nil otherwise.
func (p *PrettyPrinter) relationIdToInt(msg *pb.RelationId) *int64 {
	if msg.GetIdHigh() == 0 && msg.GetIdLow() <= 0x7FFFFFFFFFFFFFFF {
		v := int64(msg.GetIdLow())
		return &v
	}
	return nil
}

// relationIdToUint128 converts a RelationId to a UInt128Value.
func (p *PrettyPrinter) relationIdToUint128(msg *pb.RelationId) *pb.UInt128Value {
	return &pb.UInt128Value{Low: msg.GetIdLow(), High: msg.GetIdHigh()}
}

// --- Free functions ---

func uint128ToString(low, high uint64) string {
	if high == 0 {
		return fmt.Sprintf("%d", low)
	}
	result := new(big.Int).SetUint64(high)
	result.Lsh(result, 64)
	result.Add(result, new(big.Int).SetUint64(low))
	return result.String()
}

func int128ToString(low, high uint64) string {
	isNegative := (high & 0x8000000000000000) != 0
	if !isNegative {
		return uint128ToString(low, high)
	}
	result := new(big.Int).SetUint64(^high)
	result.Lsh(result, 64)
	result.Add(result, new(big.Int).SetUint64(^low))
	result.Add(result, big.NewInt(1))
	return "-" + result.String()
}

func uint128ToHexString(low, high uint64) string {
	if high == 0 {
		return fmt.Sprintf("%x", low)
	}
	return fmt.Sprintf("%x%016x", high, low)
}

func formatBool(b bool) string {
	if b {
		return "true"
	}
	return "false"
}

// --- Helper functions ---

func (p *PrettyPrinter) ExtractValueInt32(value *pb.Value, default_ int64) int32 {
	if (value != nil && hasProtoField(value, "int_value")) {
		return int32(value.GetIntValue())
	}
	return int32(default_)
}

func (p *PrettyPrinter) ExtractValueInt64(value *pb.Value, default_ int64) int64 {
	if (value != nil && hasProtoField(value, "int_value")) {
		return value.GetIntValue()
	}
	return default_
}

func (p *PrettyPrinter) ExtractValueFloat64(value *pb.Value, default_ float64) float64 {
	if (value != nil && hasProtoField(value, "float_value")) {
		return value.GetFloatValue()
	}
	return default_
}

func (p *PrettyPrinter) ExtractValueString(value *pb.Value, default_ string) string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return value.GetStringValue()
	}
	return default_
}

func (p *PrettyPrinter) ExtractValueBoolean(value *pb.Value, default_ bool) bool {
	if (value != nil && hasProtoField(value, "boolean_value")) {
		return value.GetBooleanValue()
	}
	return default_
}

func (p *PrettyPrinter) ExtractValueBytes(value *pb.Value, default_ []byte) []byte {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	return default_
}

func (p *PrettyPrinter) ExtractValueUint128(value *pb.Value, default_ *pb.UInt128Value) *pb.UInt128Value {
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	return default_
}

func (p *PrettyPrinter) ExtractValueStringList(value *pb.Value, default_ []string) []string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	return default_
}

func (p *PrettyPrinter) TryExtractValueInt64(value *pb.Value) *int64 {
	if (value != nil && hasProtoField(value, "int_value")) {
		return ptr(value.GetIntValue())
	}
	return nil
}

func (p *PrettyPrinter) TryExtractValueFloat64(value *pb.Value) *float64 {
	if (value != nil && hasProtoField(value, "float_value")) {
		return ptr(value.GetFloatValue())
	}
	return nil
}

func (p *PrettyPrinter) TryExtractValueString(value *pb.Value) *string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return ptr(value.GetStringValue())
	}
	return nil
}

func (p *PrettyPrinter) TryExtractValueBytes(value *pb.Value) []byte {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []byte(value.GetStringValue())
	}
	return nil
}

func (p *PrettyPrinter) TryExtractValueUint128(value *pb.Value) *pb.UInt128Value {
	if (value != nil && hasProtoField(value, "uint128_value")) {
		return value.GetUint128Value()
	}
	return nil
}

func (p *PrettyPrinter) TryExtractValueStringList(value *pb.Value) []string {
	if (value != nil && hasProtoField(value, "string_value")) {
		return []string{value.GetStringValue()}
	}
	return nil
}

func (p *PrettyPrinter) constructCsvConfig(config_dict [][]interface{}) *pb.CSVConfig {
	config := dictFromList(config_dict)
	_t928 := p.ExtractValueInt32(dictGetValue(config, "csv_header_row"), 1)
	header_row := _t928
	_t929 := p.ExtractValueInt64(dictGetValue(config, "csv_skip"), 0)
	skip := _t929
	_t930 := p.ExtractValueString(dictGetValue(config, "csv_new_line"), "")
	new_line := _t930
	_t931 := p.ExtractValueString(dictGetValue(config, "csv_delimiter"), ",")
	delimiter := _t931
	_t932 := p.ExtractValueString(dictGetValue(config, "csv_quotechar"), "\"")
	quotechar := _t932
	_t933 := p.ExtractValueString(dictGetValue(config, "csv_escapechar"), "\"")
	escapechar := _t933
	_t934 := p.ExtractValueString(dictGetValue(config, "csv_comment"), "")
	comment := _t934
	_t935 := p.ExtractValueStringList(dictGetValue(config, "csv_missing_strings"), []string{})
	missing_strings := _t935
	_t936 := p.ExtractValueString(dictGetValue(config, "csv_decimal_separator"), ".")
	decimal_separator := _t936
	_t937 := p.ExtractValueString(dictGetValue(config, "csv_encoding"), "utf-8")
	encoding := _t937
	_t938 := p.ExtractValueString(dictGetValue(config, "csv_compression"), "auto")
	compression := _t938
	_t939 := &pb.CSVConfig{HeaderRow: header_row, Skip: skip, NewLine: new_line, Delimiter: delimiter, Quotechar: quotechar, Escapechar: escapechar, Comment: comment, MissingStrings: missing_strings, DecimalSeparator: decimal_separator, Encoding: encoding, Compression: compression}
	return _t939
}

func (p *PrettyPrinter) constructBetreeInfo(key_types []*pb.Type, value_types []*pb.Type, config_dict [][]interface{}) *pb.BeTreeInfo {
	config := dictFromList(config_dict)
	_t940 := p.TryExtractValueFloat64(dictGetValue(config, "betree_config_epsilon"))
	epsilon := _t940
	_t941 := p.TryExtractValueInt64(dictGetValue(config, "betree_config_max_pivots"))
	max_pivots := _t941
	_t942 := p.TryExtractValueInt64(dictGetValue(config, "betree_config_max_deltas"))
	max_deltas := _t942
	_t943 := p.TryExtractValueInt64(dictGetValue(config, "betree_config_max_leaf"))
	max_leaf := _t943
	_t944 := &pb.BeTreeConfig{Epsilon: deref(epsilon, 0.0), MaxPivots: deref(max_pivots, 0), MaxDeltas: deref(max_deltas, 0), MaxLeaf: deref(max_leaf, 0)}
	storage_config := _t944
	_t945 := p.TryExtractValueUint128(dictGetValue(config, "betree_locator_root_pageid"))
	root_pageid := _t945
	_t946 := p.TryExtractValueBytes(dictGetValue(config, "betree_locator_inline_data"))
	inline_data := _t946
	_t947 := p.TryExtractValueInt64(dictGetValue(config, "betree_locator_element_count"))
	element_count := _t947
	_t948 := p.TryExtractValueInt64(dictGetValue(config, "betree_locator_tree_height"))
	tree_height := _t948
	_t949 := &pb.BeTreeLocator{ElementCount: deref(element_count, 0), TreeHeight: deref(tree_height, 0)}
	if root_pageid != nil {
		_t949.Location = &pb.BeTreeLocator_RootPageid{RootPageid: root_pageid}
	} else {
		_t949.Location = &pb.BeTreeLocator_InlineData{InlineData: inline_data}
	}
	relation_locator := _t949
	_t950 := &pb.BeTreeInfo{KeyTypes: key_types, ValueTypes: value_types, StorageConfig: storage_config, RelationLocator: relation_locator}
	return _t950
}

func (p *PrettyPrinter) defaultConfigure() *pb.Configure {
	_t951 := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	ivm_config := _t951
	_t952 := &pb.Configure{SemanticsVersion: 0, IvmConfig: ivm_config}
	return _t952
}

func (p *PrettyPrinter) constructConfigure(config_dict [][]interface{}) *pb.Configure {
	config := dictFromList(config_dict)
	maintenance_level_val := dictGetValue(config, "ivm.maintenance_level")
	maintenance_level := pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF
	if (maintenance_level_val != nil && hasProtoField(maintenance_level_val, "string_value")) {
		if maintenance_level_val.GetStringValue() == "off" {
			maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF
		} else {
			if maintenance_level_val.GetStringValue() == "auto" {
				maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO
			} else {
				if maintenance_level_val.GetStringValue() == "all" {
					maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL
				} else {
					maintenance_level = pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF
				}
			}
		}
	}
	_t953 := &pb.IVMConfig{Level: maintenance_level}
	ivm_config := _t953
	_t954 := p.ExtractValueInt64(dictGetValue(config, "semantics_version"), 0)
	semantics_version := _t954
	_t955 := &pb.Configure{SemanticsVersion: semantics_version, IvmConfig: ivm_config}
	return _t955
}

func (p *PrettyPrinter) exportCsvConfig(path string, columns []*pb.ExportCSVColumn, config_dict [][]interface{}) *pb.ExportCSVConfig {
	config := dictFromList(config_dict)
	_t956 := p.ExtractValueInt64(dictGetValue(config, "partition_size"), 0)
	partition_size := _t956
	_t957 := p.ExtractValueString(dictGetValue(config, "compression"), "")
	compression := _t957
	_t958 := p.ExtractValueBoolean(dictGetValue(config, "syntax_header_row"), true)
	syntax_header_row := _t958
	_t959 := p.ExtractValueString(dictGetValue(config, "syntax_missing_string"), "")
	syntax_missing_string := _t959
	_t960 := p.ExtractValueString(dictGetValue(config, "syntax_delim"), ",")
	syntax_delim := _t960
	_t961 := p.ExtractValueString(dictGetValue(config, "syntax_quotechar"), "\"")
	syntax_quotechar := _t961
	_t962 := p.ExtractValueString(dictGetValue(config, "syntax_escapechar"), "\\")
	syntax_escapechar := _t962
	_t963 := &pb.ExportCSVConfig{Path: path, DataColumns: columns, PartitionSize: ptr(partition_size), Compression: ptr(compression), SyntaxHeaderRow: ptr(syntax_header_row), SyntaxMissingString: ptr(syntax_missing_string), SyntaxDelim: ptr(syntax_delim), SyntaxQuotechar: ptr(syntax_quotechar), SyntaxEscapechar: ptr(syntax_escapechar)}
	return _t963
}

func (p *PrettyPrinter) MakeValueInt32(v int32) *pb.Value {
	_t964 := &pb.Value{}
	_t964.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t964
}

func (p *PrettyPrinter) MakeValueInt64(v int64) *pb.Value {
	_t965 := &pb.Value{}
	_t965.Value = &pb.Value_IntValue{IntValue: v}
	return _t965
}

func (p *PrettyPrinter) MakeValueFloat64(v float64) *pb.Value {
	_t966 := &pb.Value{}
	_t966.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t966
}

func (p *PrettyPrinter) MakeValueString(v string) *pb.Value {
	_t967 := &pb.Value{}
	_t967.Value = &pb.Value_StringValue{StringValue: v}
	return _t967
}

func (p *PrettyPrinter) MakeValueBoolean(v bool) *pb.Value {
	_t968 := &pb.Value{}
	_t968.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t968
}

func (p *PrettyPrinter) MakeValueUint128(v *pb.UInt128Value) *pb.Value {
	_t969 := &pb.Value{}
	_t969.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t969
}

func (p *PrettyPrinter) isDefaultConfigure(cfg *pb.Configure) bool {
	if cfg.GetSemanticsVersion() != 0 {
		return false
	}
	if cfg.GetIvmConfig().GetLevel() != pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
		return false
	}
	return true
}

func (p *PrettyPrinter) deconstructConfigure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t970 := p.MakeValueString("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t970})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t971 := p.MakeValueString("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t971})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t972 := p.MakeValueString("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t972})
			}
		}
	}
	_t973 := p.MakeValueInt64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t973})
	return listSort(result)
}

func (p *PrettyPrinter) deconstructCsvConfig(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t974 := p.MakeValueInt32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t974})
	_t975 := p.MakeValueInt64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t975})
	if msg.GetNewLine() != "" {
		_t976 := p.MakeValueString(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t976})
	}
	_t977 := p.MakeValueString(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t977})
	_t978 := p.MakeValueString(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t978})
	_t979 := p.MakeValueString(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t979})
	if msg.GetComment() != "" {
		_t980 := p.MakeValueString(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t980})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t981 := p.MakeValueString(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t981})
	}
	_t982 := p.MakeValueString(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t982})
	_t983 := p.MakeValueString(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t983})
	_t984 := p.MakeValueString(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t984})
	return listSort(result)
}

func (p *PrettyPrinter) deconstructBetreeInfoConfig(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t985 := p.MakeValueFloat64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t985})
	_t986 := p.MakeValueInt64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t986})
	_t987 := p.MakeValueInt64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t987})
	_t988 := p.MakeValueInt64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t988})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t989 := p.MakeValueUint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t989})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t990 := p.MakeValueString(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t990})
		}
	}
	_t991 := p.MakeValueInt64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t991})
	_t992 := p.MakeValueInt64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t992})
	return listSort(result)
}

func (p *PrettyPrinter) deconstructExportCsvConfig(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t993 := p.MakeValueInt64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t993})
	}
	if msg.Compression != nil {
		_t994 := p.MakeValueString(*msg.Compression)
		result = append(result, []interface{}{"compression", _t994})
	}
	if msg.SyntaxHeaderRow != nil {
		_t995 := p.MakeValueBoolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t995})
	}
	if msg.SyntaxMissingString != nil {
		_t996 := p.MakeValueString(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t996})
	}
	if msg.SyntaxDelim != nil {
		_t997 := p.MakeValueString(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t997})
	}
	if msg.SyntaxQuotechar != nil {
		_t998 := p.MakeValueString(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t998})
	}
	if msg.SyntaxEscapechar != nil {
		_t999 := p.MakeValueString(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t999})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstructRelationIdString(msg *pb.RelationId) *string {
	name := p.relationIdToString(msg)
	if name != "" {
		return ptr(name)
	}
	return nil
}

func (p *PrettyPrinter) deconstructRelationIdUint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	if name == "" {
		return p.relationIdToUint128(msg)
	}
	return nil
}

func (p *PrettyPrinter) deconstructBindings(abs *pb.Abstraction) []interface{} {
	n := int64(len(abs.GetVars()))
	return []interface{}{abs.GetVars()[0:n], []*pb.Binding{}}
}

func (p *PrettyPrinter) deconstructBindingsWithArity(abs *pb.Abstraction, value_arity int64) []interface{} {
	n := int64(len(abs.GetVars()))
	key_end := (n - value_arity)
	return []interface{}{abs.GetVars()[0:key_end], abs.GetVars()[key_end:n]}
}

// --- Pretty-print methods ---

func (p *PrettyPrinter) pretty_transaction(msg *pb.Transaction) {
	_t453 := func(_dollar_dollar *pb.Transaction) []interface{} {
		var _t454 interface{}
		if hasProtoField(_dollar_dollar, "configure") {
			_t454 = _dollar_dollar.GetConfigure()
		}
		var _t455 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t455 = _dollar_dollar.GetSync()
		}
		return []interface{}{_t454, _t455, _dollar_dollar.GetEpochs()}
	}
	_t456 := _t453(msg)
	fields0 := _t456
	p.write("(")
	p.write("transaction")
	p.indent()
	_t457 := fields0[0]
	var _t458 *pb.Configure
	if _t457 != nil {
		_t458 = _t457.(*pb.Configure)
	}
	field1 := _t458
	if field1 != nil {
		p.newline()
		opt_val2 := field1
		p.pretty_configure(opt_val2)
	}
	_t459 := fields0[1]
	var _t460 *pb.Sync
	if _t459 != nil {
		_t460 = _t459.(*pb.Sync)
	}
	field3 := _t460
	if field3 != nil {
		p.newline()
		opt_val4 := field3
		p.pretty_sync(opt_val4)
	}
	field5 := fields0[2].([]*pb.Epoch)
	if !(len(field5) == 0) {
		p.newline()
		for i7, elem6 := range field5 {
			if (i7 > 0) {
				p.newline()
			}
			p.pretty_epoch(elem6)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) {
	_t461 := func(_dollar_dollar *pb.Configure) [][]interface{} {
		_t462 := p.deconstructConfigure(_dollar_dollar)
		return _t462
	}
	_t463 := _t461(msg)
	fields8 := _t463
	p.write("(")
	p.write("configure")
	p.indent()
	p.newline()
	p.pretty_config_dict(fields8)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) {
	_t464 := func(_dollar_dollar [][]interface{}) [][]interface{} {
		return _dollar_dollar
	}
	_t465 := _t464(msg)
	fields9 := _t465
	p.write("{")
	if !(len(fields9) == 0) {
		p.write(" ")
		for i11, elem10 := range fields9 {
			if (i11 > 0) {
				p.newline()
			}
			p.pretty_config_key_value(elem10)
		}
	}
	p.write("}")
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) {
	_t466 := func(_dollar_dollar []interface{}) []interface{} {
		return []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
	}
	_t467 := _t466(msg)
	fields12 := _t467
	p.write(":")
	field13 := fields12[0].(string)
	p.write(field13)
	p.write(" ")
	field14 := fields12[1].(*pb.Value)
	p.pretty_value(field14)
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) {
	_t468 := func(_dollar_dollar *pb.Value) *pb.DateValue {
		var _t469 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t469 = _dollar_dollar.GetDateValue()
		}
		return _t469
	}
	_t470 := _t468(msg)
	deconstruct_result32 := _t470
	if deconstruct_result32 != nil {
		unwrapped_fields33 := deconstruct_result32
		p.pretty_date(unwrapped_fields33)
	} else {
		_t471 := func(_dollar_dollar *pb.Value) *pb.DateTimeValue {
			var _t472 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t472 = _dollar_dollar.GetDatetimeValue()
			}
			return _t472
		}
		_t473 := _t471(msg)
		deconstruct_result30 := _t473
		if deconstruct_result30 != nil {
			unwrapped_fields31 := deconstruct_result30
			p.pretty_datetime(unwrapped_fields31)
		} else {
			_t474 := func(_dollar_dollar *pb.Value) *string {
				var _t475 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t475 = ptr(_dollar_dollar.GetStringValue())
				}
				return _t475
			}
			_t476 := _t474(msg)
			deconstruct_result28 := _t476
			if deconstruct_result28 != nil {
				unwrapped_fields29 := *deconstruct_result28
				p.write(p.formatStringValue(unwrapped_fields29))
			} else {
				_t477 := func(_dollar_dollar *pb.Value) *int64 {
					var _t478 *int64
					if hasProtoField(_dollar_dollar, "int_value") {
						_t478 = ptr(_dollar_dollar.GetIntValue())
					}
					return _t478
				}
				_t479 := _t477(msg)
				deconstruct_result26 := _t479
				if deconstruct_result26 != nil {
					unwrapped_fields27 := *deconstruct_result26
					p.write(fmt.Sprintf("%d", unwrapped_fields27))
				} else {
					_t480 := func(_dollar_dollar *pb.Value) *float64 {
						var _t481 *float64
						if hasProtoField(_dollar_dollar, "float_value") {
							_t481 = ptr(_dollar_dollar.GetFloatValue())
						}
						return _t481
					}
					_t482 := _t480(msg)
					deconstruct_result24 := _t482
					if deconstruct_result24 != nil {
						unwrapped_fields25 := *deconstruct_result24
						p.write(fmt.Sprintf("%g", unwrapped_fields25))
					} else {
						_t483 := func(_dollar_dollar *pb.Value) *pb.UInt128Value {
							var _t484 *pb.UInt128Value
							if hasProtoField(_dollar_dollar, "uint128_value") {
								_t484 = _dollar_dollar.GetUint128Value()
							}
							return _t484
						}
						_t485 := _t483(msg)
						deconstruct_result22 := _t485
						if deconstruct_result22 != nil {
							unwrapped_fields23 := deconstruct_result22
							p.write(p.formatUint128(unwrapped_fields23))
						} else {
							_t486 := func(_dollar_dollar *pb.Value) *pb.Int128Value {
								var _t487 *pb.Int128Value
								if hasProtoField(_dollar_dollar, "int128_value") {
									_t487 = _dollar_dollar.GetInt128Value()
								}
								return _t487
							}
							_t488 := _t486(msg)
							deconstruct_result20 := _t488
							if deconstruct_result20 != nil {
								unwrapped_fields21 := deconstruct_result20
								p.write(p.formatInt128(unwrapped_fields21))
							} else {
								_t489 := func(_dollar_dollar *pb.Value) *pb.DecimalValue {
									var _t490 *pb.DecimalValue
									if hasProtoField(_dollar_dollar, "decimal_value") {
										_t490 = _dollar_dollar.GetDecimalValue()
									}
									return _t490
								}
								_t491 := _t489(msg)
								deconstruct_result18 := _t491
								if deconstruct_result18 != nil {
									unwrapped_fields19 := deconstruct_result18
									p.write(p.formatDecimal(unwrapped_fields19))
								} else {
									_t492 := func(_dollar_dollar *pb.Value) *bool {
										var _t493 *bool
										if hasProtoField(_dollar_dollar, "boolean_value") {
											_t493 = ptr(_dollar_dollar.GetBooleanValue())
										}
										return _t493
									}
									_t494 := _t492(msg)
									deconstruct_result16 := _t494
									if deconstruct_result16 != nil {
										unwrapped_fields17 := *deconstruct_result16
										p.pretty_boolean_value(unwrapped_fields17)
									} else {
										_t495 := func(_dollar_dollar *pb.Value) *pb.Value {
											return _dollar_dollar
										}
										_t496 := _t495(msg)
										fields15 := _t496
										_ = fields15
										p.write("missing")
									}
								}
							}
						}
					}
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_date(msg *pb.DateValue) {
	_t497 := func(_dollar_dollar *pb.DateValue) []interface{} {
		return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
	}
	_t498 := _t497(msg)
	fields34 := _t498
	p.write("(")
	p.write("date")
	p.indent()
	p.write(" ")
	field35 := fields34[0].(int64)
	p.write(fmt.Sprintf("%d", field35))
	p.newline()
	field36 := fields34[1].(int64)
	p.write(fmt.Sprintf("%d", field36))
	p.newline()
	field37 := fields34[2].(int64)
	p.write(fmt.Sprintf("%d", field37))
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) {
	_t499 := func(_dollar_dollar *pb.DateTimeValue) []interface{} {
		return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
	}
	_t500 := _t499(msg)
	fields38 := _t500
	p.write("(")
	p.write("datetime")
	p.indent()
	p.write(" ")
	field39 := fields38[0].(int64)
	p.write(fmt.Sprintf("%d", field39))
	p.newline()
	field40 := fields38[1].(int64)
	p.write(fmt.Sprintf("%d", field40))
	p.newline()
	field41 := fields38[2].(int64)
	p.write(fmt.Sprintf("%d", field41))
	p.newline()
	field42 := fields38[3].(int64)
	p.write(fmt.Sprintf("%d", field42))
	p.newline()
	field43 := fields38[4].(int64)
	p.write(fmt.Sprintf("%d", field43))
	p.newline()
	field44 := fields38[5].(int64)
	p.write(fmt.Sprintf("%d", field44))
	_t501 := fields38[6]
	var _t502 *int64
	if _t501 != nil {
		if _t503, ok := _t501.(*int64); ok {
			_t502 = _t503
		} else {
			_t504 := _t501.(int64)
			_t502 = &_t504
		}
	}
	field45 := _t502
	if field45 != nil {
		p.newline()
		opt_val46 := *field45
		p.write(fmt.Sprintf("%d", opt_val46))
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) {
	_t505 := func(_dollar_dollar bool) []interface{} {
		var _t506 []interface{}
		if _dollar_dollar {
			_t506 = []interface{}{}
		}
		return _t506
	}
	_t507 := _t505(msg)
	deconstruct_result49 := _t507
	if deconstruct_result49 != nil {
		unwrapped_fields50 := deconstruct_result49
		_ = unwrapped_fields50
		p.write("true")
	} else {
		_t508 := func(_dollar_dollar bool) []interface{} {
			var _t509 []interface{}
			if !(_dollar_dollar) {
				_t509 = []interface{}{}
			}
			return _t509
		}
		_t510 := _t508(msg)
		deconstruct_result47 := _t510
		if deconstruct_result47 != nil {
			unwrapped_fields48 := deconstruct_result47
			_ = unwrapped_fields48
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) {
	_t511 := func(_dollar_dollar *pb.Sync) []*pb.FragmentId {
		return _dollar_dollar.GetFragments()
	}
	_t512 := _t511(msg)
	fields51 := _t512
	p.write("(")
	p.write("sync")
	p.indent()
	if !(len(fields51) == 0) {
		p.newline()
		for i53, elem52 := range fields51 {
			if (i53 > 0) {
				p.newline()
			}
			p.pretty_fragment_id(elem52)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) {
	_t513 := func(_dollar_dollar *pb.FragmentId) string {
		return p.fragmentIdToString(_dollar_dollar)
	}
	_t514 := _t513(msg)
	fields54 := _t514
	p.write(":")
	p.write(fields54)
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) {
	_t515 := func(_dollar_dollar *pb.Epoch) []interface{} {
		var _t516 interface{}
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t516 = _dollar_dollar.GetWrites()
		}
		var _t517 interface{}
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t517 = _dollar_dollar.GetReads()
		}
		return []interface{}{_t516, _t517}
	}
	_t518 := _t515(msg)
	fields55 := _t518
	p.write("(")
	p.write("epoch")
	p.indent()
	_t519 := fields55[0]
	var _t520 []*pb.Write
	if _t519 != nil {
		_t520 = _t519.([]*pb.Write)
	}
	field56 := _t520
	if field56 != nil {
		p.newline()
		opt_val57 := field56
		p.pretty_epoch_writes(opt_val57)
	}
	_t521 := fields55[1]
	var _t522 []*pb.Read
	if _t521 != nil {
		_t522 = _t521.([]*pb.Read)
	}
	field58 := _t522
	if field58 != nil {
		p.newline()
		opt_val59 := field58
		p.pretty_epoch_reads(opt_val59)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) {
	_t523 := func(_dollar_dollar []*pb.Write) []*pb.Write {
		return _dollar_dollar
	}
	_t524 := _t523(msg)
	fields60 := _t524
	p.write("(")
	p.write("writes")
	p.indent()
	if !(len(fields60) == 0) {
		p.newline()
		for i62, elem61 := range fields60 {
			if (i62 > 0) {
				p.newline()
			}
			p.pretty_write(elem61)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) {
	_t525 := func(_dollar_dollar *pb.Write) *pb.Define {
		var _t526 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t526 = _dollar_dollar.GetDefine()
		}
		return _t526
	}
	_t527 := _t525(msg)
	deconstruct_result67 := _t527
	if deconstruct_result67 != nil {
		unwrapped_fields68 := deconstruct_result67
		p.pretty_define(unwrapped_fields68)
	} else {
		_t528 := func(_dollar_dollar *pb.Write) *pb.Undefine {
			var _t529 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t529 = _dollar_dollar.GetUndefine()
			}
			return _t529
		}
		_t530 := _t528(msg)
		deconstruct_result65 := _t530
		if deconstruct_result65 != nil {
			unwrapped_fields66 := deconstruct_result65
			p.pretty_undefine(unwrapped_fields66)
		} else {
			_t531 := func(_dollar_dollar *pb.Write) *pb.Context {
				var _t532 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t532 = _dollar_dollar.GetContext()
				}
				return _t532
			}
			_t533 := _t531(msg)
			deconstruct_result63 := _t533
			if deconstruct_result63 != nil {
				unwrapped_fields64 := deconstruct_result63
				p.pretty_context(unwrapped_fields64)
			} else {
				panic(ParseError{msg: "No matching rule for write"})
			}
		}
	}
}

func (p *PrettyPrinter) pretty_define(msg *pb.Define) {
	_t534 := func(_dollar_dollar *pb.Define) *pb.Fragment {
		return _dollar_dollar.GetFragment()
	}
	_t535 := _t534(msg)
	fields69 := _t535
	p.write("(")
	p.write("define")
	p.indent()
	p.newline()
	p.pretty_fragment(fields69)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) {
	_t536 := func(_dollar_dollar *pb.Fragment) []interface{} {
		p.startPrettyFragment(_dollar_dollar)
		return []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
	}
	_t537 := _t536(msg)
	fields70 := _t537
	p.write("(")
	p.write("fragment")
	p.indent()
	p.write(" ")
	field71 := fields70[0].(*pb.FragmentId)
	p.pretty_new_fragment_id(field71)
	field72 := fields70[1].([]*pb.Declaration)
	if !(len(field72) == 0) {
		p.newline()
		for i74, elem73 := range field72 {
			if (i74 > 0) {
				p.newline()
			}
			p.pretty_declaration(elem73)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) {
	_t538 := func(_dollar_dollar *pb.FragmentId) *pb.FragmentId {
		return _dollar_dollar
	}
	_t539 := _t538(msg)
	fields75 := _t539
	p.pretty_fragment_id(fields75)
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) {
	_t540 := func(_dollar_dollar *pb.Declaration) *pb.Def {
		var _t541 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t541 = _dollar_dollar.GetDef()
		}
		return _t541
	}
	_t542 := _t540(msg)
	deconstruct_result82 := _t542
	if deconstruct_result82 != nil {
		unwrapped_fields83 := deconstruct_result82
		p.pretty_def(unwrapped_fields83)
	} else {
		_t543 := func(_dollar_dollar *pb.Declaration) *pb.Algorithm {
			var _t544 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t544 = _dollar_dollar.GetAlgorithm()
			}
			return _t544
		}
		_t545 := _t543(msg)
		deconstruct_result80 := _t545
		if deconstruct_result80 != nil {
			unwrapped_fields81 := deconstruct_result80
			p.pretty_algorithm(unwrapped_fields81)
		} else {
			_t546 := func(_dollar_dollar *pb.Declaration) *pb.Constraint {
				var _t547 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t547 = _dollar_dollar.GetConstraint()
				}
				return _t547
			}
			_t548 := _t546(msg)
			deconstruct_result78 := _t548
			if deconstruct_result78 != nil {
				unwrapped_fields79 := deconstruct_result78
				p.pretty_constraint(unwrapped_fields79)
			} else {
				_t549 := func(_dollar_dollar *pb.Declaration) *pb.Data {
					var _t550 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t550 = _dollar_dollar.GetData()
					}
					return _t550
				}
				_t551 := _t549(msg)
				deconstruct_result76 := _t551
				if deconstruct_result76 != nil {
					unwrapped_fields77 := deconstruct_result76
					p.pretty_data(unwrapped_fields77)
				} else {
					panic(ParseError{msg: "No matching rule for declaration"})
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_def(msg *pb.Def) {
	_t552 := func(_dollar_dollar *pb.Def) []interface{} {
		var _t553 interface{}
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t553 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t553}
	}
	_t554 := _t552(msg)
	fields84 := _t554
	p.write("(")
	p.write("def")
	p.indent()
	p.newline()
	field85 := fields84[0].(*pb.RelationId)
	p.pretty_relation_id(field85)
	p.newline()
	field86 := fields84[1].(*pb.Abstraction)
	p.pretty_abstraction(field86)
	_t555 := fields84[2]
	var _t556 []*pb.Attribute
	if _t555 != nil {
		_t556 = _t555.([]*pb.Attribute)
	}
	field87 := _t556
	if field87 != nil {
		p.newline()
		opt_val88 := field87
		p.pretty_attrs(opt_val88)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) {
	_t557 := func(_dollar_dollar *pb.RelationId) *string {
		_t558 := p.deconstructRelationIdString(_dollar_dollar)
		return _t558
	}
	_t559 := _t557(msg)
	deconstruct_result91 := _t559
	if deconstruct_result91 != nil {
		unwrapped_fields92 := *deconstruct_result91
		p.write(":")
		p.write(unwrapped_fields92)
	} else {
		_t560 := func(_dollar_dollar *pb.RelationId) *pb.UInt128Value {
			_t561 := p.deconstructRelationIdUint128(_dollar_dollar)
			return _t561
		}
		_t562 := _t560(msg)
		deconstruct_result89 := _t562
		if deconstruct_result89 != nil {
			unwrapped_fields90 := deconstruct_result89
			p.write(p.formatUint128(unwrapped_fields90))
		} else {
			panic(ParseError{msg: "No matching rule for relation_id"})
		}
	}
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) {
	_t563 := func(_dollar_dollar *pb.Abstraction) []interface{} {
		_t564 := p.deconstructBindings(_dollar_dollar)
		return []interface{}{_t564, _dollar_dollar.GetValue()}
	}
	_t565 := _t563(msg)
	fields93 := _t565
	p.write("(")
	field94 := fields93[0].([]interface{})
	p.pretty_bindings(field94)
	p.write(" ")
	field95 := fields93[1].(*pb.Formula)
	p.pretty_formula(field95)
	p.write(")")
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) {
	_t566 := func(_dollar_dollar []interface{}) []interface{} {
		var _t567 interface{}
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t567 = _dollar_dollar[1].([]*pb.Binding)
		}
		return []interface{}{_dollar_dollar[0].([]*pb.Binding), _t567}
	}
	_t568 := _t566(msg)
	fields96 := _t568
	p.write("[")
	field97 := fields96[0].([]*pb.Binding)
	for i99, elem98 := range field97 {
		if (i99 > 0) {
			p.newline()
		}
		p.pretty_binding(elem98)
	}
	_t569 := fields96[1]
	var _t570 []*pb.Binding
	if _t569 != nil {
		_t570 = _t569.([]*pb.Binding)
	}
	field100 := _t570
	if field100 != nil {
		p.write(" ")
		opt_val101 := field100
		p.pretty_value_bindings(opt_val101)
	}
	p.write("]")
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) {
	_t571 := func(_dollar_dollar *pb.Binding) []interface{} {
		return []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
	}
	_t572 := _t571(msg)
	fields102 := _t572
	field103 := fields102[0].(string)
	p.write(field103)
	p.write("::")
	field104 := fields102[1].(*pb.Type)
	p.pretty_type(field104)
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) {
	_t573 := func(_dollar_dollar *pb.Type) *pb.UnspecifiedType {
		var _t574 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t574 = _dollar_dollar.GetUnspecifiedType()
		}
		return _t574
	}
	_t575 := _t573(msg)
	deconstruct_result125 := _t575
	if deconstruct_result125 != nil {
		unwrapped_fields126 := deconstruct_result125
		p.pretty_unspecified_type(unwrapped_fields126)
	} else {
		_t576 := func(_dollar_dollar *pb.Type) *pb.StringType {
			var _t577 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t577 = _dollar_dollar.GetStringType()
			}
			return _t577
		}
		_t578 := _t576(msg)
		deconstruct_result123 := _t578
		if deconstruct_result123 != nil {
			unwrapped_fields124 := deconstruct_result123
			p.pretty_string_type(unwrapped_fields124)
		} else {
			_t579 := func(_dollar_dollar *pb.Type) *pb.IntType {
				var _t580 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t580 = _dollar_dollar.GetIntType()
				}
				return _t580
			}
			_t581 := _t579(msg)
			deconstruct_result121 := _t581
			if deconstruct_result121 != nil {
				unwrapped_fields122 := deconstruct_result121
				p.pretty_int_type(unwrapped_fields122)
			} else {
				_t582 := func(_dollar_dollar *pb.Type) *pb.FloatType {
					var _t583 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t583 = _dollar_dollar.GetFloatType()
					}
					return _t583
				}
				_t584 := _t582(msg)
				deconstruct_result119 := _t584
				if deconstruct_result119 != nil {
					unwrapped_fields120 := deconstruct_result119
					p.pretty_float_type(unwrapped_fields120)
				} else {
					_t585 := func(_dollar_dollar *pb.Type) *pb.UInt128Type {
						var _t586 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t586 = _dollar_dollar.GetUint128Type()
						}
						return _t586
					}
					_t587 := _t585(msg)
					deconstruct_result117 := _t587
					if deconstruct_result117 != nil {
						unwrapped_fields118 := deconstruct_result117
						p.pretty_uint128_type(unwrapped_fields118)
					} else {
						_t588 := func(_dollar_dollar *pb.Type) *pb.Int128Type {
							var _t589 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t589 = _dollar_dollar.GetInt128Type()
							}
							return _t589
						}
						_t590 := _t588(msg)
						deconstruct_result115 := _t590
						if deconstruct_result115 != nil {
							unwrapped_fields116 := deconstruct_result115
							p.pretty_int128_type(unwrapped_fields116)
						} else {
							_t591 := func(_dollar_dollar *pb.Type) *pb.DateType {
								var _t592 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t592 = _dollar_dollar.GetDateType()
								}
								return _t592
							}
							_t593 := _t591(msg)
							deconstruct_result113 := _t593
							if deconstruct_result113 != nil {
								unwrapped_fields114 := deconstruct_result113
								p.pretty_date_type(unwrapped_fields114)
							} else {
								_t594 := func(_dollar_dollar *pb.Type) *pb.DateTimeType {
									var _t595 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t595 = _dollar_dollar.GetDatetimeType()
									}
									return _t595
								}
								_t596 := _t594(msg)
								deconstruct_result111 := _t596
								if deconstruct_result111 != nil {
									unwrapped_fields112 := deconstruct_result111
									p.pretty_datetime_type(unwrapped_fields112)
								} else {
									_t597 := func(_dollar_dollar *pb.Type) *pb.MissingType {
										var _t598 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t598 = _dollar_dollar.GetMissingType()
										}
										return _t598
									}
									_t599 := _t597(msg)
									deconstruct_result109 := _t599
									if deconstruct_result109 != nil {
										unwrapped_fields110 := deconstruct_result109
										p.pretty_missing_type(unwrapped_fields110)
									} else {
										_t600 := func(_dollar_dollar *pb.Type) *pb.DecimalType {
											var _t601 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t601 = _dollar_dollar.GetDecimalType()
											}
											return _t601
										}
										_t602 := _t600(msg)
										deconstruct_result107 := _t602
										if deconstruct_result107 != nil {
											unwrapped_fields108 := deconstruct_result107
											p.pretty_decimal_type(unwrapped_fields108)
										} else {
											_t603 := func(_dollar_dollar *pb.Type) *pb.BooleanType {
												var _t604 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t604 = _dollar_dollar.GetBooleanType()
												}
												return _t604
											}
											_t605 := _t603(msg)
											deconstruct_result105 := _t605
											if deconstruct_result105 != nil {
												unwrapped_fields106 := deconstruct_result105
												p.pretty_boolean_type(unwrapped_fields106)
											} else {
												panic(ParseError{msg: "No matching rule for type"})
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_unspecified_type(msg *pb.UnspecifiedType) {
	_t606 := func(_dollar_dollar *pb.UnspecifiedType) *pb.UnspecifiedType {
		return _dollar_dollar
	}
	_t607 := _t606(msg)
	fields127 := _t607
	_ = fields127
	p.write("UNKNOWN")
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) {
	_t608 := func(_dollar_dollar *pb.StringType) *pb.StringType {
		return _dollar_dollar
	}
	_t609 := _t608(msg)
	fields128 := _t609
	_ = fields128
	p.write("STRING")
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) {
	_t610 := func(_dollar_dollar *pb.IntType) *pb.IntType {
		return _dollar_dollar
	}
	_t611 := _t610(msg)
	fields129 := _t611
	_ = fields129
	p.write("INT")
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) {
	_t612 := func(_dollar_dollar *pb.FloatType) *pb.FloatType {
		return _dollar_dollar
	}
	_t613 := _t612(msg)
	fields130 := _t613
	_ = fields130
	p.write("FLOAT")
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) {
	_t614 := func(_dollar_dollar *pb.UInt128Type) *pb.UInt128Type {
		return _dollar_dollar
	}
	_t615 := _t614(msg)
	fields131 := _t615
	_ = fields131
	p.write("UINT128")
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) {
	_t616 := func(_dollar_dollar *pb.Int128Type) *pb.Int128Type {
		return _dollar_dollar
	}
	_t617 := _t616(msg)
	fields132 := _t617
	_ = fields132
	p.write("INT128")
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) {
	_t618 := func(_dollar_dollar *pb.DateType) *pb.DateType {
		return _dollar_dollar
	}
	_t619 := _t618(msg)
	fields133 := _t619
	_ = fields133
	p.write("DATE")
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) {
	_t620 := func(_dollar_dollar *pb.DateTimeType) *pb.DateTimeType {
		return _dollar_dollar
	}
	_t621 := _t620(msg)
	fields134 := _t621
	_ = fields134
	p.write("DATETIME")
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) {
	_t622 := func(_dollar_dollar *pb.MissingType) *pb.MissingType {
		return _dollar_dollar
	}
	_t623 := _t622(msg)
	fields135 := _t623
	_ = fields135
	p.write("MISSING")
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) {
	_t624 := func(_dollar_dollar *pb.DecimalType) []interface{} {
		return []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
	}
	_t625 := _t624(msg)
	fields136 := _t625
	p.write("(")
	p.write("DECIMAL")
	p.indent()
	p.write(" ")
	field137 := fields136[0].(int64)
	p.write(fmt.Sprintf("%d", field137))
	p.newline()
	field138 := fields136[1].(int64)
	p.write(fmt.Sprintf("%d", field138))
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) {
	_t626 := func(_dollar_dollar *pb.BooleanType) *pb.BooleanType {
		return _dollar_dollar
	}
	_t627 := _t626(msg)
	fields139 := _t627
	_ = fields139
	p.write("BOOLEAN")
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) {
	_t628 := func(_dollar_dollar []*pb.Binding) []*pb.Binding {
		return _dollar_dollar
	}
	_t629 := _t628(msg)
	fields140 := _t629
	p.write("|")
	if !(len(fields140) == 0) {
		p.write(" ")
		for i142, elem141 := range fields140 {
			if (i142 > 0) {
				p.newline()
			}
			p.pretty_binding(elem141)
		}
	}
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) {
	_t630 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
		var _t631 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t631 = _dollar_dollar.GetConjunction()
		}
		return _t631
	}
	_t632 := _t630(msg)
	deconstruct_result167 := _t632
	if deconstruct_result167 != nil {
		unwrapped_fields168 := deconstruct_result167
		p.pretty_true(unwrapped_fields168)
	} else {
		_t633 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
			var _t634 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t634 = _dollar_dollar.GetDisjunction()
			}
			return _t634
		}
		_t635 := _t633(msg)
		deconstruct_result165 := _t635
		if deconstruct_result165 != nil {
			unwrapped_fields166 := deconstruct_result165
			p.pretty_false(unwrapped_fields166)
		} else {
			_t636 := func(_dollar_dollar *pb.Formula) *pb.Exists {
				var _t637 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t637 = _dollar_dollar.GetExists()
				}
				return _t637
			}
			_t638 := _t636(msg)
			deconstruct_result163 := _t638
			if deconstruct_result163 != nil {
				unwrapped_fields164 := deconstruct_result163
				p.pretty_exists(unwrapped_fields164)
			} else {
				_t639 := func(_dollar_dollar *pb.Formula) *pb.Reduce {
					var _t640 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t640 = _dollar_dollar.GetReduce()
					}
					return _t640
				}
				_t641 := _t639(msg)
				deconstruct_result161 := _t641
				if deconstruct_result161 != nil {
					unwrapped_fields162 := deconstruct_result161
					p.pretty_reduce(unwrapped_fields162)
				} else {
					_t642 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
						var _t643 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t643 = _dollar_dollar.GetConjunction()
						}
						return _t643
					}
					_t644 := _t642(msg)
					deconstruct_result159 := _t644
					if deconstruct_result159 != nil {
						unwrapped_fields160 := deconstruct_result159
						p.pretty_conjunction(unwrapped_fields160)
					} else {
						_t645 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
							var _t646 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t646 = _dollar_dollar.GetDisjunction()
							}
							return _t646
						}
						_t647 := _t645(msg)
						deconstruct_result157 := _t647
						if deconstruct_result157 != nil {
							unwrapped_fields158 := deconstruct_result157
							p.pretty_disjunction(unwrapped_fields158)
						} else {
							_t648 := func(_dollar_dollar *pb.Formula) *pb.Not {
								var _t649 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t649 = _dollar_dollar.GetNot()
								}
								return _t649
							}
							_t650 := _t648(msg)
							deconstruct_result155 := _t650
							if deconstruct_result155 != nil {
								unwrapped_fields156 := deconstruct_result155
								p.pretty_not(unwrapped_fields156)
							} else {
								_t651 := func(_dollar_dollar *pb.Formula) *pb.FFI {
									var _t652 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t652 = _dollar_dollar.GetFfi()
									}
									return _t652
								}
								_t653 := _t651(msg)
								deconstruct_result153 := _t653
								if deconstruct_result153 != nil {
									unwrapped_fields154 := deconstruct_result153
									p.pretty_ffi(unwrapped_fields154)
								} else {
									_t654 := func(_dollar_dollar *pb.Formula) *pb.Atom {
										var _t655 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t655 = _dollar_dollar.GetAtom()
										}
										return _t655
									}
									_t656 := _t654(msg)
									deconstruct_result151 := _t656
									if deconstruct_result151 != nil {
										unwrapped_fields152 := deconstruct_result151
										p.pretty_atom(unwrapped_fields152)
									} else {
										_t657 := func(_dollar_dollar *pb.Formula) *pb.Pragma {
											var _t658 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t658 = _dollar_dollar.GetPragma()
											}
											return _t658
										}
										_t659 := _t657(msg)
										deconstruct_result149 := _t659
										if deconstruct_result149 != nil {
											unwrapped_fields150 := deconstruct_result149
											p.pretty_pragma(unwrapped_fields150)
										} else {
											_t660 := func(_dollar_dollar *pb.Formula) *pb.Primitive {
												var _t661 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t661 = _dollar_dollar.GetPrimitive()
												}
												return _t661
											}
											_t662 := _t660(msg)
											deconstruct_result147 := _t662
											if deconstruct_result147 != nil {
												unwrapped_fields148 := deconstruct_result147
												p.pretty_primitive(unwrapped_fields148)
											} else {
												_t663 := func(_dollar_dollar *pb.Formula) *pb.RelAtom {
													var _t664 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t664 = _dollar_dollar.GetRelAtom()
													}
													return _t664
												}
												_t665 := _t663(msg)
												deconstruct_result145 := _t665
												if deconstruct_result145 != nil {
													unwrapped_fields146 := deconstruct_result145
													p.pretty_rel_atom(unwrapped_fields146)
												} else {
													_t666 := func(_dollar_dollar *pb.Formula) *pb.Cast {
														var _t667 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t667 = _dollar_dollar.GetCast()
														}
														return _t667
													}
													_t668 := _t666(msg)
													deconstruct_result143 := _t668
													if deconstruct_result143 != nil {
														unwrapped_fields144 := deconstruct_result143
														p.pretty_cast(unwrapped_fields144)
													} else {
														panic(ParseError{msg: "No matching rule for formula"})
													}
												}
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_true(msg *pb.Conjunction) {
	_t669 := func(_dollar_dollar *pb.Conjunction) *pb.Conjunction {
		return _dollar_dollar
	}
	_t670 := _t669(msg)
	fields169 := _t670
	_ = fields169
	p.write("(")
	p.write("true")
	p.write(")")
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) {
	_t671 := func(_dollar_dollar *pb.Disjunction) *pb.Disjunction {
		return _dollar_dollar
	}
	_t672 := _t671(msg)
	fields170 := _t672
	_ = fields170
	p.write("(")
	p.write("false")
	p.write(")")
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) {
	_t673 := func(_dollar_dollar *pb.Exists) []interface{} {
		_t674 := p.deconstructBindings(_dollar_dollar.GetBody())
		return []interface{}{_t674, _dollar_dollar.GetBody().GetValue()}
	}
	_t675 := _t673(msg)
	fields171 := _t675
	p.write("(")
	p.write("exists")
	p.indent()
	p.newline()
	field172 := fields171[0].([]interface{})
	p.pretty_bindings(field172)
	p.newline()
	field173 := fields171[1].(*pb.Formula)
	p.pretty_formula(field173)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) {
	_t676 := func(_dollar_dollar *pb.Reduce) []interface{} {
		return []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
	}
	_t677 := _t676(msg)
	fields174 := _t677
	p.write("(")
	p.write("reduce")
	p.indent()
	p.newline()
	field175 := fields174[0].(*pb.Abstraction)
	p.pretty_abstraction(field175)
	p.newline()
	field176 := fields174[1].(*pb.Abstraction)
	p.pretty_abstraction(field176)
	p.newline()
	field177 := fields174[2].([]*pb.Term)
	p.pretty_terms(field177)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) {
	_t678 := func(_dollar_dollar []*pb.Term) []*pb.Term {
		return _dollar_dollar
	}
	_t679 := _t678(msg)
	fields178 := _t679
	p.write("(")
	p.write("terms")
	p.indent()
	if !(len(fields178) == 0) {
		p.newline()
		for i180, elem179 := range fields178 {
			if (i180 > 0) {
				p.newline()
			}
			p.pretty_term(elem179)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) {
	_t680 := func(_dollar_dollar *pb.Term) *pb.Var {
		var _t681 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t681 = _dollar_dollar.GetVar()
		}
		return _t681
	}
	_t682 := _t680(msg)
	deconstruct_result183 := _t682
	if deconstruct_result183 != nil {
		unwrapped_fields184 := deconstruct_result183
		p.pretty_var(unwrapped_fields184)
	} else {
		_t683 := func(_dollar_dollar *pb.Term) *pb.Value {
			var _t684 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t684 = _dollar_dollar.GetConstant()
			}
			return _t684
		}
		_t685 := _t683(msg)
		deconstruct_result181 := _t685
		if deconstruct_result181 != nil {
			unwrapped_fields182 := deconstruct_result181
			p.pretty_constant(unwrapped_fields182)
		} else {
			panic(ParseError{msg: "No matching rule for term"})
		}
	}
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) {
	_t686 := func(_dollar_dollar *pb.Var) string {
		return _dollar_dollar.GetName()
	}
	_t687 := _t686(msg)
	fields185 := _t687
	p.write(fields185)
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) {
	_t688 := func(_dollar_dollar *pb.Value) *pb.Value {
		return _dollar_dollar
	}
	_t689 := _t688(msg)
	fields186 := _t689
	p.pretty_value(fields186)
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) {
	_t690 := func(_dollar_dollar *pb.Conjunction) []*pb.Formula {
		return _dollar_dollar.GetArgs()
	}
	_t691 := _t690(msg)
	fields187 := _t691
	p.write("(")
	p.write("and")
	p.indent()
	if !(len(fields187) == 0) {
		p.newline()
		for i189, elem188 := range fields187 {
			if (i189 > 0) {
				p.newline()
			}
			p.pretty_formula(elem188)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) {
	_t692 := func(_dollar_dollar *pb.Disjunction) []*pb.Formula {
		return _dollar_dollar.GetArgs()
	}
	_t693 := _t692(msg)
	fields190 := _t693
	p.write("(")
	p.write("or")
	p.indent()
	if !(len(fields190) == 0) {
		p.newline()
		for i192, elem191 := range fields190 {
			if (i192 > 0) {
				p.newline()
			}
			p.pretty_formula(elem191)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) {
	_t694 := func(_dollar_dollar *pb.Not) *pb.Formula {
		return _dollar_dollar.GetArg()
	}
	_t695 := _t694(msg)
	fields193 := _t695
	p.write("(")
	p.write("not")
	p.indent()
	p.newline()
	p.pretty_formula(fields193)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) {
	_t696 := func(_dollar_dollar *pb.FFI) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
	}
	_t697 := _t696(msg)
	fields194 := _t697
	p.write("(")
	p.write("ffi")
	p.indent()
	p.write(" ")
	field195 := fields194[0].(string)
	p.pretty_name(field195)
	p.newline()
	field196 := fields194[1].([]*pb.Abstraction)
	p.pretty_ffi_args(field196)
	p.newline()
	field197 := fields194[2].([]*pb.Term)
	p.pretty_terms(field197)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_name(msg string) {
	_t698 := func(_dollar_dollar string) string {
		return _dollar_dollar
	}
	_t699 := _t698(msg)
	fields198 := _t699
	p.write(":")
	p.write(fields198)
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) {
	_t700 := func(_dollar_dollar []*pb.Abstraction) []*pb.Abstraction {
		return _dollar_dollar
	}
	_t701 := _t700(msg)
	fields199 := _t701
	p.write("(")
	p.write("args")
	p.indent()
	if !(len(fields199) == 0) {
		p.newline()
		for i201, elem200 := range fields199 {
			if (i201 > 0) {
				p.newline()
			}
			p.pretty_abstraction(elem200)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) {
	_t702 := func(_dollar_dollar *pb.Atom) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
	}
	_t703 := _t702(msg)
	fields202 := _t703
	p.write("(")
	p.write("atom")
	p.indent()
	p.newline()
	field203 := fields202[0].(*pb.RelationId)
	p.pretty_relation_id(field203)
	field204 := fields202[1].([]*pb.Term)
	if !(len(field204) == 0) {
		p.newline()
		for i206, elem205 := range field204 {
			if (i206 > 0) {
				p.newline()
			}
			p.pretty_term(elem205)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) {
	_t704 := func(_dollar_dollar *pb.Pragma) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
	}
	_t705 := _t704(msg)
	fields207 := _t705
	p.write("(")
	p.write("pragma")
	p.indent()
	p.write(" ")
	field208 := fields207[0].(string)
	p.pretty_name(field208)
	field209 := fields207[1].([]*pb.Term)
	if !(len(field209) == 0) {
		p.newline()
		for i211, elem210 := range field209 {
			if (i211 > 0) {
				p.newline()
			}
			p.pretty_term(elem210)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) {
	_t706 := func(_dollar_dollar *pb.Primitive) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
	}
	_t707 := _t706(msg)
	fields212 := _t707
	p.write("(")
	p.write("primitive")
	p.indent()
	p.write(" ")
	field213 := fields212[0].(string)
	p.pretty_name(field213)
	field214 := fields212[1].([]*pb.RelTerm)
	if !(len(field214) == 0) {
		p.newline()
		for i216, elem215 := range field214 {
			if (i216 > 0) {
				p.newline()
			}
			p.pretty_rel_term(elem215)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_eq(msg *pb.Primitive) {
	_t708 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t709 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t709 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t709
	}
	_t710 := _t708(msg)
	fields217 := _t710
	unwrapped_fields218 := fields217
	p.write("(")
	p.write("=")
	p.indent()
	p.newline()
	field219 := unwrapped_fields218[0].(*pb.Term)
	p.pretty_term(field219)
	p.newline()
	field220 := unwrapped_fields218[1].(*pb.Term)
	p.pretty_term(field220)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) {
	_t711 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t712 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t712 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t712
	}
	_t713 := _t711(msg)
	fields221 := _t713
	unwrapped_fields222 := fields221
	p.write("(")
	p.write("<")
	p.indent()
	p.newline()
	field223 := unwrapped_fields222[0].(*pb.Term)
	p.pretty_term(field223)
	p.newline()
	field224 := unwrapped_fields222[1].(*pb.Term)
	p.pretty_term(field224)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) {
	_t714 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t715 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t715 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t715
	}
	_t716 := _t714(msg)
	fields225 := _t716
	unwrapped_fields226 := fields225
	p.write("(")
	p.write("<=")
	p.indent()
	p.newline()
	field227 := unwrapped_fields226[0].(*pb.Term)
	p.pretty_term(field227)
	p.newline()
	field228 := unwrapped_fields226[1].(*pb.Term)
	p.pretty_term(field228)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) {
	_t717 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t718 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t718 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t718
	}
	_t719 := _t717(msg)
	fields229 := _t719
	unwrapped_fields230 := fields229
	p.write("(")
	p.write(">")
	p.indent()
	p.newline()
	field231 := unwrapped_fields230[0].(*pb.Term)
	p.pretty_term(field231)
	p.newline()
	field232 := unwrapped_fields230[1].(*pb.Term)
	p.pretty_term(field232)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) {
	_t720 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t721 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t721 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t721
	}
	_t722 := _t720(msg)
	fields233 := _t722
	unwrapped_fields234 := fields233
	p.write("(")
	p.write(">=")
	p.indent()
	p.newline()
	field235 := unwrapped_fields234[0].(*pb.Term)
	p.pretty_term(field235)
	p.newline()
	field236 := unwrapped_fields234[1].(*pb.Term)
	p.pretty_term(field236)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) {
	_t723 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t724 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t724 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		return _t724
	}
	_t725 := _t723(msg)
	fields237 := _t725
	unwrapped_fields238 := fields237
	p.write("(")
	p.write("+")
	p.indent()
	p.newline()
	field239 := unwrapped_fields238[0].(*pb.Term)
	p.pretty_term(field239)
	p.newline()
	field240 := unwrapped_fields238[1].(*pb.Term)
	p.pretty_term(field240)
	p.newline()
	field241 := unwrapped_fields238[2].(*pb.Term)
	p.pretty_term(field241)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) {
	_t726 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t727 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t727 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		return _t727
	}
	_t728 := _t726(msg)
	fields242 := _t728
	unwrapped_fields243 := fields242
	p.write("(")
	p.write("-")
	p.indent()
	p.newline()
	field244 := unwrapped_fields243[0].(*pb.Term)
	p.pretty_term(field244)
	p.newline()
	field245 := unwrapped_fields243[1].(*pb.Term)
	p.pretty_term(field245)
	p.newline()
	field246 := unwrapped_fields243[2].(*pb.Term)
	p.pretty_term(field246)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) {
	_t729 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t730 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t730 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		return _t730
	}
	_t731 := _t729(msg)
	fields247 := _t731
	unwrapped_fields248 := fields247
	p.write("(")
	p.write("*")
	p.indent()
	p.newline()
	field249 := unwrapped_fields248[0].(*pb.Term)
	p.pretty_term(field249)
	p.newline()
	field250 := unwrapped_fields248[1].(*pb.Term)
	p.pretty_term(field250)
	p.newline()
	field251 := unwrapped_fields248[2].(*pb.Term)
	p.pretty_term(field251)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) {
	_t732 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t733 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t733 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		return _t733
	}
	_t734 := _t732(msg)
	fields252 := _t734
	unwrapped_fields253 := fields252
	p.write("(")
	p.write("/")
	p.indent()
	p.newline()
	field254 := unwrapped_fields253[0].(*pb.Term)
	p.pretty_term(field254)
	p.newline()
	field255 := unwrapped_fields253[1].(*pb.Term)
	p.pretty_term(field255)
	p.newline()
	field256 := unwrapped_fields253[2].(*pb.Term)
	p.pretty_term(field256)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) {
	_t735 := func(_dollar_dollar *pb.RelTerm) *pb.Value {
		var _t736 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t736 = _dollar_dollar.GetSpecializedValue()
		}
		return _t736
	}
	_t737 := _t735(msg)
	deconstruct_result259 := _t737
	if deconstruct_result259 != nil {
		unwrapped_fields260 := deconstruct_result259
		p.pretty_specialized_value(unwrapped_fields260)
	} else {
		_t738 := func(_dollar_dollar *pb.RelTerm) *pb.Term {
			var _t739 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t739 = _dollar_dollar.GetTerm()
			}
			return _t739
		}
		_t740 := _t738(msg)
		deconstruct_result257 := _t740
		if deconstruct_result257 != nil {
			unwrapped_fields258 := deconstruct_result257
			p.pretty_term(unwrapped_fields258)
		} else {
			panic(ParseError{msg: "No matching rule for rel_term"})
		}
	}
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) {
	_t741 := func(_dollar_dollar *pb.Value) *pb.Value {
		return _dollar_dollar
	}
	_t742 := _t741(msg)
	fields261 := _t742
	p.write("#")
	p.pretty_value(fields261)
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) {
	_t743 := func(_dollar_dollar *pb.RelAtom) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
	}
	_t744 := _t743(msg)
	fields262 := _t744
	p.write("(")
	p.write("relatom")
	p.indent()
	p.write(" ")
	field263 := fields262[0].(string)
	p.pretty_name(field263)
	field264 := fields262[1].([]*pb.RelTerm)
	if !(len(field264) == 0) {
		p.newline()
		for i266, elem265 := range field264 {
			if (i266 > 0) {
				p.newline()
			}
			p.pretty_rel_term(elem265)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) {
	_t745 := func(_dollar_dollar *pb.Cast) []interface{} {
		return []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
	}
	_t746 := _t745(msg)
	fields267 := _t746
	p.write("(")
	p.write("cast")
	p.indent()
	p.newline()
	field268 := fields267[0].(*pb.Term)
	p.pretty_term(field268)
	p.newline()
	field269 := fields267[1].(*pb.Term)
	p.pretty_term(field269)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) {
	_t747 := func(_dollar_dollar []*pb.Attribute) []*pb.Attribute {
		return _dollar_dollar
	}
	_t748 := _t747(msg)
	fields270 := _t748
	p.write("(")
	p.write("attrs")
	p.indent()
	if !(len(fields270) == 0) {
		p.newline()
		for i272, elem271 := range fields270 {
			if (i272 > 0) {
				p.newline()
			}
			p.pretty_attribute(elem271)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) {
	_t749 := func(_dollar_dollar *pb.Attribute) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
	}
	_t750 := _t749(msg)
	fields273 := _t750
	p.write("(")
	p.write("attribute")
	p.indent()
	p.write(" ")
	field274 := fields273[0].(string)
	p.pretty_name(field274)
	field275 := fields273[1].([]*pb.Value)
	if !(len(field275) == 0) {
		p.newline()
		for i277, elem276 := range field275 {
			if (i277 > 0) {
				p.newline()
			}
			p.pretty_value(elem276)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) {
	_t751 := func(_dollar_dollar *pb.Algorithm) []interface{} {
		return []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
	}
	_t752 := _t751(msg)
	fields278 := _t752
	p.write("(")
	p.write("algorithm")
	p.indent()
	field279 := fields278[0].([]*pb.RelationId)
	if !(len(field279) == 0) {
		p.newline()
		for i281, elem280 := range field279 {
			if (i281 > 0) {
				p.newline()
			}
			p.pretty_relation_id(elem280)
		}
	}
	p.newline()
	field282 := fields278[1].(*pb.Script)
	p.pretty_script(field282)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) {
	_t753 := func(_dollar_dollar *pb.Script) []*pb.Construct {
		return _dollar_dollar.GetConstructs()
	}
	_t754 := _t753(msg)
	fields283 := _t754
	p.write("(")
	p.write("script")
	p.indent()
	if !(len(fields283) == 0) {
		p.newline()
		for i285, elem284 := range fields283 {
			if (i285 > 0) {
				p.newline()
			}
			p.pretty_construct(elem284)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) {
	_t755 := func(_dollar_dollar *pb.Construct) *pb.Loop {
		var _t756 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t756 = _dollar_dollar.GetLoop()
		}
		return _t756
	}
	_t757 := _t755(msg)
	deconstruct_result288 := _t757
	if deconstruct_result288 != nil {
		unwrapped_fields289 := deconstruct_result288
		p.pretty_loop(unwrapped_fields289)
	} else {
		_t758 := func(_dollar_dollar *pb.Construct) *pb.Instruction {
			var _t759 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t759 = _dollar_dollar.GetInstruction()
			}
			return _t759
		}
		_t760 := _t758(msg)
		deconstruct_result286 := _t760
		if deconstruct_result286 != nil {
			unwrapped_fields287 := deconstruct_result286
			p.pretty_instruction(unwrapped_fields287)
		} else {
			panic(ParseError{msg: "No matching rule for construct"})
		}
	}
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) {
	_t761 := func(_dollar_dollar *pb.Loop) []interface{} {
		return []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
	}
	_t762 := _t761(msg)
	fields290 := _t762
	p.write("(")
	p.write("loop")
	p.indent()
	p.newline()
	field291 := fields290[0].([]*pb.Instruction)
	p.pretty_init(field291)
	p.newline()
	field292 := fields290[1].(*pb.Script)
	p.pretty_script(field292)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) {
	_t763 := func(_dollar_dollar []*pb.Instruction) []*pb.Instruction {
		return _dollar_dollar
	}
	_t764 := _t763(msg)
	fields293 := _t764
	p.write("(")
	p.write("init")
	p.indent()
	if !(len(fields293) == 0) {
		p.newline()
		for i295, elem294 := range fields293 {
			if (i295 > 0) {
				p.newline()
			}
			p.pretty_instruction(elem294)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) {
	_t765 := func(_dollar_dollar *pb.Instruction) *pb.Assign {
		var _t766 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t766 = _dollar_dollar.GetAssign()
		}
		return _t766
	}
	_t767 := _t765(msg)
	deconstruct_result304 := _t767
	if deconstruct_result304 != nil {
		unwrapped_fields305 := deconstruct_result304
		p.pretty_assign(unwrapped_fields305)
	} else {
		_t768 := func(_dollar_dollar *pb.Instruction) *pb.Upsert {
			var _t769 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t769 = _dollar_dollar.GetUpsert()
			}
			return _t769
		}
		_t770 := _t768(msg)
		deconstruct_result302 := _t770
		if deconstruct_result302 != nil {
			unwrapped_fields303 := deconstruct_result302
			p.pretty_upsert(unwrapped_fields303)
		} else {
			_t771 := func(_dollar_dollar *pb.Instruction) *pb.Break {
				var _t772 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t772 = _dollar_dollar.GetBreak()
				}
				return _t772
			}
			_t773 := _t771(msg)
			deconstruct_result300 := _t773
			if deconstruct_result300 != nil {
				unwrapped_fields301 := deconstruct_result300
				p.pretty_break(unwrapped_fields301)
			} else {
				_t774 := func(_dollar_dollar *pb.Instruction) *pb.MonoidDef {
					var _t775 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t775 = _dollar_dollar.GetMonoidDef()
					}
					return _t775
				}
				_t776 := _t774(msg)
				deconstruct_result298 := _t776
				if deconstruct_result298 != nil {
					unwrapped_fields299 := deconstruct_result298
					p.pretty_monoid_def(unwrapped_fields299)
				} else {
					_t777 := func(_dollar_dollar *pb.Instruction) *pb.MonusDef {
						var _t778 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t778 = _dollar_dollar.GetMonusDef()
						}
						return _t778
					}
					_t779 := _t777(msg)
					deconstruct_result296 := _t779
					if deconstruct_result296 != nil {
						unwrapped_fields297 := deconstruct_result296
						p.pretty_monus_def(unwrapped_fields297)
					} else {
						panic(ParseError{msg: "No matching rule for instruction"})
					}
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_assign(msg *pb.Assign) {
	_t780 := func(_dollar_dollar *pb.Assign) []interface{} {
		var _t781 interface{}
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t781 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t781}
	}
	_t782 := _t780(msg)
	fields306 := _t782
	p.write("(")
	p.write("assign")
	p.indent()
	p.newline()
	field307 := fields306[0].(*pb.RelationId)
	p.pretty_relation_id(field307)
	p.newline()
	field308 := fields306[1].(*pb.Abstraction)
	p.pretty_abstraction(field308)
	_t783 := fields306[2]
	var _t784 []*pb.Attribute
	if _t783 != nil {
		_t784 = _t783.([]*pb.Attribute)
	}
	field309 := _t784
	if field309 != nil {
		p.newline()
		opt_val310 := field309
		p.pretty_attrs(opt_val310)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) {
	_t785 := func(_dollar_dollar *pb.Upsert) []interface{} {
		var _t786 interface{}
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t786 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t786}
	}
	_t787 := _t785(msg)
	fields311 := _t787
	p.write("(")
	p.write("upsert")
	p.indent()
	p.newline()
	field312 := fields311[0].(*pb.RelationId)
	p.pretty_relation_id(field312)
	p.newline()
	field313 := fields311[1].([]interface{})
	p.pretty_abstraction_with_arity(field313)
	_t788 := fields311[2]
	var _t789 []*pb.Attribute
	if _t788 != nil {
		_t789 = _t788.([]*pb.Attribute)
	}
	field314 := _t789
	if field314 != nil {
		p.newline()
		opt_val315 := field314
		p.pretty_attrs(opt_val315)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) {
	_t790 := func(_dollar_dollar []interface{}) []interface{} {
		_t791 := p.deconstructBindingsWithArity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		return []interface{}{_t791, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
	}
	_t792 := _t790(msg)
	fields316 := _t792
	p.write("(")
	field317 := fields316[0].([]interface{})
	p.pretty_bindings(field317)
	p.write(" ")
	field318 := fields316[1].(*pb.Formula)
	p.pretty_formula(field318)
	p.write(")")
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) {
	_t793 := func(_dollar_dollar *pb.Break) []interface{} {
		var _t794 interface{}
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t794 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t794}
	}
	_t795 := _t793(msg)
	fields319 := _t795
	p.write("(")
	p.write("break")
	p.indent()
	p.newline()
	field320 := fields319[0].(*pb.RelationId)
	p.pretty_relation_id(field320)
	p.newline()
	field321 := fields319[1].(*pb.Abstraction)
	p.pretty_abstraction(field321)
	_t796 := fields319[2]
	var _t797 []*pb.Attribute
	if _t796 != nil {
		_t797 = _t796.([]*pb.Attribute)
	}
	field322 := _t797
	if field322 != nil {
		p.newline()
		opt_val323 := field322
		p.pretty_attrs(opt_val323)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) {
	_t798 := func(_dollar_dollar *pb.MonoidDef) []interface{} {
		var _t799 interface{}
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t799 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t799}
	}
	_t800 := _t798(msg)
	fields324 := _t800
	p.write("(")
	p.write("monoid")
	p.indent()
	p.newline()
	field325 := fields324[0].(*pb.Monoid)
	p.pretty_monoid(field325)
	p.newline()
	field326 := fields324[1].(*pb.RelationId)
	p.pretty_relation_id(field326)
	p.newline()
	field327 := fields324[2].([]interface{})
	p.pretty_abstraction_with_arity(field327)
	_t801 := fields324[3]
	var _t802 []*pb.Attribute
	if _t801 != nil {
		_t802 = _t801.([]*pb.Attribute)
	}
	field328 := _t802
	if field328 != nil {
		p.newline()
		opt_val329 := field328
		p.pretty_attrs(opt_val329)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) {
	_t803 := func(_dollar_dollar *pb.Monoid) *pb.OrMonoid {
		var _t804 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t804 = _dollar_dollar.GetOrMonoid()
		}
		return _t804
	}
	_t805 := _t803(msg)
	deconstruct_result336 := _t805
	if deconstruct_result336 != nil {
		unwrapped_fields337 := deconstruct_result336
		p.pretty_or_monoid(unwrapped_fields337)
	} else {
		_t806 := func(_dollar_dollar *pb.Monoid) *pb.MinMonoid {
			var _t807 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t807 = _dollar_dollar.GetMinMonoid()
			}
			return _t807
		}
		_t808 := _t806(msg)
		deconstruct_result334 := _t808
		if deconstruct_result334 != nil {
			unwrapped_fields335 := deconstruct_result334
			p.pretty_min_monoid(unwrapped_fields335)
		} else {
			_t809 := func(_dollar_dollar *pb.Monoid) *pb.MaxMonoid {
				var _t810 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t810 = _dollar_dollar.GetMaxMonoid()
				}
				return _t810
			}
			_t811 := _t809(msg)
			deconstruct_result332 := _t811
			if deconstruct_result332 != nil {
				unwrapped_fields333 := deconstruct_result332
				p.pretty_max_monoid(unwrapped_fields333)
			} else {
				_t812 := func(_dollar_dollar *pb.Monoid) *pb.SumMonoid {
					var _t813 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t813 = _dollar_dollar.GetSumMonoid()
					}
					return _t813
				}
				_t814 := _t812(msg)
				deconstruct_result330 := _t814
				if deconstruct_result330 != nil {
					unwrapped_fields331 := deconstruct_result330
					p.pretty_sum_monoid(unwrapped_fields331)
				} else {
					panic(ParseError{msg: "No matching rule for monoid"})
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_or_monoid(msg *pb.OrMonoid) {
	_t815 := func(_dollar_dollar *pb.OrMonoid) *pb.OrMonoid {
		return _dollar_dollar
	}
	_t816 := _t815(msg)
	fields338 := _t816
	_ = fields338
	p.write("(")
	p.write("or")
	p.write(")")
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) {
	_t817 := func(_dollar_dollar *pb.MinMonoid) *pb.Type {
		return _dollar_dollar.GetType()
	}
	_t818 := _t817(msg)
	fields339 := _t818
	p.write("(")
	p.write("min")
	p.indent()
	p.newline()
	p.pretty_type(fields339)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) {
	_t819 := func(_dollar_dollar *pb.MaxMonoid) *pb.Type {
		return _dollar_dollar.GetType()
	}
	_t820 := _t819(msg)
	fields340 := _t820
	p.write("(")
	p.write("max")
	p.indent()
	p.newline()
	p.pretty_type(fields340)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) {
	_t821 := func(_dollar_dollar *pb.SumMonoid) *pb.Type {
		return _dollar_dollar.GetType()
	}
	_t822 := _t821(msg)
	fields341 := _t822
	p.write("(")
	p.write("sum")
	p.indent()
	p.newline()
	p.pretty_type(fields341)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) {
	_t823 := func(_dollar_dollar *pb.MonusDef) []interface{} {
		var _t824 interface{}
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t824 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t824}
	}
	_t825 := _t823(msg)
	fields342 := _t825
	p.write("(")
	p.write("monus")
	p.indent()
	p.newline()
	field343 := fields342[0].(*pb.Monoid)
	p.pretty_monoid(field343)
	p.newline()
	field344 := fields342[1].(*pb.RelationId)
	p.pretty_relation_id(field344)
	p.newline()
	field345 := fields342[2].([]interface{})
	p.pretty_abstraction_with_arity(field345)
	_t826 := fields342[3]
	var _t827 []*pb.Attribute
	if _t826 != nil {
		_t827 = _t826.([]*pb.Attribute)
	}
	field346 := _t827
	if field346 != nil {
		p.newline()
		opt_val347 := field346
		p.pretty_attrs(opt_val347)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) {
	_t828 := func(_dollar_dollar *pb.Constraint) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
	}
	_t829 := _t828(msg)
	fields348 := _t829
	p.write("(")
	p.write("functional_dependency")
	p.indent()
	p.newline()
	field349 := fields348[0].(*pb.RelationId)
	p.pretty_relation_id(field349)
	p.newline()
	field350 := fields348[1].(*pb.Abstraction)
	p.pretty_abstraction(field350)
	p.newline()
	field351 := fields348[2].([]*pb.Var)
	p.pretty_functional_dependency_keys(field351)
	p.newline()
	field352 := fields348[3].([]*pb.Var)
	p.pretty_functional_dependency_values(field352)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) {
	_t830 := func(_dollar_dollar []*pb.Var) []*pb.Var {
		return _dollar_dollar
	}
	_t831 := _t830(msg)
	fields353 := _t831
	p.write("(")
	p.write("keys")
	p.indent()
	if !(len(fields353) == 0) {
		p.newline()
		for i355, elem354 := range fields353 {
			if (i355 > 0) {
				p.newline()
			}
			p.pretty_var(elem354)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) {
	_t832 := func(_dollar_dollar []*pb.Var) []*pb.Var {
		return _dollar_dollar
	}
	_t833 := _t832(msg)
	fields356 := _t833
	p.write("(")
	p.write("values")
	p.indent()
	if !(len(fields356) == 0) {
		p.newline()
		for i358, elem357 := range fields356 {
			if (i358 > 0) {
				p.newline()
			}
			p.pretty_var(elem357)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) {
	_t834 := func(_dollar_dollar *pb.Data) *pb.RelEDB {
		var _t835 *pb.RelEDB
		if hasProtoField(_dollar_dollar, "rel_edb") {
			_t835 = _dollar_dollar.GetRelEdb()
		}
		return _t835
	}
	_t836 := _t834(msg)
	deconstruct_result363 := _t836
	if deconstruct_result363 != nil {
		unwrapped_fields364 := deconstruct_result363
		p.pretty_rel_edb(unwrapped_fields364)
	} else {
		_t837 := func(_dollar_dollar *pb.Data) *pb.BeTreeRelation {
			var _t838 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t838 = _dollar_dollar.GetBetreeRelation()
			}
			return _t838
		}
		_t839 := _t837(msg)
		deconstruct_result361 := _t839
		if deconstruct_result361 != nil {
			unwrapped_fields362 := deconstruct_result361
			p.pretty_betree_relation(unwrapped_fields362)
		} else {
			_t840 := func(_dollar_dollar *pb.Data) *pb.CSVData {
				var _t841 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t841 = _dollar_dollar.GetCsvData()
				}
				return _t841
			}
			_t842 := _t840(msg)
			deconstruct_result359 := _t842
			if deconstruct_result359 != nil {
				unwrapped_fields360 := deconstruct_result359
				p.pretty_csv_data(unwrapped_fields360)
			} else {
				panic(ParseError{msg: "No matching rule for data"})
			}
		}
	}
}

func (p *PrettyPrinter) pretty_rel_edb(msg *pb.RelEDB) {
	_t843 := func(_dollar_dollar *pb.RelEDB) []interface{} {
		return []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
	}
	_t844 := _t843(msg)
	fields365 := _t844
	p.write("(")
	p.write("rel_edb")
	p.indent()
	p.newline()
	field366 := fields365[0].(*pb.RelationId)
	p.pretty_relation_id(field366)
	p.newline()
	field367 := fields365[1].([]string)
	p.pretty_rel_edb_path(field367)
	p.newline()
	field368 := fields365[2].([]*pb.Type)
	p.pretty_rel_edb_types(field368)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_rel_edb_path(msg []string) {
	_t845 := func(_dollar_dollar []string) []string {
		return _dollar_dollar
	}
	_t846 := _t845(msg)
	fields369 := _t846
	p.write("[")
	for i371, elem370 := range fields369 {
		if (i371 > 0) {
			p.newline()
		}
		p.write(p.formatStringValue(elem370))
	}
	p.write("]")
}

func (p *PrettyPrinter) pretty_rel_edb_types(msg []*pb.Type) {
	_t847 := func(_dollar_dollar []*pb.Type) []*pb.Type {
		return _dollar_dollar
	}
	_t848 := _t847(msg)
	fields372 := _t848
	p.write("[")
	for i374, elem373 := range fields372 {
		if (i374 > 0) {
			p.newline()
		}
		p.pretty_type(elem373)
	}
	p.write("]")
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) {
	_t849 := func(_dollar_dollar *pb.BeTreeRelation) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
	}
	_t850 := _t849(msg)
	fields375 := _t850
	p.write("(")
	p.write("betree_relation")
	p.indent()
	p.newline()
	field376 := fields375[0].(*pb.RelationId)
	p.pretty_relation_id(field376)
	p.newline()
	field377 := fields375[1].(*pb.BeTreeInfo)
	p.pretty_betree_info(field377)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) {
	_t851 := func(_dollar_dollar *pb.BeTreeInfo) []interface{} {
		_t852 := p.deconstructBetreeInfoConfig(_dollar_dollar)
		return []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t852}
	}
	_t853 := _t851(msg)
	fields378 := _t853
	p.write("(")
	p.write("betree_info")
	p.indent()
	p.newline()
	field379 := fields378[0].([]*pb.Type)
	p.pretty_betree_info_key_types(field379)
	p.newline()
	field380 := fields378[1].([]*pb.Type)
	p.pretty_betree_info_value_types(field380)
	p.newline()
	field381 := fields378[2].([][]interface{})
	p.pretty_config_dict(field381)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) {
	_t854 := func(_dollar_dollar []*pb.Type) []*pb.Type {
		return _dollar_dollar
	}
	_t855 := _t854(msg)
	fields382 := _t855
	p.write("(")
	p.write("key_types")
	p.indent()
	if !(len(fields382) == 0) {
		p.newline()
		for i384, elem383 := range fields382 {
			if (i384 > 0) {
				p.newline()
			}
			p.pretty_type(elem383)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) {
	_t856 := func(_dollar_dollar []*pb.Type) []*pb.Type {
		return _dollar_dollar
	}
	_t857 := _t856(msg)
	fields385 := _t857
	p.write("(")
	p.write("value_types")
	p.indent()
	if !(len(fields385) == 0) {
		p.newline()
		for i387, elem386 := range fields385 {
			if (i387 > 0) {
				p.newline()
			}
			p.pretty_type(elem386)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) {
	_t858 := func(_dollar_dollar *pb.CSVData) []interface{} {
		return []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
	}
	_t859 := _t858(msg)
	fields388 := _t859
	p.write("(")
	p.write("csv_data")
	p.indent()
	p.newline()
	field389 := fields388[0].(*pb.CSVLocator)
	p.pretty_csvlocator(field389)
	p.newline()
	field390 := fields388[1].(*pb.CSVConfig)
	p.pretty_csv_config(field390)
	p.newline()
	field391 := fields388[2].([]*pb.CSVColumn)
	p.pretty_csv_columns(field391)
	p.write(" ")
	field392 := fields388[3].(string)
	p.pretty_csv_asof(field392)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) {
	_t860 := func(_dollar_dollar *pb.CSVLocator) []interface{} {
		var _t861 interface{}
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t861 = _dollar_dollar.GetPaths()
		}
		var _t862 interface{}
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t862 = string(_dollar_dollar.GetInlineData())
		}
		return []interface{}{_t861, _t862}
	}
	_t863 := _t860(msg)
	fields393 := _t863
	p.write("(")
	p.write("csv_locator")
	p.indent()
	_t864 := fields393[0]
	var _t865 []string
	if _t864 != nil {
		_t865 = _t864.([]string)
	}
	field394 := _t865
	if field394 != nil {
		p.newline()
		opt_val395 := field394
		p.pretty_csv_locator_paths(opt_val395)
	}
	_t866 := fields393[1]
	var _t867 *string
	if _t866 != nil {
		if _t868, ok := _t866.(*string); ok {
			_t867 = _t868
		} else {
			_t869 := _t866.(string)
			_t867 = &_t869
		}
	}
	field396 := _t867
	if field396 != nil {
		p.newline()
		opt_val397 := *field396
		p.pretty_csv_locator_inline_data(opt_val397)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) {
	_t870 := func(_dollar_dollar []string) []string {
		return _dollar_dollar
	}
	_t871 := _t870(msg)
	fields398 := _t871
	p.write("(")
	p.write("paths")
	p.indent()
	if !(len(fields398) == 0) {
		p.newline()
		for i400, elem399 := range fields398 {
			if (i400 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem399))
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) {
	_t872 := func(_dollar_dollar string) string {
		return _dollar_dollar
	}
	_t873 := _t872(msg)
	fields401 := _t873
	p.write("(")
	p.write("inline_data")
	p.indent()
	p.write(" ")
	p.write(p.formatStringValue(fields401))
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) {
	_t874 := func(_dollar_dollar *pb.CSVConfig) [][]interface{} {
		_t875 := p.deconstructCsvConfig(_dollar_dollar)
		return _t875
	}
	_t876 := _t874(msg)
	fields402 := _t876
	p.write("(")
	p.write("csv_config")
	p.indent()
	p.newline()
	p.pretty_config_dict(fields402)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_columns(msg []*pb.CSVColumn) {
	_t877 := func(_dollar_dollar []*pb.CSVColumn) []*pb.CSVColumn {
		return _dollar_dollar
	}
	_t878 := _t877(msg)
	fields403 := _t878
	p.write("(")
	p.write("columns")
	p.indent()
	if !(len(fields403) == 0) {
		p.newline()
		for i405, elem404 := range fields403 {
			if (i405 > 0) {
				p.newline()
			}
			p.pretty_csv_column(elem404)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_column(msg *pb.CSVColumn) {
	_t879 := func(_dollar_dollar *pb.CSVColumn) []interface{} {
		return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetTargetId(), _dollar_dollar.GetTypes()}
	}
	_t880 := _t879(msg)
	fields406 := _t880
	p.write("(")
	p.write("column")
	p.indent()
	p.write(" ")
	field407 := fields406[0].(string)
	p.write(p.formatStringValue(field407))
	p.newline()
	field408 := fields406[1].(*pb.RelationId)
	p.pretty_relation_id(field408)
	p.newline()
	p.write("[")
	field409 := fields406[2].([]*pb.Type)
	for i411, elem410 := range field409 {
		if (i411 > 0) {
			p.newline()
		}
		p.pretty_type(elem410)
	}
	p.write("]")
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) {
	_t881 := func(_dollar_dollar string) string {
		return _dollar_dollar
	}
	_t882 := _t881(msg)
	fields412 := _t882
	p.write("(")
	p.write("asof")
	p.indent()
	p.write(" ")
	p.write(p.formatStringValue(fields412))
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) {
	_t883 := func(_dollar_dollar *pb.Undefine) *pb.FragmentId {
		return _dollar_dollar.GetFragmentId()
	}
	_t884 := _t883(msg)
	fields413 := _t884
	p.write("(")
	p.write("undefine")
	p.indent()
	p.write(" ")
	p.pretty_fragment_id(fields413)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) {
	_t885 := func(_dollar_dollar *pb.Context) []*pb.RelationId {
		return _dollar_dollar.GetRelations()
	}
	_t886 := _t885(msg)
	fields414 := _t886
	p.write("(")
	p.write("context")
	p.indent()
	if !(len(fields414) == 0) {
		p.newline()
		for i416, elem415 := range fields414 {
			if (i416 > 0) {
				p.newline()
			}
			p.pretty_relation_id(elem415)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) {
	_t887 := func(_dollar_dollar []*pb.Read) []*pb.Read {
		return _dollar_dollar
	}
	_t888 := _t887(msg)
	fields417 := _t888
	p.write("(")
	p.write("reads")
	p.indent()
	if !(len(fields417) == 0) {
		p.newline()
		for i419, elem418 := range fields417 {
			if (i419 > 0) {
				p.newline()
			}
			p.pretty_read(elem418)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) {
	_t889 := func(_dollar_dollar *pb.Read) *pb.Demand {
		var _t890 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t890 = _dollar_dollar.GetDemand()
		}
		return _t890
	}
	_t891 := _t889(msg)
	deconstruct_result428 := _t891
	if deconstruct_result428 != nil {
		unwrapped_fields429 := deconstruct_result428
		p.pretty_demand(unwrapped_fields429)
	} else {
		_t892 := func(_dollar_dollar *pb.Read) *pb.Output {
			var _t893 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t893 = _dollar_dollar.GetOutput()
			}
			return _t893
		}
		_t894 := _t892(msg)
		deconstruct_result426 := _t894
		if deconstruct_result426 != nil {
			unwrapped_fields427 := deconstruct_result426
			p.pretty_output(unwrapped_fields427)
		} else {
			_t895 := func(_dollar_dollar *pb.Read) *pb.WhatIf {
				var _t896 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t896 = _dollar_dollar.GetWhatIf()
				}
				return _t896
			}
			_t897 := _t895(msg)
			deconstruct_result424 := _t897
			if deconstruct_result424 != nil {
				unwrapped_fields425 := deconstruct_result424
				p.pretty_what_if(unwrapped_fields425)
			} else {
				_t898 := func(_dollar_dollar *pb.Read) *pb.Abort {
					var _t899 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t899 = _dollar_dollar.GetAbort()
					}
					return _t899
				}
				_t900 := _t898(msg)
				deconstruct_result422 := _t900
				if deconstruct_result422 != nil {
					unwrapped_fields423 := deconstruct_result422
					p.pretty_abort(unwrapped_fields423)
				} else {
					_t901 := func(_dollar_dollar *pb.Read) *pb.Export {
						var _t902 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t902 = _dollar_dollar.GetExport()
						}
						return _t902
					}
					_t903 := _t901(msg)
					deconstruct_result420 := _t903
					if deconstruct_result420 != nil {
						unwrapped_fields421 := deconstruct_result420
						p.pretty_export(unwrapped_fields421)
					} else {
						panic(ParseError{msg: "No matching rule for read"})
					}
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_demand(msg *pb.Demand) {
	_t904 := func(_dollar_dollar *pb.Demand) *pb.RelationId {
		return _dollar_dollar.GetRelationId()
	}
	_t905 := _t904(msg)
	fields430 := _t905
	p.write("(")
	p.write("demand")
	p.indent()
	p.newline()
	p.pretty_relation_id(fields430)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) {
	_t906 := func(_dollar_dollar *pb.Output) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
	}
	_t907 := _t906(msg)
	fields431 := _t907
	p.write("(")
	p.write("output")
	p.indent()
	p.write(" ")
	field432 := fields431[0].(string)
	p.pretty_name(field432)
	p.newline()
	field433 := fields431[1].(*pb.RelationId)
	p.pretty_relation_id(field433)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) {
	_t908 := func(_dollar_dollar *pb.WhatIf) []interface{} {
		return []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
	}
	_t909 := _t908(msg)
	fields434 := _t909
	p.write("(")
	p.write("what_if")
	p.indent()
	p.write(" ")
	field435 := fields434[0].(string)
	p.pretty_name(field435)
	p.newline()
	field436 := fields434[1].(*pb.Epoch)
	p.pretty_epoch(field436)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) {
	_t910 := func(_dollar_dollar *pb.Abort) []interface{} {
		var _t911 interface{}
		if _dollar_dollar.GetName() != "abort" {
			_t911 = _dollar_dollar.GetName()
		}
		return []interface{}{_t911, _dollar_dollar.GetRelationId()}
	}
	_t912 := _t910(msg)
	fields437 := _t912
	p.write("(")
	p.write("abort")
	p.indent()
	_t913 := fields437[0]
	var _t914 *string
	if _t913 != nil {
		if _t915, ok := _t913.(*string); ok {
			_t914 = _t915
		} else {
			_t916 := _t913.(string)
			_t914 = &_t916
		}
	}
	field438 := _t914
	if field438 != nil {
		p.newline()
		opt_val439 := *field438
		p.pretty_name(opt_val439)
	}
	p.newline()
	field440 := fields437[1].(*pb.RelationId)
	p.pretty_relation_id(field440)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) {
	_t917 := func(_dollar_dollar *pb.Export) *pb.ExportCSVConfig {
		return _dollar_dollar.GetCsvConfig()
	}
	_t918 := _t917(msg)
	fields441 := _t918
	p.write("(")
	p.write("export")
	p.indent()
	p.newline()
	p.pretty_export_csv_config(fields441)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) {
	_t919 := func(_dollar_dollar *pb.ExportCSVConfig) []interface{} {
		_t920 := p.deconstructExportCsvConfig(_dollar_dollar)
		return []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t920}
	}
	_t921 := _t919(msg)
	fields442 := _t921
	p.write("(")
	p.write("export_csv_config")
	p.indent()
	p.write(" ")
	field443 := fields442[0].(string)
	p.pretty_export_csv_path(field443)
	p.newline()
	field444 := fields442[1].([]*pb.ExportCSVColumn)
	p.pretty_export_csv_columns(field444)
	p.newline()
	field445 := fields442[2].([][]interface{})
	p.pretty_config_dict(field445)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) {
	_t922 := func(_dollar_dollar string) string {
		return _dollar_dollar
	}
	_t923 := _t922(msg)
	fields446 := _t923
	p.write("(")
	p.write("path")
	p.indent()
	p.write(" ")
	p.write(p.formatStringValue(fields446))
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_export_csv_columns(msg []*pb.ExportCSVColumn) {
	_t924 := func(_dollar_dollar []*pb.ExportCSVColumn) []*pb.ExportCSVColumn {
		return _dollar_dollar
	}
	_t925 := _t924(msg)
	fields447 := _t925
	p.write("(")
	p.write("columns")
	p.indent()
	if !(len(fields447) == 0) {
		p.newline()
		for i449, elem448 := range fields447 {
			if (i449 > 0) {
				p.newline()
			}
			p.pretty_export_csv_column(elem448)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_export_csv_column(msg *pb.ExportCSVColumn) {
	_t926 := func(_dollar_dollar *pb.ExportCSVColumn) []interface{} {
		return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
	}
	_t927 := _t926(msg)
	fields450 := _t927
	p.write("(")
	p.write("column")
	p.indent()
	p.write(" ")
	field451 := fields450[0].(string)
	p.write(p.formatStringValue(field451))
	p.newline()
	field452 := fields450[1].(*pb.RelationId)
	p.pretty_relation_id(field452)
	p.dedent()
	p.write(")")
}


// ProgramToStr pretty-prints a Transaction protobuf message to a string.
func ProgramToStr(msg *pb.Transaction) string {
	var buf bytes.Buffer
	p := &PrettyPrinter{
		w:           &buf,
		indentLevel: 0,
		atLineStart: true,
		debugInfo:   make(map[[2]uint64]string),
	}
	p.pretty_transaction(msg)
	p.newline()
	return p.getOutput()
}
