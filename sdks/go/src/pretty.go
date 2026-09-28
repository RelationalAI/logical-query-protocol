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
	var _t1874 interface{}
	if hasProtoField(msg, "load_errors") {
		return msg.GetLoadErrors()
	}
	_ = _t1874
	return nil
}

func (p *PrettyPrinter) deconstruct_csv_data_columns_optional(msg *pb.CSVData) []*pb.GNFColumn {
	var _t1875 interface{}
	if hasProtoField(msg, "relations") {
		return nil
	}
	_ = _t1875
	return msg.GetColumns()
}

func (p *PrettyPrinter) deconstruct_csv_data_relations_optional(msg *pb.CSVData) *pb.TargetRelations {
	var _t1876 interface{}
	if hasProtoField(msg, "relations") {
		return msg.GetRelations()
	}
	_ = _t1876
	return nil
}

func (p *PrettyPrinter) deconstruct_export_csv_output_location(msg *pb.ExportCSVConfig) []interface{} {
	return []interface{}{msg.GetPath(), msg.GetTransactionOutputName()}
}

func (p *PrettyPrinter) _make_value_int32(v int32) *pb.Value {
	_t1877 := &pb.Value{}
	_t1877.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1877
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1878 := &pb.Value{}
	_t1878.Value = &pb.Value_IntValue{IntValue: v}
	return _t1878
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1879 := &pb.Value{}
	_t1879.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1879
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1880 := &pb.Value{}
	_t1880.Value = &pb.Value_StringValue{StringValue: v}
	return _t1880
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1881 := &pb.Value{}
	_t1881.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1881
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1882 := &pb.Value{}
	_t1882.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1882
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1883 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1883})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1884 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1884})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1885 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1885})
			}
		}
	}
	_t1886 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1886})
	for _, pair := range valueMapToPairs(msg.GetConfigurationValues()) {
		result = append(result, pair)
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1887 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1887})
	_t1888 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1888})
	if msg.GetNewLine() != "" {
		_t1889 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1889})
	}
	_t1890 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1890})
	_t1891 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1891})
	_t1892 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1892})
	if msg.GetComment() != "" {
		_t1893 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1893})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1894 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1894})
	}
	_t1895 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1895})
	_t1896 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1896})
	_t1897 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1897})
	if msg.GetPartitionSizeMb() != 0 {
		_t1898 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1898})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_storage_integration_optional(msg *pb.CSVConfig) [][]interface{} {
	var _t1899 interface{}
	if !(hasProtoField(msg, "storage_integration")) {
		return nil
	}
	_ = _t1899
	si := msg.GetStorageIntegration()
	result := [][]interface{}{}
	if si.GetProvider() != "" {
		_t1900 := p._make_value_string(si.GetProvider())
		result = append(result, []interface{}{"provider", _t1900})
	}
	if si.GetAzureSasToken() != "" {
		_t1901 := p._make_value_string("***")
		result = append(result, []interface{}{"azure_sas_token", _t1901})
	}
	if si.GetS3Region() != "" {
		_t1902 := p._make_value_string(si.GetS3Region())
		result = append(result, []interface{}{"s3_region", _t1902})
	}
	if si.GetS3AccessKeyId() != "" {
		_t1903 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_access_key_id", _t1903})
	}
	if si.GetS3SecretAccessKey() != "" {
		_t1904 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_secret_access_key", _t1904})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1905 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1905})
	_t1906 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1906})
	_t1907 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1907})
	_t1908 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1908})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1909 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1909})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1910 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1910})
		}
	}
	_t1911 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1911})
	_t1912 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1912})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1913 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1913})
	}
	if msg.Compression != nil {
		_t1914 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1914})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1915 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1915})
	}
	if msg.SyntaxMissingString != nil {
		_t1916 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1916})
	}
	if msg.SyntaxDelim != nil {
		_t1917 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1917})
	}
	if msg.SyntaxQuotechar != nil {
		_t1918 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1918})
	}
	if msg.SyntaxEscapechar != nil {
		_t1919 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1919})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1920 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1920
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1921 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1921
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1922 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1922
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1923 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1923})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1924 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1924})
	}
	if msg.GetCompression() != "" {
		_t1925 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1925})
	}
	var _t1926 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1926
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1927 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1927
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
	flat868 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat868 != nil {
		p.write(*flat868)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1718 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1718 = _dollar_dollar.GetConfigure()
		}
		var _t1719 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1719 = _dollar_dollar.GetSync()
		}
		fields859 := []interface{}{_t1718, _t1719, _dollar_dollar.GetEpochs()}
		unwrapped_fields860 := fields859
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field861 := unwrapped_fields860[0].(*pb.Configure)
		if field861 != nil {
			p.newline()
			opt_val862 := field861
			p.pretty_configure(opt_val862)
		}
		field863 := unwrapped_fields860[1].(*pb.Sync)
		if field863 != nil {
			p.newline()
			opt_val864 := field863
			p.pretty_sync(opt_val864)
		}
		field865 := unwrapped_fields860[2].([]*pb.Epoch)
		if !(len(field865) == 0) {
			p.newline()
			for i867, elem866 := range field865 {
				if (i867 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem866)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat871 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat871 != nil {
		p.write(*flat871)
		return nil
	} else {
		_dollar_dollar := msg
		_t1720 := p.deconstruct_configure(_dollar_dollar)
		fields869 := _t1720
		unwrapped_fields870 := fields869
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields870)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat875 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat875 != nil {
		p.write(*flat875)
		return nil
	} else {
		fields872 := msg
		p.write("{")
		p.indent()
		if !(len(fields872) == 0) {
			p.newline()
			for i874, elem873 := range fields872 {
				if (i874 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem873)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat880 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat880 != nil {
		p.write(*flat880)
		return nil
	} else {
		_dollar_dollar := msg
		fields876 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields877 := fields876
		p.write(":")
		field878 := unwrapped_fields877[0].(string)
		p.write(field878)
		p.write(" ")
		field879 := unwrapped_fields877[1].(*pb.Value)
		p.pretty_raw_value(field879)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat906 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat906 != nil {
		p.write(*flat906)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1721 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1721 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result904 := _t1721
		if deconstruct_result904 != nil {
			unwrapped905 := deconstruct_result904
			p.pretty_raw_date(unwrapped905)
		} else {
			_dollar_dollar := msg
			var _t1722 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1722 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result902 := _t1722
			if deconstruct_result902 != nil {
				unwrapped903 := deconstruct_result902
				p.pretty_raw_datetime(unwrapped903)
			} else {
				_dollar_dollar := msg
				var _t1723 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1723 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result900 := _t1723
				if deconstruct_result900 != nil {
					unwrapped901 := *deconstruct_result900
					p.write(p.formatStringValue(unwrapped901))
				} else {
					_dollar_dollar := msg
					var _t1724 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1724 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result898 := _t1724
					if deconstruct_result898 != nil {
						unwrapped899 := *deconstruct_result898
						p.write(fmt.Sprintf("%di32", unwrapped899))
					} else {
						_dollar_dollar := msg
						var _t1725 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1725 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result896 := _t1725
						if deconstruct_result896 != nil {
							unwrapped897 := *deconstruct_result896
							p.write(fmt.Sprintf("%d", unwrapped897))
						} else {
							_dollar_dollar := msg
							var _t1726 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1726 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result894 := _t1726
							if deconstruct_result894 != nil {
								unwrapped895 := *deconstruct_result894
								p.write(formatFloat32(unwrapped895))
							} else {
								_dollar_dollar := msg
								var _t1727 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1727 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result892 := _t1727
								if deconstruct_result892 != nil {
									unwrapped893 := *deconstruct_result892
									p.write(formatFloat64(unwrapped893))
								} else {
									_dollar_dollar := msg
									var _t1728 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1728 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result890 := _t1728
									if deconstruct_result890 != nil {
										unwrapped891 := *deconstruct_result890
										p.write(fmt.Sprintf("%du32", unwrapped891))
									} else {
										_dollar_dollar := msg
										var _t1729 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1729 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result888 := _t1729
										if deconstruct_result888 != nil {
											unwrapped889 := deconstruct_result888
											p.write(p.formatUint128(unwrapped889))
										} else {
											_dollar_dollar := msg
											var _t1730 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1730 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result886 := _t1730
											if deconstruct_result886 != nil {
												unwrapped887 := deconstruct_result886
												p.write(p.formatInt128(unwrapped887))
											} else {
												_dollar_dollar := msg
												var _t1731 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1731 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result884 := _t1731
												if deconstruct_result884 != nil {
													unwrapped885 := deconstruct_result884
													p.write(p.formatDecimal(unwrapped885))
												} else {
													_dollar_dollar := msg
													var _t1732 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1732 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result882 := _t1732
													if deconstruct_result882 != nil {
														unwrapped883 := *deconstruct_result882
														p.pretty_boolean_value(unwrapped883)
													} else {
														fields881 := msg
														_ = fields881
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
	flat912 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat912 != nil {
		p.write(*flat912)
		return nil
	} else {
		_dollar_dollar := msg
		fields907 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields908 := fields907
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field909 := unwrapped_fields908[0].(int64)
		p.write(fmt.Sprintf("%d", field909))
		p.newline()
		field910 := unwrapped_fields908[1].(int64)
		p.write(fmt.Sprintf("%d", field910))
		p.newline()
		field911 := unwrapped_fields908[2].(int64)
		p.write(fmt.Sprintf("%d", field911))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat923 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat923 != nil {
		p.write(*flat923)
		return nil
	} else {
		_dollar_dollar := msg
		fields913 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields914 := fields913
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field915 := unwrapped_fields914[0].(int64)
		p.write(fmt.Sprintf("%d", field915))
		p.newline()
		field916 := unwrapped_fields914[1].(int64)
		p.write(fmt.Sprintf("%d", field916))
		p.newline()
		field917 := unwrapped_fields914[2].(int64)
		p.write(fmt.Sprintf("%d", field917))
		p.newline()
		field918 := unwrapped_fields914[3].(int64)
		p.write(fmt.Sprintf("%d", field918))
		p.newline()
		field919 := unwrapped_fields914[4].(int64)
		p.write(fmt.Sprintf("%d", field919))
		p.newline()
		field920 := unwrapped_fields914[5].(int64)
		p.write(fmt.Sprintf("%d", field920))
		field921 := unwrapped_fields914[6].(*int64)
		if field921 != nil {
			p.newline()
			opt_val922 := *field921
			p.write(fmt.Sprintf("%d", opt_val922))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1733 []interface{}
	if _dollar_dollar {
		_t1733 = []interface{}{}
	}
	deconstruct_result926 := _t1733
	if deconstruct_result926 != nil {
		unwrapped927 := deconstruct_result926
		_ = unwrapped927
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1734 []interface{}
		if !(_dollar_dollar) {
			_t1734 = []interface{}{}
		}
		deconstruct_result924 := _t1734
		if deconstruct_result924 != nil {
			unwrapped925 := deconstruct_result924
			_ = unwrapped925
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat932 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat932 != nil {
		p.write(*flat932)
		return nil
	} else {
		_dollar_dollar := msg
		fields928 := _dollar_dollar.GetFragments()
		unwrapped_fields929 := fields928
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields929) == 0) {
			p.newline()
			for i931, elem930 := range unwrapped_fields929 {
				if (i931 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem930)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat935 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat935 != nil {
		p.write(*flat935)
		return nil
	} else {
		_dollar_dollar := msg
		fields933 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields934 := fields933
		p.write(":")
		p.write(unwrapped_fields934)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat942 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat942 != nil {
		p.write(*flat942)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1735 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1735 = _dollar_dollar.GetWrites()
		}
		var _t1736 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1736 = _dollar_dollar.GetReads()
		}
		fields936 := []interface{}{_t1735, _t1736}
		unwrapped_fields937 := fields936
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field938 := unwrapped_fields937[0].([]*pb.Write)
		if field938 != nil {
			p.newline()
			opt_val939 := field938
			p.pretty_epoch_writes(opt_val939)
		}
		field940 := unwrapped_fields937[1].([]*pb.Read)
		if field940 != nil {
			p.newline()
			opt_val941 := field940
			p.pretty_epoch_reads(opt_val941)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat946 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat946 != nil {
		p.write(*flat946)
		return nil
	} else {
		fields943 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields943) == 0) {
			p.newline()
			for i945, elem944 := range fields943 {
				if (i945 > 0) {
					p.newline()
				}
				p.pretty_write(elem944)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat955 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat955 != nil {
		p.write(*flat955)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1737 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1737 = _dollar_dollar.GetDefine()
		}
		deconstruct_result953 := _t1737
		if deconstruct_result953 != nil {
			unwrapped954 := deconstruct_result953
			p.pretty_define(unwrapped954)
		} else {
			_dollar_dollar := msg
			var _t1738 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1738 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result951 := _t1738
			if deconstruct_result951 != nil {
				unwrapped952 := deconstruct_result951
				p.pretty_undefine(unwrapped952)
			} else {
				_dollar_dollar := msg
				var _t1739 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1739 = _dollar_dollar.GetContext()
				}
				deconstruct_result949 := _t1739
				if deconstruct_result949 != nil {
					unwrapped950 := deconstruct_result949
					p.pretty_context(unwrapped950)
				} else {
					_dollar_dollar := msg
					var _t1740 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1740 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result947 := _t1740
					if deconstruct_result947 != nil {
						unwrapped948 := deconstruct_result947
						p.pretty_snapshot(unwrapped948)
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
	flat958 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat958 != nil {
		p.write(*flat958)
		return nil
	} else {
		_dollar_dollar := msg
		fields956 := _dollar_dollar.GetFragment()
		unwrapped_fields957 := fields956
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields957)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat965 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat965 != nil {
		p.write(*flat965)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields959 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields960 := fields959
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field961 := unwrapped_fields960[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field961)
		field962 := unwrapped_fields960[1].([]*pb.Declaration)
		if !(len(field962) == 0) {
			p.newline()
			for i964, elem963 := range field962 {
				if (i964 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem963)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat967 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat967 != nil {
		p.write(*flat967)
		return nil
	} else {
		fields966 := msg
		p.pretty_fragment_id(fields966)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat976 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat976 != nil {
		p.write(*flat976)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1741 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1741 = _dollar_dollar.GetDef()
		}
		deconstruct_result974 := _t1741
		if deconstruct_result974 != nil {
			unwrapped975 := deconstruct_result974
			p.pretty_def(unwrapped975)
		} else {
			_dollar_dollar := msg
			var _t1742 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1742 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result972 := _t1742
			if deconstruct_result972 != nil {
				unwrapped973 := deconstruct_result972
				p.pretty_algorithm(unwrapped973)
			} else {
				_dollar_dollar := msg
				var _t1743 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1743 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result970 := _t1743
				if deconstruct_result970 != nil {
					unwrapped971 := deconstruct_result970
					p.pretty_constraint(unwrapped971)
				} else {
					_dollar_dollar := msg
					var _t1744 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1744 = _dollar_dollar.GetData()
					}
					deconstruct_result968 := _t1744
					if deconstruct_result968 != nil {
						unwrapped969 := deconstruct_result968
						p.pretty_data(unwrapped969)
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
	flat983 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat983 != nil {
		p.write(*flat983)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1745 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1745 = _dollar_dollar.GetAttrs()
		}
		fields977 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1745}
		unwrapped_fields978 := fields977
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field979 := unwrapped_fields978[0].(*pb.RelationId)
		p.pretty_relation_id(field979)
		p.newline()
		field980 := unwrapped_fields978[1].(*pb.Abstraction)
		p.pretty_abstraction(field980)
		field981 := unwrapped_fields978[2].([]*pb.Attribute)
		if field981 != nil {
			p.newline()
			opt_val982 := field981
			p.pretty_attrs(opt_val982)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat988 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat988 != nil {
		p.write(*flat988)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1746 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1747 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1746 = ptr(_t1747)
		}
		deconstruct_result986 := _t1746
		if deconstruct_result986 != nil {
			unwrapped987 := *deconstruct_result986
			p.write(":")
			p.write(unwrapped987)
		} else {
			_dollar_dollar := msg
			_t1748 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result984 := _t1748
			if deconstruct_result984 != nil {
				unwrapped985 := deconstruct_result984
				p.write(p.formatUint128(unwrapped985))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat993 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat993 != nil {
		p.write(*flat993)
		return nil
	} else {
		_dollar_dollar := msg
		_t1749 := p.deconstruct_bindings(_dollar_dollar)
		fields989 := []interface{}{_t1749, _dollar_dollar.GetValue()}
		unwrapped_fields990 := fields989
		p.write("(")
		p.indent()
		field991 := unwrapped_fields990[0].([]interface{})
		p.pretty_bindings(field991)
		p.newline()
		field992 := unwrapped_fields990[1].(*pb.Formula)
		p.pretty_formula(field992)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat1001 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat1001 != nil {
		p.write(*flat1001)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1750 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1750 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields994 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1750}
		unwrapped_fields995 := fields994
		p.write("[")
		p.indent()
		field996 := unwrapped_fields995[0].([]*pb.Binding)
		for i998, elem997 := range field996 {
			if (i998 > 0) {
				p.newline()
			}
			p.pretty_binding(elem997)
		}
		field999 := unwrapped_fields995[1].([]*pb.Binding)
		if field999 != nil {
			p.newline()
			opt_val1000 := field999
			p.pretty_value_bindings(opt_val1000)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat1006 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat1006 != nil {
		p.write(*flat1006)
		return nil
	} else {
		_dollar_dollar := msg
		fields1002 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields1003 := fields1002
		field1004 := unwrapped_fields1003[0].(string)
		p.write(field1004)
		p.write("::")
		field1005 := unwrapped_fields1003[1].(*pb.Type)
		p.pretty_type(field1005)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat1037 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat1037 != nil {
		p.write(*flat1037)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1751 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1751 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result1035 := _t1751
		if deconstruct_result1035 != nil {
			unwrapped1036 := deconstruct_result1035
			p.pretty_unspecified_type(unwrapped1036)
		} else {
			_dollar_dollar := msg
			var _t1752 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1752 = _dollar_dollar.GetStringType()
			}
			deconstruct_result1033 := _t1752
			if deconstruct_result1033 != nil {
				unwrapped1034 := deconstruct_result1033
				p.pretty_string_type(unwrapped1034)
			} else {
				_dollar_dollar := msg
				var _t1753 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1753 = _dollar_dollar.GetIntType()
				}
				deconstruct_result1031 := _t1753
				if deconstruct_result1031 != nil {
					unwrapped1032 := deconstruct_result1031
					p.pretty_int_type(unwrapped1032)
				} else {
					_dollar_dollar := msg
					var _t1754 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1754 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result1029 := _t1754
					if deconstruct_result1029 != nil {
						unwrapped1030 := deconstruct_result1029
						p.pretty_float_type(unwrapped1030)
					} else {
						_dollar_dollar := msg
						var _t1755 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1755 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result1027 := _t1755
						if deconstruct_result1027 != nil {
							unwrapped1028 := deconstruct_result1027
							p.pretty_uint128_type(unwrapped1028)
						} else {
							_dollar_dollar := msg
							var _t1756 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1756 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result1025 := _t1756
							if deconstruct_result1025 != nil {
								unwrapped1026 := deconstruct_result1025
								p.pretty_int128_type(unwrapped1026)
							} else {
								_dollar_dollar := msg
								var _t1757 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1757 = _dollar_dollar.GetDateType()
								}
								deconstruct_result1023 := _t1757
								if deconstruct_result1023 != nil {
									unwrapped1024 := deconstruct_result1023
									p.pretty_date_type(unwrapped1024)
								} else {
									_dollar_dollar := msg
									var _t1758 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1758 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result1021 := _t1758
									if deconstruct_result1021 != nil {
										unwrapped1022 := deconstruct_result1021
										p.pretty_datetime_type(unwrapped1022)
									} else {
										_dollar_dollar := msg
										var _t1759 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1759 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result1019 := _t1759
										if deconstruct_result1019 != nil {
											unwrapped1020 := deconstruct_result1019
											p.pretty_missing_type(unwrapped1020)
										} else {
											_dollar_dollar := msg
											var _t1760 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1760 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result1017 := _t1760
											if deconstruct_result1017 != nil {
												unwrapped1018 := deconstruct_result1017
												p.pretty_decimal_type(unwrapped1018)
											} else {
												_dollar_dollar := msg
												var _t1761 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1761 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result1015 := _t1761
												if deconstruct_result1015 != nil {
													unwrapped1016 := deconstruct_result1015
													p.pretty_boolean_type(unwrapped1016)
												} else {
													_dollar_dollar := msg
													var _t1762 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1762 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result1013 := _t1762
													if deconstruct_result1013 != nil {
														unwrapped1014 := deconstruct_result1013
														p.pretty_int32_type(unwrapped1014)
													} else {
														_dollar_dollar := msg
														var _t1763 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1763 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result1011 := _t1763
														if deconstruct_result1011 != nil {
															unwrapped1012 := deconstruct_result1011
															p.pretty_float32_type(unwrapped1012)
														} else {
															_dollar_dollar := msg
															var _t1764 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1764 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result1009 := _t1764
															if deconstruct_result1009 != nil {
																unwrapped1010 := deconstruct_result1009
																p.pretty_uint32_type(unwrapped1010)
															} else {
																_dollar_dollar := msg
																var _t1765 *pb.FixedType
																if hasProtoField(_dollar_dollar, "fixed_type") {
																	_t1765 = _dollar_dollar.GetFixedType()
																}
																deconstruct_result1007 := _t1765
																if deconstruct_result1007 != nil {
																	unwrapped1008 := deconstruct_result1007
																	p.pretty_fixed_type(unwrapped1008)
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
	fields1038 := msg
	_ = fields1038
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields1039 := msg
	_ = fields1039
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields1040 := msg
	_ = fields1040
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields1041 := msg
	_ = fields1041
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields1042 := msg
	_ = fields1042
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields1043 := msg
	_ = fields1043
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields1044 := msg
	_ = fields1044
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields1045 := msg
	_ = fields1045
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields1046 := msg
	_ = fields1046
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat1051 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat1051 != nil {
		p.write(*flat1051)
		return nil
	} else {
		_dollar_dollar := msg
		fields1047 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields1048 := fields1047
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field1049 := unwrapped_fields1048[0].(int64)
		p.write(fmt.Sprintf("%d", field1049))
		p.newline()
		field1050 := unwrapped_fields1048[1].(int64)
		p.write(fmt.Sprintf("%d", field1050))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields1052 := msg
	_ = fields1052
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields1053 := msg
	_ = fields1053
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields1054 := msg
	_ = fields1054
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields1055 := msg
	_ = fields1055
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_fixed_type(msg *pb.FixedType) interface{} {
	flat1058 := p.tryFlat(msg, func() { p.pretty_fixed_type(msg) })
	if flat1058 != nil {
		p.write(*flat1058)
		return nil
	} else {
		_dollar_dollar := msg
		fields1056 := int64(_dollar_dollar.GetLength())
		unwrapped_fields1057 := fields1056
		p.write("(")
		p.write("FIXED")
		p.indentSexp()
		p.newline()
		p.write(fmt.Sprintf("%d", unwrapped_fields1057))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat1062 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat1062 != nil {
		p.write(*flat1062)
		return nil
	} else {
		fields1059 := msg
		p.write("|")
		if !(len(fields1059) == 0) {
			p.write(" ")
			for i1061, elem1060 := range fields1059 {
				if (i1061 > 0) {
					p.newline()
				}
				p.pretty_binding(elem1060)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1089 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1089 != nil {
		p.write(*flat1089)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1766 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1766 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1087 := _t1766
		if deconstruct_result1087 != nil {
			unwrapped1088 := deconstruct_result1087
			p.pretty_true(unwrapped1088)
		} else {
			_dollar_dollar := msg
			var _t1767 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1767 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1085 := _t1767
			if deconstruct_result1085 != nil {
				unwrapped1086 := deconstruct_result1085
				p.pretty_false(unwrapped1086)
			} else {
				_dollar_dollar := msg
				var _t1768 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1768 = _dollar_dollar.GetExists()
				}
				deconstruct_result1083 := _t1768
				if deconstruct_result1083 != nil {
					unwrapped1084 := deconstruct_result1083
					p.pretty_exists(unwrapped1084)
				} else {
					_dollar_dollar := msg
					var _t1769 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1769 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1081 := _t1769
					if deconstruct_result1081 != nil {
						unwrapped1082 := deconstruct_result1081
						p.pretty_reduce(unwrapped1082)
					} else {
						_dollar_dollar := msg
						var _t1770 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1770 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1079 := _t1770
						if deconstruct_result1079 != nil {
							unwrapped1080 := deconstruct_result1079
							p.pretty_conjunction(unwrapped1080)
						} else {
							_dollar_dollar := msg
							var _t1771 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1771 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1077 := _t1771
							if deconstruct_result1077 != nil {
								unwrapped1078 := deconstruct_result1077
								p.pretty_disjunction(unwrapped1078)
							} else {
								_dollar_dollar := msg
								var _t1772 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1772 = _dollar_dollar.GetNot()
								}
								deconstruct_result1075 := _t1772
								if deconstruct_result1075 != nil {
									unwrapped1076 := deconstruct_result1075
									p.pretty_not(unwrapped1076)
								} else {
									_dollar_dollar := msg
									var _t1773 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1773 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1073 := _t1773
									if deconstruct_result1073 != nil {
										unwrapped1074 := deconstruct_result1073
										p.pretty_ffi(unwrapped1074)
									} else {
										_dollar_dollar := msg
										var _t1774 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1774 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1071 := _t1774
										if deconstruct_result1071 != nil {
											unwrapped1072 := deconstruct_result1071
											p.pretty_atom(unwrapped1072)
										} else {
											_dollar_dollar := msg
											var _t1775 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1775 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1069 := _t1775
											if deconstruct_result1069 != nil {
												unwrapped1070 := deconstruct_result1069
												p.pretty_pragma(unwrapped1070)
											} else {
												_dollar_dollar := msg
												var _t1776 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1776 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1067 := _t1776
												if deconstruct_result1067 != nil {
													unwrapped1068 := deconstruct_result1067
													p.pretty_primitive(unwrapped1068)
												} else {
													_dollar_dollar := msg
													var _t1777 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1777 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1065 := _t1777
													if deconstruct_result1065 != nil {
														unwrapped1066 := deconstruct_result1065
														p.pretty_rel_atom(unwrapped1066)
													} else {
														_dollar_dollar := msg
														var _t1778 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1778 = _dollar_dollar.GetCast()
														}
														deconstruct_result1063 := _t1778
														if deconstruct_result1063 != nil {
															unwrapped1064 := deconstruct_result1063
															p.pretty_cast(unwrapped1064)
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
	fields1090 := msg
	_ = fields1090
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1091 := msg
	_ = fields1091
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1096 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1096 != nil {
		p.write(*flat1096)
		return nil
	} else {
		_dollar_dollar := msg
		_t1779 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1092 := []interface{}{_t1779, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1093 := fields1092
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1094 := unwrapped_fields1093[0].([]interface{})
		p.pretty_bindings(field1094)
		p.newline()
		field1095 := unwrapped_fields1093[1].(*pb.Formula)
		p.pretty_formula(field1095)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1102 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1102 != nil {
		p.write(*flat1102)
		return nil
	} else {
		_dollar_dollar := msg
		fields1097 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1098 := fields1097
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1099 := unwrapped_fields1098[0].(*pb.Abstraction)
		p.pretty_abstraction(field1099)
		p.newline()
		field1100 := unwrapped_fields1098[1].(*pb.Abstraction)
		p.pretty_abstraction(field1100)
		p.newline()
		field1101 := unwrapped_fields1098[2].([]*pb.Term)
		p.pretty_terms(field1101)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1106 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1106 != nil {
		p.write(*flat1106)
		return nil
	} else {
		fields1103 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1103) == 0) {
			p.newline()
			for i1105, elem1104 := range fields1103 {
				if (i1105 > 0) {
					p.newline()
				}
				p.pretty_term(elem1104)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1111 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1111 != nil {
		p.write(*flat1111)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1780 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1780 = _dollar_dollar.GetVar()
		}
		deconstruct_result1109 := _t1780
		if deconstruct_result1109 != nil {
			unwrapped1110 := deconstruct_result1109
			p.pretty_var(unwrapped1110)
		} else {
			_dollar_dollar := msg
			var _t1781 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1781 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1107 := _t1781
			if deconstruct_result1107 != nil {
				unwrapped1108 := deconstruct_result1107
				p.pretty_value(unwrapped1108)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1114 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1114 != nil {
		p.write(*flat1114)
		return nil
	} else {
		_dollar_dollar := msg
		fields1112 := _dollar_dollar.GetName()
		unwrapped_fields1113 := fields1112
		p.write(unwrapped_fields1113)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1140 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1140 != nil {
		p.write(*flat1140)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1782 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1782 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1138 := _t1782
		if deconstruct_result1138 != nil {
			unwrapped1139 := deconstruct_result1138
			p.pretty_date(unwrapped1139)
		} else {
			_dollar_dollar := msg
			var _t1783 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1783 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1136 := _t1783
			if deconstruct_result1136 != nil {
				unwrapped1137 := deconstruct_result1136
				p.pretty_datetime(unwrapped1137)
			} else {
				_dollar_dollar := msg
				var _t1784 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1784 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1134 := _t1784
				if deconstruct_result1134 != nil {
					unwrapped1135 := *deconstruct_result1134
					p.write(p.formatStringValue(unwrapped1135))
				} else {
					_dollar_dollar := msg
					var _t1785 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1785 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1132 := _t1785
					if deconstruct_result1132 != nil {
						unwrapped1133 := *deconstruct_result1132
						p.write(fmt.Sprintf("%di32", unwrapped1133))
					} else {
						_dollar_dollar := msg
						var _t1786 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1786 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1130 := _t1786
						if deconstruct_result1130 != nil {
							unwrapped1131 := *deconstruct_result1130
							p.write(fmt.Sprintf("%d", unwrapped1131))
						} else {
							_dollar_dollar := msg
							var _t1787 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1787 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1128 := _t1787
							if deconstruct_result1128 != nil {
								unwrapped1129 := *deconstruct_result1128
								p.write(formatFloat32(unwrapped1129))
							} else {
								_dollar_dollar := msg
								var _t1788 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1788 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1126 := _t1788
								if deconstruct_result1126 != nil {
									unwrapped1127 := *deconstruct_result1126
									p.write(formatFloat64(unwrapped1127))
								} else {
									_dollar_dollar := msg
									var _t1789 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1789 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1124 := _t1789
									if deconstruct_result1124 != nil {
										unwrapped1125 := *deconstruct_result1124
										p.write(fmt.Sprintf("%du32", unwrapped1125))
									} else {
										_dollar_dollar := msg
										var _t1790 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1790 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1122 := _t1790
										if deconstruct_result1122 != nil {
											unwrapped1123 := deconstruct_result1122
											p.write(p.formatUint128(unwrapped1123))
										} else {
											_dollar_dollar := msg
											var _t1791 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1791 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1120 := _t1791
											if deconstruct_result1120 != nil {
												unwrapped1121 := deconstruct_result1120
												p.write(p.formatInt128(unwrapped1121))
											} else {
												_dollar_dollar := msg
												var _t1792 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1792 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1118 := _t1792
												if deconstruct_result1118 != nil {
													unwrapped1119 := deconstruct_result1118
													p.write(p.formatDecimal(unwrapped1119))
												} else {
													_dollar_dollar := msg
													var _t1793 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1793 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1116 := _t1793
													if deconstruct_result1116 != nil {
														unwrapped1117 := *deconstruct_result1116
														p.pretty_boolean_value(unwrapped1117)
													} else {
														fields1115 := msg
														_ = fields1115
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
	flat1146 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1146 != nil {
		p.write(*flat1146)
		return nil
	} else {
		_dollar_dollar := msg
		fields1141 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1142 := fields1141
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1143 := unwrapped_fields1142[0].(int64)
		p.write(fmt.Sprintf("%d", field1143))
		p.newline()
		field1144 := unwrapped_fields1142[1].(int64)
		p.write(fmt.Sprintf("%d", field1144))
		p.newline()
		field1145 := unwrapped_fields1142[2].(int64)
		p.write(fmt.Sprintf("%d", field1145))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1157 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1157 != nil {
		p.write(*flat1157)
		return nil
	} else {
		_dollar_dollar := msg
		fields1147 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1148 := fields1147
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1149 := unwrapped_fields1148[0].(int64)
		p.write(fmt.Sprintf("%d", field1149))
		p.newline()
		field1150 := unwrapped_fields1148[1].(int64)
		p.write(fmt.Sprintf("%d", field1150))
		p.newline()
		field1151 := unwrapped_fields1148[2].(int64)
		p.write(fmt.Sprintf("%d", field1151))
		p.newline()
		field1152 := unwrapped_fields1148[3].(int64)
		p.write(fmt.Sprintf("%d", field1152))
		p.newline()
		field1153 := unwrapped_fields1148[4].(int64)
		p.write(fmt.Sprintf("%d", field1153))
		p.newline()
		field1154 := unwrapped_fields1148[5].(int64)
		p.write(fmt.Sprintf("%d", field1154))
		field1155 := unwrapped_fields1148[6].(*int64)
		if field1155 != nil {
			p.newline()
			opt_val1156 := *field1155
			p.write(fmt.Sprintf("%d", opt_val1156))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1162 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1162 != nil {
		p.write(*flat1162)
		return nil
	} else {
		_dollar_dollar := msg
		fields1158 := _dollar_dollar.GetArgs()
		unwrapped_fields1159 := fields1158
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1159) == 0) {
			p.newline()
			for i1161, elem1160 := range unwrapped_fields1159 {
				if (i1161 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1160)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1167 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1167 != nil {
		p.write(*flat1167)
		return nil
	} else {
		_dollar_dollar := msg
		fields1163 := _dollar_dollar.GetArgs()
		unwrapped_fields1164 := fields1163
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1164) == 0) {
			p.newline()
			for i1166, elem1165 := range unwrapped_fields1164 {
				if (i1166 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1165)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1170 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1170 != nil {
		p.write(*flat1170)
		return nil
	} else {
		_dollar_dollar := msg
		fields1168 := _dollar_dollar.GetArg()
		unwrapped_fields1169 := fields1168
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1169)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1176 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1176 != nil {
		p.write(*flat1176)
		return nil
	} else {
		_dollar_dollar := msg
		fields1171 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1172 := fields1171
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1173 := unwrapped_fields1172[0].(string)
		p.pretty_name(field1173)
		p.newline()
		field1174 := unwrapped_fields1172[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1174)
		p.newline()
		field1175 := unwrapped_fields1172[2].([]*pb.Term)
		p.pretty_terms(field1175)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1178 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1178 != nil {
		p.write(*flat1178)
		return nil
	} else {
		fields1177 := msg
		p.write(":")
		p.write(fields1177)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1182 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1182 != nil {
		p.write(*flat1182)
		return nil
	} else {
		fields1179 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1179) == 0) {
			p.newline()
			for i1181, elem1180 := range fields1179 {
				if (i1181 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1180)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1189 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1189 != nil {
		p.write(*flat1189)
		return nil
	} else {
		_dollar_dollar := msg
		fields1183 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1184 := fields1183
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1185 := unwrapped_fields1184[0].(*pb.RelationId)
		p.pretty_relation_id(field1185)
		field1186 := unwrapped_fields1184[1].([]*pb.Term)
		if !(len(field1186) == 0) {
			p.newline()
			for i1188, elem1187 := range field1186 {
				if (i1188 > 0) {
					p.newline()
				}
				p.pretty_term(elem1187)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1196 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1196 != nil {
		p.write(*flat1196)
		return nil
	} else {
		_dollar_dollar := msg
		fields1190 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1191 := fields1190
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1192 := unwrapped_fields1191[0].(string)
		p.pretty_name(field1192)
		field1193 := unwrapped_fields1191[1].([]*pb.Term)
		if !(len(field1193) == 0) {
			p.newline()
			for i1195, elem1194 := range field1193 {
				if (i1195 > 0) {
					p.newline()
				}
				p.pretty_term(elem1194)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1212 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1212 != nil {
		p.write(*flat1212)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1794 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1794 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1211 := _t1794
		if guard_result1211 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1795 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1795 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1210 := _t1795
			if guard_result1210 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1796 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1796 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1209 := _t1796
				if guard_result1209 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1797 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1797 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1208 := _t1797
					if guard_result1208 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1798 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1798 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1207 := _t1798
						if guard_result1207 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1799 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1799 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1206 := _t1799
							if guard_result1206 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1800 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1800 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1205 := _t1800
								if guard_result1205 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1801 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1801 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1204 := _t1801
									if guard_result1204 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1802 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1802 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1203 := _t1802
										if guard_result1203 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1197 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1198 := fields1197
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1199 := unwrapped_fields1198[0].(string)
											p.pretty_name(field1199)
											field1200 := unwrapped_fields1198[1].([]*pb.RelTerm)
											if !(len(field1200) == 0) {
												p.newline()
												for i1202, elem1201 := range field1200 {
													if (i1202 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1201)
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
	flat1217 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1217 != nil {
		p.write(*flat1217)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1803 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1803 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1213 := _t1803
		unwrapped_fields1214 := fields1213
		p.write("(")
		p.write("=")
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

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1222 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1222 != nil {
		p.write(*flat1222)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1804 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1804 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1218 := _t1804
		unwrapped_fields1219 := fields1218
		p.write("(")
		p.write("<")
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

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1227 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1227 != nil {
		p.write(*flat1227)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1805 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1805 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1223 := _t1805
		unwrapped_fields1224 := fields1223
		p.write("(")
		p.write("<=")
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

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1232 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1232 != nil {
		p.write(*flat1232)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1806 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1806 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1228 := _t1806
		unwrapped_fields1229 := fields1228
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1230 := unwrapped_fields1229[0].(*pb.Term)
		p.pretty_term(field1230)
		p.newline()
		field1231 := unwrapped_fields1229[1].(*pb.Term)
		p.pretty_term(field1231)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1237 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1237 != nil {
		p.write(*flat1237)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1807 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1807 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1233 := _t1807
		unwrapped_fields1234 := fields1233
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1235 := unwrapped_fields1234[0].(*pb.Term)
		p.pretty_term(field1235)
		p.newline()
		field1236 := unwrapped_fields1234[1].(*pb.Term)
		p.pretty_term(field1236)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1243 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1243 != nil {
		p.write(*flat1243)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1808 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1808 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1238 := _t1808
		unwrapped_fields1239 := fields1238
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1240 := unwrapped_fields1239[0].(*pb.Term)
		p.pretty_term(field1240)
		p.newline()
		field1241 := unwrapped_fields1239[1].(*pb.Term)
		p.pretty_term(field1241)
		p.newline()
		field1242 := unwrapped_fields1239[2].(*pb.Term)
		p.pretty_term(field1242)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1249 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1249 != nil {
		p.write(*flat1249)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1809 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1809 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1244 := _t1809
		unwrapped_fields1245 := fields1244
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1246 := unwrapped_fields1245[0].(*pb.Term)
		p.pretty_term(field1246)
		p.newline()
		field1247 := unwrapped_fields1245[1].(*pb.Term)
		p.pretty_term(field1247)
		p.newline()
		field1248 := unwrapped_fields1245[2].(*pb.Term)
		p.pretty_term(field1248)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1255 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1255 != nil {
		p.write(*flat1255)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1810 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1810 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1250 := _t1810
		unwrapped_fields1251 := fields1250
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1252 := unwrapped_fields1251[0].(*pb.Term)
		p.pretty_term(field1252)
		p.newline()
		field1253 := unwrapped_fields1251[1].(*pb.Term)
		p.pretty_term(field1253)
		p.newline()
		field1254 := unwrapped_fields1251[2].(*pb.Term)
		p.pretty_term(field1254)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1261 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1261 != nil {
		p.write(*flat1261)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1811 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1811 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1256 := _t1811
		unwrapped_fields1257 := fields1256
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1258 := unwrapped_fields1257[0].(*pb.Term)
		p.pretty_term(field1258)
		p.newline()
		field1259 := unwrapped_fields1257[1].(*pb.Term)
		p.pretty_term(field1259)
		p.newline()
		field1260 := unwrapped_fields1257[2].(*pb.Term)
		p.pretty_term(field1260)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1266 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1266 != nil {
		p.write(*flat1266)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1812 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1812 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1264 := _t1812
		if deconstruct_result1264 != nil {
			unwrapped1265 := deconstruct_result1264
			p.pretty_specialized_value(unwrapped1265)
		} else {
			_dollar_dollar := msg
			var _t1813 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1813 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1262 := _t1813
			if deconstruct_result1262 != nil {
				unwrapped1263 := deconstruct_result1262
				p.pretty_term(unwrapped1263)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1268 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1268 != nil {
		p.write(*flat1268)
		return nil
	} else {
		fields1267 := msg
		p.write("#")
		p.pretty_raw_value(fields1267)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1275 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1275 != nil {
		p.write(*flat1275)
		return nil
	} else {
		_dollar_dollar := msg
		fields1269 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1270 := fields1269
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1271 := unwrapped_fields1270[0].(string)
		p.pretty_name(field1271)
		field1272 := unwrapped_fields1270[1].([]*pb.RelTerm)
		if !(len(field1272) == 0) {
			p.newline()
			for i1274, elem1273 := range field1272 {
				if (i1274 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1273)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1280 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1280 != nil {
		p.write(*flat1280)
		return nil
	} else {
		_dollar_dollar := msg
		fields1276 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1277 := fields1276
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1278 := unwrapped_fields1277[0].(*pb.Term)
		p.pretty_term(field1278)
		p.newline()
		field1279 := unwrapped_fields1277[1].(*pb.Term)
		p.pretty_term(field1279)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1284 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1284 != nil {
		p.write(*flat1284)
		return nil
	} else {
		fields1281 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1281) == 0) {
			p.newline()
			for i1283, elem1282 := range fields1281 {
				if (i1283 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1282)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1291 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1291 != nil {
		p.write(*flat1291)
		return nil
	} else {
		_dollar_dollar := msg
		fields1285 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1286 := fields1285
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1287 := unwrapped_fields1286[0].(string)
		p.pretty_name(field1287)
		field1288 := unwrapped_fields1286[1].([]*pb.Value)
		if !(len(field1288) == 0) {
			p.newline()
			for i1290, elem1289 := range field1288 {
				if (i1290 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1289)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1300 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1300 != nil {
		p.write(*flat1300)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1814 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1814 = _dollar_dollar.GetAttrs()
		}
		fields1292 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1814}
		unwrapped_fields1293 := fields1292
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1294 := unwrapped_fields1293[0].([]*pb.RelationId)
		if !(len(field1294) == 0) {
			p.newline()
			for i1296, elem1295 := range field1294 {
				if (i1296 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1295)
			}
		}
		p.newline()
		field1297 := unwrapped_fields1293[1].(*pb.Script)
		p.pretty_script(field1297)
		field1298 := unwrapped_fields1293[2].([]*pb.Attribute)
		if field1298 != nil {
			p.newline()
			opt_val1299 := field1298
			p.pretty_attrs(opt_val1299)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1305 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1305 != nil {
		p.write(*flat1305)
		return nil
	} else {
		_dollar_dollar := msg
		fields1301 := _dollar_dollar.GetConstructs()
		unwrapped_fields1302 := fields1301
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1302) == 0) {
			p.newline()
			for i1304, elem1303 := range unwrapped_fields1302 {
				if (i1304 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1303)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1310 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1310 != nil {
		p.write(*flat1310)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1815 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1815 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1308 := _t1815
		if deconstruct_result1308 != nil {
			unwrapped1309 := deconstruct_result1308
			p.pretty_loop(unwrapped1309)
		} else {
			_dollar_dollar := msg
			var _t1816 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1816 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1306 := _t1816
			if deconstruct_result1306 != nil {
				unwrapped1307 := deconstruct_result1306
				p.pretty_instruction(unwrapped1307)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1317 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1317 != nil {
		p.write(*flat1317)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1817 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1817 = _dollar_dollar.GetAttrs()
		}
		fields1311 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1817}
		unwrapped_fields1312 := fields1311
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1313 := unwrapped_fields1312[0].([]*pb.Instruction)
		p.pretty_init(field1313)
		p.newline()
		field1314 := unwrapped_fields1312[1].(*pb.Script)
		p.pretty_script(field1314)
		field1315 := unwrapped_fields1312[2].([]*pb.Attribute)
		if field1315 != nil {
			p.newline()
			opt_val1316 := field1315
			p.pretty_attrs(opt_val1316)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1321 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1321 != nil {
		p.write(*flat1321)
		return nil
	} else {
		fields1318 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1318) == 0) {
			p.newline()
			for i1320, elem1319 := range fields1318 {
				if (i1320 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1319)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1332 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1332 != nil {
		p.write(*flat1332)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1818 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1818 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1330 := _t1818
		if deconstruct_result1330 != nil {
			unwrapped1331 := deconstruct_result1330
			p.pretty_assign(unwrapped1331)
		} else {
			_dollar_dollar := msg
			var _t1819 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1819 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1328 := _t1819
			if deconstruct_result1328 != nil {
				unwrapped1329 := deconstruct_result1328
				p.pretty_upsert(unwrapped1329)
			} else {
				_dollar_dollar := msg
				var _t1820 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1820 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1326 := _t1820
				if deconstruct_result1326 != nil {
					unwrapped1327 := deconstruct_result1326
					p.pretty_break(unwrapped1327)
				} else {
					_dollar_dollar := msg
					var _t1821 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1821 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1324 := _t1821
					if deconstruct_result1324 != nil {
						unwrapped1325 := deconstruct_result1324
						p.pretty_monoid_def(unwrapped1325)
					} else {
						_dollar_dollar := msg
						var _t1822 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1822 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1322 := _t1822
						if deconstruct_result1322 != nil {
							unwrapped1323 := deconstruct_result1322
							p.pretty_monus_def(unwrapped1323)
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
	flat1339 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1339 != nil {
		p.write(*flat1339)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1823 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1823 = _dollar_dollar.GetAttrs()
		}
		fields1333 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1823}
		unwrapped_fields1334 := fields1333
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1335 := unwrapped_fields1334[0].(*pb.RelationId)
		p.pretty_relation_id(field1335)
		p.newline()
		field1336 := unwrapped_fields1334[1].(*pb.Abstraction)
		p.pretty_abstraction(field1336)
		field1337 := unwrapped_fields1334[2].([]*pb.Attribute)
		if field1337 != nil {
			p.newline()
			opt_val1338 := field1337
			p.pretty_attrs(opt_val1338)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1346 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1346 != nil {
		p.write(*flat1346)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1824 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1824 = _dollar_dollar.GetAttrs()
		}
		fields1340 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1824}
		unwrapped_fields1341 := fields1340
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1342 := unwrapped_fields1341[0].(*pb.RelationId)
		p.pretty_relation_id(field1342)
		p.newline()
		field1343 := unwrapped_fields1341[1].([]interface{})
		p.pretty_abstraction_with_arity(field1343)
		field1344 := unwrapped_fields1341[2].([]*pb.Attribute)
		if field1344 != nil {
			p.newline()
			opt_val1345 := field1344
			p.pretty_attrs(opt_val1345)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1351 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1351 != nil {
		p.write(*flat1351)
		return nil
	} else {
		_dollar_dollar := msg
		_t1825 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1347 := []interface{}{_t1825, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1348 := fields1347
		p.write("(")
		p.indent()
		field1349 := unwrapped_fields1348[0].([]interface{})
		p.pretty_bindings(field1349)
		p.newline()
		field1350 := unwrapped_fields1348[1].(*pb.Formula)
		p.pretty_formula(field1350)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1358 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1358 != nil {
		p.write(*flat1358)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1826 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1826 = _dollar_dollar.GetAttrs()
		}
		fields1352 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1826}
		unwrapped_fields1353 := fields1352
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1354 := unwrapped_fields1353[0].(*pb.RelationId)
		p.pretty_relation_id(field1354)
		p.newline()
		field1355 := unwrapped_fields1353[1].(*pb.Abstraction)
		p.pretty_abstraction(field1355)
		field1356 := unwrapped_fields1353[2].([]*pb.Attribute)
		if field1356 != nil {
			p.newline()
			opt_val1357 := field1356
			p.pretty_attrs(opt_val1357)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1366 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1366 != nil {
		p.write(*flat1366)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1827 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1827 = _dollar_dollar.GetAttrs()
		}
		fields1359 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1827}
		unwrapped_fields1360 := fields1359
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1361 := unwrapped_fields1360[0].(*pb.Monoid)
		p.pretty_monoid(field1361)
		p.newline()
		field1362 := unwrapped_fields1360[1].(*pb.RelationId)
		p.pretty_relation_id(field1362)
		p.newline()
		field1363 := unwrapped_fields1360[2].([]interface{})
		p.pretty_abstraction_with_arity(field1363)
		field1364 := unwrapped_fields1360[3].([]*pb.Attribute)
		if field1364 != nil {
			p.newline()
			opt_val1365 := field1364
			p.pretty_attrs(opt_val1365)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1375 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1375 != nil {
		p.write(*flat1375)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1828 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1828 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1373 := _t1828
		if deconstruct_result1373 != nil {
			unwrapped1374 := deconstruct_result1373
			p.pretty_or_monoid(unwrapped1374)
		} else {
			_dollar_dollar := msg
			var _t1829 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1829 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1371 := _t1829
			if deconstruct_result1371 != nil {
				unwrapped1372 := deconstruct_result1371
				p.pretty_min_monoid(unwrapped1372)
			} else {
				_dollar_dollar := msg
				var _t1830 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1830 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1369 := _t1830
				if deconstruct_result1369 != nil {
					unwrapped1370 := deconstruct_result1369
					p.pretty_max_monoid(unwrapped1370)
				} else {
					_dollar_dollar := msg
					var _t1831 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1831 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1367 := _t1831
					if deconstruct_result1367 != nil {
						unwrapped1368 := deconstruct_result1367
						p.pretty_sum_monoid(unwrapped1368)
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
	fields1376 := msg
	_ = fields1376
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1379 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1379 != nil {
		p.write(*flat1379)
		return nil
	} else {
		_dollar_dollar := msg
		fields1377 := _dollar_dollar.GetType()
		unwrapped_fields1378 := fields1377
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1378)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1382 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1382 != nil {
		p.write(*flat1382)
		return nil
	} else {
		_dollar_dollar := msg
		fields1380 := _dollar_dollar.GetType()
		unwrapped_fields1381 := fields1380
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1381)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1385 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1385 != nil {
		p.write(*flat1385)
		return nil
	} else {
		_dollar_dollar := msg
		fields1383 := _dollar_dollar.GetType()
		unwrapped_fields1384 := fields1383
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1384)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1393 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1393 != nil {
		p.write(*flat1393)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1832 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1832 = _dollar_dollar.GetAttrs()
		}
		fields1386 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1832}
		unwrapped_fields1387 := fields1386
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1388 := unwrapped_fields1387[0].(*pb.Monoid)
		p.pretty_monoid(field1388)
		p.newline()
		field1389 := unwrapped_fields1387[1].(*pb.RelationId)
		p.pretty_relation_id(field1389)
		p.newline()
		field1390 := unwrapped_fields1387[2].([]interface{})
		p.pretty_abstraction_with_arity(field1390)
		field1391 := unwrapped_fields1387[3].([]*pb.Attribute)
		if field1391 != nil {
			p.newline()
			opt_val1392 := field1391
			p.pretty_attrs(opt_val1392)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1400 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1400 != nil {
		p.write(*flat1400)
		return nil
	} else {
		_dollar_dollar := msg
		fields1394 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1395 := fields1394
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1396 := unwrapped_fields1395[0].(*pb.RelationId)
		p.pretty_relation_id(field1396)
		p.newline()
		field1397 := unwrapped_fields1395[1].(*pb.Abstraction)
		p.pretty_abstraction(field1397)
		p.newline()
		field1398 := unwrapped_fields1395[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1398)
		p.newline()
		field1399 := unwrapped_fields1395[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1399)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1404 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1404 != nil {
		p.write(*flat1404)
		return nil
	} else {
		fields1401 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1401) == 0) {
			p.newline()
			for i1403, elem1402 := range fields1401 {
				if (i1403 > 0) {
					p.newline()
				}
				p.pretty_var(elem1402)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1408 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1408 != nil {
		p.write(*flat1408)
		return nil
	} else {
		fields1405 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1405) == 0) {
			p.newline()
			for i1407, elem1406 := range fields1405 {
				if (i1407 > 0) {
					p.newline()
				}
				p.pretty_var(elem1406)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1417 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1417 != nil {
		p.write(*flat1417)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1833 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1833 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1415 := _t1833
		if deconstruct_result1415 != nil {
			unwrapped1416 := deconstruct_result1415
			p.pretty_edb(unwrapped1416)
		} else {
			_dollar_dollar := msg
			var _t1834 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1834 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1413 := _t1834
			if deconstruct_result1413 != nil {
				unwrapped1414 := deconstruct_result1413
				p.pretty_betree_relation(unwrapped1414)
			} else {
				_dollar_dollar := msg
				var _t1835 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1835 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1411 := _t1835
				if deconstruct_result1411 != nil {
					unwrapped1412 := deconstruct_result1411
					p.pretty_csv_data(unwrapped1412)
				} else {
					_dollar_dollar := msg
					var _t1836 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1836 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1409 := _t1836
					if deconstruct_result1409 != nil {
						unwrapped1410 := deconstruct_result1409
						p.pretty_iceberg_data(unwrapped1410)
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
	flat1423 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1423 != nil {
		p.write(*flat1423)
		return nil
	} else {
		_dollar_dollar := msg
		fields1418 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1419 := fields1418
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1420 := unwrapped_fields1419[0].(*pb.RelationId)
		p.pretty_relation_id(field1420)
		p.newline()
		field1421 := unwrapped_fields1419[1].([]string)
		p.pretty_edb_path(field1421)
		p.newline()
		field1422 := unwrapped_fields1419[2].([]*pb.Type)
		p.pretty_edb_types(field1422)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1427 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1427 != nil {
		p.write(*flat1427)
		return nil
	} else {
		fields1424 := msg
		p.write("[")
		p.indent()
		for i1426, elem1425 := range fields1424 {
			if (i1426 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1425))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1431 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1431 != nil {
		p.write(*flat1431)
		return nil
	} else {
		fields1428 := msg
		p.write("[")
		p.indent()
		for i1430, elem1429 := range fields1428 {
			if (i1430 > 0) {
				p.newline()
			}
			p.pretty_type(elem1429)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1436 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1436 != nil {
		p.write(*flat1436)
		return nil
	} else {
		_dollar_dollar := msg
		fields1432 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1433 := fields1432
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1434 := unwrapped_fields1433[0].(*pb.RelationId)
		p.pretty_relation_id(field1434)
		p.newline()
		field1435 := unwrapped_fields1433[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1435)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1442 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1442 != nil {
		p.write(*flat1442)
		return nil
	} else {
		_dollar_dollar := msg
		_t1837 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1437 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1837}
		unwrapped_fields1438 := fields1437
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1439 := unwrapped_fields1438[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1439)
		p.newline()
		field1440 := unwrapped_fields1438[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1440)
		p.newline()
		field1441 := unwrapped_fields1438[2].([][]interface{})
		p.pretty_config_dict(field1441)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1446 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1446 != nil {
		p.write(*flat1446)
		return nil
	} else {
		fields1443 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1443) == 0) {
			p.newline()
			for i1445, elem1444 := range fields1443 {
				if (i1445 > 0) {
					p.newline()
				}
				p.pretty_type(elem1444)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1450 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1450 != nil {
		p.write(*flat1450)
		return nil
	} else {
		fields1447 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1447) == 0) {
			p.newline()
			for i1449, elem1448 := range fields1447 {
				if (i1449 > 0) {
					p.newline()
				}
				p.pretty_type(elem1448)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1460 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1460 != nil {
		p.write(*flat1460)
		return nil
	} else {
		_dollar_dollar := msg
		_t1838 := p.deconstruct_csv_data_columns_optional(_dollar_dollar)
		_t1839 := p.deconstruct_csv_data_relations_optional(_dollar_dollar)
		fields1451 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _t1838, _t1839, _dollar_dollar.GetAsof()}
		unwrapped_fields1452 := fields1451
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1453 := unwrapped_fields1452[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1453)
		p.newline()
		field1454 := unwrapped_fields1452[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1454)
		field1455 := unwrapped_fields1452[2].([]*pb.GNFColumn)
		if field1455 != nil {
			p.newline()
			opt_val1456 := field1455
			p.pretty_gnf_columns(opt_val1456)
		}
		field1457 := unwrapped_fields1452[3].(*pb.TargetRelations)
		if field1457 != nil {
			p.newline()
			opt_val1458 := field1457
			p.pretty_target_relations(opt_val1458)
		}
		p.newline()
		field1459 := unwrapped_fields1452[4].(string)
		p.pretty_csv_asof(field1459)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1467 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1467 != nil {
		p.write(*flat1467)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1840 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1840 = _dollar_dollar.GetPaths()
		}
		var _t1841 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1841 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1461 := []interface{}{_t1840, _t1841}
		unwrapped_fields1462 := fields1461
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1463 := unwrapped_fields1462[0].([]string)
		if field1463 != nil {
			p.newline()
			opt_val1464 := field1463
			p.pretty_csv_locator_paths(opt_val1464)
		}
		field1465 := unwrapped_fields1462[1].(*string)
		if field1465 != nil {
			p.newline()
			opt_val1466 := *field1465
			p.pretty_csv_locator_inline_data(opt_val1466)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1471 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1471 != nil {
		p.write(*flat1471)
		return nil
	} else {
		fields1468 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1468) == 0) {
			p.newline()
			for i1470, elem1469 := range fields1468 {
				if (i1470 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1469))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1473 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1473 != nil {
		p.write(*flat1473)
		return nil
	} else {
		fields1472 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1472))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1479 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1479 != nil {
		p.write(*flat1479)
		return nil
	} else {
		_dollar_dollar := msg
		_t1842 := p.deconstruct_csv_config(_dollar_dollar)
		_t1843 := p.deconstruct_csv_storage_integration_optional(_dollar_dollar)
		fields1474 := []interface{}{_t1842, _t1843}
		unwrapped_fields1475 := fields1474
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		field1476 := unwrapped_fields1475[0].([][]interface{})
		p.pretty_config_dict(field1476)
		field1477 := unwrapped_fields1475[1].([][]interface{})
		if field1477 != nil {
			p.newline()
			opt_val1478 := field1477
			p.pretty__storage_integration(opt_val1478)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty__storage_integration(msg [][]interface{}) interface{} {
	flat1481 := p.tryFlat(msg, func() { p.pretty__storage_integration(msg) })
	if flat1481 != nil {
		p.write(*flat1481)
		return nil
	} else {
		fields1480 := msg
		p.write("(")
		p.write("storage_integration")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(fields1480)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1485 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1485 != nil {
		p.write(*flat1485)
		return nil
	} else {
		fields1482 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1482) == 0) {
			p.newline()
			for i1484, elem1483 := range fields1482 {
				if (i1484 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1483)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1494 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1494 != nil {
		p.write(*flat1494)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1844 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1844 = _dollar_dollar.GetTargetId()
		}
		fields1486 := []interface{}{_dollar_dollar.GetColumnPath(), _t1844, _dollar_dollar.GetTypes()}
		unwrapped_fields1487 := fields1486
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1488 := unwrapped_fields1487[0].([]string)
		p.pretty_gnf_column_path(field1488)
		field1489 := unwrapped_fields1487[1].(*pb.RelationId)
		if field1489 != nil {
			p.newline()
			opt_val1490 := field1489
			p.pretty_relation_id(opt_val1490)
		}
		p.newline()
		p.write("[")
		field1491 := unwrapped_fields1487[2].([]*pb.Type)
		for i1493, elem1492 := range field1491 {
			if (i1493 > 0) {
				p.newline()
			}
			p.pretty_type(elem1492)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1501 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1501 != nil {
		p.write(*flat1501)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1845 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1845 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1499 := _t1845
		if deconstruct_result1499 != nil {
			unwrapped1500 := *deconstruct_result1499
			p.write(p.formatStringValue(unwrapped1500))
		} else {
			_dollar_dollar := msg
			var _t1846 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1846 = _dollar_dollar
			}
			deconstruct_result1495 := _t1846
			if deconstruct_result1495 != nil {
				unwrapped1496 := deconstruct_result1495
				p.write("[")
				p.indent()
				for i1498, elem1497 := range unwrapped1496 {
					if (i1498 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1497))
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
	flat1508 := p.tryFlat(msg, func() { p.pretty_target_relations(msg) })
	if flat1508 != nil {
		p.write(*flat1508)
		return nil
	} else {
		_dollar_dollar := msg
		_t1847 := p.deconstruct_relation_keys(_dollar_dollar)
		_t1848 := p.deconstruct_load_errors_optional(_dollar_dollar)
		fields1502 := []interface{}{_t1847, _dollar_dollar, _t1848}
		unwrapped_fields1503 := fields1502
		p.write("(")
		p.write("relations")
		p.indentSexp()
		p.newline()
		field1504 := unwrapped_fields1503[0].([]interface{})
		p.pretty_relation_keys(field1504)
		p.newline()
		field1505 := unwrapped_fields1503[1].(*pb.TargetRelations)
		p.pretty_relation_body(field1505)
		field1506 := unwrapped_fields1503[2].(*pb.RelationId)
		if field1506 != nil {
			p.newline()
			opt_val1507 := field1506
			p.pretty_load_errors(opt_val1507)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_keys(msg []interface{}) interface{} {
	flat1515 := p.tryFlat(msg, func() { p.pretty_relation_keys(msg) })
	if flat1515 != nil {
		p.write(*flat1515)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1849 []*pb.NamedColumn
		if !(_dollar_dollar[1].(bool)) {
			_t1849 = _dollar_dollar[0].([]*pb.NamedColumn)
		}
		deconstruct_result1511 := _t1849
		if deconstruct_result1511 != nil {
			unwrapped1512 := deconstruct_result1511
			p.write("(")
			p.write("keys")
			p.indentSexp()
			if !(len(unwrapped1512) == 0) {
				p.newline()
				for i1514, elem1513 := range unwrapped1512 {
					if (i1514 > 0) {
						p.newline()
					}
					p.pretty_named_column(elem1513)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1850 []interface{}
			if _dollar_dollar[1].(bool) {
				_t1850 = []interface{}{}
			}
			deconstruct_result1509 := _t1850
			if deconstruct_result1509 != nil {
				unwrapped1510 := deconstruct_result1509
				_ = unwrapped1510
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
	flat1520 := p.tryFlat(msg, func() { p.pretty_named_column(msg) })
	if flat1520 != nil {
		p.write(*flat1520)
		return nil
	} else {
		_dollar_dollar := msg
		fields1516 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetType()}
		unwrapped_fields1517 := fields1516
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1518 := unwrapped_fields1517[0].(string)
		p.write(p.formatStringValue(field1518))
		p.newline()
		field1519 := unwrapped_fields1517[1].(*pb.Type)
		p.pretty_type(field1519)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_body(msg *pb.TargetRelations) interface{} {
	flat1527 := p.tryFlat(msg, func() { p.pretty_relation_body(msg) })
	if flat1527 != nil {
		p.write(*flat1527)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1851 []*pb.TargetRelation
		if hasProtoField(_dollar_dollar, "plain") {
			_t1851 = _dollar_dollar.GetPlain().GetTargets()
		}
		deconstruct_result1525 := _t1851
		if deconstruct_result1525 != nil {
			unwrapped1526 := deconstruct_result1525
			p.pretty_non_cdc_relations(unwrapped1526)
		} else {
			_dollar_dollar := msg
			var _t1852 []interface{}
			if hasProtoField(_dollar_dollar, "cdc") {
				_t1852 = []interface{}{_dollar_dollar.GetCdc().GetInserts(), _dollar_dollar.GetCdc().GetDeletes()}
			}
			deconstruct_result1521 := _t1852
			if deconstruct_result1521 != nil {
				unwrapped1522 := deconstruct_result1521
				field1523 := unwrapped1522[0].([]*pb.TargetRelation)
				p.pretty_cdc_inserts(field1523)
				p.write(" ")
				field1524 := unwrapped1522[1].([]*pb.TargetRelation)
				p.pretty_cdc_deletes(field1524)
			} else {
				panic(ParseError{msg: "No matching rule for relation_body"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_non_cdc_relations(msg []*pb.TargetRelation) interface{} {
	flat1531 := p.tryFlat(msg, func() { p.pretty_non_cdc_relations(msg) })
	if flat1531 != nil {
		p.write(*flat1531)
		return nil
	} else {
		fields1528 := msg
		for i1530, elem1529 := range fields1528 {
			if (i1530 > 0) {
				p.newline()
			}
			p.pretty_target_relation(elem1529)
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_target_relation(msg *pb.TargetRelation) interface{} {
	flat1538 := p.tryFlat(msg, func() { p.pretty_target_relation(msg) })
	if flat1538 != nil {
		p.write(*flat1538)
		return nil
	} else {
		_dollar_dollar := msg
		fields1532 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetValues()}
		unwrapped_fields1533 := fields1532
		p.write("(")
		p.write("relation")
		p.indentSexp()
		p.newline()
		field1534 := unwrapped_fields1533[0].(*pb.RelationId)
		p.pretty_relation_id(field1534)
		field1535 := unwrapped_fields1533[1].([]*pb.NamedColumn)
		if !(len(field1535) == 0) {
			p.newline()
			for i1537, elem1536 := range field1535 {
				if (i1537 > 0) {
					p.newline()
				}
				p.pretty_named_column(elem1536)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_inserts(msg []*pb.TargetRelation) interface{} {
	flat1542 := p.tryFlat(msg, func() { p.pretty_cdc_inserts(msg) })
	if flat1542 != nil {
		p.write(*flat1542)
		return nil
	} else {
		fields1539 := msg
		p.write("(")
		p.write("inserts")
		p.indentSexp()
		if !(len(fields1539) == 0) {
			p.newline()
			for i1541, elem1540 := range fields1539 {
				if (i1541 > 0) {
					p.newline()
				}
				p.pretty_target_relation(elem1540)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_deletes(msg []*pb.TargetRelation) interface{} {
	flat1546 := p.tryFlat(msg, func() { p.pretty_cdc_deletes(msg) })
	if flat1546 != nil {
		p.write(*flat1546)
		return nil
	} else {
		fields1543 := msg
		p.write("(")
		p.write("deletes")
		p.indentSexp()
		if !(len(fields1543) == 0) {
			p.newline()
			for i1545, elem1544 := range fields1543 {
				if (i1545 > 0) {
					p.newline()
				}
				p.pretty_target_relation(elem1544)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_load_errors(msg *pb.RelationId) interface{} {
	flat1548 := p.tryFlat(msg, func() { p.pretty_load_errors(msg) })
	if flat1548 != nil {
		p.write(*flat1548)
		return nil
	} else {
		fields1547 := msg
		p.write("(")
		p.write("load_errors")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1547)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1550 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1550 != nil {
		p.write(*flat1550)
		return nil
	} else {
		fields1549 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1549))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1561 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1561 != nil {
		p.write(*flat1561)
		return nil
	} else {
		_dollar_dollar := msg
		_t1853 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1854 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1551 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1853, _t1854, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1552 := fields1551
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1553 := unwrapped_fields1552[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1553)
		p.newline()
		field1554 := unwrapped_fields1552[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1554)
		p.newline()
		field1555 := unwrapped_fields1552[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1555)
		field1556 := unwrapped_fields1552[3].(*string)
		if field1556 != nil {
			p.newline()
			opt_val1557 := *field1556
			p.pretty_iceberg_from_snapshot(opt_val1557)
		}
		field1558 := unwrapped_fields1552[4].(*string)
		if field1558 != nil {
			p.newline()
			opt_val1559 := *field1558
			p.pretty_iceberg_to_snapshot(opt_val1559)
		}
		p.newline()
		field1560 := unwrapped_fields1552[5].(bool)
		p.pretty_boolean_value(field1560)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1567 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1567 != nil {
		p.write(*flat1567)
		return nil
	} else {
		_dollar_dollar := msg
		fields1562 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1563 := fields1562
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1564 := unwrapped_fields1563[0].(string)
		p.pretty_iceberg_locator_table_name(field1564)
		p.newline()
		field1565 := unwrapped_fields1563[1].([]string)
		p.pretty_iceberg_locator_namespace(field1565)
		p.newline()
		field1566 := unwrapped_fields1563[2].(string)
		p.pretty_iceberg_locator_warehouse(field1566)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1569 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1569 != nil {
		p.write(*flat1569)
		return nil
	} else {
		fields1568 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1568))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1573 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1573 != nil {
		p.write(*flat1573)
		return nil
	} else {
		fields1570 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1570) == 0) {
			p.newline()
			for i1572, elem1571 := range fields1570 {
				if (i1572 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1571))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1575 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1575 != nil {
		p.write(*flat1575)
		return nil
	} else {
		fields1574 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1574))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1583 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1583 != nil {
		p.write(*flat1583)
		return nil
	} else {
		_dollar_dollar := msg
		_t1855 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1576 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1855, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1577 := fields1576
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1578 := unwrapped_fields1577[0].(string)
		p.pretty_iceberg_catalog_uri(field1578)
		field1579 := unwrapped_fields1577[1].(*string)
		if field1579 != nil {
			p.newline()
			opt_val1580 := *field1579
			p.pretty_iceberg_catalog_config_scope(opt_val1580)
		}
		p.newline()
		field1581 := unwrapped_fields1577[2].([][]interface{})
		p.pretty_iceberg_properties(field1581)
		p.newline()
		field1582 := unwrapped_fields1577[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1582)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1585 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1585 != nil {
		p.write(*flat1585)
		return nil
	} else {
		fields1584 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1584))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1587 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1587 != nil {
		p.write(*flat1587)
		return nil
	} else {
		fields1586 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1586))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1591 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1591 != nil {
		p.write(*flat1591)
		return nil
	} else {
		fields1588 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1588) == 0) {
			p.newline()
			for i1590, elem1589 := range fields1588 {
				if (i1590 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1589)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1596 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1596 != nil {
		p.write(*flat1596)
		return nil
	} else {
		_dollar_dollar := msg
		fields1592 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1593 := fields1592
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1594 := unwrapped_fields1593[0].(string)
		p.write(p.formatStringValue(field1594))
		p.newline()
		field1595 := unwrapped_fields1593[1].(string)
		p.write(p.formatStringValue(field1595))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1600 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1600 != nil {
		p.write(*flat1600)
		return nil
	} else {
		fields1597 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1597) == 0) {
			p.newline()
			for i1599, elem1598 := range fields1597 {
				if (i1599 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1598)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1605 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1605 != nil {
		p.write(*flat1605)
		return nil
	} else {
		_dollar_dollar := msg
		_t1856 := p.mask_secret_value(_dollar_dollar)
		fields1601 := []interface{}{_dollar_dollar[0].(string), _t1856}
		unwrapped_fields1602 := fields1601
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1603 := unwrapped_fields1602[0].(string)
		p.write(p.formatStringValue(field1603))
		p.newline()
		field1604 := unwrapped_fields1602[1].(string)
		p.write(p.formatStringValue(field1604))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1607 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1607 != nil {
		p.write(*flat1607)
		return nil
	} else {
		fields1606 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1606))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1609 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1609 != nil {
		p.write(*flat1609)
		return nil
	} else {
		fields1608 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1608))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1612 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1612 != nil {
		p.write(*flat1612)
		return nil
	} else {
		_dollar_dollar := msg
		fields1610 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1611 := fields1610
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1611)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1617 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1617 != nil {
		p.write(*flat1617)
		return nil
	} else {
		_dollar_dollar := msg
		fields1613 := _dollar_dollar.GetRelations()
		unwrapped_fields1614 := fields1613
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1614) == 0) {
			p.newline()
			for i1616, elem1615 := range unwrapped_fields1614 {
				if (i1616 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1615)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1624 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1624 != nil {
		p.write(*flat1624)
		return nil
	} else {
		_dollar_dollar := msg
		fields1618 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1619 := fields1618
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1620 := unwrapped_fields1619[0].([]string)
		p.pretty_edb_path(field1620)
		field1621 := unwrapped_fields1619[1].([]*pb.SnapshotMapping)
		if !(len(field1621) == 0) {
			p.newline()
			for i1623, elem1622 := range field1621 {
				if (i1623 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1622)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1629 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1629 != nil {
		p.write(*flat1629)
		return nil
	} else {
		_dollar_dollar := msg
		fields1625 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1626 := fields1625
		field1627 := unwrapped_fields1626[0].([]string)
		p.pretty_edb_path(field1627)
		p.write(" ")
		field1628 := unwrapped_fields1626[1].(*pb.RelationId)
		p.pretty_relation_id(field1628)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1633 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1633 != nil {
		p.write(*flat1633)
		return nil
	} else {
		fields1630 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1630) == 0) {
			p.newline()
			for i1632, elem1631 := range fields1630 {
				if (i1632 > 0) {
					p.newline()
				}
				p.pretty_read(elem1631)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1644 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1644 != nil {
		p.write(*flat1644)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1857 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1857 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1642 := _t1857
		if deconstruct_result1642 != nil {
			unwrapped1643 := deconstruct_result1642
			p.pretty_demand(unwrapped1643)
		} else {
			_dollar_dollar := msg
			var _t1858 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1858 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1640 := _t1858
			if deconstruct_result1640 != nil {
				unwrapped1641 := deconstruct_result1640
				p.pretty_output(unwrapped1641)
			} else {
				_dollar_dollar := msg
				var _t1859 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1859 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1638 := _t1859
				if deconstruct_result1638 != nil {
					unwrapped1639 := deconstruct_result1638
					p.pretty_what_if(unwrapped1639)
				} else {
					_dollar_dollar := msg
					var _t1860 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1860 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1636 := _t1860
					if deconstruct_result1636 != nil {
						unwrapped1637 := deconstruct_result1636
						p.pretty_abort(unwrapped1637)
					} else {
						_dollar_dollar := msg
						var _t1861 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1861 = _dollar_dollar.GetExport()
						}
						deconstruct_result1634 := _t1861
						if deconstruct_result1634 != nil {
							unwrapped1635 := deconstruct_result1634
							p.pretty_export(unwrapped1635)
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
	flat1647 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1647 != nil {
		p.write(*flat1647)
		return nil
	} else {
		_dollar_dollar := msg
		fields1645 := _dollar_dollar.GetRelationId()
		unwrapped_fields1646 := fields1645
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1646)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1652 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1652 != nil {
		p.write(*flat1652)
		return nil
	} else {
		_dollar_dollar := msg
		fields1648 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1649 := fields1648
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1650 := unwrapped_fields1649[0].(string)
		p.pretty_name(field1650)
		p.newline()
		field1651 := unwrapped_fields1649[1].(*pb.RelationId)
		p.pretty_relation_id(field1651)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1657 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1657 != nil {
		p.write(*flat1657)
		return nil
	} else {
		_dollar_dollar := msg
		fields1653 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1654 := fields1653
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1655 := unwrapped_fields1654[0].(string)
		p.pretty_name(field1655)
		p.newline()
		field1656 := unwrapped_fields1654[1].(*pb.Epoch)
		p.pretty_epoch(field1656)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1663 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1663 != nil {
		p.write(*flat1663)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1862 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1862 = ptr(_dollar_dollar.GetName())
		}
		fields1658 := []interface{}{_t1862, _dollar_dollar.GetRelationId()}
		unwrapped_fields1659 := fields1658
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1660 := unwrapped_fields1659[0].(*string)
		if field1660 != nil {
			p.newline()
			opt_val1661 := *field1660
			p.pretty_name(opt_val1661)
		}
		p.newline()
		field1662 := unwrapped_fields1659[1].(*pb.RelationId)
		p.pretty_relation_id(field1662)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1668 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1668 != nil {
		p.write(*flat1668)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1863 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1863 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1666 := _t1863
		if deconstruct_result1666 != nil {
			unwrapped1667 := deconstruct_result1666
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1667)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1864 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1864 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1664 := _t1864
			if deconstruct_result1664 != nil {
				unwrapped1665 := deconstruct_result1664
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1665)
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
	flat1679 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1679 != nil {
		p.write(*flat1679)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1865 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1866 := p.deconstruct_export_csv_output_location(_dollar_dollar)
			_t1865 = []interface{}{_t1866, _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1674 := _t1865
		if deconstruct_result1674 != nil {
			unwrapped1675 := deconstruct_result1674
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1676 := unwrapped1675[0].([]interface{})
			p.pretty_export_csv_output_location(field1676)
			p.newline()
			field1677 := unwrapped1675[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1677)
			p.newline()
			field1678 := unwrapped1675[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1678)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1867 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1868 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1867 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1868}
			}
			deconstruct_result1669 := _t1867
			if deconstruct_result1669 != nil {
				unwrapped1670 := deconstruct_result1669
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1671 := unwrapped1670[0].(string)
				p.pretty_export_csv_path(field1671)
				p.newline()
				field1672 := unwrapped1670[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1672)
				p.newline()
				field1673 := unwrapped1670[2].([][]interface{})
				p.pretty_config_dict(field1673)
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
	flat1684 := p.tryFlat(msg, func() { p.pretty_export_csv_output_location(msg) })
	if flat1684 != nil {
		p.write(*flat1684)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1869 *string
		if _dollar_dollar[0].(string) != "" {
			_t1869 = ptr(_dollar_dollar[0].(string))
		}
		deconstruct_result1682 := _t1869
		if deconstruct_result1682 != nil {
			unwrapped1683 := *deconstruct_result1682
			p.write("(")
			p.write("path")
			p.indentSexp()
			p.newline()
			p.write(p.formatStringValue(unwrapped1683))
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1870 *string
			if _dollar_dollar[1].(string) != "" {
				_t1870 = ptr(_dollar_dollar[1].(string))
			}
			deconstruct_result1680 := _t1870
			if deconstruct_result1680 != nil {
				unwrapped1681 := *deconstruct_result1680
				p.write("(")
				p.write("transaction_output_name")
				p.indentSexp()
				p.newline()
				p.pretty_name(unwrapped1681)
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
	flat1691 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1691 != nil {
		p.write(*flat1691)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1871 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1871 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1687 := _t1871
		if deconstruct_result1687 != nil {
			unwrapped1688 := deconstruct_result1687
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1688) == 0) {
				p.newline()
				for i1690, elem1689 := range unwrapped1688 {
					if (i1690 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1689)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1872 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1872 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1685 := _t1872
			if deconstruct_result1685 != nil {
				unwrapped1686 := deconstruct_result1685
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1686)
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
	flat1696 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1696 != nil {
		p.write(*flat1696)
		return nil
	} else {
		_dollar_dollar := msg
		fields1692 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1693 := fields1692
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1694 := unwrapped_fields1693[0].(string)
		p.write(p.formatStringValue(field1694))
		p.newline()
		field1695 := unwrapped_fields1693[1].(*pb.RelationId)
		p.pretty_relation_id(field1695)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1698 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1698 != nil {
		p.write(*flat1698)
		return nil
	} else {
		fields1697 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1697))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1702 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1702 != nil {
		p.write(*flat1702)
		return nil
	} else {
		fields1699 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1699) == 0) {
			p.newline()
			for i1701, elem1700 := range fields1699 {
				if (i1701 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1700)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1711 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1711 != nil {
		p.write(*flat1711)
		return nil
	} else {
		_dollar_dollar := msg
		_t1873 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1703 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1873}
		unwrapped_fields1704 := fields1703
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1705 := unwrapped_fields1704[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1705)
		p.newline()
		field1706 := unwrapped_fields1704[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1706)
		p.newline()
		field1707 := unwrapped_fields1704[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1707)
		p.newline()
		field1708 := unwrapped_fields1704[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1708)
		field1709 := unwrapped_fields1704[4].([][]interface{})
		if field1709 != nil {
			p.newline()
			opt_val1710 := field1709
			p.pretty_config_dict(opt_val1710)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1713 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1713 != nil {
		p.write(*flat1713)
		return nil
	} else {
		fields1712 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1712)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1717 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1717 != nil {
		p.write(*flat1717)
		return nil
	} else {
		fields1714 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1714) == 0) {
			p.newline()
			for i1716, elem1715 := range fields1714 {
				if (i1716 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1715)
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
		_t1928 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1928)
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
