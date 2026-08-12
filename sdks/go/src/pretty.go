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
	"math"
	"math/big"
	"reflect"
	"sort"
	"strconv"
	"strings"

	pb "github.com/RelationalAI/logical-query-protocol/sdks/go/src/lqp/v1"
)

const maxWidth = 92

// PrettyPrinter holds state for pretty printing protobuf messages.
type PrettyPrinter struct {
	w                       *bytes.Buffer
	indentStack             []int
	column                  int
	atLineStart             bool
	separator               string
	maxWidth                int
	computing               map[uintptr]bool
	memo                    map[uintptr]string
	memoRefs                []interface{}
	debugInfo               map[[2]uint64]string
	printSymbolicRelationIds bool
}

func (p *PrettyPrinter) indentLevel() int {
	if len(p.indentStack) > 0 {
		return p.indentStack[len(p.indentStack)-1]
	}
	return 0
}

func (p *PrettyPrinter) write(s string) {
	if p.separator == "\n" && p.atLineStart && strings.TrimSpace(s) != "" {
		spaces := p.indentLevel()
		p.w.WriteString(strings.Repeat(" ", spaces))
		p.column = spaces
		p.atLineStart = false
	}
	p.w.WriteString(s)
	if idx := strings.LastIndex(s, "\n"); idx >= 0 {
		p.column = len(s) - idx - 1
	} else {
		p.column += len(s)
	}
}

func (p *PrettyPrinter) newline() {
	p.w.WriteString(p.separator)
	if p.separator == "\n" {
		p.atLineStart = true
		p.column = 0
	}
}

func (p *PrettyPrinter) indent() {
	if p.separator == "\n" {
		p.indentStack = append(p.indentStack, p.column)
	}
}

func (p *PrettyPrinter) indentSexp() {
	if p.separator == "\n" {
		p.indentStack = append(p.indentStack, p.indentLevel()+2)
	}
}

func (p *PrettyPrinter) dedent() {
	if p.separator == "\n" && len(p.indentStack) > 1 {
		p.indentStack = p.indentStack[:len(p.indentStack)-1]
	}
}

func (p *PrettyPrinter) tryFlat(msg interface{}, prettyFn func()) *string {
	v := reflect.ValueOf(msg)
	// Only memoize pointer types. Slices share underlying array
	// pointers (especially nil/empty slices), causing collisions.
	canMemo := v.Kind() == reflect.Ptr
	if canMemo {
		key := v.Pointer()
		if _, ok := p.memo[key]; !ok && !p.computing[key] {
			p.computing[key] = true
			flat := p.renderFlat(prettyFn)
			p.memo[key] = flat
			p.memoRefs = append(p.memoRefs, msg)
			delete(p.computing, key)
		}
		if flat, ok := p.memo[key]; ok {
			return p.fitsWidth(flat)
		}
		return nil
	}
	// Non-pointer types (e.g., RelationId passed to different wrapper nonterminals)
	// cannot be safely memoized because the same value may need different renderings
	// depending on the calling context. Always render fresh.
	// If already in flat mode, return nil to prevent infinite recursion.
	if p.separator != "\n" {
		return nil
	}
	flat := p.renderFlat(prettyFn)
	return p.fitsWidth(flat)
}

func (p *PrettyPrinter) renderFlat(prettyFn func()) string {
	savedW := p.w
	savedSep := p.separator
	savedIndent := p.indentStack
	savedCol := p.column
	savedAtLineStart := p.atLineStart
	var buf bytes.Buffer
	p.w = &buf
	p.separator = " "
	p.indentStack = []int{0}
	p.column = 0
	p.atLineStart = false
	prettyFn()
	result := buf.String()
	p.w = savedW
	p.separator = savedSep
	p.indentStack = savedIndent
	p.column = savedCol
	p.atLineStart = savedAtLineStart
	return result
}

func (p *PrettyPrinter) fitsWidth(flat string) *string {
	if p.separator != "\n" {
		return &flat
	}
	effectiveCol := p.column
	if p.atLineStart {
		effectiveCol = p.indentLevel()
	}
	if len(flat)+effectiveCol <= p.maxWidth {
		return &flat
	}
	return nil
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
func (p *PrettyPrinter) relationIdToString(msg *pb.RelationId) *string {
	if !p.printSymbolicRelationIds {
		return nil
	}
	key := [2]uint64{msg.GetIdLow(), msg.GetIdHigh()}
	if name, ok := p.debugInfo[key]; ok {
		return &name
	}
	return nil
}

// relationIdToUint128 converts a RelationId to a UInt128Value.
func (p *PrettyPrinter) relationIdToUint128(msg *pb.RelationId) *pb.UInt128Value {
	return &pb.UInt128Value{Low: msg.GetIdLow(), High: msg.GetIdHigh()}
}

// listSort sorts a slice of []interface{} pairs by their first element (string key).
func listSort(pairs [][]interface{}) [][]interface{} {
	sort.Slice(pairs, func(i, j int) bool {
		ki, _ := pairs[i][0].(string)
		kj, _ := pairs[j][0].(string)
		return ki < kj
	})
	return pairs
}

// valueMapToPairs converts map[string]*pb.Value to sorted key/value rows for pretty printing.
func valueMapToPairs(m map[string]*pb.Value) [][]interface{} {
	if len(m) == 0 {
		return nil
	}
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := make([][]interface{}, 0, len(keys))
	for _, k := range keys {
		out = append(out, []interface{}{k, m[k]})
	}
	return out
}

// dictToPairs converts map[string]string to sorted key/value rows for pretty printing.
func dictToPairs(m map[string]string) [][]interface{} {
	if len(m) == 0 {
		return nil
	}
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := make([][]interface{}, 0, len(keys))
	for _, k := range keys {
		out = append(out, []interface{}{k, m[k]})
	}
	return out
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

func formatFloat64(v float64) string {
	s := fmt.Sprintf("%g", v)
	// Match Python's str(float) output: lowercase, no leading +.
	s = strings.ToLower(s)
	s = strings.TrimPrefix(s, "+")
	if !strings.ContainsAny(s, ".einn") {
		s += ".0"
	}
	return s
}

func formatFloat32(v float32) string {
	if math.IsInf(float64(v), 0) {
		return "inf32"
	}
	if math.IsNaN(float64(v)) {
		return "nan32"
	}
	return fmt.Sprintf("%sf32", strconv.FormatFloat(float64(v), 'g', -1, 32))
}

func formatBool(b bool) string {
	if b {
		return "true"
	}
	return "false"
}

// --- Helper functions ---

func (p *PrettyPrinter) deconstruct_relation_keys(msg *pb.TargetRelations) []interface{} {
	return []interface{}{msg.GetKeys(), msg.GetSyntheticKey()}
}

func (p *PrettyPrinter) deconstruct_load_errors_optional(msg *pb.TargetRelations) *pb.RelationId {
	var _t1863 interface{}
	if hasProtoField(msg, "load_errors") {
		return msg.GetLoadErrors()
	}
	_ = _t1863
	return nil
}

func (p *PrettyPrinter) deconstruct_csv_data_columns_optional(msg *pb.CSVData) []*pb.GNFColumn {
	var _t1864 interface{}
	if hasProtoField(msg, "relations") {
		return nil
	}
	_ = _t1864
	return msg.GetColumns()
}

func (p *PrettyPrinter) deconstruct_csv_data_relations_optional(msg *pb.CSVData) *pb.TargetRelations {
	var _t1865 interface{}
	if hasProtoField(msg, "relations") {
		return msg.GetRelations()
	}
	_ = _t1865
	return nil
}

func (p *PrettyPrinter) deconstruct_export_csv_output_location(msg *pb.ExportCSVConfig) []interface{} {
	return []interface{}{msg.GetPath(), msg.GetTransactionOutputName()}
}

func (p *PrettyPrinter) _make_value_int32(v int32) *pb.Value {
	_t1866 := &pb.Value{}
	_t1866.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1866
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1867 := &pb.Value{}
	_t1867.Value = &pb.Value_IntValue{IntValue: v}
	return _t1867
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1868 := &pb.Value{}
	_t1868.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1868
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1869 := &pb.Value{}
	_t1869.Value = &pb.Value_StringValue{StringValue: v}
	return _t1869
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1870 := &pb.Value{}
	_t1870.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1870
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1871 := &pb.Value{}
	_t1871.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1871
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1872 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1872})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1873 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1873})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1874 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1874})
			}
		}
	}
	_t1875 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1875})
	for _, pair := range valueMapToPairs(msg.GetConfigurationValues()) {
		result = append(result, pair)
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1876 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1876})
	_t1877 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1877})
	if msg.GetNewLine() != "" {
		_t1878 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1878})
	}
	_t1879 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1879})
	_t1880 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1880})
	_t1881 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1881})
	if msg.GetComment() != "" {
		_t1882 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1882})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1883 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1883})
	}
	_t1884 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1884})
	_t1885 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1885})
	_t1886 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1886})
	if msg.GetPartitionSizeMb() != 0 {
		_t1887 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1887})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_storage_integration_optional(msg *pb.CSVConfig) [][]interface{} {
	var _t1888 interface{}
	if !(hasProtoField(msg, "storage_integration")) {
		return nil
	}
	_ = _t1888
	si := msg.GetStorageIntegration()
	result := [][]interface{}{}
	if si.GetProvider() != "" {
		_t1889 := p._make_value_string(si.GetProvider())
		result = append(result, []interface{}{"provider", _t1889})
	}
	if si.GetAzureSasToken() != "" {
		_t1890 := p._make_value_string("***")
		result = append(result, []interface{}{"azure_sas_token", _t1890})
	}
	if si.GetS3Region() != "" {
		_t1891 := p._make_value_string(si.GetS3Region())
		result = append(result, []interface{}{"s3_region", _t1891})
	}
	if si.GetS3AccessKeyId() != "" {
		_t1892 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_access_key_id", _t1892})
	}
	if si.GetS3SecretAccessKey() != "" {
		_t1893 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_secret_access_key", _t1893})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1894 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1894})
	_t1895 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1895})
	_t1896 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1896})
	_t1897 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1897})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1898 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1898})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1899 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1899})
		}
	}
	_t1900 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1900})
	_t1901 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1901})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1902 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1902})
	}
	if msg.Compression != nil {
		_t1903 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1903})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1904 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1904})
	}
	if msg.SyntaxMissingString != nil {
		_t1905 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1905})
	}
	if msg.SyntaxDelim != nil {
		_t1906 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1906})
	}
	if msg.SyntaxQuotechar != nil {
		_t1907 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1907})
	}
	if msg.SyntaxEscapechar != nil {
		_t1908 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1908})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1909 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1909
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1910 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1910
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1911 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1911
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1912 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1912})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1913 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1913})
	}
	if msg.GetCompression() != "" {
		_t1914 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1914})
	}
	var _t1915 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1915
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1916 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1916
	return nil
}

func (p *PrettyPrinter) deconstruct_bindings(abs *pb.Abstraction) []interface{} {
	n := int64(len(abs.GetVars()))
	return []interface{}{abs.GetVars()[0:n], []*pb.Binding{}}
}

func (p *PrettyPrinter) deconstruct_bindings_with_arity(abs *pb.Abstraction, value_arity int64) []interface{} {
	n := int64(len(abs.GetVars()))
	key_end := (n - value_arity)
	return []interface{}{abs.GetVars()[0:key_end], abs.GetVars()[key_end:n]}
}

// --- Pretty-print methods ---

func (p *PrettyPrinter) pretty_transaction(msg *pb.Transaction) interface{} {
	flat863 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat863 != nil {
		p.write(*flat863)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1708 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1708 = _dollar_dollar.GetConfigure()
		}
		var _t1709 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1709 = _dollar_dollar.GetSync()
		}
		fields854 := []interface{}{_t1708, _t1709, _dollar_dollar.GetEpochs()}
		unwrapped_fields855 := fields854
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field856 := unwrapped_fields855[0].(*pb.Configure)
		if field856 != nil {
			p.newline()
			opt_val857 := field856
			p.pretty_configure(opt_val857)
		}
		field858 := unwrapped_fields855[1].(*pb.Sync)
		if field858 != nil {
			p.newline()
			opt_val859 := field858
			p.pretty_sync(opt_val859)
		}
		field860 := unwrapped_fields855[2].([]*pb.Epoch)
		if !(len(field860) == 0) {
			p.newline()
			for i862, elem861 := range field860 {
				if (i862 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem861)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat866 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat866 != nil {
		p.write(*flat866)
		return nil
	} else {
		_dollar_dollar := msg
		_t1710 := p.deconstruct_configure(_dollar_dollar)
		fields864 := _t1710
		unwrapped_fields865 := fields864
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields865)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat870 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat870 != nil {
		p.write(*flat870)
		return nil
	} else {
		fields867 := msg
		p.write("{")
		p.indent()
		if !(len(fields867) == 0) {
			p.newline()
			for i869, elem868 := range fields867 {
				if (i869 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem868)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat875 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat875 != nil {
		p.write(*flat875)
		return nil
	} else {
		_dollar_dollar := msg
		fields871 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields872 := fields871
		p.write(":")
		field873 := unwrapped_fields872[0].(string)
		p.write(field873)
		p.write(" ")
		field874 := unwrapped_fields872[1].(*pb.Value)
		p.pretty_raw_value(field874)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat901 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat901 != nil {
		p.write(*flat901)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1711 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1711 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result899 := _t1711
		if deconstruct_result899 != nil {
			unwrapped900 := deconstruct_result899
			p.pretty_raw_date(unwrapped900)
		} else {
			_dollar_dollar := msg
			var _t1712 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1712 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result897 := _t1712
			if deconstruct_result897 != nil {
				unwrapped898 := deconstruct_result897
				p.pretty_raw_datetime(unwrapped898)
			} else {
				_dollar_dollar := msg
				var _t1713 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1713 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result895 := _t1713
				if deconstruct_result895 != nil {
					unwrapped896 := *deconstruct_result895
					p.write(p.formatStringValue(unwrapped896))
				} else {
					_dollar_dollar := msg
					var _t1714 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1714 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result893 := _t1714
					if deconstruct_result893 != nil {
						unwrapped894 := *deconstruct_result893
						p.write(fmt.Sprintf("%di32", unwrapped894))
					} else {
						_dollar_dollar := msg
						var _t1715 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1715 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result891 := _t1715
						if deconstruct_result891 != nil {
							unwrapped892 := *deconstruct_result891
							p.write(fmt.Sprintf("%d", unwrapped892))
						} else {
							_dollar_dollar := msg
							var _t1716 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1716 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result889 := _t1716
							if deconstruct_result889 != nil {
								unwrapped890 := *deconstruct_result889
								p.write(formatFloat32(unwrapped890))
							} else {
								_dollar_dollar := msg
								var _t1717 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1717 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result887 := _t1717
								if deconstruct_result887 != nil {
									unwrapped888 := *deconstruct_result887
									p.write(formatFloat64(unwrapped888))
								} else {
									_dollar_dollar := msg
									var _t1718 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1718 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result885 := _t1718
									if deconstruct_result885 != nil {
										unwrapped886 := *deconstruct_result885
										p.write(fmt.Sprintf("%du32", unwrapped886))
									} else {
										_dollar_dollar := msg
										var _t1719 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1719 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result883 := _t1719
										if deconstruct_result883 != nil {
											unwrapped884 := deconstruct_result883
											p.write(p.formatUint128(unwrapped884))
										} else {
											_dollar_dollar := msg
											var _t1720 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1720 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result881 := _t1720
											if deconstruct_result881 != nil {
												unwrapped882 := deconstruct_result881
												p.write(p.formatInt128(unwrapped882))
											} else {
												_dollar_dollar := msg
												var _t1721 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1721 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result879 := _t1721
												if deconstruct_result879 != nil {
													unwrapped880 := deconstruct_result879
													p.write(p.formatDecimal(unwrapped880))
												} else {
													_dollar_dollar := msg
													var _t1722 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1722 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result877 := _t1722
													if deconstruct_result877 != nil {
														unwrapped878 := *deconstruct_result877
														p.pretty_boolean_value(unwrapped878)
													} else {
														fields876 := msg
														_ = fields876
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
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_date(msg *pb.DateValue) interface{} {
	flat907 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat907 != nil {
		p.write(*flat907)
		return nil
	} else {
		_dollar_dollar := msg
		fields902 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields903 := fields902
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field904 := unwrapped_fields903[0].(int64)
		p.write(fmt.Sprintf("%d", field904))
		p.newline()
		field905 := unwrapped_fields903[1].(int64)
		p.write(fmt.Sprintf("%d", field905))
		p.newline()
		field906 := unwrapped_fields903[2].(int64)
		p.write(fmt.Sprintf("%d", field906))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat918 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat918 != nil {
		p.write(*flat918)
		return nil
	} else {
		_dollar_dollar := msg
		fields908 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields909 := fields908
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field910 := unwrapped_fields909[0].(int64)
		p.write(fmt.Sprintf("%d", field910))
		p.newline()
		field911 := unwrapped_fields909[1].(int64)
		p.write(fmt.Sprintf("%d", field911))
		p.newline()
		field912 := unwrapped_fields909[2].(int64)
		p.write(fmt.Sprintf("%d", field912))
		p.newline()
		field913 := unwrapped_fields909[3].(int64)
		p.write(fmt.Sprintf("%d", field913))
		p.newline()
		field914 := unwrapped_fields909[4].(int64)
		p.write(fmt.Sprintf("%d", field914))
		p.newline()
		field915 := unwrapped_fields909[5].(int64)
		p.write(fmt.Sprintf("%d", field915))
		field916 := unwrapped_fields909[6].(*int64)
		if field916 != nil {
			p.newline()
			opt_val917 := *field916
			p.write(fmt.Sprintf("%d", opt_val917))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1723 []interface{}
	if _dollar_dollar {
		_t1723 = []interface{}{}
	}
	deconstruct_result921 := _t1723
	if deconstruct_result921 != nil {
		unwrapped922 := deconstruct_result921
		_ = unwrapped922
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1724 []interface{}
		if !(_dollar_dollar) {
			_t1724 = []interface{}{}
		}
		deconstruct_result919 := _t1724
		if deconstruct_result919 != nil {
			unwrapped920 := deconstruct_result919
			_ = unwrapped920
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat927 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat927 != nil {
		p.write(*flat927)
		return nil
	} else {
		_dollar_dollar := msg
		fields923 := _dollar_dollar.GetFragments()
		unwrapped_fields924 := fields923
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields924) == 0) {
			p.newline()
			for i926, elem925 := range unwrapped_fields924 {
				if (i926 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem925)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat930 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat930 != nil {
		p.write(*flat930)
		return nil
	} else {
		_dollar_dollar := msg
		fields928 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields929 := fields928
		p.write(":")
		p.write(unwrapped_fields929)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat937 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat937 != nil {
		p.write(*flat937)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1725 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1725 = _dollar_dollar.GetWrites()
		}
		var _t1726 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1726 = _dollar_dollar.GetReads()
		}
		fields931 := []interface{}{_t1725, _t1726}
		unwrapped_fields932 := fields931
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field933 := unwrapped_fields932[0].([]*pb.Write)
		if field933 != nil {
			p.newline()
			opt_val934 := field933
			p.pretty_epoch_writes(opt_val934)
		}
		field935 := unwrapped_fields932[1].([]*pb.Read)
		if field935 != nil {
			p.newline()
			opt_val936 := field935
			p.pretty_epoch_reads(opt_val936)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat941 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat941 != nil {
		p.write(*flat941)
		return nil
	} else {
		fields938 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields938) == 0) {
			p.newline()
			for i940, elem939 := range fields938 {
				if (i940 > 0) {
					p.newline()
				}
				p.pretty_write(elem939)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat950 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat950 != nil {
		p.write(*flat950)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1727 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1727 = _dollar_dollar.GetDefine()
		}
		deconstruct_result948 := _t1727
		if deconstruct_result948 != nil {
			unwrapped949 := deconstruct_result948
			p.pretty_define(unwrapped949)
		} else {
			_dollar_dollar := msg
			var _t1728 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1728 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result946 := _t1728
			if deconstruct_result946 != nil {
				unwrapped947 := deconstruct_result946
				p.pretty_undefine(unwrapped947)
			} else {
				_dollar_dollar := msg
				var _t1729 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1729 = _dollar_dollar.GetContext()
				}
				deconstruct_result944 := _t1729
				if deconstruct_result944 != nil {
					unwrapped945 := deconstruct_result944
					p.pretty_context(unwrapped945)
				} else {
					_dollar_dollar := msg
					var _t1730 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1730 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result942 := _t1730
					if deconstruct_result942 != nil {
						unwrapped943 := deconstruct_result942
						p.pretty_snapshot(unwrapped943)
					} else {
						panic(ParseError{msg: "No matching rule for write"})
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_define(msg *pb.Define) interface{} {
	flat953 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat953 != nil {
		p.write(*flat953)
		return nil
	} else {
		_dollar_dollar := msg
		fields951 := _dollar_dollar.GetFragment()
		unwrapped_fields952 := fields951
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields952)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat960 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat960 != nil {
		p.write(*flat960)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields954 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields955 := fields954
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field956 := unwrapped_fields955[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field956)
		field957 := unwrapped_fields955[1].([]*pb.Declaration)
		if !(len(field957) == 0) {
			p.newline()
			for i959, elem958 := range field957 {
				if (i959 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem958)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat962 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat962 != nil {
		p.write(*flat962)
		return nil
	} else {
		fields961 := msg
		p.pretty_fragment_id(fields961)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat971 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat971 != nil {
		p.write(*flat971)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1731 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1731 = _dollar_dollar.GetDef()
		}
		deconstruct_result969 := _t1731
		if deconstruct_result969 != nil {
			unwrapped970 := deconstruct_result969
			p.pretty_def(unwrapped970)
		} else {
			_dollar_dollar := msg
			var _t1732 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1732 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result967 := _t1732
			if deconstruct_result967 != nil {
				unwrapped968 := deconstruct_result967
				p.pretty_algorithm(unwrapped968)
			} else {
				_dollar_dollar := msg
				var _t1733 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1733 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result965 := _t1733
				if deconstruct_result965 != nil {
					unwrapped966 := deconstruct_result965
					p.pretty_constraint(unwrapped966)
				} else {
					_dollar_dollar := msg
					var _t1734 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1734 = _dollar_dollar.GetData()
					}
					deconstruct_result963 := _t1734
					if deconstruct_result963 != nil {
						unwrapped964 := deconstruct_result963
						p.pretty_data(unwrapped964)
					} else {
						panic(ParseError{msg: "No matching rule for declaration"})
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_def(msg *pb.Def) interface{} {
	flat978 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat978 != nil {
		p.write(*flat978)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1735 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1735 = _dollar_dollar.GetAttrs()
		}
		fields972 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1735}
		unwrapped_fields973 := fields972
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field974 := unwrapped_fields973[0].(*pb.RelationId)
		p.pretty_relation_id(field974)
		p.newline()
		field975 := unwrapped_fields973[1].(*pb.Abstraction)
		p.pretty_abstraction(field975)
		field976 := unwrapped_fields973[2].([]*pb.Attribute)
		if field976 != nil {
			p.newline()
			opt_val977 := field976
			p.pretty_attrs(opt_val977)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat983 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat983 != nil {
		p.write(*flat983)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1736 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1737 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1736 = ptr(_t1737)
		}
		deconstruct_result981 := _t1736
		if deconstruct_result981 != nil {
			unwrapped982 := *deconstruct_result981
			p.write(":")
			p.write(unwrapped982)
		} else {
			_dollar_dollar := msg
			_t1738 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result979 := _t1738
			if deconstruct_result979 != nil {
				unwrapped980 := deconstruct_result979
				p.write(p.formatUint128(unwrapped980))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat988 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat988 != nil {
		p.write(*flat988)
		return nil
	} else {
		_dollar_dollar := msg
		_t1739 := p.deconstruct_bindings(_dollar_dollar)
		fields984 := []interface{}{_t1739, _dollar_dollar.GetValue()}
		unwrapped_fields985 := fields984
		p.write("(")
		p.indent()
		field986 := unwrapped_fields985[0].([]interface{})
		p.pretty_bindings(field986)
		p.newline()
		field987 := unwrapped_fields985[1].(*pb.Formula)
		p.pretty_formula(field987)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat996 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat996 != nil {
		p.write(*flat996)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1740 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1740 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields989 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1740}
		unwrapped_fields990 := fields989
		p.write("[")
		p.indent()
		field991 := unwrapped_fields990[0].([]*pb.Binding)
		for i993, elem992 := range field991 {
			if (i993 > 0) {
				p.newline()
			}
			p.pretty_binding(elem992)
		}
		field994 := unwrapped_fields990[1].([]*pb.Binding)
		if field994 != nil {
			p.newline()
			opt_val995 := field994
			p.pretty_value_bindings(opt_val995)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat1001 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat1001 != nil {
		p.write(*flat1001)
		return nil
	} else {
		_dollar_dollar := msg
		fields997 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields998 := fields997
		field999 := unwrapped_fields998[0].(string)
		p.write(field999)
		p.write("::")
		field1000 := unwrapped_fields998[1].(*pb.Type)
		p.pretty_type(field1000)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat1030 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat1030 != nil {
		p.write(*flat1030)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1741 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1741 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result1028 := _t1741
		if deconstruct_result1028 != nil {
			unwrapped1029 := deconstruct_result1028
			p.pretty_unspecified_type(unwrapped1029)
		} else {
			_dollar_dollar := msg
			var _t1742 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1742 = _dollar_dollar.GetStringType()
			}
			deconstruct_result1026 := _t1742
			if deconstruct_result1026 != nil {
				unwrapped1027 := deconstruct_result1026
				p.pretty_string_type(unwrapped1027)
			} else {
				_dollar_dollar := msg
				var _t1743 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1743 = _dollar_dollar.GetIntType()
				}
				deconstruct_result1024 := _t1743
				if deconstruct_result1024 != nil {
					unwrapped1025 := deconstruct_result1024
					p.pretty_int_type(unwrapped1025)
				} else {
					_dollar_dollar := msg
					var _t1744 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1744 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result1022 := _t1744
					if deconstruct_result1022 != nil {
						unwrapped1023 := deconstruct_result1022
						p.pretty_float_type(unwrapped1023)
					} else {
						_dollar_dollar := msg
						var _t1745 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1745 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result1020 := _t1745
						if deconstruct_result1020 != nil {
							unwrapped1021 := deconstruct_result1020
							p.pretty_uint128_type(unwrapped1021)
						} else {
							_dollar_dollar := msg
							var _t1746 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1746 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result1018 := _t1746
							if deconstruct_result1018 != nil {
								unwrapped1019 := deconstruct_result1018
								p.pretty_int128_type(unwrapped1019)
							} else {
								_dollar_dollar := msg
								var _t1747 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1747 = _dollar_dollar.GetDateType()
								}
								deconstruct_result1016 := _t1747
								if deconstruct_result1016 != nil {
									unwrapped1017 := deconstruct_result1016
									p.pretty_date_type(unwrapped1017)
								} else {
									_dollar_dollar := msg
									var _t1748 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1748 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result1014 := _t1748
									if deconstruct_result1014 != nil {
										unwrapped1015 := deconstruct_result1014
										p.pretty_datetime_type(unwrapped1015)
									} else {
										_dollar_dollar := msg
										var _t1749 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1749 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result1012 := _t1749
										if deconstruct_result1012 != nil {
											unwrapped1013 := deconstruct_result1012
											p.pretty_missing_type(unwrapped1013)
										} else {
											_dollar_dollar := msg
											var _t1750 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1750 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result1010 := _t1750
											if deconstruct_result1010 != nil {
												unwrapped1011 := deconstruct_result1010
												p.pretty_decimal_type(unwrapped1011)
											} else {
												_dollar_dollar := msg
												var _t1751 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1751 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result1008 := _t1751
												if deconstruct_result1008 != nil {
													unwrapped1009 := deconstruct_result1008
													p.pretty_boolean_type(unwrapped1009)
												} else {
													_dollar_dollar := msg
													var _t1752 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1752 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result1006 := _t1752
													if deconstruct_result1006 != nil {
														unwrapped1007 := deconstruct_result1006
														p.pretty_int32_type(unwrapped1007)
													} else {
														_dollar_dollar := msg
														var _t1753 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1753 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result1004 := _t1753
														if deconstruct_result1004 != nil {
															unwrapped1005 := deconstruct_result1004
															p.pretty_float32_type(unwrapped1005)
														} else {
															_dollar_dollar := msg
															var _t1754 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1754 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result1002 := _t1754
															if deconstruct_result1002 != nil {
																unwrapped1003 := deconstruct_result1002
																p.pretty_uint32_type(unwrapped1003)
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
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_unspecified_type(msg *pb.UnspecifiedType) interface{} {
	fields1031 := msg
	_ = fields1031
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields1032 := msg
	_ = fields1032
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields1033 := msg
	_ = fields1033
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields1034 := msg
	_ = fields1034
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields1035 := msg
	_ = fields1035
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields1036 := msg
	_ = fields1036
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields1037 := msg
	_ = fields1037
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields1038 := msg
	_ = fields1038
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields1039 := msg
	_ = fields1039
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat1044 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat1044 != nil {
		p.write(*flat1044)
		return nil
	} else {
		_dollar_dollar := msg
		fields1040 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields1041 := fields1040
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field1042 := unwrapped_fields1041[0].(int64)
		p.write(fmt.Sprintf("%d", field1042))
		p.newline()
		field1043 := unwrapped_fields1041[1].(int64)
		p.write(fmt.Sprintf("%d", field1043))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields1045 := msg
	_ = fields1045
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields1046 := msg
	_ = fields1046
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields1047 := msg
	_ = fields1047
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields1048 := msg
	_ = fields1048
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat1052 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat1052 != nil {
		p.write(*flat1052)
		return nil
	} else {
		fields1049 := msg
		p.write("|")
		if !(len(fields1049) == 0) {
			p.write(" ")
			for i1051, elem1050 := range fields1049 {
				if (i1051 > 0) {
					p.newline()
				}
				p.pretty_binding(elem1050)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1079 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1079 != nil {
		p.write(*flat1079)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1755 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1755 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1077 := _t1755
		if deconstruct_result1077 != nil {
			unwrapped1078 := deconstruct_result1077
			p.pretty_true(unwrapped1078)
		} else {
			_dollar_dollar := msg
			var _t1756 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1756 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1075 := _t1756
			if deconstruct_result1075 != nil {
				unwrapped1076 := deconstruct_result1075
				p.pretty_false(unwrapped1076)
			} else {
				_dollar_dollar := msg
				var _t1757 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1757 = _dollar_dollar.GetExists()
				}
				deconstruct_result1073 := _t1757
				if deconstruct_result1073 != nil {
					unwrapped1074 := deconstruct_result1073
					p.pretty_exists(unwrapped1074)
				} else {
					_dollar_dollar := msg
					var _t1758 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1758 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1071 := _t1758
					if deconstruct_result1071 != nil {
						unwrapped1072 := deconstruct_result1071
						p.pretty_reduce(unwrapped1072)
					} else {
						_dollar_dollar := msg
						var _t1759 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1759 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1069 := _t1759
						if deconstruct_result1069 != nil {
							unwrapped1070 := deconstruct_result1069
							p.pretty_conjunction(unwrapped1070)
						} else {
							_dollar_dollar := msg
							var _t1760 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1760 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1067 := _t1760
							if deconstruct_result1067 != nil {
								unwrapped1068 := deconstruct_result1067
								p.pretty_disjunction(unwrapped1068)
							} else {
								_dollar_dollar := msg
								var _t1761 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1761 = _dollar_dollar.GetNot()
								}
								deconstruct_result1065 := _t1761
								if deconstruct_result1065 != nil {
									unwrapped1066 := deconstruct_result1065
									p.pretty_not(unwrapped1066)
								} else {
									_dollar_dollar := msg
									var _t1762 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1762 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1063 := _t1762
									if deconstruct_result1063 != nil {
										unwrapped1064 := deconstruct_result1063
										p.pretty_ffi(unwrapped1064)
									} else {
										_dollar_dollar := msg
										var _t1763 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1763 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1061 := _t1763
										if deconstruct_result1061 != nil {
											unwrapped1062 := deconstruct_result1061
											p.pretty_atom(unwrapped1062)
										} else {
											_dollar_dollar := msg
											var _t1764 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1764 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1059 := _t1764
											if deconstruct_result1059 != nil {
												unwrapped1060 := deconstruct_result1059
												p.pretty_pragma(unwrapped1060)
											} else {
												_dollar_dollar := msg
												var _t1765 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1765 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1057 := _t1765
												if deconstruct_result1057 != nil {
													unwrapped1058 := deconstruct_result1057
													p.pretty_primitive(unwrapped1058)
												} else {
													_dollar_dollar := msg
													var _t1766 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1766 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1055 := _t1766
													if deconstruct_result1055 != nil {
														unwrapped1056 := deconstruct_result1055
														p.pretty_rel_atom(unwrapped1056)
													} else {
														_dollar_dollar := msg
														var _t1767 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1767 = _dollar_dollar.GetCast()
														}
														deconstruct_result1053 := _t1767
														if deconstruct_result1053 != nil {
															unwrapped1054 := deconstruct_result1053
															p.pretty_cast(unwrapped1054)
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
	return nil
}

func (p *PrettyPrinter) pretty_true(msg *pb.Conjunction) interface{} {
	fields1080 := msg
	_ = fields1080
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1081 := msg
	_ = fields1081
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1086 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1086 != nil {
		p.write(*flat1086)
		return nil
	} else {
		_dollar_dollar := msg
		_t1768 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1082 := []interface{}{_t1768, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1083 := fields1082
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1084 := unwrapped_fields1083[0].([]interface{})
		p.pretty_bindings(field1084)
		p.newline()
		field1085 := unwrapped_fields1083[1].(*pb.Formula)
		p.pretty_formula(field1085)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1092 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1092 != nil {
		p.write(*flat1092)
		return nil
	} else {
		_dollar_dollar := msg
		fields1087 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1088 := fields1087
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1089 := unwrapped_fields1088[0].(*pb.Abstraction)
		p.pretty_abstraction(field1089)
		p.newline()
		field1090 := unwrapped_fields1088[1].(*pb.Abstraction)
		p.pretty_abstraction(field1090)
		p.newline()
		field1091 := unwrapped_fields1088[2].([]*pb.Term)
		p.pretty_terms(field1091)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1096 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1096 != nil {
		p.write(*flat1096)
		return nil
	} else {
		fields1093 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1093) == 0) {
			p.newline()
			for i1095, elem1094 := range fields1093 {
				if (i1095 > 0) {
					p.newline()
				}
				p.pretty_term(elem1094)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1101 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1101 != nil {
		p.write(*flat1101)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1769 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1769 = _dollar_dollar.GetVar()
		}
		deconstruct_result1099 := _t1769
		if deconstruct_result1099 != nil {
			unwrapped1100 := deconstruct_result1099
			p.pretty_var(unwrapped1100)
		} else {
			_dollar_dollar := msg
			var _t1770 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1770 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1097 := _t1770
			if deconstruct_result1097 != nil {
				unwrapped1098 := deconstruct_result1097
				p.pretty_value(unwrapped1098)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1104 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1104 != nil {
		p.write(*flat1104)
		return nil
	} else {
		_dollar_dollar := msg
		fields1102 := _dollar_dollar.GetName()
		unwrapped_fields1103 := fields1102
		p.write(unwrapped_fields1103)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1130 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1130 != nil {
		p.write(*flat1130)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1771 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1771 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1128 := _t1771
		if deconstruct_result1128 != nil {
			unwrapped1129 := deconstruct_result1128
			p.pretty_date(unwrapped1129)
		} else {
			_dollar_dollar := msg
			var _t1772 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1772 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1126 := _t1772
			if deconstruct_result1126 != nil {
				unwrapped1127 := deconstruct_result1126
				p.pretty_datetime(unwrapped1127)
			} else {
				_dollar_dollar := msg
				var _t1773 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1773 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1124 := _t1773
				if deconstruct_result1124 != nil {
					unwrapped1125 := *deconstruct_result1124
					p.write(p.formatStringValue(unwrapped1125))
				} else {
					_dollar_dollar := msg
					var _t1774 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1774 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1122 := _t1774
					if deconstruct_result1122 != nil {
						unwrapped1123 := *deconstruct_result1122
						p.write(fmt.Sprintf("%di32", unwrapped1123))
					} else {
						_dollar_dollar := msg
						var _t1775 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1775 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1120 := _t1775
						if deconstruct_result1120 != nil {
							unwrapped1121 := *deconstruct_result1120
							p.write(fmt.Sprintf("%d", unwrapped1121))
						} else {
							_dollar_dollar := msg
							var _t1776 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1776 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1118 := _t1776
							if deconstruct_result1118 != nil {
								unwrapped1119 := *deconstruct_result1118
								p.write(formatFloat32(unwrapped1119))
							} else {
								_dollar_dollar := msg
								var _t1777 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1777 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1116 := _t1777
								if deconstruct_result1116 != nil {
									unwrapped1117 := *deconstruct_result1116
									p.write(formatFloat64(unwrapped1117))
								} else {
									_dollar_dollar := msg
									var _t1778 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1778 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1114 := _t1778
									if deconstruct_result1114 != nil {
										unwrapped1115 := *deconstruct_result1114
										p.write(fmt.Sprintf("%du32", unwrapped1115))
									} else {
										_dollar_dollar := msg
										var _t1779 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1779 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1112 := _t1779
										if deconstruct_result1112 != nil {
											unwrapped1113 := deconstruct_result1112
											p.write(p.formatUint128(unwrapped1113))
										} else {
											_dollar_dollar := msg
											var _t1780 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1780 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1110 := _t1780
											if deconstruct_result1110 != nil {
												unwrapped1111 := deconstruct_result1110
												p.write(p.formatInt128(unwrapped1111))
											} else {
												_dollar_dollar := msg
												var _t1781 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1781 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1108 := _t1781
												if deconstruct_result1108 != nil {
													unwrapped1109 := deconstruct_result1108
													p.write(p.formatDecimal(unwrapped1109))
												} else {
													_dollar_dollar := msg
													var _t1782 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1782 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1106 := _t1782
													if deconstruct_result1106 != nil {
														unwrapped1107 := *deconstruct_result1106
														p.pretty_boolean_value(unwrapped1107)
													} else {
														fields1105 := msg
														_ = fields1105
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
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_date(msg *pb.DateValue) interface{} {
	flat1136 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1136 != nil {
		p.write(*flat1136)
		return nil
	} else {
		_dollar_dollar := msg
		fields1131 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1132 := fields1131
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1133 := unwrapped_fields1132[0].(int64)
		p.write(fmt.Sprintf("%d", field1133))
		p.newline()
		field1134 := unwrapped_fields1132[1].(int64)
		p.write(fmt.Sprintf("%d", field1134))
		p.newline()
		field1135 := unwrapped_fields1132[2].(int64)
		p.write(fmt.Sprintf("%d", field1135))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1147 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1147 != nil {
		p.write(*flat1147)
		return nil
	} else {
		_dollar_dollar := msg
		fields1137 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1138 := fields1137
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1139 := unwrapped_fields1138[0].(int64)
		p.write(fmt.Sprintf("%d", field1139))
		p.newline()
		field1140 := unwrapped_fields1138[1].(int64)
		p.write(fmt.Sprintf("%d", field1140))
		p.newline()
		field1141 := unwrapped_fields1138[2].(int64)
		p.write(fmt.Sprintf("%d", field1141))
		p.newline()
		field1142 := unwrapped_fields1138[3].(int64)
		p.write(fmt.Sprintf("%d", field1142))
		p.newline()
		field1143 := unwrapped_fields1138[4].(int64)
		p.write(fmt.Sprintf("%d", field1143))
		p.newline()
		field1144 := unwrapped_fields1138[5].(int64)
		p.write(fmt.Sprintf("%d", field1144))
		field1145 := unwrapped_fields1138[6].(*int64)
		if field1145 != nil {
			p.newline()
			opt_val1146 := *field1145
			p.write(fmt.Sprintf("%d", opt_val1146))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1152 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1152 != nil {
		p.write(*flat1152)
		return nil
	} else {
		_dollar_dollar := msg
		fields1148 := _dollar_dollar.GetArgs()
		unwrapped_fields1149 := fields1148
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1149) == 0) {
			p.newline()
			for i1151, elem1150 := range unwrapped_fields1149 {
				if (i1151 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1150)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1157 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1157 != nil {
		p.write(*flat1157)
		return nil
	} else {
		_dollar_dollar := msg
		fields1153 := _dollar_dollar.GetArgs()
		unwrapped_fields1154 := fields1153
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1154) == 0) {
			p.newline()
			for i1156, elem1155 := range unwrapped_fields1154 {
				if (i1156 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1155)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1160 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1160 != nil {
		p.write(*flat1160)
		return nil
	} else {
		_dollar_dollar := msg
		fields1158 := _dollar_dollar.GetArg()
		unwrapped_fields1159 := fields1158
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1159)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1166 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1166 != nil {
		p.write(*flat1166)
		return nil
	} else {
		_dollar_dollar := msg
		fields1161 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1162 := fields1161
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1163 := unwrapped_fields1162[0].(string)
		p.pretty_name(field1163)
		p.newline()
		field1164 := unwrapped_fields1162[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1164)
		p.newline()
		field1165 := unwrapped_fields1162[2].([]*pb.Term)
		p.pretty_terms(field1165)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1168 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1168 != nil {
		p.write(*flat1168)
		return nil
	} else {
		fields1167 := msg
		p.write(":")
		p.write(fields1167)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1172 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1172 != nil {
		p.write(*flat1172)
		return nil
	} else {
		fields1169 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1169) == 0) {
			p.newline()
			for i1171, elem1170 := range fields1169 {
				if (i1171 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1170)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		_dollar_dollar := msg
		fields1173 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1174 := fields1173
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1175 := unwrapped_fields1174[0].(*pb.RelationId)
		p.pretty_relation_id(field1175)
		field1176 := unwrapped_fields1174[1].([]*pb.Term)
		if !(len(field1176) == 0) {
			p.newline()
			for i1178, elem1177 := range field1176 {
				if (i1178 > 0) {
					p.newline()
				}
				p.pretty_term(elem1177)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1186 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1186 != nil {
		p.write(*flat1186)
		return nil
	} else {
		_dollar_dollar := msg
		fields1180 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1181 := fields1180
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1182 := unwrapped_fields1181[0].(string)
		p.pretty_name(field1182)
		field1183 := unwrapped_fields1181[1].([]*pb.Term)
		if !(len(field1183) == 0) {
			p.newline()
			for i1185, elem1184 := range field1183 {
				if (i1185 > 0) {
					p.newline()
				}
				p.pretty_term(elem1184)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1202 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1202 != nil {
		p.write(*flat1202)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1783 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1783 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1201 := _t1783
		if guard_result1201 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1784 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1784 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1200 := _t1784
			if guard_result1200 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1785 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1785 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1199 := _t1785
				if guard_result1199 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1786 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1786 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1198 := _t1786
					if guard_result1198 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1787 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1787 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1197 := _t1787
						if guard_result1197 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1788 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1788 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1196 := _t1788
							if guard_result1196 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1789 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1789 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1195 := _t1789
								if guard_result1195 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1790 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1790 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1194 := _t1790
									if guard_result1194 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1791 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1791 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1193 := _t1791
										if guard_result1193 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1187 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1188 := fields1187
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1189 := unwrapped_fields1188[0].(string)
											p.pretty_name(field1189)
											field1190 := unwrapped_fields1188[1].([]*pb.RelTerm)
											if !(len(field1190) == 0) {
												p.newline()
												for i1192, elem1191 := range field1190 {
													if (i1192 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1191)
												}
											}
											p.dedent()
											p.write(")")
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
	return nil
}

func (p *PrettyPrinter) pretty_eq(msg *pb.Primitive) interface{} {
	flat1207 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1207 != nil {
		p.write(*flat1207)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1792 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1792 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1203 := _t1792
		unwrapped_fields1204 := fields1203
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1205 := unwrapped_fields1204[0].(*pb.Term)
		p.pretty_term(field1205)
		p.newline()
		field1206 := unwrapped_fields1204[1].(*pb.Term)
		p.pretty_term(field1206)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1212 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1212 != nil {
		p.write(*flat1212)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1793 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1793 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1208 := _t1793
		unwrapped_fields1209 := fields1208
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1210 := unwrapped_fields1209[0].(*pb.Term)
		p.pretty_term(field1210)
		p.newline()
		field1211 := unwrapped_fields1209[1].(*pb.Term)
		p.pretty_term(field1211)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1217 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1217 != nil {
		p.write(*flat1217)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1794 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1794 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1213 := _t1794
		unwrapped_fields1214 := fields1213
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1215 := unwrapped_fields1214[0].(*pb.Term)
		p.pretty_term(field1215)
		p.newline()
		field1216 := unwrapped_fields1214[1].(*pb.Term)
		p.pretty_term(field1216)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1222 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1222 != nil {
		p.write(*flat1222)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1795 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1795 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1218 := _t1795
		unwrapped_fields1219 := fields1218
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1220 := unwrapped_fields1219[0].(*pb.Term)
		p.pretty_term(field1220)
		p.newline()
		field1221 := unwrapped_fields1219[1].(*pb.Term)
		p.pretty_term(field1221)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1227 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1227 != nil {
		p.write(*flat1227)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1796 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1796 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1223 := _t1796
		unwrapped_fields1224 := fields1223
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1225 := unwrapped_fields1224[0].(*pb.Term)
		p.pretty_term(field1225)
		p.newline()
		field1226 := unwrapped_fields1224[1].(*pb.Term)
		p.pretty_term(field1226)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1233 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1233 != nil {
		p.write(*flat1233)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1797 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1797 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1228 := _t1797
		unwrapped_fields1229 := fields1228
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1230 := unwrapped_fields1229[0].(*pb.Term)
		p.pretty_term(field1230)
		p.newline()
		field1231 := unwrapped_fields1229[1].(*pb.Term)
		p.pretty_term(field1231)
		p.newline()
		field1232 := unwrapped_fields1229[2].(*pb.Term)
		p.pretty_term(field1232)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1239 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1239 != nil {
		p.write(*flat1239)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1798 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1798 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1234 := _t1798
		unwrapped_fields1235 := fields1234
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1236 := unwrapped_fields1235[0].(*pb.Term)
		p.pretty_term(field1236)
		p.newline()
		field1237 := unwrapped_fields1235[1].(*pb.Term)
		p.pretty_term(field1237)
		p.newline()
		field1238 := unwrapped_fields1235[2].(*pb.Term)
		p.pretty_term(field1238)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1245 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1245 != nil {
		p.write(*flat1245)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1799 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1799 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1240 := _t1799
		unwrapped_fields1241 := fields1240
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1242 := unwrapped_fields1241[0].(*pb.Term)
		p.pretty_term(field1242)
		p.newline()
		field1243 := unwrapped_fields1241[1].(*pb.Term)
		p.pretty_term(field1243)
		p.newline()
		field1244 := unwrapped_fields1241[2].(*pb.Term)
		p.pretty_term(field1244)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1251 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1251 != nil {
		p.write(*flat1251)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1800 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1800 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1246 := _t1800
		unwrapped_fields1247 := fields1246
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1248 := unwrapped_fields1247[0].(*pb.Term)
		p.pretty_term(field1248)
		p.newline()
		field1249 := unwrapped_fields1247[1].(*pb.Term)
		p.pretty_term(field1249)
		p.newline()
		field1250 := unwrapped_fields1247[2].(*pb.Term)
		p.pretty_term(field1250)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1256 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1256 != nil {
		p.write(*flat1256)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1801 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1801 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1254 := _t1801
		if deconstruct_result1254 != nil {
			unwrapped1255 := deconstruct_result1254
			p.pretty_specialized_value(unwrapped1255)
		} else {
			_dollar_dollar := msg
			var _t1802 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1802 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1252 := _t1802
			if deconstruct_result1252 != nil {
				unwrapped1253 := deconstruct_result1252
				p.pretty_term(unwrapped1253)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1258 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1258 != nil {
		p.write(*flat1258)
		return nil
	} else {
		fields1257 := msg
		p.write("#")
		p.pretty_raw_value(fields1257)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1265 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1265 != nil {
		p.write(*flat1265)
		return nil
	} else {
		_dollar_dollar := msg
		fields1259 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1260 := fields1259
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1261 := unwrapped_fields1260[0].(string)
		p.pretty_name(field1261)
		field1262 := unwrapped_fields1260[1].([]*pb.RelTerm)
		if !(len(field1262) == 0) {
			p.newline()
			for i1264, elem1263 := range field1262 {
				if (i1264 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1263)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1270 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1270 != nil {
		p.write(*flat1270)
		return nil
	} else {
		_dollar_dollar := msg
		fields1266 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1267 := fields1266
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1268 := unwrapped_fields1267[0].(*pb.Term)
		p.pretty_term(field1268)
		p.newline()
		field1269 := unwrapped_fields1267[1].(*pb.Term)
		p.pretty_term(field1269)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1274 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1274 != nil {
		p.write(*flat1274)
		return nil
	} else {
		fields1271 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1271) == 0) {
			p.newline()
			for i1273, elem1272 := range fields1271 {
				if (i1273 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1272)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1281 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1281 != nil {
		p.write(*flat1281)
		return nil
	} else {
		_dollar_dollar := msg
		fields1275 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1276 := fields1275
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1277 := unwrapped_fields1276[0].(string)
		p.pretty_name(field1277)
		field1278 := unwrapped_fields1276[1].([]*pb.Value)
		if !(len(field1278) == 0) {
			p.newline()
			for i1280, elem1279 := range field1278 {
				if (i1280 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1279)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1290 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1290 != nil {
		p.write(*flat1290)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1803 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1803 = _dollar_dollar.GetAttrs()
		}
		fields1282 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1803}
		unwrapped_fields1283 := fields1282
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1284 := unwrapped_fields1283[0].([]*pb.RelationId)
		if !(len(field1284) == 0) {
			p.newline()
			for i1286, elem1285 := range field1284 {
				if (i1286 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1285)
			}
		}
		p.newline()
		field1287 := unwrapped_fields1283[1].(*pb.Script)
		p.pretty_script(field1287)
		field1288 := unwrapped_fields1283[2].([]*pb.Attribute)
		if field1288 != nil {
			p.newline()
			opt_val1289 := field1288
			p.pretty_attrs(opt_val1289)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1295 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1295 != nil {
		p.write(*flat1295)
		return nil
	} else {
		_dollar_dollar := msg
		fields1291 := _dollar_dollar.GetConstructs()
		unwrapped_fields1292 := fields1291
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1292) == 0) {
			p.newline()
			for i1294, elem1293 := range unwrapped_fields1292 {
				if (i1294 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1293)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1300 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1300 != nil {
		p.write(*flat1300)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1804 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1804 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1298 := _t1804
		if deconstruct_result1298 != nil {
			unwrapped1299 := deconstruct_result1298
			p.pretty_loop(unwrapped1299)
		} else {
			_dollar_dollar := msg
			var _t1805 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1805 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1296 := _t1805
			if deconstruct_result1296 != nil {
				unwrapped1297 := deconstruct_result1296
				p.pretty_instruction(unwrapped1297)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1307 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1307 != nil {
		p.write(*flat1307)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1806 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1806 = _dollar_dollar.GetAttrs()
		}
		fields1301 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1806}
		unwrapped_fields1302 := fields1301
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1303 := unwrapped_fields1302[0].([]*pb.Instruction)
		p.pretty_init(field1303)
		p.newline()
		field1304 := unwrapped_fields1302[1].(*pb.Script)
		p.pretty_script(field1304)
		field1305 := unwrapped_fields1302[2].([]*pb.Attribute)
		if field1305 != nil {
			p.newline()
			opt_val1306 := field1305
			p.pretty_attrs(opt_val1306)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1311 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1311 != nil {
		p.write(*flat1311)
		return nil
	} else {
		fields1308 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1308) == 0) {
			p.newline()
			for i1310, elem1309 := range fields1308 {
				if (i1310 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1309)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1322 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1322 != nil {
		p.write(*flat1322)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1807 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1807 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1320 := _t1807
		if deconstruct_result1320 != nil {
			unwrapped1321 := deconstruct_result1320
			p.pretty_assign(unwrapped1321)
		} else {
			_dollar_dollar := msg
			var _t1808 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1808 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1318 := _t1808
			if deconstruct_result1318 != nil {
				unwrapped1319 := deconstruct_result1318
				p.pretty_upsert(unwrapped1319)
			} else {
				_dollar_dollar := msg
				var _t1809 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1809 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1316 := _t1809
				if deconstruct_result1316 != nil {
					unwrapped1317 := deconstruct_result1316
					p.pretty_break(unwrapped1317)
				} else {
					_dollar_dollar := msg
					var _t1810 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1810 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1314 := _t1810
					if deconstruct_result1314 != nil {
						unwrapped1315 := deconstruct_result1314
						p.pretty_monoid_def(unwrapped1315)
					} else {
						_dollar_dollar := msg
						var _t1811 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1811 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1312 := _t1811
						if deconstruct_result1312 != nil {
							unwrapped1313 := deconstruct_result1312
							p.pretty_monus_def(unwrapped1313)
						} else {
							panic(ParseError{msg: "No matching rule for instruction"})
						}
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_assign(msg *pb.Assign) interface{} {
	flat1329 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1329 != nil {
		p.write(*flat1329)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1812 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1812 = _dollar_dollar.GetAttrs()
		}
		fields1323 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1812}
		unwrapped_fields1324 := fields1323
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1325 := unwrapped_fields1324[0].(*pb.RelationId)
		p.pretty_relation_id(field1325)
		p.newline()
		field1326 := unwrapped_fields1324[1].(*pb.Abstraction)
		p.pretty_abstraction(field1326)
		field1327 := unwrapped_fields1324[2].([]*pb.Attribute)
		if field1327 != nil {
			p.newline()
			opt_val1328 := field1327
			p.pretty_attrs(opt_val1328)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1336 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1336 != nil {
		p.write(*flat1336)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1813 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1813 = _dollar_dollar.GetAttrs()
		}
		fields1330 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1813}
		unwrapped_fields1331 := fields1330
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1332 := unwrapped_fields1331[0].(*pb.RelationId)
		p.pretty_relation_id(field1332)
		p.newline()
		field1333 := unwrapped_fields1331[1].([]interface{})
		p.pretty_abstraction_with_arity(field1333)
		field1334 := unwrapped_fields1331[2].([]*pb.Attribute)
		if field1334 != nil {
			p.newline()
			opt_val1335 := field1334
			p.pretty_attrs(opt_val1335)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1341 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1341 != nil {
		p.write(*flat1341)
		return nil
	} else {
		_dollar_dollar := msg
		_t1814 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1337 := []interface{}{_t1814, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1338 := fields1337
		p.write("(")
		p.indent()
		field1339 := unwrapped_fields1338[0].([]interface{})
		p.pretty_bindings(field1339)
		p.newline()
		field1340 := unwrapped_fields1338[1].(*pb.Formula)
		p.pretty_formula(field1340)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1348 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1348 != nil {
		p.write(*flat1348)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1815 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1815 = _dollar_dollar.GetAttrs()
		}
		fields1342 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1815}
		unwrapped_fields1343 := fields1342
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1344 := unwrapped_fields1343[0].(*pb.RelationId)
		p.pretty_relation_id(field1344)
		p.newline()
		field1345 := unwrapped_fields1343[1].(*pb.Abstraction)
		p.pretty_abstraction(field1345)
		field1346 := unwrapped_fields1343[2].([]*pb.Attribute)
		if field1346 != nil {
			p.newline()
			opt_val1347 := field1346
			p.pretty_attrs(opt_val1347)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1356 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1356 != nil {
		p.write(*flat1356)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1816 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1816 = _dollar_dollar.GetAttrs()
		}
		fields1349 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1816}
		unwrapped_fields1350 := fields1349
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1351 := unwrapped_fields1350[0].(*pb.Monoid)
		p.pretty_monoid(field1351)
		p.newline()
		field1352 := unwrapped_fields1350[1].(*pb.RelationId)
		p.pretty_relation_id(field1352)
		p.newline()
		field1353 := unwrapped_fields1350[2].([]interface{})
		p.pretty_abstraction_with_arity(field1353)
		field1354 := unwrapped_fields1350[3].([]*pb.Attribute)
		if field1354 != nil {
			p.newline()
			opt_val1355 := field1354
			p.pretty_attrs(opt_val1355)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1365 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1365 != nil {
		p.write(*flat1365)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1817 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1817 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1363 := _t1817
		if deconstruct_result1363 != nil {
			unwrapped1364 := deconstruct_result1363
			p.pretty_or_monoid(unwrapped1364)
		} else {
			_dollar_dollar := msg
			var _t1818 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1818 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1361 := _t1818
			if deconstruct_result1361 != nil {
				unwrapped1362 := deconstruct_result1361
				p.pretty_min_monoid(unwrapped1362)
			} else {
				_dollar_dollar := msg
				var _t1819 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1819 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1359 := _t1819
				if deconstruct_result1359 != nil {
					unwrapped1360 := deconstruct_result1359
					p.pretty_max_monoid(unwrapped1360)
				} else {
					_dollar_dollar := msg
					var _t1820 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1820 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1357 := _t1820
					if deconstruct_result1357 != nil {
						unwrapped1358 := deconstruct_result1357
						p.pretty_sum_monoid(unwrapped1358)
					} else {
						panic(ParseError{msg: "No matching rule for monoid"})
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_or_monoid(msg *pb.OrMonoid) interface{} {
	fields1366 := msg
	_ = fields1366
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1369 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1369 != nil {
		p.write(*flat1369)
		return nil
	} else {
		_dollar_dollar := msg
		fields1367 := _dollar_dollar.GetType()
		unwrapped_fields1368 := fields1367
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1368)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1372 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1372 != nil {
		p.write(*flat1372)
		return nil
	} else {
		_dollar_dollar := msg
		fields1370 := _dollar_dollar.GetType()
		unwrapped_fields1371 := fields1370
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1371)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1375 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1375 != nil {
		p.write(*flat1375)
		return nil
	} else {
		_dollar_dollar := msg
		fields1373 := _dollar_dollar.GetType()
		unwrapped_fields1374 := fields1373
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1374)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1383 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1383 != nil {
		p.write(*flat1383)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1821 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1821 = _dollar_dollar.GetAttrs()
		}
		fields1376 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1821}
		unwrapped_fields1377 := fields1376
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1378 := unwrapped_fields1377[0].(*pb.Monoid)
		p.pretty_monoid(field1378)
		p.newline()
		field1379 := unwrapped_fields1377[1].(*pb.RelationId)
		p.pretty_relation_id(field1379)
		p.newline()
		field1380 := unwrapped_fields1377[2].([]interface{})
		p.pretty_abstraction_with_arity(field1380)
		field1381 := unwrapped_fields1377[3].([]*pb.Attribute)
		if field1381 != nil {
			p.newline()
			opt_val1382 := field1381
			p.pretty_attrs(opt_val1382)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1390 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1390 != nil {
		p.write(*flat1390)
		return nil
	} else {
		_dollar_dollar := msg
		fields1384 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1385 := fields1384
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1386 := unwrapped_fields1385[0].(*pb.RelationId)
		p.pretty_relation_id(field1386)
		p.newline()
		field1387 := unwrapped_fields1385[1].(*pb.Abstraction)
		p.pretty_abstraction(field1387)
		p.newline()
		field1388 := unwrapped_fields1385[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1388)
		p.newline()
		field1389 := unwrapped_fields1385[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1389)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1394 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1394 != nil {
		p.write(*flat1394)
		return nil
	} else {
		fields1391 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1391) == 0) {
			p.newline()
			for i1393, elem1392 := range fields1391 {
				if (i1393 > 0) {
					p.newline()
				}
				p.pretty_var(elem1392)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1398 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1398 != nil {
		p.write(*flat1398)
		return nil
	} else {
		fields1395 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1395) == 0) {
			p.newline()
			for i1397, elem1396 := range fields1395 {
				if (i1397 > 0) {
					p.newline()
				}
				p.pretty_var(elem1396)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1407 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1407 != nil {
		p.write(*flat1407)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1822 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1822 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1405 := _t1822
		if deconstruct_result1405 != nil {
			unwrapped1406 := deconstruct_result1405
			p.pretty_edb(unwrapped1406)
		} else {
			_dollar_dollar := msg
			var _t1823 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1823 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1403 := _t1823
			if deconstruct_result1403 != nil {
				unwrapped1404 := deconstruct_result1403
				p.pretty_betree_relation(unwrapped1404)
			} else {
				_dollar_dollar := msg
				var _t1824 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1824 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1401 := _t1824
				if deconstruct_result1401 != nil {
					unwrapped1402 := deconstruct_result1401
					p.pretty_csv_data(unwrapped1402)
				} else {
					_dollar_dollar := msg
					var _t1825 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1825 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1399 := _t1825
					if deconstruct_result1399 != nil {
						unwrapped1400 := deconstruct_result1399
						p.pretty_iceberg_data(unwrapped1400)
					} else {
						panic(ParseError{msg: "No matching rule for data"})
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb(msg *pb.EDB) interface{} {
	flat1413 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1413 != nil {
		p.write(*flat1413)
		return nil
	} else {
		_dollar_dollar := msg
		fields1408 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1409 := fields1408
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1410 := unwrapped_fields1409[0].(*pb.RelationId)
		p.pretty_relation_id(field1410)
		p.newline()
		field1411 := unwrapped_fields1409[1].([]string)
		p.pretty_edb_path(field1411)
		p.newline()
		field1412 := unwrapped_fields1409[2].([]*pb.Type)
		p.pretty_edb_types(field1412)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1417 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1417 != nil {
		p.write(*flat1417)
		return nil
	} else {
		fields1414 := msg
		p.write("[")
		p.indent()
		for i1416, elem1415 := range fields1414 {
			if (i1416 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1415))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1421 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1421 != nil {
		p.write(*flat1421)
		return nil
	} else {
		fields1418 := msg
		p.write("[")
		p.indent()
		for i1420, elem1419 := range fields1418 {
			if (i1420 > 0) {
				p.newline()
			}
			p.pretty_type(elem1419)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1426 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1426 != nil {
		p.write(*flat1426)
		return nil
	} else {
		_dollar_dollar := msg
		fields1422 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1423 := fields1422
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1424 := unwrapped_fields1423[0].(*pb.RelationId)
		p.pretty_relation_id(field1424)
		p.newline()
		field1425 := unwrapped_fields1423[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1425)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1432 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1432 != nil {
		p.write(*flat1432)
		return nil
	} else {
		_dollar_dollar := msg
		_t1826 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1427 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1826}
		unwrapped_fields1428 := fields1427
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1429 := unwrapped_fields1428[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1429)
		p.newline()
		field1430 := unwrapped_fields1428[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1430)
		p.newline()
		field1431 := unwrapped_fields1428[2].([][]interface{})
		p.pretty_config_dict(field1431)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1436 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1436 != nil {
		p.write(*flat1436)
		return nil
	} else {
		fields1433 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1433) == 0) {
			p.newline()
			for i1435, elem1434 := range fields1433 {
				if (i1435 > 0) {
					p.newline()
				}
				p.pretty_type(elem1434)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1440 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1440 != nil {
		p.write(*flat1440)
		return nil
	} else {
		fields1437 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1437) == 0) {
			p.newline()
			for i1439, elem1438 := range fields1437 {
				if (i1439 > 0) {
					p.newline()
				}
				p.pretty_type(elem1438)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1450 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1450 != nil {
		p.write(*flat1450)
		return nil
	} else {
		_dollar_dollar := msg
		_t1827 := p.deconstruct_csv_data_columns_optional(_dollar_dollar)
		_t1828 := p.deconstruct_csv_data_relations_optional(_dollar_dollar)
		fields1441 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _t1827, _t1828, _dollar_dollar.GetAsof()}
		unwrapped_fields1442 := fields1441
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1443 := unwrapped_fields1442[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1443)
		p.newline()
		field1444 := unwrapped_fields1442[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1444)
		field1445 := unwrapped_fields1442[2].([]*pb.GNFColumn)
		if field1445 != nil {
			p.newline()
			opt_val1446 := field1445
			p.pretty_gnf_columns(opt_val1446)
		}
		field1447 := unwrapped_fields1442[3].(*pb.TargetRelations)
		if field1447 != nil {
			p.newline()
			opt_val1448 := field1447
			p.pretty_target_relations(opt_val1448)
		}
		p.newline()
		field1449 := unwrapped_fields1442[4].(string)
		p.pretty_csv_asof(field1449)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1457 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1457 != nil {
		p.write(*flat1457)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1829 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1829 = _dollar_dollar.GetPaths()
		}
		var _t1830 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1830 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1451 := []interface{}{_t1829, _t1830}
		unwrapped_fields1452 := fields1451
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1453 := unwrapped_fields1452[0].([]string)
		if field1453 != nil {
			p.newline()
			opt_val1454 := field1453
			p.pretty_csv_locator_paths(opt_val1454)
		}
		field1455 := unwrapped_fields1452[1].(*string)
		if field1455 != nil {
			p.newline()
			opt_val1456 := *field1455
			p.pretty_csv_locator_inline_data(opt_val1456)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1461 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1461 != nil {
		p.write(*flat1461)
		return nil
	} else {
		fields1458 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1458) == 0) {
			p.newline()
			for i1460, elem1459 := range fields1458 {
				if (i1460 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1459))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1463 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1463 != nil {
		p.write(*flat1463)
		return nil
	} else {
		fields1462 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1462))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1469 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1469 != nil {
		p.write(*flat1469)
		return nil
	} else {
		_dollar_dollar := msg
		_t1831 := p.deconstruct_csv_config(_dollar_dollar)
		_t1832 := p.deconstruct_csv_storage_integration_optional(_dollar_dollar)
		fields1464 := []interface{}{_t1831, _t1832}
		unwrapped_fields1465 := fields1464
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		field1466 := unwrapped_fields1465[0].([][]interface{})
		p.pretty_config_dict(field1466)
		field1467 := unwrapped_fields1465[1].([][]interface{})
		if field1467 != nil {
			p.newline()
			opt_val1468 := field1467
			p.pretty__storage_integration(opt_val1468)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty__storage_integration(msg [][]interface{}) interface{} {
	flat1471 := p.tryFlat(msg, func() { p.pretty__storage_integration(msg) })
	if flat1471 != nil {
		p.write(*flat1471)
		return nil
	} else {
		fields1470 := msg
		p.write("(")
		p.write("storage_integration")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(fields1470)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1475 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1475 != nil {
		p.write(*flat1475)
		return nil
	} else {
		fields1472 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1472) == 0) {
			p.newline()
			for i1474, elem1473 := range fields1472 {
				if (i1474 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1473)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1484 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1484 != nil {
		p.write(*flat1484)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1833 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1833 = _dollar_dollar.GetTargetId()
		}
		fields1476 := []interface{}{_dollar_dollar.GetColumnPath(), _t1833, _dollar_dollar.GetTypes()}
		unwrapped_fields1477 := fields1476
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1478 := unwrapped_fields1477[0].([]string)
		p.pretty_gnf_column_path(field1478)
		field1479 := unwrapped_fields1477[1].(*pb.RelationId)
		if field1479 != nil {
			p.newline()
			opt_val1480 := field1479
			p.pretty_relation_id(opt_val1480)
		}
		p.newline()
		p.write("[")
		field1481 := unwrapped_fields1477[2].([]*pb.Type)
		for i1483, elem1482 := range field1481 {
			if (i1483 > 0) {
				p.newline()
			}
			p.pretty_type(elem1482)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1491 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1491 != nil {
		p.write(*flat1491)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1834 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1834 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1489 := _t1834
		if deconstruct_result1489 != nil {
			unwrapped1490 := *deconstruct_result1489
			p.write(p.formatStringValue(unwrapped1490))
		} else {
			_dollar_dollar := msg
			var _t1835 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1835 = _dollar_dollar
			}
			deconstruct_result1485 := _t1835
			if deconstruct_result1485 != nil {
				unwrapped1486 := deconstruct_result1485
				p.write("[")
				p.indent()
				for i1488, elem1487 := range unwrapped1486 {
					if (i1488 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1487))
				}
				p.dedent()
				p.write("]")
			} else {
				panic(ParseError{msg: "No matching rule for gnf_column_path"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_target_relations(msg *pb.TargetRelations) interface{} {
	flat1498 := p.tryFlat(msg, func() { p.pretty_target_relations(msg) })
	if flat1498 != nil {
		p.write(*flat1498)
		return nil
	} else {
		_dollar_dollar := msg
		_t1836 := p.deconstruct_relation_keys(_dollar_dollar)
		_t1837 := p.deconstruct_load_errors_optional(_dollar_dollar)
		fields1492 := []interface{}{_t1836, _dollar_dollar, _t1837}
		unwrapped_fields1493 := fields1492
		p.write("(")
		p.write("relations")
		p.indentSexp()
		p.newline()
		field1494 := unwrapped_fields1493[0].([]interface{})
		p.pretty_relation_keys(field1494)
		p.newline()
		field1495 := unwrapped_fields1493[1].(*pb.TargetRelations)
		p.pretty_relation_body(field1495)
		field1496 := unwrapped_fields1493[2].(*pb.RelationId)
		if field1496 != nil {
			p.newline()
			opt_val1497 := field1496
			p.pretty_load_errors(opt_val1497)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_keys(msg []interface{}) interface{} {
	flat1505 := p.tryFlat(msg, func() { p.pretty_relation_keys(msg) })
	if flat1505 != nil {
		p.write(*flat1505)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1838 []*pb.NamedColumn
		if !(_dollar_dollar[1].(bool)) {
			_t1838 = _dollar_dollar[0].([]*pb.NamedColumn)
		}
		deconstruct_result1501 := _t1838
		if deconstruct_result1501 != nil {
			unwrapped1502 := deconstruct_result1501
			p.write("(")
			p.write("keys")
			p.indentSexp()
			if !(len(unwrapped1502) == 0) {
				p.newline()
				for i1504, elem1503 := range unwrapped1502 {
					if (i1504 > 0) {
						p.newline()
					}
					p.pretty_named_column(elem1503)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1839 []interface{}
			if _dollar_dollar[1].(bool) {
				_t1839 = []interface{}{}
			}
			deconstruct_result1499 := _t1839
			if deconstruct_result1499 != nil {
				unwrapped1500 := deconstruct_result1499
				_ = unwrapped1500
				p.write("(")
				p.write("keys")
				p.newline()
				p.write("synthetic")
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for relation_keys"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_named_column(msg *pb.NamedColumn) interface{} {
	flat1510 := p.tryFlat(msg, func() { p.pretty_named_column(msg) })
	if flat1510 != nil {
		p.write(*flat1510)
		return nil
	} else {
		_dollar_dollar := msg
		fields1506 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetType()}
		unwrapped_fields1507 := fields1506
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1508 := unwrapped_fields1507[0].(string)
		p.write(p.formatStringValue(field1508))
		p.newline()
		field1509 := unwrapped_fields1507[1].(*pb.Type)
		p.pretty_type(field1509)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_body(msg *pb.TargetRelations) interface{} {
	flat1517 := p.tryFlat(msg, func() { p.pretty_relation_body(msg) })
	if flat1517 != nil {
		p.write(*flat1517)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1840 []*pb.TargetRelation
		if hasProtoField(_dollar_dollar, "plain") {
			_t1840 = _dollar_dollar.GetPlain().GetTargets()
		}
		deconstruct_result1515 := _t1840
		if deconstruct_result1515 != nil {
			unwrapped1516 := deconstruct_result1515
			p.pretty_non_cdc_relations(unwrapped1516)
		} else {
			_dollar_dollar := msg
			var _t1841 []interface{}
			if hasProtoField(_dollar_dollar, "cdc") {
				_t1841 = []interface{}{_dollar_dollar.GetCdc().GetInserts(), _dollar_dollar.GetCdc().GetDeletes()}
			}
			deconstruct_result1511 := _t1841
			if deconstruct_result1511 != nil {
				unwrapped1512 := deconstruct_result1511
				field1513 := unwrapped1512[0].([]*pb.TargetRelation)
				p.pretty_cdc_inserts(field1513)
				p.write(" ")
				field1514 := unwrapped1512[1].([]*pb.TargetRelation)
				p.pretty_cdc_deletes(field1514)
			} else {
				panic(ParseError{msg: "No matching rule for relation_body"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_non_cdc_relations(msg []*pb.TargetRelation) interface{} {
	flat1521 := p.tryFlat(msg, func() { p.pretty_non_cdc_relations(msg) })
	if flat1521 != nil {
		p.write(*flat1521)
		return nil
	} else {
		fields1518 := msg
		for i1520, elem1519 := range fields1518 {
			if (i1520 > 0) {
				p.newline()
			}
			p.pretty_target_relation(elem1519)
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_target_relation(msg *pb.TargetRelation) interface{} {
	flat1528 := p.tryFlat(msg, func() { p.pretty_target_relation(msg) })
	if flat1528 != nil {
		p.write(*flat1528)
		return nil
	} else {
		_dollar_dollar := msg
		fields1522 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetValues()}
		unwrapped_fields1523 := fields1522
		p.write("(")
		p.write("relation")
		p.indentSexp()
		p.newline()
		field1524 := unwrapped_fields1523[0].(*pb.RelationId)
		p.pretty_relation_id(field1524)
		field1525 := unwrapped_fields1523[1].([]*pb.NamedColumn)
		if !(len(field1525) == 0) {
			p.newline()
			for i1527, elem1526 := range field1525 {
				if (i1527 > 0) {
					p.newline()
				}
				p.pretty_named_column(elem1526)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_inserts(msg []*pb.TargetRelation) interface{} {
	flat1532 := p.tryFlat(msg, func() { p.pretty_cdc_inserts(msg) })
	if flat1532 != nil {
		p.write(*flat1532)
		return nil
	} else {
		fields1529 := msg
		p.write("(")
		p.write("inserts")
		p.indentSexp()
		if !(len(fields1529) == 0) {
			p.newline()
			for i1531, elem1530 := range fields1529 {
				if (i1531 > 0) {
					p.newline()
				}
				p.pretty_target_relation(elem1530)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_deletes(msg []*pb.TargetRelation) interface{} {
	flat1536 := p.tryFlat(msg, func() { p.pretty_cdc_deletes(msg) })
	if flat1536 != nil {
		p.write(*flat1536)
		return nil
	} else {
		fields1533 := msg
		p.write("(")
		p.write("deletes")
		p.indentSexp()
		if !(len(fields1533) == 0) {
			p.newline()
			for i1535, elem1534 := range fields1533 {
				if (i1535 > 0) {
					p.newline()
				}
				p.pretty_target_relation(elem1534)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_load_errors(msg *pb.RelationId) interface{} {
	flat1538 := p.tryFlat(msg, func() { p.pretty_load_errors(msg) })
	if flat1538 != nil {
		p.write(*flat1538)
		return nil
	} else {
		fields1537 := msg
		p.write("(")
		p.write("load_errors")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1537)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1540 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1540 != nil {
		p.write(*flat1540)
		return nil
	} else {
		fields1539 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1539))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1551 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1551 != nil {
		p.write(*flat1551)
		return nil
	} else {
		_dollar_dollar := msg
		_t1842 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1843 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1541 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1842, _t1843, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1542 := fields1541
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1543 := unwrapped_fields1542[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1543)
		p.newline()
		field1544 := unwrapped_fields1542[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1544)
		p.newline()
		field1545 := unwrapped_fields1542[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1545)
		field1546 := unwrapped_fields1542[3].(*string)
		if field1546 != nil {
			p.newline()
			opt_val1547 := *field1546
			p.pretty_iceberg_from_snapshot(opt_val1547)
		}
		field1548 := unwrapped_fields1542[4].(*string)
		if field1548 != nil {
			p.newline()
			opt_val1549 := *field1548
			p.pretty_iceberg_to_snapshot(opt_val1549)
		}
		p.newline()
		field1550 := unwrapped_fields1542[5].(bool)
		p.pretty_boolean_value(field1550)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1557 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1557 != nil {
		p.write(*flat1557)
		return nil
	} else {
		_dollar_dollar := msg
		fields1552 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1553 := fields1552
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1554 := unwrapped_fields1553[0].(string)
		p.pretty_iceberg_locator_table_name(field1554)
		p.newline()
		field1555 := unwrapped_fields1553[1].([]string)
		p.pretty_iceberg_locator_namespace(field1555)
		p.newline()
		field1556 := unwrapped_fields1553[2].(string)
		p.pretty_iceberg_locator_warehouse(field1556)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1559 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1559 != nil {
		p.write(*flat1559)
		return nil
	} else {
		fields1558 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1558))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1563 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1563 != nil {
		p.write(*flat1563)
		return nil
	} else {
		fields1560 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1560) == 0) {
			p.newline()
			for i1562, elem1561 := range fields1560 {
				if (i1562 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1561))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1565 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1565 != nil {
		p.write(*flat1565)
		return nil
	} else {
		fields1564 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1564))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1573 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1573 != nil {
		p.write(*flat1573)
		return nil
	} else {
		_dollar_dollar := msg
		_t1844 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1566 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1844, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1567 := fields1566
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1568 := unwrapped_fields1567[0].(string)
		p.pretty_iceberg_catalog_uri(field1568)
		field1569 := unwrapped_fields1567[1].(*string)
		if field1569 != nil {
			p.newline()
			opt_val1570 := *field1569
			p.pretty_iceberg_catalog_config_scope(opt_val1570)
		}
		p.newline()
		field1571 := unwrapped_fields1567[2].([][]interface{})
		p.pretty_iceberg_properties(field1571)
		p.newline()
		field1572 := unwrapped_fields1567[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1572)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1575 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1575 != nil {
		p.write(*flat1575)
		return nil
	} else {
		fields1574 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1574))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1577 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1577 != nil {
		p.write(*flat1577)
		return nil
	} else {
		fields1576 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1576))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1581 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1581 != nil {
		p.write(*flat1581)
		return nil
	} else {
		fields1578 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1578) == 0) {
			p.newline()
			for i1580, elem1579 := range fields1578 {
				if (i1580 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1579)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1586 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1586 != nil {
		p.write(*flat1586)
		return nil
	} else {
		_dollar_dollar := msg
		fields1582 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1583 := fields1582
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1584 := unwrapped_fields1583[0].(string)
		p.write(p.formatStringValue(field1584))
		p.newline()
		field1585 := unwrapped_fields1583[1].(string)
		p.write(p.formatStringValue(field1585))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1590 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1590 != nil {
		p.write(*flat1590)
		return nil
	} else {
		fields1587 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1587) == 0) {
			p.newline()
			for i1589, elem1588 := range fields1587 {
				if (i1589 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1588)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1595 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1595 != nil {
		p.write(*flat1595)
		return nil
	} else {
		_dollar_dollar := msg
		_t1845 := p.mask_secret_value(_dollar_dollar)
		fields1591 := []interface{}{_dollar_dollar[0].(string), _t1845}
		unwrapped_fields1592 := fields1591
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1593 := unwrapped_fields1592[0].(string)
		p.write(p.formatStringValue(field1593))
		p.newline()
		field1594 := unwrapped_fields1592[1].(string)
		p.write(p.formatStringValue(field1594))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1597 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1597 != nil {
		p.write(*flat1597)
		return nil
	} else {
		fields1596 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1596))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1599 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1599 != nil {
		p.write(*flat1599)
		return nil
	} else {
		fields1598 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1598))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1602 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1602 != nil {
		p.write(*flat1602)
		return nil
	} else {
		_dollar_dollar := msg
		fields1600 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1601 := fields1600
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1601)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1607 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1607 != nil {
		p.write(*flat1607)
		return nil
	} else {
		_dollar_dollar := msg
		fields1603 := _dollar_dollar.GetRelations()
		unwrapped_fields1604 := fields1603
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1604) == 0) {
			p.newline()
			for i1606, elem1605 := range unwrapped_fields1604 {
				if (i1606 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1605)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1614 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1614 != nil {
		p.write(*flat1614)
		return nil
	} else {
		_dollar_dollar := msg
		fields1608 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1609 := fields1608
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1610 := unwrapped_fields1609[0].([]string)
		p.pretty_edb_path(field1610)
		field1611 := unwrapped_fields1609[1].([]*pb.SnapshotMapping)
		if !(len(field1611) == 0) {
			p.newline()
			for i1613, elem1612 := range field1611 {
				if (i1613 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1612)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1619 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1619 != nil {
		p.write(*flat1619)
		return nil
	} else {
		_dollar_dollar := msg
		fields1615 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1616 := fields1615
		field1617 := unwrapped_fields1616[0].([]string)
		p.pretty_edb_path(field1617)
		p.write(" ")
		field1618 := unwrapped_fields1616[1].(*pb.RelationId)
		p.pretty_relation_id(field1618)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1623 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1623 != nil {
		p.write(*flat1623)
		return nil
	} else {
		fields1620 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1620) == 0) {
			p.newline()
			for i1622, elem1621 := range fields1620 {
				if (i1622 > 0) {
					p.newline()
				}
				p.pretty_read(elem1621)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1634 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1634 != nil {
		p.write(*flat1634)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1846 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1846 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1632 := _t1846
		if deconstruct_result1632 != nil {
			unwrapped1633 := deconstruct_result1632
			p.pretty_demand(unwrapped1633)
		} else {
			_dollar_dollar := msg
			var _t1847 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1847 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1630 := _t1847
			if deconstruct_result1630 != nil {
				unwrapped1631 := deconstruct_result1630
				p.pretty_output(unwrapped1631)
			} else {
				_dollar_dollar := msg
				var _t1848 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1848 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1628 := _t1848
				if deconstruct_result1628 != nil {
					unwrapped1629 := deconstruct_result1628
					p.pretty_what_if(unwrapped1629)
				} else {
					_dollar_dollar := msg
					var _t1849 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1849 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1626 := _t1849
					if deconstruct_result1626 != nil {
						unwrapped1627 := deconstruct_result1626
						p.pretty_abort(unwrapped1627)
					} else {
						_dollar_dollar := msg
						var _t1850 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1850 = _dollar_dollar.GetExport()
						}
						deconstruct_result1624 := _t1850
						if deconstruct_result1624 != nil {
							unwrapped1625 := deconstruct_result1624
							p.pretty_export(unwrapped1625)
						} else {
							panic(ParseError{msg: "No matching rule for read"})
						}
					}
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_demand(msg *pb.Demand) interface{} {
	flat1637 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1637 != nil {
		p.write(*flat1637)
		return nil
	} else {
		_dollar_dollar := msg
		fields1635 := _dollar_dollar.GetRelationId()
		unwrapped_fields1636 := fields1635
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1636)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1642 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1642 != nil {
		p.write(*flat1642)
		return nil
	} else {
		_dollar_dollar := msg
		fields1638 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1639 := fields1638
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1640 := unwrapped_fields1639[0].(string)
		p.pretty_name(field1640)
		p.newline()
		field1641 := unwrapped_fields1639[1].(*pb.RelationId)
		p.pretty_relation_id(field1641)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1647 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1647 != nil {
		p.write(*flat1647)
		return nil
	} else {
		_dollar_dollar := msg
		fields1643 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1644 := fields1643
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1645 := unwrapped_fields1644[0].(string)
		p.pretty_name(field1645)
		p.newline()
		field1646 := unwrapped_fields1644[1].(*pb.Epoch)
		p.pretty_epoch(field1646)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1653 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1653 != nil {
		p.write(*flat1653)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1851 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1851 = ptr(_dollar_dollar.GetName())
		}
		fields1648 := []interface{}{_t1851, _dollar_dollar.GetRelationId()}
		unwrapped_fields1649 := fields1648
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1650 := unwrapped_fields1649[0].(*string)
		if field1650 != nil {
			p.newline()
			opt_val1651 := *field1650
			p.pretty_name(opt_val1651)
		}
		p.newline()
		field1652 := unwrapped_fields1649[1].(*pb.RelationId)
		p.pretty_relation_id(field1652)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1658 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1658 != nil {
		p.write(*flat1658)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1852 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1852 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1656 := _t1852
		if deconstruct_result1656 != nil {
			unwrapped1657 := deconstruct_result1656
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1657)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1853 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1853 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1654 := _t1853
			if deconstruct_result1654 != nil {
				unwrapped1655 := deconstruct_result1654
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1655)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1669 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1669 != nil {
		p.write(*flat1669)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1854 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1855 := p.deconstruct_export_csv_output_location(_dollar_dollar)
			_t1854 = []interface{}{_t1855, _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1664 := _t1854
		if deconstruct_result1664 != nil {
			unwrapped1665 := deconstruct_result1664
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1666 := unwrapped1665[0].([]interface{})
			p.pretty_export_csv_output_location(field1666)
			p.newline()
			field1667 := unwrapped1665[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1667)
			p.newline()
			field1668 := unwrapped1665[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1668)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1856 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1857 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1856 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1857}
			}
			deconstruct_result1659 := _t1856
			if deconstruct_result1659 != nil {
				unwrapped1660 := deconstruct_result1659
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1661 := unwrapped1660[0].(string)
				p.pretty_export_csv_path(field1661)
				p.newline()
				field1662 := unwrapped1660[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1662)
				p.newline()
				field1663 := unwrapped1660[2].([][]interface{})
				p.pretty_config_dict(field1663)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export_csv_config"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_output_location(msg []interface{}) interface{} {
	flat1674 := p.tryFlat(msg, func() { p.pretty_export_csv_output_location(msg) })
	if flat1674 != nil {
		p.write(*flat1674)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1858 *string
		if _dollar_dollar[0].(string) != "" {
			_t1858 = ptr(_dollar_dollar[0].(string))
		}
		deconstruct_result1672 := _t1858
		if deconstruct_result1672 != nil {
			unwrapped1673 := *deconstruct_result1672
			p.write("(")
			p.write("path")
			p.indentSexp()
			p.newline()
			p.write(p.formatStringValue(unwrapped1673))
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1859 *string
			if _dollar_dollar[1].(string) != "" {
				_t1859 = ptr(_dollar_dollar[1].(string))
			}
			deconstruct_result1670 := _t1859
			if deconstruct_result1670 != nil {
				unwrapped1671 := *deconstruct_result1670
				p.write("(")
				p.write("transaction_output_name")
				p.indentSexp()
				p.newline()
				p.pretty_name(unwrapped1671)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export_csv_output_location"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1681 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1681 != nil {
		p.write(*flat1681)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1860 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1860 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1677 := _t1860
		if deconstruct_result1677 != nil {
			unwrapped1678 := deconstruct_result1677
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1678) == 0) {
				p.newline()
				for i1680, elem1679 := range unwrapped1678 {
					if (i1680 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1679)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1861 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1861 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1675 := _t1861
			if deconstruct_result1675 != nil {
				unwrapped1676 := deconstruct_result1675
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1676)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export_csv_source"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_column(msg *pb.ExportCSVColumn) interface{} {
	flat1686 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1686 != nil {
		p.write(*flat1686)
		return nil
	} else {
		_dollar_dollar := msg
		fields1682 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1683 := fields1682
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1684 := unwrapped_fields1683[0].(string)
		p.write(p.formatStringValue(field1684))
		p.newline()
		field1685 := unwrapped_fields1683[1].(*pb.RelationId)
		p.pretty_relation_id(field1685)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1688 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1688 != nil {
		p.write(*flat1688)
		return nil
	} else {
		fields1687 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1687))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1692 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1692 != nil {
		p.write(*flat1692)
		return nil
	} else {
		fields1689 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1689) == 0) {
			p.newline()
			for i1691, elem1690 := range fields1689 {
				if (i1691 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1690)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1701 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1701 != nil {
		p.write(*flat1701)
		return nil
	} else {
		_dollar_dollar := msg
		_t1862 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1693 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1862}
		unwrapped_fields1694 := fields1693
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1695 := unwrapped_fields1694[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1695)
		p.newline()
		field1696 := unwrapped_fields1694[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1696)
		p.newline()
		field1697 := unwrapped_fields1694[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1697)
		p.newline()
		field1698 := unwrapped_fields1694[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1698)
		field1699 := unwrapped_fields1694[4].([][]interface{})
		if field1699 != nil {
			p.newline()
			opt_val1700 := field1699
			p.pretty_config_dict(opt_val1700)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1703 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1703 != nil {
		p.write(*flat1703)
		return nil
	} else {
		fields1702 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1702)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1707 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1707 != nil {
		p.write(*flat1707)
		return nil
	} else {
		fields1704 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1704) == 0) {
			p.newline()
			for i1706, elem1705 := range fields1704 {
				if (i1706 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1705)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}


// --- Auto-generated printers for uncovered proto types ---

func (p *PrettyPrinter) pretty_debug_info(msg *pb.DebugInfo) interface{} {
	p.write("(debug_info")
	p.indentSexp()
	for _idx, _rid := range msg.GetIds() {
		p.newline()
		p.write("(")
		_t1917 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1917)
		p.write(" ")
		p.write(p.formatStringValue(msg.GetOrigNames()[_idx]))
		p.write(")")
	}
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_be_tree_config(msg *pb.BeTreeConfig) interface{} {
	p.write("(be_tree_config")
	p.indentSexp()
	p.newline()
	p.write(":epsilon ")
	p.write(formatFloat64(msg.GetEpsilon()))
	p.newline()
	p.write(":max_pivots ")
	p.write(fmt.Sprintf("%d", msg.GetMaxPivots()))
	p.newline()
	p.write(":max_deltas ")
	p.write(fmt.Sprintf("%d", msg.GetMaxDeltas()))
	p.newline()
	p.write(":max_leaf ")
	p.write(fmt.Sprintf("%d", msg.GetMaxLeaf()))
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_be_tree_locator(msg *pb.BeTreeLocator) interface{} {
	p.write("(be_tree_locator")
	p.indentSexp()
	p.newline()
	p.write(":element_count ")
	p.write(fmt.Sprintf("%d", msg.GetElementCount()))
	p.newline()
	p.write(":tree_height ")
	p.write(fmt.Sprintf("%d", msg.GetTreeHeight()))
	p.newline()
	p.write(":location ")
	if hasProtoField(msg, "root_pageid") {
		p.write("(:root_pageid ")
		p.pprintDispatch(msg.GetRootPageid())
		p.write(")")
	} else {
		if hasProtoField(msg, "inline_data") {
			p.write("(:inline_data ")
			p.write(fmt.Sprintf("0x%x", msg.GetInlineData()))
			p.write(")")
		} else {
			p.write("nothing")
		}
	}
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_cdc_targets(msg *pb.CDCTargets) interface{} {
	p.write("(cdc_targets")
	p.indentSexp()
	p.newline()
	p.write(":inserts ")
	p.write("(")
	for _idx, _elem := range msg.GetInserts() {
		if (_idx > 0) {
			p.write(" ")
		}
		p.pprintDispatch(_elem)
	}
	p.write(")")
	p.newline()
	p.write(":deletes ")
	p.write("(")
	for _idx, _elem := range msg.GetDeletes() {
		if (_idx > 0) {
			p.write(" ")
		}
		p.pprintDispatch(_elem)
	}
	p.write(")")
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_decimal_value(msg *pb.DecimalValue) interface{} {
	p.write(p.formatDecimal(msg))
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency(msg *pb.FunctionalDependency) interface{} {
	p.write("(functional_dependency")
	p.indentSexp()
	p.newline()
	p.write(":guard ")
	p.pprintDispatch(msg.GetGuard())
	p.newline()
	p.write(":keys ")
	p.write("(")
	for _idx, _elem := range msg.GetKeys() {
		if (_idx > 0) {
			p.write(" ")
		}
		p.pprintDispatch(_elem)
	}
	p.write(")")
	p.newline()
	p.write(":values ")
	p.write("(")
	for _idx, _elem := range msg.GetValues() {
		if (_idx > 0) {
			p.write(" ")
		}
		p.pprintDispatch(_elem)
	}
	p.write(")")
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_int128_value(msg *pb.Int128Value) interface{} {
	p.write(p.formatInt128(msg))
	return nil
}

func (p *PrettyPrinter) pretty_missing_value(msg *pb.MissingValue) interface{} {
	p.write("missing")
	return nil
}

func (p *PrettyPrinter) pretty_plain_targets(msg *pb.PlainTargets) interface{} {
	p.write("(plain_targets")
	p.indentSexp()
	p.newline()
	p.write(":targets ")
	p.write("(")
	for _idx, _elem := range msg.GetTargets() {
		if (_idx > 0) {
			p.write(" ")
		}
		p.pprintDispatch(_elem)
	}
	p.write(")")
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_storage_integration(msg *pb.StorageIntegration) interface{} {
	p.write("(storage_integration")
	p.indentSexp()
	p.newline()
	p.write(":provider ")
	p.write(p.formatStringValue(msg.GetProvider()))
	p.newline()
	p.write(":azure_sas_token ")
	p.write(p.formatStringValue(msg.GetAzureSasToken()))
	p.newline()
	p.write(":s3_region ")
	p.write(p.formatStringValue(msg.GetS3Region()))
	p.newline()
	p.write(":s3_access_key_id ")
	p.write(p.formatStringValue(msg.GetS3AccessKeyId()))
	p.newline()
	p.write(":s3_secret_access_key ")
	p.write(p.formatStringValue(msg.GetS3SecretAccessKey()))
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_u_int128_value(msg *pb.UInt128Value) interface{} {
	p.write(p.formatUint128(msg))
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns(msg *pb.ExportCSVColumns) interface{} {
	p.write("(export_csv_columns")
	p.indentSexp()
	p.newline()
	p.write(":columns ")
	p.write("(")
	for _idx, _elem := range msg.GetColumns() {
		if (_idx > 0) {
			p.write(" ")
		}
		p.pprintDispatch(_elem)
	}
	p.write(")")
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_ivm_config(msg *pb.IVMConfig) interface{} {
	p.write("(ivm_config")
	p.indentSexp()
	p.newline()
	p.write(":level ")
	p.pprintDispatch(msg.GetLevel())
	p.write(")")
	p.dedent()
	return nil
}

func (p *PrettyPrinter) pretty_maintenance_level(x pb.MaintenanceLevel) interface{} {
	if x == pb.MaintenanceLevel_MAINTENANCE_LEVEL_UNSPECIFIED {
		p.write("unspecified")
	} else {
		if x == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
			p.write("off")
		} else {
			if x == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
				p.write("auto")
			} else {
				if x == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
					p.write("all")
				}
			}
		}
	}
	return nil
}

// --- Dispatch function ---
func (p *PrettyPrinter) pprintDispatch(msg interface{}) {
	switch m := msg.(type) {
	case *pb.Transaction:
		p.pretty_transaction(m)
	case *pb.Configure:
		p.pretty_configure(m)
	case [][]interface{}:
		p.pretty_config_dict(m)
	case []interface{}:
		p.pretty_config_key_value(m)
	case *pb.Value:
		p.pretty_value(m)
	case *pb.DateValue:
		p.pretty_raw_date(m)
	case *pb.DateTimeValue:
		p.pretty_raw_datetime(m)
	case bool:
		p.pretty_boolean_value(m)
	case *pb.Sync:
		p.pretty_sync(m)
	case *pb.FragmentId:
		p.pretty_fragment_id(m)
	case *pb.Epoch:
		p.pretty_epoch(m)
	case []*pb.Write:
		p.pretty_epoch_writes(m)
	case *pb.Write:
		p.pretty_write(m)
	case *pb.Define:
		p.pretty_define(m)
	case *pb.Fragment:
		p.pretty_fragment(m)
	case *pb.Declaration:
		p.pretty_declaration(m)
	case *pb.Def:
		p.pretty_def(m)
	case *pb.RelationId:
		p.pretty_relation_id(m)
	case *pb.Abstraction:
		p.pretty_abstraction(m)
	case *pb.Binding:
		p.pretty_binding(m)
	case *pb.Type:
		p.pretty_type(m)
	case *pb.UnspecifiedType:
		p.pretty_unspecified_type(m)
	case *pb.StringType:
		p.pretty_string_type(m)
	case *pb.IntType:
		p.pretty_int_type(m)
	case *pb.FloatType:
		p.pretty_float_type(m)
	case *pb.UInt128Type:
		p.pretty_uint128_type(m)
	case *pb.Int128Type:
		p.pretty_int128_type(m)
	case *pb.DateType:
		p.pretty_date_type(m)
	case *pb.DateTimeType:
		p.pretty_datetime_type(m)
	case *pb.MissingType:
		p.pretty_missing_type(m)
	case *pb.DecimalType:
		p.pretty_decimal_type(m)
	case *pb.BooleanType:
		p.pretty_boolean_type(m)
	case *pb.Int32Type:
		p.pretty_int32_type(m)
	case *pb.Float32Type:
		p.pretty_float32_type(m)
	case *pb.UInt32Type:
		p.pretty_uint32_type(m)
	case []*pb.Binding:
		p.pretty_value_bindings(m)
	case *pb.Formula:
		p.pretty_formula(m)
	case *pb.Conjunction:
		p.pretty_conjunction(m)
	case *pb.Disjunction:
		p.pretty_disjunction(m)
	case *pb.Exists:
		p.pretty_exists(m)
	case *pb.Reduce:
		p.pretty_reduce(m)
	case []*pb.Term:
		p.pretty_terms(m)
	case *pb.Term:
		p.pretty_term(m)
	case *pb.Var:
		p.pretty_var(m)
	case *pb.Not:
		p.pretty_not(m)
	case *pb.FFI:
		p.pretty_ffi(m)
	case string:
		p.pretty_name(m)
	case []*pb.Abstraction:
		p.pretty_ffi_args(m)
	case *pb.Atom:
		p.pretty_atom(m)
	case *pb.Pragma:
		p.pretty_pragma(m)
	case *pb.Primitive:
		p.pretty_primitive(m)
	case *pb.RelTerm:
		p.pretty_rel_term(m)
	case *pb.RelAtom:
		p.pretty_rel_atom(m)
	case *pb.Cast:
		p.pretty_cast(m)
	case []*pb.Attribute:
		p.pretty_attrs(m)
	case *pb.Attribute:
		p.pretty_attribute(m)
	case *pb.Algorithm:
		p.pretty_algorithm(m)
	case *pb.Script:
		p.pretty_script(m)
	case *pb.Construct:
		p.pretty_construct(m)
	case *pb.Loop:
		p.pretty_loop(m)
	case []*pb.Instruction:
		p.pretty_init(m)
	case *pb.Instruction:
		p.pretty_instruction(m)
	case *pb.Assign:
		p.pretty_assign(m)
	case *pb.Upsert:
		p.pretty_upsert(m)
	case *pb.Break:
		p.pretty_break(m)
	case *pb.MonoidDef:
		p.pretty_monoid_def(m)
	case *pb.Monoid:
		p.pretty_monoid(m)
	case *pb.OrMonoid:
		p.pretty_or_monoid(m)
	case *pb.MinMonoid:
		p.pretty_min_monoid(m)
	case *pb.MaxMonoid:
		p.pretty_max_monoid(m)
	case *pb.SumMonoid:
		p.pretty_sum_monoid(m)
	case *pb.MonusDef:
		p.pretty_monus_def(m)
	case *pb.Constraint:
		p.pretty_constraint(m)
	case []*pb.Var:
		p.pretty_functional_dependency_keys(m)
	case *pb.Data:
		p.pretty_data(m)
	case *pb.EDB:
		p.pretty_edb(m)
	case []string:
		p.pretty_edb_path(m)
	case []*pb.Type:
		p.pretty_edb_types(m)
	case *pb.BeTreeRelation:
		p.pretty_betree_relation(m)
	case *pb.BeTreeInfo:
		p.pretty_betree_info(m)
	case *pb.CSVData:
		p.pretty_csv_data(m)
	case *pb.CSVLocator:
		p.pretty_csvlocator(m)
	case *pb.CSVConfig:
		p.pretty_csv_config(m)
	case []*pb.GNFColumn:
		p.pretty_gnf_columns(m)
	case *pb.GNFColumn:
		p.pretty_gnf_column(m)
	case *pb.TargetRelations:
		p.pretty_target_relations(m)
	case *pb.NamedColumn:
		p.pretty_named_column(m)
	case []*pb.TargetRelation:
		p.pretty_non_cdc_relations(m)
	case *pb.TargetRelation:
		p.pretty_target_relation(m)
	case *pb.IcebergData:
		p.pretty_iceberg_data(m)
	case *pb.IcebergLocator:
		p.pretty_iceberg_locator(m)
	case *pb.IcebergCatalogConfig:
		p.pretty_iceberg_catalog_config(m)
	case *pb.Undefine:
		p.pretty_undefine(m)
	case *pb.Context:
		p.pretty_context(m)
	case *pb.Snapshot:
		p.pretty_snapshot(m)
	case *pb.SnapshotMapping:
		p.pretty_snapshot_mapping(m)
	case []*pb.Read:
		p.pretty_epoch_reads(m)
	case *pb.Read:
		p.pretty_read(m)
	case *pb.Demand:
		p.pretty_demand(m)
	case *pb.Output:
		p.pretty_output(m)
	case *pb.WhatIf:
		p.pretty_what_if(m)
	case *pb.Abort:
		p.pretty_abort(m)
	case *pb.Export:
		p.pretty_export(m)
	case *pb.ExportCSVConfig:
		p.pretty_export_csv_config(m)
	case *pb.ExportCSVSource:
		p.pretty_export_csv_source(m)
	case *pb.ExportCSVColumn:
		p.pretty_export_csv_column(m)
	case []*pb.ExportCSVColumn:
		p.pretty_export_csv_columns_list(m)
	case *pb.ExportIcebergConfig:
		p.pretty_export_iceberg_config(m)
	case *pb.DebugInfo:
		p.pretty_debug_info(m)
	case *pb.BeTreeConfig:
		p.pretty_be_tree_config(m)
	case *pb.BeTreeLocator:
		p.pretty_be_tree_locator(m)
	case *pb.CDCTargets:
		p.pretty_cdc_targets(m)
	case *pb.DecimalValue:
		p.pretty_decimal_value(m)
	case *pb.FunctionalDependency:
		p.pretty_functional_dependency(m)
	case *pb.Int128Value:
		p.pretty_int128_value(m)
	case *pb.MissingValue:
		p.pretty_missing_value(m)
	case *pb.PlainTargets:
		p.pretty_plain_targets(m)
	case *pb.StorageIntegration:
		p.pretty_storage_integration(m)
	case *pb.UInt128Value:
		p.pretty_u_int128_value(m)
	case *pb.ExportCSVColumns:
		p.pretty_export_csv_columns(m)
	case *pb.IVMConfig:
		p.pretty_ivm_config(m)
	case pb.MaintenanceLevel:
		p.pretty_maintenance_level(m)
	default:
		panic(fmt.Sprintf("no pretty printer for %T", msg))
	}
}

// writeDebugInfo writes accumulated debug info as comments at the end of the output.
func (p *PrettyPrinter) writeDebugInfo() {
	if len(p.debugInfo) == 0 {
		return
	}
	// Collect and sort entries by name for deterministic output.
	type debugEntry struct {
		key  [2]uint64
		name string
	}
	entries := make([]debugEntry, 0, len(p.debugInfo))
	for key, name := range p.debugInfo {
		entries = append(entries, debugEntry{key, name})
	}
	sort.Slice(entries, func(i, j int) bool {
		return entries[i].name < entries[j].name
	})
	p.w.WriteString("\n;; Debug information\n")
	p.w.WriteString(";; -----------------------\n")
	p.w.WriteString(";; Original names\n")
	for _, e := range entries {
		value := new(big.Int).SetUint64(e.key[1])
		value.Lsh(value, 64)
		value.Or(value, new(big.Int).SetUint64(e.key[0]))
		p.w.WriteString(fmt.Sprintf(";; \t ID `0x%x` -> `%s`\n", value, e.name))
	}
}


// ProgramToStr pretty-prints a Transaction protobuf message to a string.
func ProgramToStr(msg *pb.Transaction) string {
	var buf bytes.Buffer
	p := &PrettyPrinter{
		w:                       &buf,
		indentStack:             []int{0},
		column:                  0,
		atLineStart:             true,
		separator:               "\n",
		maxWidth:                maxWidth,
		computing:               make(map[uintptr]bool),
		memo:                    make(map[uintptr]string),
		debugInfo:               make(map[[2]uint64]string),
		printSymbolicRelationIds: true,
	}
	p.pretty_transaction(msg)
	p.newline()
	return p.getOutput()
}

// ProgramToStrDebug pretty-prints with raw relation IDs and debug info appended as comments.
func ProgramToStrDebug(msg *pb.Transaction) string {
	var buf bytes.Buffer
	p := &PrettyPrinter{
		w:                       &buf,
		indentStack:             []int{0},
		column:                  0,
		atLineStart:             true,
		separator:               "\n",
		maxWidth:                maxWidth,
		computing:               make(map[uintptr]bool),
		memo:                    make(map[uintptr]string),
		debugInfo:               make(map[[2]uint64]string),
		printSymbolicRelationIds: false,
	}
	p.pretty_transaction(msg)
	p.newline()
	p.writeDebugInfo()
	return p.getOutput()
}
