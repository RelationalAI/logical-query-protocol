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
	var _t1882 interface{}
	if hasProtoField(msg, "load_errors") {
		return msg.GetLoadErrors()
	}
	_ = _t1882
	return nil
}

func (p *PrettyPrinter) deconstruct_csv_data_columns_optional(msg *pb.CSVData) []*pb.GNFColumn {
	var _t1883 interface{}
	if hasProtoField(msg, "relations") {
		return nil
	}
	_ = _t1883
	return msg.GetColumns()
}

func (p *PrettyPrinter) deconstruct_csv_data_relations_optional(msg *pb.CSVData) *pb.TargetRelations {
	var _t1884 interface{}
	if hasProtoField(msg, "relations") {
		return msg.GetRelations()
	}
	_ = _t1884
	return nil
}

func (p *PrettyPrinter) deconstruct_export_csv_output_location(msg *pb.ExportCSVConfig) []interface{} {
	return []interface{}{msg.GetPath(), msg.GetTransactionOutputName()}
}

func (p *PrettyPrinter) _make_value_int32(v int32) *pb.Value {
	_t1885 := &pb.Value{}
	_t1885.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1885
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1886 := &pb.Value{}
	_t1886.Value = &pb.Value_IntValue{IntValue: v}
	return _t1886
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1887 := &pb.Value{}
	_t1887.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1887
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1888 := &pb.Value{}
	_t1888.Value = &pb.Value_StringValue{StringValue: v}
	return _t1888
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1889 := &pb.Value{}
	_t1889.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1889
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1890 := &pb.Value{}
	_t1890.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1890
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1891 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1891})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1892 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1892})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1893 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1893})
			}
		}
	}
	_t1894 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1894})
	for _, pair := range valueMapToPairs(msg.GetConfigurationValues()) {
		result = append(result, pair)
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1895 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1895})
	_t1896 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1896})
	if msg.GetNewLine() != "" {
		_t1897 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1897})
	}
	_t1898 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1898})
	_t1899 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1899})
	_t1900 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1900})
	if msg.GetComment() != "" {
		_t1901 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1901})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1902 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1902})
	}
	_t1903 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1903})
	_t1904 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1904})
	_t1905 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1905})
	if msg.GetPartitionSizeMb() != 0 {
		_t1906 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1906})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_storage_integration_optional(msg *pb.CSVConfig) [][]interface{} {
	var _t1907 interface{}
	if !(hasProtoField(msg, "storage_integration")) {
		return nil
	}
	_ = _t1907
	si := msg.GetStorageIntegration()
	result := [][]interface{}{}
	if si.GetProvider() != "" {
		_t1908 := p._make_value_string(si.GetProvider())
		result = append(result, []interface{}{"provider", _t1908})
	}
	if si.GetAzureSasToken() != "" {
		_t1909 := p._make_value_string("***")
		result = append(result, []interface{}{"azure_sas_token", _t1909})
	}
	if si.GetS3Region() != "" {
		_t1910 := p._make_value_string(si.GetS3Region())
		result = append(result, []interface{}{"s3_region", _t1910})
	}
	if si.GetS3AccessKeyId() != "" {
		_t1911 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_access_key_id", _t1911})
	}
	if si.GetS3SecretAccessKey() != "" {
		_t1912 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_secret_access_key", _t1912})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1913 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1913})
	_t1914 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1914})
	_t1915 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1915})
	_t1916 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1916})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1917 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1917})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1918 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1918})
		}
	}
	_t1919 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1919})
	_t1920 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1920})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1921 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1921})
	}
	if msg.Compression != nil {
		_t1922 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1922})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1923 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1923})
	}
	if msg.SyntaxMissingString != nil {
		_t1924 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1924})
	}
	if msg.SyntaxDelim != nil {
		_t1925 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1925})
	}
	if msg.SyntaxQuotechar != nil {
		_t1926 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1926})
	}
	if msg.SyntaxEscapechar != nil {
		_t1927 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1927})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1928 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1928
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_columns_optional(msg *pb.IcebergData) []*pb.GNFColumn {
	var _t1929 interface{}
	if hasProtoField(msg, "relations") {
		return nil
	}
	_ = _t1929
	return msg.GetColumns()
}

func (p *PrettyPrinter) deconstruct_iceberg_data_relations_optional(msg *pb.IcebergData) *pb.TargetRelations {
	var _t1930 interface{}
	if hasProtoField(msg, "relations") {
		return msg.GetRelations()
	}
	_ = _t1930
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1931 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1931
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1932 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1932
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1933 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1933})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1934 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1934})
	}
	if msg.GetCompression() != "" {
		_t1935 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1935})
	}
	var _t1936 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1936
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1937 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1937
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
	flat871 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat871 != nil {
		p.write(*flat871)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1724 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1724 = _dollar_dollar.GetConfigure()
		}
		var _t1725 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1725 = _dollar_dollar.GetSync()
		}
		fields862 := []interface{}{_t1724, _t1725, _dollar_dollar.GetEpochs()}
		unwrapped_fields863 := fields862
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field864 := unwrapped_fields863[0].(*pb.Configure)
		if field864 != nil {
			p.newline()
			opt_val865 := field864
			p.pretty_configure(opt_val865)
		}
		field866 := unwrapped_fields863[1].(*pb.Sync)
		if field866 != nil {
			p.newline()
			opt_val867 := field866
			p.pretty_sync(opt_val867)
		}
		field868 := unwrapped_fields863[2].([]*pb.Epoch)
		if !(len(field868) == 0) {
			p.newline()
			for i870, elem869 := range field868 {
				if (i870 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem869)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat874 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat874 != nil {
		p.write(*flat874)
		return nil
	} else {
		_dollar_dollar := msg
		_t1726 := p.deconstruct_configure(_dollar_dollar)
		fields872 := _t1726
		unwrapped_fields873 := fields872
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields873)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat878 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat878 != nil {
		p.write(*flat878)
		return nil
	} else {
		fields875 := msg
		p.write("{")
		p.indent()
		if !(len(fields875) == 0) {
			p.newline()
			for i877, elem876 := range fields875 {
				if (i877 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem876)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat883 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat883 != nil {
		p.write(*flat883)
		return nil
	} else {
		_dollar_dollar := msg
		fields879 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields880 := fields879
		p.write(":")
		field881 := unwrapped_fields880[0].(string)
		p.write(field881)
		p.write(" ")
		field882 := unwrapped_fields880[1].(*pb.Value)
		p.pretty_raw_value(field882)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat909 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat909 != nil {
		p.write(*flat909)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1727 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1727 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result907 := _t1727
		if deconstruct_result907 != nil {
			unwrapped908 := deconstruct_result907
			p.pretty_raw_date(unwrapped908)
		} else {
			_dollar_dollar := msg
			var _t1728 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1728 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result905 := _t1728
			if deconstruct_result905 != nil {
				unwrapped906 := deconstruct_result905
				p.pretty_raw_datetime(unwrapped906)
			} else {
				_dollar_dollar := msg
				var _t1729 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1729 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result903 := _t1729
				if deconstruct_result903 != nil {
					unwrapped904 := *deconstruct_result903
					p.write(p.formatStringValue(unwrapped904))
				} else {
					_dollar_dollar := msg
					var _t1730 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1730 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result901 := _t1730
					if deconstruct_result901 != nil {
						unwrapped902 := *deconstruct_result901
						p.write(fmt.Sprintf("%di32", unwrapped902))
					} else {
						_dollar_dollar := msg
						var _t1731 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1731 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result899 := _t1731
						if deconstruct_result899 != nil {
							unwrapped900 := *deconstruct_result899
							p.write(fmt.Sprintf("%d", unwrapped900))
						} else {
							_dollar_dollar := msg
							var _t1732 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1732 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result897 := _t1732
							if deconstruct_result897 != nil {
								unwrapped898 := *deconstruct_result897
								p.write(formatFloat32(unwrapped898))
							} else {
								_dollar_dollar := msg
								var _t1733 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1733 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result895 := _t1733
								if deconstruct_result895 != nil {
									unwrapped896 := *deconstruct_result895
									p.write(formatFloat64(unwrapped896))
								} else {
									_dollar_dollar := msg
									var _t1734 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1734 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result893 := _t1734
									if deconstruct_result893 != nil {
										unwrapped894 := *deconstruct_result893
										p.write(fmt.Sprintf("%du32", unwrapped894))
									} else {
										_dollar_dollar := msg
										var _t1735 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1735 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result891 := _t1735
										if deconstruct_result891 != nil {
											unwrapped892 := deconstruct_result891
											p.write(p.formatUint128(unwrapped892))
										} else {
											_dollar_dollar := msg
											var _t1736 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1736 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result889 := _t1736
											if deconstruct_result889 != nil {
												unwrapped890 := deconstruct_result889
												p.write(p.formatInt128(unwrapped890))
											} else {
												_dollar_dollar := msg
												var _t1737 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1737 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result887 := _t1737
												if deconstruct_result887 != nil {
													unwrapped888 := deconstruct_result887
													p.write(p.formatDecimal(unwrapped888))
												} else {
													_dollar_dollar := msg
													var _t1738 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1738 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result885 := _t1738
													if deconstruct_result885 != nil {
														unwrapped886 := *deconstruct_result885
														p.pretty_boolean_value(unwrapped886)
													} else {
														fields884 := msg
														_ = fields884
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
	flat915 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat915 != nil {
		p.write(*flat915)
		return nil
	} else {
		_dollar_dollar := msg
		fields910 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields911 := fields910
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field912 := unwrapped_fields911[0].(int64)
		p.write(fmt.Sprintf("%d", field912))
		p.newline()
		field913 := unwrapped_fields911[1].(int64)
		p.write(fmt.Sprintf("%d", field913))
		p.newline()
		field914 := unwrapped_fields911[2].(int64)
		p.write(fmt.Sprintf("%d", field914))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat926 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat926 != nil {
		p.write(*flat926)
		return nil
	} else {
		_dollar_dollar := msg
		fields916 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields917 := fields916
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field918 := unwrapped_fields917[0].(int64)
		p.write(fmt.Sprintf("%d", field918))
		p.newline()
		field919 := unwrapped_fields917[1].(int64)
		p.write(fmt.Sprintf("%d", field919))
		p.newline()
		field920 := unwrapped_fields917[2].(int64)
		p.write(fmt.Sprintf("%d", field920))
		p.newline()
		field921 := unwrapped_fields917[3].(int64)
		p.write(fmt.Sprintf("%d", field921))
		p.newline()
		field922 := unwrapped_fields917[4].(int64)
		p.write(fmt.Sprintf("%d", field922))
		p.newline()
		field923 := unwrapped_fields917[5].(int64)
		p.write(fmt.Sprintf("%d", field923))
		field924 := unwrapped_fields917[6].(*int64)
		if field924 != nil {
			p.newline()
			opt_val925 := *field924
			p.write(fmt.Sprintf("%d", opt_val925))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1739 []interface{}
	if _dollar_dollar {
		_t1739 = []interface{}{}
	}
	deconstruct_result929 := _t1739
	if deconstruct_result929 != nil {
		unwrapped930 := deconstruct_result929
		_ = unwrapped930
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1740 []interface{}
		if !(_dollar_dollar) {
			_t1740 = []interface{}{}
		}
		deconstruct_result927 := _t1740
		if deconstruct_result927 != nil {
			unwrapped928 := deconstruct_result927
			_ = unwrapped928
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat935 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat935 != nil {
		p.write(*flat935)
		return nil
	} else {
		_dollar_dollar := msg
		fields931 := _dollar_dollar.GetFragments()
		unwrapped_fields932 := fields931
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields932) == 0) {
			p.newline()
			for i934, elem933 := range unwrapped_fields932 {
				if (i934 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem933)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat938 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat938 != nil {
		p.write(*flat938)
		return nil
	} else {
		_dollar_dollar := msg
		fields936 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields937 := fields936
		p.write(":")
		p.write(unwrapped_fields937)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat945 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat945 != nil {
		p.write(*flat945)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1741 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1741 = _dollar_dollar.GetWrites()
		}
		var _t1742 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1742 = _dollar_dollar.GetReads()
		}
		fields939 := []interface{}{_t1741, _t1742}
		unwrapped_fields940 := fields939
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field941 := unwrapped_fields940[0].([]*pb.Write)
		if field941 != nil {
			p.newline()
			opt_val942 := field941
			p.pretty_epoch_writes(opt_val942)
		}
		field943 := unwrapped_fields940[1].([]*pb.Read)
		if field943 != nil {
			p.newline()
			opt_val944 := field943
			p.pretty_epoch_reads(opt_val944)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat949 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat949 != nil {
		p.write(*flat949)
		return nil
	} else {
		fields946 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields946) == 0) {
			p.newline()
			for i948, elem947 := range fields946 {
				if (i948 > 0) {
					p.newline()
				}
				p.pretty_write(elem947)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat958 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat958 != nil {
		p.write(*flat958)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1743 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1743 = _dollar_dollar.GetDefine()
		}
		deconstruct_result956 := _t1743
		if deconstruct_result956 != nil {
			unwrapped957 := deconstruct_result956
			p.pretty_define(unwrapped957)
		} else {
			_dollar_dollar := msg
			var _t1744 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1744 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result954 := _t1744
			if deconstruct_result954 != nil {
				unwrapped955 := deconstruct_result954
				p.pretty_undefine(unwrapped955)
			} else {
				_dollar_dollar := msg
				var _t1745 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1745 = _dollar_dollar.GetContext()
				}
				deconstruct_result952 := _t1745
				if deconstruct_result952 != nil {
					unwrapped953 := deconstruct_result952
					p.pretty_context(unwrapped953)
				} else {
					_dollar_dollar := msg
					var _t1746 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1746 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result950 := _t1746
					if deconstruct_result950 != nil {
						unwrapped951 := deconstruct_result950
						p.pretty_snapshot(unwrapped951)
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
	flat961 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat961 != nil {
		p.write(*flat961)
		return nil
	} else {
		_dollar_dollar := msg
		fields959 := _dollar_dollar.GetFragment()
		unwrapped_fields960 := fields959
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields960)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat968 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat968 != nil {
		p.write(*flat968)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields962 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields963 := fields962
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field964 := unwrapped_fields963[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field964)
		field965 := unwrapped_fields963[1].([]*pb.Declaration)
		if !(len(field965) == 0) {
			p.newline()
			for i967, elem966 := range field965 {
				if (i967 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem966)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat970 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat970 != nil {
		p.write(*flat970)
		return nil
	} else {
		fields969 := msg
		p.pretty_fragment_id(fields969)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat979 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat979 != nil {
		p.write(*flat979)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1747 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1747 = _dollar_dollar.GetDef()
		}
		deconstruct_result977 := _t1747
		if deconstruct_result977 != nil {
			unwrapped978 := deconstruct_result977
			p.pretty_def(unwrapped978)
		} else {
			_dollar_dollar := msg
			var _t1748 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1748 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result975 := _t1748
			if deconstruct_result975 != nil {
				unwrapped976 := deconstruct_result975
				p.pretty_algorithm(unwrapped976)
			} else {
				_dollar_dollar := msg
				var _t1749 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1749 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result973 := _t1749
				if deconstruct_result973 != nil {
					unwrapped974 := deconstruct_result973
					p.pretty_constraint(unwrapped974)
				} else {
					_dollar_dollar := msg
					var _t1750 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1750 = _dollar_dollar.GetData()
					}
					deconstruct_result971 := _t1750
					if deconstruct_result971 != nil {
						unwrapped972 := deconstruct_result971
						p.pretty_data(unwrapped972)
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
	flat986 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat986 != nil {
		p.write(*flat986)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1751 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1751 = _dollar_dollar.GetAttrs()
		}
		fields980 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1751}
		unwrapped_fields981 := fields980
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field982 := unwrapped_fields981[0].(*pb.RelationId)
		p.pretty_relation_id(field982)
		p.newline()
		field983 := unwrapped_fields981[1].(*pb.Abstraction)
		p.pretty_abstraction(field983)
		field984 := unwrapped_fields981[2].([]*pb.Attribute)
		if field984 != nil {
			p.newline()
			opt_val985 := field984
			p.pretty_attrs(opt_val985)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat991 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat991 != nil {
		p.write(*flat991)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1752 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1753 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1752 = ptr(_t1753)
		}
		deconstruct_result989 := _t1752
		if deconstruct_result989 != nil {
			unwrapped990 := *deconstruct_result989
			p.write(":")
			p.write(unwrapped990)
		} else {
			_dollar_dollar := msg
			_t1754 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result987 := _t1754
			if deconstruct_result987 != nil {
				unwrapped988 := deconstruct_result987
				p.write(p.formatUint128(unwrapped988))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat996 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat996 != nil {
		p.write(*flat996)
		return nil
	} else {
		_dollar_dollar := msg
		_t1755 := p.deconstruct_bindings(_dollar_dollar)
		fields992 := []interface{}{_t1755, _dollar_dollar.GetValue()}
		unwrapped_fields993 := fields992
		p.write("(")
		p.indent()
		field994 := unwrapped_fields993[0].([]interface{})
		p.pretty_bindings(field994)
		p.newline()
		field995 := unwrapped_fields993[1].(*pb.Formula)
		p.pretty_formula(field995)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat1004 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat1004 != nil {
		p.write(*flat1004)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1756 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1756 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields997 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1756}
		unwrapped_fields998 := fields997
		p.write("[")
		p.indent()
		field999 := unwrapped_fields998[0].([]*pb.Binding)
		for i1001, elem1000 := range field999 {
			if (i1001 > 0) {
				p.newline()
			}
			p.pretty_binding(elem1000)
		}
		field1002 := unwrapped_fields998[1].([]*pb.Binding)
		if field1002 != nil {
			p.newline()
			opt_val1003 := field1002
			p.pretty_value_bindings(opt_val1003)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat1009 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat1009 != nil {
		p.write(*flat1009)
		return nil
	} else {
		_dollar_dollar := msg
		fields1005 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields1006 := fields1005
		field1007 := unwrapped_fields1006[0].(string)
		p.write(field1007)
		p.write("::")
		field1008 := unwrapped_fields1006[1].(*pb.Type)
		p.pretty_type(field1008)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat1040 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat1040 != nil {
		p.write(*flat1040)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1757 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1757 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result1038 := _t1757
		if deconstruct_result1038 != nil {
			unwrapped1039 := deconstruct_result1038
			p.pretty_unspecified_type(unwrapped1039)
		} else {
			_dollar_dollar := msg
			var _t1758 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1758 = _dollar_dollar.GetStringType()
			}
			deconstruct_result1036 := _t1758
			if deconstruct_result1036 != nil {
				unwrapped1037 := deconstruct_result1036
				p.pretty_string_type(unwrapped1037)
			} else {
				_dollar_dollar := msg
				var _t1759 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1759 = _dollar_dollar.GetIntType()
				}
				deconstruct_result1034 := _t1759
				if deconstruct_result1034 != nil {
					unwrapped1035 := deconstruct_result1034
					p.pretty_int_type(unwrapped1035)
				} else {
					_dollar_dollar := msg
					var _t1760 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1760 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result1032 := _t1760
					if deconstruct_result1032 != nil {
						unwrapped1033 := deconstruct_result1032
						p.pretty_float_type(unwrapped1033)
					} else {
						_dollar_dollar := msg
						var _t1761 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1761 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result1030 := _t1761
						if deconstruct_result1030 != nil {
							unwrapped1031 := deconstruct_result1030
							p.pretty_uint128_type(unwrapped1031)
						} else {
							_dollar_dollar := msg
							var _t1762 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1762 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result1028 := _t1762
							if deconstruct_result1028 != nil {
								unwrapped1029 := deconstruct_result1028
								p.pretty_int128_type(unwrapped1029)
							} else {
								_dollar_dollar := msg
								var _t1763 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1763 = _dollar_dollar.GetDateType()
								}
								deconstruct_result1026 := _t1763
								if deconstruct_result1026 != nil {
									unwrapped1027 := deconstruct_result1026
									p.pretty_date_type(unwrapped1027)
								} else {
									_dollar_dollar := msg
									var _t1764 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1764 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result1024 := _t1764
									if deconstruct_result1024 != nil {
										unwrapped1025 := deconstruct_result1024
										p.pretty_datetime_type(unwrapped1025)
									} else {
										_dollar_dollar := msg
										var _t1765 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1765 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result1022 := _t1765
										if deconstruct_result1022 != nil {
											unwrapped1023 := deconstruct_result1022
											p.pretty_missing_type(unwrapped1023)
										} else {
											_dollar_dollar := msg
											var _t1766 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1766 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result1020 := _t1766
											if deconstruct_result1020 != nil {
												unwrapped1021 := deconstruct_result1020
												p.pretty_decimal_type(unwrapped1021)
											} else {
												_dollar_dollar := msg
												var _t1767 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1767 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result1018 := _t1767
												if deconstruct_result1018 != nil {
													unwrapped1019 := deconstruct_result1018
													p.pretty_boolean_type(unwrapped1019)
												} else {
													_dollar_dollar := msg
													var _t1768 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1768 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result1016 := _t1768
													if deconstruct_result1016 != nil {
														unwrapped1017 := deconstruct_result1016
														p.pretty_int32_type(unwrapped1017)
													} else {
														_dollar_dollar := msg
														var _t1769 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1769 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result1014 := _t1769
														if deconstruct_result1014 != nil {
															unwrapped1015 := deconstruct_result1014
															p.pretty_float32_type(unwrapped1015)
														} else {
															_dollar_dollar := msg
															var _t1770 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1770 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result1012 := _t1770
															if deconstruct_result1012 != nil {
																unwrapped1013 := deconstruct_result1012
																p.pretty_uint32_type(unwrapped1013)
															} else {
																_dollar_dollar := msg
																var _t1771 *pb.FixedType
																if hasProtoField(_dollar_dollar, "fixed_type") {
																	_t1771 = _dollar_dollar.GetFixedType()
																}
																deconstruct_result1010 := _t1771
																if deconstruct_result1010 != nil {
																	unwrapped1011 := deconstruct_result1010
																	p.pretty_fixed_type(unwrapped1011)
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
	}
	return nil
}

func (p *PrettyPrinter) pretty_unspecified_type(msg *pb.UnspecifiedType) interface{} {
	fields1041 := msg
	_ = fields1041
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields1042 := msg
	_ = fields1042
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields1043 := msg
	_ = fields1043
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields1044 := msg
	_ = fields1044
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields1045 := msg
	_ = fields1045
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields1046 := msg
	_ = fields1046
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields1047 := msg
	_ = fields1047
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields1048 := msg
	_ = fields1048
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields1049 := msg
	_ = fields1049
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat1054 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat1054 != nil {
		p.write(*flat1054)
		return nil
	} else {
		_dollar_dollar := msg
		fields1050 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields1051 := fields1050
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field1052 := unwrapped_fields1051[0].(int64)
		p.write(fmt.Sprintf("%d", field1052))
		p.newline()
		field1053 := unwrapped_fields1051[1].(int64)
		p.write(fmt.Sprintf("%d", field1053))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields1055 := msg
	_ = fields1055
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields1056 := msg
	_ = fields1056
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields1057 := msg
	_ = fields1057
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields1058 := msg
	_ = fields1058
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_fixed_type(msg *pb.FixedType) interface{} {
	flat1061 := p.tryFlat(msg, func() { p.pretty_fixed_type(msg) })
	if flat1061 != nil {
		p.write(*flat1061)
		return nil
	} else {
		_dollar_dollar := msg
		fields1059 := int64(_dollar_dollar.GetLength())
		unwrapped_fields1060 := fields1059
		p.write("(")
		p.write("FIXED")
		p.indentSexp()
		p.newline()
		p.write(fmt.Sprintf("%d", unwrapped_fields1060))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat1065 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat1065 != nil {
		p.write(*flat1065)
		return nil
	} else {
		fields1062 := msg
		p.write("|")
		if !(len(fields1062) == 0) {
			p.write(" ")
			for i1064, elem1063 := range fields1062 {
				if (i1064 > 0) {
					p.newline()
				}
				p.pretty_binding(elem1063)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1092 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1092 != nil {
		p.write(*flat1092)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1772 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1772 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1090 := _t1772
		if deconstruct_result1090 != nil {
			unwrapped1091 := deconstruct_result1090
			p.pretty_true(unwrapped1091)
		} else {
			_dollar_dollar := msg
			var _t1773 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1773 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1088 := _t1773
			if deconstruct_result1088 != nil {
				unwrapped1089 := deconstruct_result1088
				p.pretty_false(unwrapped1089)
			} else {
				_dollar_dollar := msg
				var _t1774 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1774 = _dollar_dollar.GetExists()
				}
				deconstruct_result1086 := _t1774
				if deconstruct_result1086 != nil {
					unwrapped1087 := deconstruct_result1086
					p.pretty_exists(unwrapped1087)
				} else {
					_dollar_dollar := msg
					var _t1775 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1775 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1084 := _t1775
					if deconstruct_result1084 != nil {
						unwrapped1085 := deconstruct_result1084
						p.pretty_reduce(unwrapped1085)
					} else {
						_dollar_dollar := msg
						var _t1776 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1776 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1082 := _t1776
						if deconstruct_result1082 != nil {
							unwrapped1083 := deconstruct_result1082
							p.pretty_conjunction(unwrapped1083)
						} else {
							_dollar_dollar := msg
							var _t1777 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1777 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1080 := _t1777
							if deconstruct_result1080 != nil {
								unwrapped1081 := deconstruct_result1080
								p.pretty_disjunction(unwrapped1081)
							} else {
								_dollar_dollar := msg
								var _t1778 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1778 = _dollar_dollar.GetNot()
								}
								deconstruct_result1078 := _t1778
								if deconstruct_result1078 != nil {
									unwrapped1079 := deconstruct_result1078
									p.pretty_not(unwrapped1079)
								} else {
									_dollar_dollar := msg
									var _t1779 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1779 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1076 := _t1779
									if deconstruct_result1076 != nil {
										unwrapped1077 := deconstruct_result1076
										p.pretty_ffi(unwrapped1077)
									} else {
										_dollar_dollar := msg
										var _t1780 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1780 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1074 := _t1780
										if deconstruct_result1074 != nil {
											unwrapped1075 := deconstruct_result1074
											p.pretty_atom(unwrapped1075)
										} else {
											_dollar_dollar := msg
											var _t1781 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1781 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1072 := _t1781
											if deconstruct_result1072 != nil {
												unwrapped1073 := deconstruct_result1072
												p.pretty_pragma(unwrapped1073)
											} else {
												_dollar_dollar := msg
												var _t1782 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1782 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1070 := _t1782
												if deconstruct_result1070 != nil {
													unwrapped1071 := deconstruct_result1070
													p.pretty_primitive(unwrapped1071)
												} else {
													_dollar_dollar := msg
													var _t1783 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1783 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1068 := _t1783
													if deconstruct_result1068 != nil {
														unwrapped1069 := deconstruct_result1068
														p.pretty_rel_atom(unwrapped1069)
													} else {
														_dollar_dollar := msg
														var _t1784 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1784 = _dollar_dollar.GetCast()
														}
														deconstruct_result1066 := _t1784
														if deconstruct_result1066 != nil {
															unwrapped1067 := deconstruct_result1066
															p.pretty_cast(unwrapped1067)
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
	fields1093 := msg
	_ = fields1093
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1094 := msg
	_ = fields1094
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1099 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1099 != nil {
		p.write(*flat1099)
		return nil
	} else {
		_dollar_dollar := msg
		_t1785 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1095 := []interface{}{_t1785, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1096 := fields1095
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1097 := unwrapped_fields1096[0].([]interface{})
		p.pretty_bindings(field1097)
		p.newline()
		field1098 := unwrapped_fields1096[1].(*pb.Formula)
		p.pretty_formula(field1098)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1105 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1105 != nil {
		p.write(*flat1105)
		return nil
	} else {
		_dollar_dollar := msg
		fields1100 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1101 := fields1100
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1102 := unwrapped_fields1101[0].(*pb.Abstraction)
		p.pretty_abstraction(field1102)
		p.newline()
		field1103 := unwrapped_fields1101[1].(*pb.Abstraction)
		p.pretty_abstraction(field1103)
		p.newline()
		field1104 := unwrapped_fields1101[2].([]*pb.Term)
		p.pretty_terms(field1104)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1109 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1109 != nil {
		p.write(*flat1109)
		return nil
	} else {
		fields1106 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1106) == 0) {
			p.newline()
			for i1108, elem1107 := range fields1106 {
				if (i1108 > 0) {
					p.newline()
				}
				p.pretty_term(elem1107)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1114 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1114 != nil {
		p.write(*flat1114)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1786 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1786 = _dollar_dollar.GetVar()
		}
		deconstruct_result1112 := _t1786
		if deconstruct_result1112 != nil {
			unwrapped1113 := deconstruct_result1112
			p.pretty_var(unwrapped1113)
		} else {
			_dollar_dollar := msg
			var _t1787 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1787 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1110 := _t1787
			if deconstruct_result1110 != nil {
				unwrapped1111 := deconstruct_result1110
				p.pretty_value(unwrapped1111)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1117 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1117 != nil {
		p.write(*flat1117)
		return nil
	} else {
		_dollar_dollar := msg
		fields1115 := _dollar_dollar.GetName()
		unwrapped_fields1116 := fields1115
		p.write(unwrapped_fields1116)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1143 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1143 != nil {
		p.write(*flat1143)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1788 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1788 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1141 := _t1788
		if deconstruct_result1141 != nil {
			unwrapped1142 := deconstruct_result1141
			p.pretty_date(unwrapped1142)
		} else {
			_dollar_dollar := msg
			var _t1789 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1789 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1139 := _t1789
			if deconstruct_result1139 != nil {
				unwrapped1140 := deconstruct_result1139
				p.pretty_datetime(unwrapped1140)
			} else {
				_dollar_dollar := msg
				var _t1790 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1790 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1137 := _t1790
				if deconstruct_result1137 != nil {
					unwrapped1138 := *deconstruct_result1137
					p.write(p.formatStringValue(unwrapped1138))
				} else {
					_dollar_dollar := msg
					var _t1791 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1791 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1135 := _t1791
					if deconstruct_result1135 != nil {
						unwrapped1136 := *deconstruct_result1135
						p.write(fmt.Sprintf("%di32", unwrapped1136))
					} else {
						_dollar_dollar := msg
						var _t1792 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1792 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1133 := _t1792
						if deconstruct_result1133 != nil {
							unwrapped1134 := *deconstruct_result1133
							p.write(fmt.Sprintf("%d", unwrapped1134))
						} else {
							_dollar_dollar := msg
							var _t1793 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1793 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1131 := _t1793
							if deconstruct_result1131 != nil {
								unwrapped1132 := *deconstruct_result1131
								p.write(formatFloat32(unwrapped1132))
							} else {
								_dollar_dollar := msg
								var _t1794 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1794 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1129 := _t1794
								if deconstruct_result1129 != nil {
									unwrapped1130 := *deconstruct_result1129
									p.write(formatFloat64(unwrapped1130))
								} else {
									_dollar_dollar := msg
									var _t1795 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1795 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1127 := _t1795
									if deconstruct_result1127 != nil {
										unwrapped1128 := *deconstruct_result1127
										p.write(fmt.Sprintf("%du32", unwrapped1128))
									} else {
										_dollar_dollar := msg
										var _t1796 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1796 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1125 := _t1796
										if deconstruct_result1125 != nil {
											unwrapped1126 := deconstruct_result1125
											p.write(p.formatUint128(unwrapped1126))
										} else {
											_dollar_dollar := msg
											var _t1797 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1797 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1123 := _t1797
											if deconstruct_result1123 != nil {
												unwrapped1124 := deconstruct_result1123
												p.write(p.formatInt128(unwrapped1124))
											} else {
												_dollar_dollar := msg
												var _t1798 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1798 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1121 := _t1798
												if deconstruct_result1121 != nil {
													unwrapped1122 := deconstruct_result1121
													p.write(p.formatDecimal(unwrapped1122))
												} else {
													_dollar_dollar := msg
													var _t1799 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1799 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1119 := _t1799
													if deconstruct_result1119 != nil {
														unwrapped1120 := *deconstruct_result1119
														p.pretty_boolean_value(unwrapped1120)
													} else {
														fields1118 := msg
														_ = fields1118
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
	flat1149 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1149 != nil {
		p.write(*flat1149)
		return nil
	} else {
		_dollar_dollar := msg
		fields1144 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1145 := fields1144
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1146 := unwrapped_fields1145[0].(int64)
		p.write(fmt.Sprintf("%d", field1146))
		p.newline()
		field1147 := unwrapped_fields1145[1].(int64)
		p.write(fmt.Sprintf("%d", field1147))
		p.newline()
		field1148 := unwrapped_fields1145[2].(int64)
		p.write(fmt.Sprintf("%d", field1148))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1160 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1160 != nil {
		p.write(*flat1160)
		return nil
	} else {
		_dollar_dollar := msg
		fields1150 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1151 := fields1150
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1152 := unwrapped_fields1151[0].(int64)
		p.write(fmt.Sprintf("%d", field1152))
		p.newline()
		field1153 := unwrapped_fields1151[1].(int64)
		p.write(fmt.Sprintf("%d", field1153))
		p.newline()
		field1154 := unwrapped_fields1151[2].(int64)
		p.write(fmt.Sprintf("%d", field1154))
		p.newline()
		field1155 := unwrapped_fields1151[3].(int64)
		p.write(fmt.Sprintf("%d", field1155))
		p.newline()
		field1156 := unwrapped_fields1151[4].(int64)
		p.write(fmt.Sprintf("%d", field1156))
		p.newline()
		field1157 := unwrapped_fields1151[5].(int64)
		p.write(fmt.Sprintf("%d", field1157))
		field1158 := unwrapped_fields1151[6].(*int64)
		if field1158 != nil {
			p.newline()
			opt_val1159 := *field1158
			p.write(fmt.Sprintf("%d", opt_val1159))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1165 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1165 != nil {
		p.write(*flat1165)
		return nil
	} else {
		_dollar_dollar := msg
		fields1161 := _dollar_dollar.GetArgs()
		unwrapped_fields1162 := fields1161
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1162) == 0) {
			p.newline()
			for i1164, elem1163 := range unwrapped_fields1162 {
				if (i1164 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1163)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1170 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1170 != nil {
		p.write(*flat1170)
		return nil
	} else {
		_dollar_dollar := msg
		fields1166 := _dollar_dollar.GetArgs()
		unwrapped_fields1167 := fields1166
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1167) == 0) {
			p.newline()
			for i1169, elem1168 := range unwrapped_fields1167 {
				if (i1169 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1168)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1173 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1173 != nil {
		p.write(*flat1173)
		return nil
	} else {
		_dollar_dollar := msg
		fields1171 := _dollar_dollar.GetArg()
		unwrapped_fields1172 := fields1171
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1172)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		_dollar_dollar := msg
		fields1174 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1175 := fields1174
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1176 := unwrapped_fields1175[0].(string)
		p.pretty_name(field1176)
		p.newline()
		field1177 := unwrapped_fields1175[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1177)
		p.newline()
		field1178 := unwrapped_fields1175[2].([]*pb.Term)
		p.pretty_terms(field1178)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1181 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1181 != nil {
		p.write(*flat1181)
		return nil
	} else {
		fields1180 := msg
		p.write(":")
		p.write(fields1180)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1185 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1185 != nil {
		p.write(*flat1185)
		return nil
	} else {
		fields1182 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1182) == 0) {
			p.newline()
			for i1184, elem1183 := range fields1182 {
				if (i1184 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1183)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1192 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1192 != nil {
		p.write(*flat1192)
		return nil
	} else {
		_dollar_dollar := msg
		fields1186 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1187 := fields1186
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1188 := unwrapped_fields1187[0].(*pb.RelationId)
		p.pretty_relation_id(field1188)
		field1189 := unwrapped_fields1187[1].([]*pb.Term)
		if !(len(field1189) == 0) {
			p.newline()
			for i1191, elem1190 := range field1189 {
				if (i1191 > 0) {
					p.newline()
				}
				p.pretty_term(elem1190)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1199 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1199 != nil {
		p.write(*flat1199)
		return nil
	} else {
		_dollar_dollar := msg
		fields1193 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1194 := fields1193
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1195 := unwrapped_fields1194[0].(string)
		p.pretty_name(field1195)
		field1196 := unwrapped_fields1194[1].([]*pb.Term)
		if !(len(field1196) == 0) {
			p.newline()
			for i1198, elem1197 := range field1196 {
				if (i1198 > 0) {
					p.newline()
				}
				p.pretty_term(elem1197)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1215 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1215 != nil {
		p.write(*flat1215)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1800 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1800 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1214 := _t1800
		if guard_result1214 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1801 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1801 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1213 := _t1801
			if guard_result1213 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1802 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1802 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1212 := _t1802
				if guard_result1212 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1803 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1803 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1211 := _t1803
					if guard_result1211 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1804 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1804 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1210 := _t1804
						if guard_result1210 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1805 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1805 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1209 := _t1805
							if guard_result1209 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1806 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1806 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1208 := _t1806
								if guard_result1208 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1807 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1807 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1207 := _t1807
									if guard_result1207 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1808 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1808 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1206 := _t1808
										if guard_result1206 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1200 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1201 := fields1200
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1202 := unwrapped_fields1201[0].(string)
											p.pretty_name(field1202)
											field1203 := unwrapped_fields1201[1].([]*pb.RelTerm)
											if !(len(field1203) == 0) {
												p.newline()
												for i1205, elem1204 := range field1203 {
													if (i1205 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1204)
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
	flat1220 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1220 != nil {
		p.write(*flat1220)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1809 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1809 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1216 := _t1809
		unwrapped_fields1217 := fields1216
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1218 := unwrapped_fields1217[0].(*pb.Term)
		p.pretty_term(field1218)
		p.newline()
		field1219 := unwrapped_fields1217[1].(*pb.Term)
		p.pretty_term(field1219)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1225 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1225 != nil {
		p.write(*flat1225)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1810 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1810 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1221 := _t1810
		unwrapped_fields1222 := fields1221
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1223 := unwrapped_fields1222[0].(*pb.Term)
		p.pretty_term(field1223)
		p.newline()
		field1224 := unwrapped_fields1222[1].(*pb.Term)
		p.pretty_term(field1224)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1230 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1230 != nil {
		p.write(*flat1230)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1811 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1811 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1226 := _t1811
		unwrapped_fields1227 := fields1226
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1228 := unwrapped_fields1227[0].(*pb.Term)
		p.pretty_term(field1228)
		p.newline()
		field1229 := unwrapped_fields1227[1].(*pb.Term)
		p.pretty_term(field1229)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1235 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1235 != nil {
		p.write(*flat1235)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1812 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1812 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1231 := _t1812
		unwrapped_fields1232 := fields1231
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1233 := unwrapped_fields1232[0].(*pb.Term)
		p.pretty_term(field1233)
		p.newline()
		field1234 := unwrapped_fields1232[1].(*pb.Term)
		p.pretty_term(field1234)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1240 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1240 != nil {
		p.write(*flat1240)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1813 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1813 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1236 := _t1813
		unwrapped_fields1237 := fields1236
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1238 := unwrapped_fields1237[0].(*pb.Term)
		p.pretty_term(field1238)
		p.newline()
		field1239 := unwrapped_fields1237[1].(*pb.Term)
		p.pretty_term(field1239)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1246 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1246 != nil {
		p.write(*flat1246)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1814 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1814 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1241 := _t1814
		unwrapped_fields1242 := fields1241
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1243 := unwrapped_fields1242[0].(*pb.Term)
		p.pretty_term(field1243)
		p.newline()
		field1244 := unwrapped_fields1242[1].(*pb.Term)
		p.pretty_term(field1244)
		p.newline()
		field1245 := unwrapped_fields1242[2].(*pb.Term)
		p.pretty_term(field1245)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1252 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1252 != nil {
		p.write(*flat1252)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1815 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1815 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1247 := _t1815
		unwrapped_fields1248 := fields1247
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1249 := unwrapped_fields1248[0].(*pb.Term)
		p.pretty_term(field1249)
		p.newline()
		field1250 := unwrapped_fields1248[1].(*pb.Term)
		p.pretty_term(field1250)
		p.newline()
		field1251 := unwrapped_fields1248[2].(*pb.Term)
		p.pretty_term(field1251)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1258 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1258 != nil {
		p.write(*flat1258)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1816 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1816 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1253 := _t1816
		unwrapped_fields1254 := fields1253
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1255 := unwrapped_fields1254[0].(*pb.Term)
		p.pretty_term(field1255)
		p.newline()
		field1256 := unwrapped_fields1254[1].(*pb.Term)
		p.pretty_term(field1256)
		p.newline()
		field1257 := unwrapped_fields1254[2].(*pb.Term)
		p.pretty_term(field1257)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1264 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1264 != nil {
		p.write(*flat1264)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1817 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1817 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1259 := _t1817
		unwrapped_fields1260 := fields1259
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1261 := unwrapped_fields1260[0].(*pb.Term)
		p.pretty_term(field1261)
		p.newline()
		field1262 := unwrapped_fields1260[1].(*pb.Term)
		p.pretty_term(field1262)
		p.newline()
		field1263 := unwrapped_fields1260[2].(*pb.Term)
		p.pretty_term(field1263)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1269 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1269 != nil {
		p.write(*flat1269)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1818 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1818 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1267 := _t1818
		if deconstruct_result1267 != nil {
			unwrapped1268 := deconstruct_result1267
			p.pretty_specialized_value(unwrapped1268)
		} else {
			_dollar_dollar := msg
			var _t1819 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1819 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1265 := _t1819
			if deconstruct_result1265 != nil {
				unwrapped1266 := deconstruct_result1265
				p.pretty_term(unwrapped1266)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1271 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1271 != nil {
		p.write(*flat1271)
		return nil
	} else {
		fields1270 := msg
		p.write("#")
		p.pretty_raw_value(fields1270)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1278 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1278 != nil {
		p.write(*flat1278)
		return nil
	} else {
		_dollar_dollar := msg
		fields1272 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1273 := fields1272
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1274 := unwrapped_fields1273[0].(string)
		p.pretty_name(field1274)
		field1275 := unwrapped_fields1273[1].([]*pb.RelTerm)
		if !(len(field1275) == 0) {
			p.newline()
			for i1277, elem1276 := range field1275 {
				if (i1277 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1276)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1283 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1283 != nil {
		p.write(*flat1283)
		return nil
	} else {
		_dollar_dollar := msg
		fields1279 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1280 := fields1279
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1281 := unwrapped_fields1280[0].(*pb.Term)
		p.pretty_term(field1281)
		p.newline()
		field1282 := unwrapped_fields1280[1].(*pb.Term)
		p.pretty_term(field1282)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1287 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1287 != nil {
		p.write(*flat1287)
		return nil
	} else {
		fields1284 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1284) == 0) {
			p.newline()
			for i1286, elem1285 := range fields1284 {
				if (i1286 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1285)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1294 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1294 != nil {
		p.write(*flat1294)
		return nil
	} else {
		_dollar_dollar := msg
		fields1288 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1289 := fields1288
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1290 := unwrapped_fields1289[0].(string)
		p.pretty_name(field1290)
		field1291 := unwrapped_fields1289[1].([]*pb.Value)
		if !(len(field1291) == 0) {
			p.newline()
			for i1293, elem1292 := range field1291 {
				if (i1293 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1292)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1303 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1303 != nil {
		p.write(*flat1303)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1820 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1820 = _dollar_dollar.GetAttrs()
		}
		fields1295 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1820}
		unwrapped_fields1296 := fields1295
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1297 := unwrapped_fields1296[0].([]*pb.RelationId)
		if !(len(field1297) == 0) {
			p.newline()
			for i1299, elem1298 := range field1297 {
				if (i1299 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1298)
			}
		}
		p.newline()
		field1300 := unwrapped_fields1296[1].(*pb.Script)
		p.pretty_script(field1300)
		field1301 := unwrapped_fields1296[2].([]*pb.Attribute)
		if field1301 != nil {
			p.newline()
			opt_val1302 := field1301
			p.pretty_attrs(opt_val1302)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1308 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1308 != nil {
		p.write(*flat1308)
		return nil
	} else {
		_dollar_dollar := msg
		fields1304 := _dollar_dollar.GetConstructs()
		unwrapped_fields1305 := fields1304
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1305) == 0) {
			p.newline()
			for i1307, elem1306 := range unwrapped_fields1305 {
				if (i1307 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1306)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1313 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1313 != nil {
		p.write(*flat1313)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1821 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1821 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1311 := _t1821
		if deconstruct_result1311 != nil {
			unwrapped1312 := deconstruct_result1311
			p.pretty_loop(unwrapped1312)
		} else {
			_dollar_dollar := msg
			var _t1822 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1822 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1309 := _t1822
			if deconstruct_result1309 != nil {
				unwrapped1310 := deconstruct_result1309
				p.pretty_instruction(unwrapped1310)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1320 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1320 != nil {
		p.write(*flat1320)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1823 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1823 = _dollar_dollar.GetAttrs()
		}
		fields1314 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1823}
		unwrapped_fields1315 := fields1314
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1316 := unwrapped_fields1315[0].([]*pb.Instruction)
		p.pretty_init(field1316)
		p.newline()
		field1317 := unwrapped_fields1315[1].(*pb.Script)
		p.pretty_script(field1317)
		field1318 := unwrapped_fields1315[2].([]*pb.Attribute)
		if field1318 != nil {
			p.newline()
			opt_val1319 := field1318
			p.pretty_attrs(opt_val1319)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1324 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1324 != nil {
		p.write(*flat1324)
		return nil
	} else {
		fields1321 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1321) == 0) {
			p.newline()
			for i1323, elem1322 := range fields1321 {
				if (i1323 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1322)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1335 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1335 != nil {
		p.write(*flat1335)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1824 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1824 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1333 := _t1824
		if deconstruct_result1333 != nil {
			unwrapped1334 := deconstruct_result1333
			p.pretty_assign(unwrapped1334)
		} else {
			_dollar_dollar := msg
			var _t1825 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1825 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1331 := _t1825
			if deconstruct_result1331 != nil {
				unwrapped1332 := deconstruct_result1331
				p.pretty_upsert(unwrapped1332)
			} else {
				_dollar_dollar := msg
				var _t1826 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1826 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1329 := _t1826
				if deconstruct_result1329 != nil {
					unwrapped1330 := deconstruct_result1329
					p.pretty_break(unwrapped1330)
				} else {
					_dollar_dollar := msg
					var _t1827 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1827 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1327 := _t1827
					if deconstruct_result1327 != nil {
						unwrapped1328 := deconstruct_result1327
						p.pretty_monoid_def(unwrapped1328)
					} else {
						_dollar_dollar := msg
						var _t1828 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1828 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1325 := _t1828
						if deconstruct_result1325 != nil {
							unwrapped1326 := deconstruct_result1325
							p.pretty_monus_def(unwrapped1326)
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
	flat1342 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1342 != nil {
		p.write(*flat1342)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1829 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1829 = _dollar_dollar.GetAttrs()
		}
		fields1336 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1829}
		unwrapped_fields1337 := fields1336
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1338 := unwrapped_fields1337[0].(*pb.RelationId)
		p.pretty_relation_id(field1338)
		p.newline()
		field1339 := unwrapped_fields1337[1].(*pb.Abstraction)
		p.pretty_abstraction(field1339)
		field1340 := unwrapped_fields1337[2].([]*pb.Attribute)
		if field1340 != nil {
			p.newline()
			opt_val1341 := field1340
			p.pretty_attrs(opt_val1341)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1349 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1349 != nil {
		p.write(*flat1349)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1830 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1830 = _dollar_dollar.GetAttrs()
		}
		fields1343 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1830}
		unwrapped_fields1344 := fields1343
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1345 := unwrapped_fields1344[0].(*pb.RelationId)
		p.pretty_relation_id(field1345)
		p.newline()
		field1346 := unwrapped_fields1344[1].([]interface{})
		p.pretty_abstraction_with_arity(field1346)
		field1347 := unwrapped_fields1344[2].([]*pb.Attribute)
		if field1347 != nil {
			p.newline()
			opt_val1348 := field1347
			p.pretty_attrs(opt_val1348)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1354 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1354 != nil {
		p.write(*flat1354)
		return nil
	} else {
		_dollar_dollar := msg
		_t1831 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1350 := []interface{}{_t1831, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1351 := fields1350
		p.write("(")
		p.indent()
		field1352 := unwrapped_fields1351[0].([]interface{})
		p.pretty_bindings(field1352)
		p.newline()
		field1353 := unwrapped_fields1351[1].(*pb.Formula)
		p.pretty_formula(field1353)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1361 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1361 != nil {
		p.write(*flat1361)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1832 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1832 = _dollar_dollar.GetAttrs()
		}
		fields1355 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1832}
		unwrapped_fields1356 := fields1355
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1357 := unwrapped_fields1356[0].(*pb.RelationId)
		p.pretty_relation_id(field1357)
		p.newline()
		field1358 := unwrapped_fields1356[1].(*pb.Abstraction)
		p.pretty_abstraction(field1358)
		field1359 := unwrapped_fields1356[2].([]*pb.Attribute)
		if field1359 != nil {
			p.newline()
			opt_val1360 := field1359
			p.pretty_attrs(opt_val1360)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1369 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1369 != nil {
		p.write(*flat1369)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1833 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1833 = _dollar_dollar.GetAttrs()
		}
		fields1362 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1833}
		unwrapped_fields1363 := fields1362
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1364 := unwrapped_fields1363[0].(*pb.Monoid)
		p.pretty_monoid(field1364)
		p.newline()
		field1365 := unwrapped_fields1363[1].(*pb.RelationId)
		p.pretty_relation_id(field1365)
		p.newline()
		field1366 := unwrapped_fields1363[2].([]interface{})
		p.pretty_abstraction_with_arity(field1366)
		field1367 := unwrapped_fields1363[3].([]*pb.Attribute)
		if field1367 != nil {
			p.newline()
			opt_val1368 := field1367
			p.pretty_attrs(opt_val1368)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1378 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1378 != nil {
		p.write(*flat1378)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1834 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1834 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1376 := _t1834
		if deconstruct_result1376 != nil {
			unwrapped1377 := deconstruct_result1376
			p.pretty_or_monoid(unwrapped1377)
		} else {
			_dollar_dollar := msg
			var _t1835 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1835 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1374 := _t1835
			if deconstruct_result1374 != nil {
				unwrapped1375 := deconstruct_result1374
				p.pretty_min_monoid(unwrapped1375)
			} else {
				_dollar_dollar := msg
				var _t1836 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1836 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1372 := _t1836
				if deconstruct_result1372 != nil {
					unwrapped1373 := deconstruct_result1372
					p.pretty_max_monoid(unwrapped1373)
				} else {
					_dollar_dollar := msg
					var _t1837 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1837 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1370 := _t1837
					if deconstruct_result1370 != nil {
						unwrapped1371 := deconstruct_result1370
						p.pretty_sum_monoid(unwrapped1371)
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
	fields1379 := msg
	_ = fields1379
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1382 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1382 != nil {
		p.write(*flat1382)
		return nil
	} else {
		_dollar_dollar := msg
		fields1380 := _dollar_dollar.GetType()
		unwrapped_fields1381 := fields1380
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1381)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1385 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1385 != nil {
		p.write(*flat1385)
		return nil
	} else {
		_dollar_dollar := msg
		fields1383 := _dollar_dollar.GetType()
		unwrapped_fields1384 := fields1383
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1384)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1388 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1388 != nil {
		p.write(*flat1388)
		return nil
	} else {
		_dollar_dollar := msg
		fields1386 := _dollar_dollar.GetType()
		unwrapped_fields1387 := fields1386
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1387)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1396 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1396 != nil {
		p.write(*flat1396)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1838 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1838 = _dollar_dollar.GetAttrs()
		}
		fields1389 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1838}
		unwrapped_fields1390 := fields1389
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1391 := unwrapped_fields1390[0].(*pb.Monoid)
		p.pretty_monoid(field1391)
		p.newline()
		field1392 := unwrapped_fields1390[1].(*pb.RelationId)
		p.pretty_relation_id(field1392)
		p.newline()
		field1393 := unwrapped_fields1390[2].([]interface{})
		p.pretty_abstraction_with_arity(field1393)
		field1394 := unwrapped_fields1390[3].([]*pb.Attribute)
		if field1394 != nil {
			p.newline()
			opt_val1395 := field1394
			p.pretty_attrs(opt_val1395)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1403 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1403 != nil {
		p.write(*flat1403)
		return nil
	} else {
		_dollar_dollar := msg
		fields1397 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1398 := fields1397
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1399 := unwrapped_fields1398[0].(*pb.RelationId)
		p.pretty_relation_id(field1399)
		p.newline()
		field1400 := unwrapped_fields1398[1].(*pb.Abstraction)
		p.pretty_abstraction(field1400)
		p.newline()
		field1401 := unwrapped_fields1398[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1401)
		p.newline()
		field1402 := unwrapped_fields1398[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1402)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1407 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1407 != nil {
		p.write(*flat1407)
		return nil
	} else {
		fields1404 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1404) == 0) {
			p.newline()
			for i1406, elem1405 := range fields1404 {
				if (i1406 > 0) {
					p.newline()
				}
				p.pretty_var(elem1405)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1411 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1411 != nil {
		p.write(*flat1411)
		return nil
	} else {
		fields1408 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1408) == 0) {
			p.newline()
			for i1410, elem1409 := range fields1408 {
				if (i1410 > 0) {
					p.newline()
				}
				p.pretty_var(elem1409)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1420 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1420 != nil {
		p.write(*flat1420)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1839 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1839 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1418 := _t1839
		if deconstruct_result1418 != nil {
			unwrapped1419 := deconstruct_result1418
			p.pretty_edb(unwrapped1419)
		} else {
			_dollar_dollar := msg
			var _t1840 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1840 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1416 := _t1840
			if deconstruct_result1416 != nil {
				unwrapped1417 := deconstruct_result1416
				p.pretty_betree_relation(unwrapped1417)
			} else {
				_dollar_dollar := msg
				var _t1841 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1841 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1414 := _t1841
				if deconstruct_result1414 != nil {
					unwrapped1415 := deconstruct_result1414
					p.pretty_csv_data(unwrapped1415)
				} else {
					_dollar_dollar := msg
					var _t1842 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1842 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1412 := _t1842
					if deconstruct_result1412 != nil {
						unwrapped1413 := deconstruct_result1412
						p.pretty_iceberg_data(unwrapped1413)
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
	flat1426 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1426 != nil {
		p.write(*flat1426)
		return nil
	} else {
		_dollar_dollar := msg
		fields1421 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1422 := fields1421
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1423 := unwrapped_fields1422[0].(*pb.RelationId)
		p.pretty_relation_id(field1423)
		p.newline()
		field1424 := unwrapped_fields1422[1].([]string)
		p.pretty_edb_path(field1424)
		p.newline()
		field1425 := unwrapped_fields1422[2].([]*pb.Type)
		p.pretty_edb_types(field1425)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1430 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1430 != nil {
		p.write(*flat1430)
		return nil
	} else {
		fields1427 := msg
		p.write("[")
		p.indent()
		for i1429, elem1428 := range fields1427 {
			if (i1429 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1428))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1434 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1434 != nil {
		p.write(*flat1434)
		return nil
	} else {
		fields1431 := msg
		p.write("[")
		p.indent()
		for i1433, elem1432 := range fields1431 {
			if (i1433 > 0) {
				p.newline()
			}
			p.pretty_type(elem1432)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1439 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1439 != nil {
		p.write(*flat1439)
		return nil
	} else {
		_dollar_dollar := msg
		fields1435 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1436 := fields1435
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1437 := unwrapped_fields1436[0].(*pb.RelationId)
		p.pretty_relation_id(field1437)
		p.newline()
		field1438 := unwrapped_fields1436[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1438)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1445 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1445 != nil {
		p.write(*flat1445)
		return nil
	} else {
		_dollar_dollar := msg
		_t1843 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1440 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1843}
		unwrapped_fields1441 := fields1440
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1442 := unwrapped_fields1441[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1442)
		p.newline()
		field1443 := unwrapped_fields1441[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1443)
		p.newline()
		field1444 := unwrapped_fields1441[2].([][]interface{})
		p.pretty_config_dict(field1444)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1449 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1449 != nil {
		p.write(*flat1449)
		return nil
	} else {
		fields1446 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1446) == 0) {
			p.newline()
			for i1448, elem1447 := range fields1446 {
				if (i1448 > 0) {
					p.newline()
				}
				p.pretty_type(elem1447)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1453 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1453 != nil {
		p.write(*flat1453)
		return nil
	} else {
		fields1450 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1450) == 0) {
			p.newline()
			for i1452, elem1451 := range fields1450 {
				if (i1452 > 0) {
					p.newline()
				}
				p.pretty_type(elem1451)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1463 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1463 != nil {
		p.write(*flat1463)
		return nil
	} else {
		_dollar_dollar := msg
		_t1844 := p.deconstruct_csv_data_columns_optional(_dollar_dollar)
		_t1845 := p.deconstruct_csv_data_relations_optional(_dollar_dollar)
		fields1454 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _t1844, _t1845, _dollar_dollar.GetAsof()}
		unwrapped_fields1455 := fields1454
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1456 := unwrapped_fields1455[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1456)
		p.newline()
		field1457 := unwrapped_fields1455[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1457)
		field1458 := unwrapped_fields1455[2].([]*pb.GNFColumn)
		if field1458 != nil {
			p.newline()
			opt_val1459 := field1458
			p.pretty_gnf_columns(opt_val1459)
		}
		field1460 := unwrapped_fields1455[3].(*pb.TargetRelations)
		if field1460 != nil {
			p.newline()
			opt_val1461 := field1460
			p.pretty_target_relations(opt_val1461)
		}
		p.newline()
		field1462 := unwrapped_fields1455[4].(string)
		p.pretty_csv_asof(field1462)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1470 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1470 != nil {
		p.write(*flat1470)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1846 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1846 = _dollar_dollar.GetPaths()
		}
		var _t1847 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1847 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1464 := []interface{}{_t1846, _t1847}
		unwrapped_fields1465 := fields1464
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1466 := unwrapped_fields1465[0].([]string)
		if field1466 != nil {
			p.newline()
			opt_val1467 := field1466
			p.pretty_csv_locator_paths(opt_val1467)
		}
		field1468 := unwrapped_fields1465[1].(*string)
		if field1468 != nil {
			p.newline()
			opt_val1469 := *field1468
			p.pretty_csv_locator_inline_data(opt_val1469)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1474 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1474 != nil {
		p.write(*flat1474)
		return nil
	} else {
		fields1471 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1471) == 0) {
			p.newline()
			for i1473, elem1472 := range fields1471 {
				if (i1473 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1472))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1476 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1476 != nil {
		p.write(*flat1476)
		return nil
	} else {
		fields1475 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1475))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1482 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1482 != nil {
		p.write(*flat1482)
		return nil
	} else {
		_dollar_dollar := msg
		_t1848 := p.deconstruct_csv_config(_dollar_dollar)
		_t1849 := p.deconstruct_csv_storage_integration_optional(_dollar_dollar)
		fields1477 := []interface{}{_t1848, _t1849}
		unwrapped_fields1478 := fields1477
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		field1479 := unwrapped_fields1478[0].([][]interface{})
		p.pretty_config_dict(field1479)
		field1480 := unwrapped_fields1478[1].([][]interface{})
		if field1480 != nil {
			p.newline()
			opt_val1481 := field1480
			p.pretty__storage_integration(opt_val1481)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty__storage_integration(msg [][]interface{}) interface{} {
	flat1484 := p.tryFlat(msg, func() { p.pretty__storage_integration(msg) })
	if flat1484 != nil {
		p.write(*flat1484)
		return nil
	} else {
		fields1483 := msg
		p.write("(")
		p.write("storage_integration")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(fields1483)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1488 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1488 != nil {
		p.write(*flat1488)
		return nil
	} else {
		fields1485 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1485) == 0) {
			p.newline()
			for i1487, elem1486 := range fields1485 {
				if (i1487 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1486)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1497 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1497 != nil {
		p.write(*flat1497)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1850 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1850 = _dollar_dollar.GetTargetId()
		}
		fields1489 := []interface{}{_dollar_dollar.GetColumnPath(), _t1850, _dollar_dollar.GetTypes()}
		unwrapped_fields1490 := fields1489
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1491 := unwrapped_fields1490[0].([]string)
		p.pretty_gnf_column_path(field1491)
		field1492 := unwrapped_fields1490[1].(*pb.RelationId)
		if field1492 != nil {
			p.newline()
			opt_val1493 := field1492
			p.pretty_relation_id(opt_val1493)
		}
		p.newline()
		p.write("[")
		field1494 := unwrapped_fields1490[2].([]*pb.Type)
		for i1496, elem1495 := range field1494 {
			if (i1496 > 0) {
				p.newline()
			}
			p.pretty_type(elem1495)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1504 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1504 != nil {
		p.write(*flat1504)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1851 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1851 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1502 := _t1851
		if deconstruct_result1502 != nil {
			unwrapped1503 := *deconstruct_result1502
			p.write(p.formatStringValue(unwrapped1503))
		} else {
			_dollar_dollar := msg
			var _t1852 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1852 = _dollar_dollar
			}
			deconstruct_result1498 := _t1852
			if deconstruct_result1498 != nil {
				unwrapped1499 := deconstruct_result1498
				p.write("[")
				p.indent()
				for i1501, elem1500 := range unwrapped1499 {
					if (i1501 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1500))
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
	flat1511 := p.tryFlat(msg, func() { p.pretty_target_relations(msg) })
	if flat1511 != nil {
		p.write(*flat1511)
		return nil
	} else {
		_dollar_dollar := msg
		_t1853 := p.deconstruct_relation_keys(_dollar_dollar)
		_t1854 := p.deconstruct_load_errors_optional(_dollar_dollar)
		fields1505 := []interface{}{_t1853, _dollar_dollar, _t1854}
		unwrapped_fields1506 := fields1505
		p.write("(")
		p.write("relations")
		p.indentSexp()
		p.newline()
		field1507 := unwrapped_fields1506[0].([]interface{})
		p.pretty_relation_keys(field1507)
		p.newline()
		field1508 := unwrapped_fields1506[1].(*pb.TargetRelations)
		p.pretty_relation_body(field1508)
		field1509 := unwrapped_fields1506[2].(*pb.RelationId)
		if field1509 != nil {
			p.newline()
			opt_val1510 := field1509
			p.pretty_load_errors(opt_val1510)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_keys(msg []interface{}) interface{} {
	flat1518 := p.tryFlat(msg, func() { p.pretty_relation_keys(msg) })
	if flat1518 != nil {
		p.write(*flat1518)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1855 []*pb.NamedColumn
		if !(_dollar_dollar[1].(bool)) {
			_t1855 = _dollar_dollar[0].([]*pb.NamedColumn)
		}
		deconstruct_result1514 := _t1855
		if deconstruct_result1514 != nil {
			unwrapped1515 := deconstruct_result1514
			p.write("(")
			p.write("keys")
			p.indentSexp()
			if !(len(unwrapped1515) == 0) {
				p.newline()
				for i1517, elem1516 := range unwrapped1515 {
					if (i1517 > 0) {
						p.newline()
					}
					p.pretty_named_column(elem1516)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1856 []interface{}
			if _dollar_dollar[1].(bool) {
				_t1856 = []interface{}{}
			}
			deconstruct_result1512 := _t1856
			if deconstruct_result1512 != nil {
				unwrapped1513 := deconstruct_result1512
				_ = unwrapped1513
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
	flat1523 := p.tryFlat(msg, func() { p.pretty_named_column(msg) })
	if flat1523 != nil {
		p.write(*flat1523)
		return nil
	} else {
		_dollar_dollar := msg
		fields1519 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetType()}
		unwrapped_fields1520 := fields1519
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1521 := unwrapped_fields1520[0].(string)
		p.write(p.formatStringValue(field1521))
		p.newline()
		field1522 := unwrapped_fields1520[1].(*pb.Type)
		p.pretty_type(field1522)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_body(msg *pb.TargetRelations) interface{} {
	flat1530 := p.tryFlat(msg, func() { p.pretty_relation_body(msg) })
	if flat1530 != nil {
		p.write(*flat1530)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1857 []*pb.TargetRelation
		if hasProtoField(_dollar_dollar, "plain") {
			_t1857 = _dollar_dollar.GetPlain().GetTargets()
		}
		deconstruct_result1528 := _t1857
		if deconstruct_result1528 != nil {
			unwrapped1529 := deconstruct_result1528
			p.pretty_non_cdc_relations(unwrapped1529)
		} else {
			_dollar_dollar := msg
			var _t1858 []interface{}
			if hasProtoField(_dollar_dollar, "cdc") {
				_t1858 = []interface{}{_dollar_dollar.GetCdc().GetInserts(), _dollar_dollar.GetCdc().GetDeletes()}
			}
			deconstruct_result1524 := _t1858
			if deconstruct_result1524 != nil {
				unwrapped1525 := deconstruct_result1524
				field1526 := unwrapped1525[0].([]*pb.TargetRelation)
				p.pretty_cdc_inserts(field1526)
				p.write(" ")
				field1527 := unwrapped1525[1].([]*pb.TargetRelation)
				p.pretty_cdc_deletes(field1527)
			} else {
				panic(ParseError{msg: "No matching rule for relation_body"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_non_cdc_relations(msg []*pb.TargetRelation) interface{} {
	flat1534 := p.tryFlat(msg, func() { p.pretty_non_cdc_relations(msg) })
	if flat1534 != nil {
		p.write(*flat1534)
		return nil
	} else {
		fields1531 := msg
		for i1533, elem1532 := range fields1531 {
			if (i1533 > 0) {
				p.newline()
			}
			p.pretty_target_relation(elem1532)
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_target_relation(msg *pb.TargetRelation) interface{} {
	flat1541 := p.tryFlat(msg, func() { p.pretty_target_relation(msg) })
	if flat1541 != nil {
		p.write(*flat1541)
		return nil
	} else {
		_dollar_dollar := msg
		fields1535 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetValues()}
		unwrapped_fields1536 := fields1535
		p.write("(")
		p.write("relation")
		p.indentSexp()
		p.newline()
		field1537 := unwrapped_fields1536[0].(*pb.RelationId)
		p.pretty_relation_id(field1537)
		field1538 := unwrapped_fields1536[1].([]*pb.NamedColumn)
		if !(len(field1538) == 0) {
			p.newline()
			for i1540, elem1539 := range field1538 {
				if (i1540 > 0) {
					p.newline()
				}
				p.pretty_named_column(elem1539)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_inserts(msg []*pb.TargetRelation) interface{} {
	flat1545 := p.tryFlat(msg, func() { p.pretty_cdc_inserts(msg) })
	if flat1545 != nil {
		p.write(*flat1545)
		return nil
	} else {
		fields1542 := msg
		p.write("(")
		p.write("inserts")
		p.indentSexp()
		if !(len(fields1542) == 0) {
			p.newline()
			for i1544, elem1543 := range fields1542 {
				if (i1544 > 0) {
					p.newline()
				}
				p.pretty_target_relation(elem1543)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_deletes(msg []*pb.TargetRelation) interface{} {
	flat1549 := p.tryFlat(msg, func() { p.pretty_cdc_deletes(msg) })
	if flat1549 != nil {
		p.write(*flat1549)
		return nil
	} else {
		fields1546 := msg
		p.write("(")
		p.write("deletes")
		p.indentSexp()
		if !(len(fields1546) == 0) {
			p.newline()
			for i1548, elem1547 := range fields1546 {
				if (i1548 > 0) {
					p.newline()
				}
				p.pretty_target_relation(elem1547)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_load_errors(msg *pb.RelationId) interface{} {
	flat1551 := p.tryFlat(msg, func() { p.pretty_load_errors(msg) })
	if flat1551 != nil {
		p.write(*flat1551)
		return nil
	} else {
		fields1550 := msg
		p.write("(")
		p.write("load_errors")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1550)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1553 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1553 != nil {
		p.write(*flat1553)
		return nil
	} else {
		fields1552 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1552))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1567 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1567 != nil {
		p.write(*flat1567)
		return nil
	} else {
		_dollar_dollar := msg
		_t1859 := p.deconstruct_iceberg_data_columns_optional(_dollar_dollar)
		_t1860 := p.deconstruct_iceberg_data_relations_optional(_dollar_dollar)
		_t1861 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1862 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1554 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _t1859, _t1860, _t1861, _t1862, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1555 := fields1554
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1556 := unwrapped_fields1555[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1556)
		p.newline()
		field1557 := unwrapped_fields1555[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1557)
		field1558 := unwrapped_fields1555[2].([]*pb.GNFColumn)
		if field1558 != nil {
			p.newline()
			opt_val1559 := field1558
			p.pretty_gnf_columns(opt_val1559)
		}
		field1560 := unwrapped_fields1555[3].(*pb.TargetRelations)
		if field1560 != nil {
			p.newline()
			opt_val1561 := field1560
			p.pretty_target_relations(opt_val1561)
		}
		field1562 := unwrapped_fields1555[4].(*string)
		if field1562 != nil {
			p.newline()
			opt_val1563 := *field1562
			p.pretty_iceberg_from_snapshot(opt_val1563)
		}
		field1564 := unwrapped_fields1555[5].(*string)
		if field1564 != nil {
			p.newline()
			opt_val1565 := *field1564
			p.pretty_iceberg_to_snapshot(opt_val1565)
		}
		p.newline()
		field1566 := unwrapped_fields1555[6].(bool)
		p.pretty_boolean_value(field1566)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1573 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1573 != nil {
		p.write(*flat1573)
		return nil
	} else {
		_dollar_dollar := msg
		fields1568 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1569 := fields1568
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1570 := unwrapped_fields1569[0].(string)
		p.pretty_iceberg_locator_table_name(field1570)
		p.newline()
		field1571 := unwrapped_fields1569[1].([]string)
		p.pretty_iceberg_locator_namespace(field1571)
		p.newline()
		field1572 := unwrapped_fields1569[2].(string)
		p.pretty_iceberg_locator_warehouse(field1572)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1575 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1575 != nil {
		p.write(*flat1575)
		return nil
	} else {
		fields1574 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1574))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1579 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1579 != nil {
		p.write(*flat1579)
		return nil
	} else {
		fields1576 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1576) == 0) {
			p.newline()
			for i1578, elem1577 := range fields1576 {
				if (i1578 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1577))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1581 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1581 != nil {
		p.write(*flat1581)
		return nil
	} else {
		fields1580 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1580))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1589 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1589 != nil {
		p.write(*flat1589)
		return nil
	} else {
		_dollar_dollar := msg
		_t1863 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1582 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1863, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1583 := fields1582
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1584 := unwrapped_fields1583[0].(string)
		p.pretty_iceberg_catalog_uri(field1584)
		field1585 := unwrapped_fields1583[1].(*string)
		if field1585 != nil {
			p.newline()
			opt_val1586 := *field1585
			p.pretty_iceberg_catalog_config_scope(opt_val1586)
		}
		p.newline()
		field1587 := unwrapped_fields1583[2].([][]interface{})
		p.pretty_iceberg_properties(field1587)
		p.newline()
		field1588 := unwrapped_fields1583[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1588)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1591 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1591 != nil {
		p.write(*flat1591)
		return nil
	} else {
		fields1590 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1590))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1593 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1593 != nil {
		p.write(*flat1593)
		return nil
	} else {
		fields1592 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1592))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1597 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1597 != nil {
		p.write(*flat1597)
		return nil
	} else {
		fields1594 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1594) == 0) {
			p.newline()
			for i1596, elem1595 := range fields1594 {
				if (i1596 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1595)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1602 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1602 != nil {
		p.write(*flat1602)
		return nil
	} else {
		_dollar_dollar := msg
		fields1598 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1599 := fields1598
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1600 := unwrapped_fields1599[0].(string)
		p.write(p.formatStringValue(field1600))
		p.newline()
		field1601 := unwrapped_fields1599[1].(string)
		p.write(p.formatStringValue(field1601))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1606 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1606 != nil {
		p.write(*flat1606)
		return nil
	} else {
		fields1603 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1603) == 0) {
			p.newline()
			for i1605, elem1604 := range fields1603 {
				if (i1605 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1604)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1611 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1611 != nil {
		p.write(*flat1611)
		return nil
	} else {
		_dollar_dollar := msg
		_t1864 := p.mask_secret_value(_dollar_dollar)
		fields1607 := []interface{}{_dollar_dollar[0].(string), _t1864}
		unwrapped_fields1608 := fields1607
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1609 := unwrapped_fields1608[0].(string)
		p.write(p.formatStringValue(field1609))
		p.newline()
		field1610 := unwrapped_fields1608[1].(string)
		p.write(p.formatStringValue(field1610))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1613 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1613 != nil {
		p.write(*flat1613)
		return nil
	} else {
		fields1612 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1612))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1615 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1615 != nil {
		p.write(*flat1615)
		return nil
	} else {
		fields1614 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1614))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1618 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1618 != nil {
		p.write(*flat1618)
		return nil
	} else {
		_dollar_dollar := msg
		fields1616 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1617 := fields1616
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1617)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1623 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1623 != nil {
		p.write(*flat1623)
		return nil
	} else {
		_dollar_dollar := msg
		fields1619 := _dollar_dollar.GetRelations()
		unwrapped_fields1620 := fields1619
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1620) == 0) {
			p.newline()
			for i1622, elem1621 := range unwrapped_fields1620 {
				if (i1622 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1621)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1630 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1630 != nil {
		p.write(*flat1630)
		return nil
	} else {
		_dollar_dollar := msg
		fields1624 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1625 := fields1624
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1626 := unwrapped_fields1625[0].([]string)
		p.pretty_edb_path(field1626)
		field1627 := unwrapped_fields1625[1].([]*pb.SnapshotMapping)
		if !(len(field1627) == 0) {
			p.newline()
			for i1629, elem1628 := range field1627 {
				if (i1629 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1628)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1635 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1635 != nil {
		p.write(*flat1635)
		return nil
	} else {
		_dollar_dollar := msg
		fields1631 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1632 := fields1631
		field1633 := unwrapped_fields1632[0].([]string)
		p.pretty_edb_path(field1633)
		p.write(" ")
		field1634 := unwrapped_fields1632[1].(*pb.RelationId)
		p.pretty_relation_id(field1634)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1639 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1639 != nil {
		p.write(*flat1639)
		return nil
	} else {
		fields1636 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1636) == 0) {
			p.newline()
			for i1638, elem1637 := range fields1636 {
				if (i1638 > 0) {
					p.newline()
				}
				p.pretty_read(elem1637)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1650 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1650 != nil {
		p.write(*flat1650)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1865 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1865 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1648 := _t1865
		if deconstruct_result1648 != nil {
			unwrapped1649 := deconstruct_result1648
			p.pretty_demand(unwrapped1649)
		} else {
			_dollar_dollar := msg
			var _t1866 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1866 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1646 := _t1866
			if deconstruct_result1646 != nil {
				unwrapped1647 := deconstruct_result1646
				p.pretty_output(unwrapped1647)
			} else {
				_dollar_dollar := msg
				var _t1867 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1867 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1644 := _t1867
				if deconstruct_result1644 != nil {
					unwrapped1645 := deconstruct_result1644
					p.pretty_what_if(unwrapped1645)
				} else {
					_dollar_dollar := msg
					var _t1868 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1868 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1642 := _t1868
					if deconstruct_result1642 != nil {
						unwrapped1643 := deconstruct_result1642
						p.pretty_abort(unwrapped1643)
					} else {
						_dollar_dollar := msg
						var _t1869 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1869 = _dollar_dollar.GetExport()
						}
						deconstruct_result1640 := _t1869
						if deconstruct_result1640 != nil {
							unwrapped1641 := deconstruct_result1640
							p.pretty_export(unwrapped1641)
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
	flat1653 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1653 != nil {
		p.write(*flat1653)
		return nil
	} else {
		_dollar_dollar := msg
		fields1651 := _dollar_dollar.GetRelationId()
		unwrapped_fields1652 := fields1651
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1652)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1658 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1658 != nil {
		p.write(*flat1658)
		return nil
	} else {
		_dollar_dollar := msg
		fields1654 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1655 := fields1654
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1656 := unwrapped_fields1655[0].(string)
		p.pretty_name(field1656)
		p.newline()
		field1657 := unwrapped_fields1655[1].(*pb.RelationId)
		p.pretty_relation_id(field1657)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1663 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1663 != nil {
		p.write(*flat1663)
		return nil
	} else {
		_dollar_dollar := msg
		fields1659 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1660 := fields1659
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1661 := unwrapped_fields1660[0].(string)
		p.pretty_name(field1661)
		p.newline()
		field1662 := unwrapped_fields1660[1].(*pb.Epoch)
		p.pretty_epoch(field1662)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1669 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1669 != nil {
		p.write(*flat1669)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1870 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1870 = ptr(_dollar_dollar.GetName())
		}
		fields1664 := []interface{}{_t1870, _dollar_dollar.GetRelationId()}
		unwrapped_fields1665 := fields1664
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1666 := unwrapped_fields1665[0].(*string)
		if field1666 != nil {
			p.newline()
			opt_val1667 := *field1666
			p.pretty_name(opt_val1667)
		}
		p.newline()
		field1668 := unwrapped_fields1665[1].(*pb.RelationId)
		p.pretty_relation_id(field1668)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1674 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1674 != nil {
		p.write(*flat1674)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1871 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1871 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1672 := _t1871
		if deconstruct_result1672 != nil {
			unwrapped1673 := deconstruct_result1672
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1673)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1872 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1872 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1670 := _t1872
			if deconstruct_result1670 != nil {
				unwrapped1671 := deconstruct_result1670
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1671)
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
	flat1685 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1685 != nil {
		p.write(*flat1685)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1873 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1874 := p.deconstruct_export_csv_output_location(_dollar_dollar)
			_t1873 = []interface{}{_t1874, _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1680 := _t1873
		if deconstruct_result1680 != nil {
			unwrapped1681 := deconstruct_result1680
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1682 := unwrapped1681[0].([]interface{})
			p.pretty_export_csv_output_location(field1682)
			p.newline()
			field1683 := unwrapped1681[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1683)
			p.newline()
			field1684 := unwrapped1681[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1684)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1875 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1876 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1875 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1876}
			}
			deconstruct_result1675 := _t1875
			if deconstruct_result1675 != nil {
				unwrapped1676 := deconstruct_result1675
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1677 := unwrapped1676[0].(string)
				p.pretty_export_csv_path(field1677)
				p.newline()
				field1678 := unwrapped1676[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1678)
				p.newline()
				field1679 := unwrapped1676[2].([][]interface{})
				p.pretty_config_dict(field1679)
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
	flat1690 := p.tryFlat(msg, func() { p.pretty_export_csv_output_location(msg) })
	if flat1690 != nil {
		p.write(*flat1690)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1877 *string
		if _dollar_dollar[0].(string) != "" {
			_t1877 = ptr(_dollar_dollar[0].(string))
		}
		deconstruct_result1688 := _t1877
		if deconstruct_result1688 != nil {
			unwrapped1689 := *deconstruct_result1688
			p.write("(")
			p.write("path")
			p.indentSexp()
			p.newline()
			p.write(p.formatStringValue(unwrapped1689))
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1878 *string
			if _dollar_dollar[1].(string) != "" {
				_t1878 = ptr(_dollar_dollar[1].(string))
			}
			deconstruct_result1686 := _t1878
			if deconstruct_result1686 != nil {
				unwrapped1687 := *deconstruct_result1686
				p.write("(")
				p.write("transaction_output_name")
				p.indentSexp()
				p.newline()
				p.pretty_name(unwrapped1687)
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
	flat1697 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1697 != nil {
		p.write(*flat1697)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1879 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1879 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1693 := _t1879
		if deconstruct_result1693 != nil {
			unwrapped1694 := deconstruct_result1693
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1694) == 0) {
				p.newline()
				for i1696, elem1695 := range unwrapped1694 {
					if (i1696 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1695)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1880 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1880 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1691 := _t1880
			if deconstruct_result1691 != nil {
				unwrapped1692 := deconstruct_result1691
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1692)
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
	flat1702 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1702 != nil {
		p.write(*flat1702)
		return nil
	} else {
		_dollar_dollar := msg
		fields1698 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1699 := fields1698
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1700 := unwrapped_fields1699[0].(string)
		p.write(p.formatStringValue(field1700))
		p.newline()
		field1701 := unwrapped_fields1699[1].(*pb.RelationId)
		p.pretty_relation_id(field1701)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1704 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1704 != nil {
		p.write(*flat1704)
		return nil
	} else {
		fields1703 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1703))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1708 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1708 != nil {
		p.write(*flat1708)
		return nil
	} else {
		fields1705 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1705) == 0) {
			p.newline()
			for i1707, elem1706 := range fields1705 {
				if (i1707 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1706)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1717 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1717 != nil {
		p.write(*flat1717)
		return nil
	} else {
		_dollar_dollar := msg
		_t1881 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1709 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1881}
		unwrapped_fields1710 := fields1709
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1711 := unwrapped_fields1710[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1711)
		p.newline()
		field1712 := unwrapped_fields1710[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1712)
		p.newline()
		field1713 := unwrapped_fields1710[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1713)
		p.newline()
		field1714 := unwrapped_fields1710[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1714)
		field1715 := unwrapped_fields1710[4].([][]interface{})
		if field1715 != nil {
			p.newline()
			opt_val1716 := field1715
			p.pretty_config_dict(opt_val1716)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1719 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1719 != nil {
		p.write(*flat1719)
		return nil
	} else {
		fields1718 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1718)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1723 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1723 != nil {
		p.write(*flat1723)
		return nil
	} else {
		fields1720 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1720) == 0) {
			p.newline()
			for i1722, elem1721 := range fields1720 {
				if (i1722 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1721)
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
		_t1938 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1938)
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
	case *pb.FixedType:
		p.pretty_fixed_type(m)
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
