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

func (p *PrettyPrinter) deconstruct_csv_data_columns_optional(msg *pb.CSVData) []*pb.GNFColumn {
	var _t1845 interface{}
	if hasProtoField(msg, "relations") {
		return nil
	}
	_ = _t1845
	return msg.GetColumns()
}

func (p *PrettyPrinter) deconstruct_csv_data_relations_optional(msg *pb.CSVData) *pb.TargetRelations {
	var _t1846 interface{}
	if hasProtoField(msg, "relations") {
		return msg.GetRelations()
	}
	_ = _t1846
	return nil
}

func (p *PrettyPrinter) deconstruct_export_csv_output_location(msg *pb.ExportCSVConfig) []interface{} {
	return []interface{}{msg.GetPath(), msg.GetTransactionOutputName()}
}

func (p *PrettyPrinter) _make_value_int32(v int32) *pb.Value {
	_t1847 := &pb.Value{}
	_t1847.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1847
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1848 := &pb.Value{}
	_t1848.Value = &pb.Value_IntValue{IntValue: v}
	return _t1848
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1849 := &pb.Value{}
	_t1849.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1849
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1850 := &pb.Value{}
	_t1850.Value = &pb.Value_StringValue{StringValue: v}
	return _t1850
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1851 := &pb.Value{}
	_t1851.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1851
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1852 := &pb.Value{}
	_t1852.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1852
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1853 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1853})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1854 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1854})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1855 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1855})
			}
		}
	}
	_t1856 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1856})
	if msg.GetAstSizeLimit().GetWarningLimit() != 0 {
		_t1857 := p._make_value_int64(msg.GetAstSizeLimit().GetWarningLimit())
		result = append(result, []interface{}{"ast_size.warning_limit", _t1857})
	}
	if msg.GetAstSizeLimit().GetExceptionLimit() != 0 {
		_t1858 := p._make_value_int64(msg.GetAstSizeLimit().GetExceptionLimit())
		result = append(result, []interface{}{"ast_size.exception_limit", _t1858})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1859 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1859})
	_t1860 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1860})
	if msg.GetNewLine() != "" {
		_t1861 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1861})
	}
	_t1862 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1862})
	_t1863 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1863})
	_t1864 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1864})
	if msg.GetComment() != "" {
		_t1865 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1865})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1866 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1866})
	}
	_t1867 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1867})
	_t1868 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1868})
	_t1869 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1869})
	if msg.GetPartitionSizeMb() != 0 {
		_t1870 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1870})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_storage_integration_optional(msg *pb.CSVConfig) [][]interface{} {
	var _t1871 interface{}
	if !(hasProtoField(msg, "storage_integration")) {
		return nil
	}
	_ = _t1871
	si := msg.GetStorageIntegration()
	result := [][]interface{}{}
	if si.GetProvider() != "" {
		_t1872 := p._make_value_string(si.GetProvider())
		result = append(result, []interface{}{"provider", _t1872})
	}
	if si.GetAzureSasToken() != "" {
		_t1873 := p._make_value_string("***")
		result = append(result, []interface{}{"azure_sas_token", _t1873})
	}
	if si.GetS3Region() != "" {
		_t1874 := p._make_value_string(si.GetS3Region())
		result = append(result, []interface{}{"s3_region", _t1874})
	}
	if si.GetS3AccessKeyId() != "" {
		_t1875 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_access_key_id", _t1875})
	}
	if si.GetS3SecretAccessKey() != "" {
		_t1876 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_secret_access_key", _t1876})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1877 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1877})
	_t1878 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1878})
	_t1879 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1879})
	_t1880 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1880})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1881 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1881})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1882 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1882})
		}
	}
	_t1883 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1883})
	_t1884 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1884})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1885 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1885})
	}
	if msg.Compression != nil {
		_t1886 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1886})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1887 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1887})
	}
	if msg.SyntaxMissingString != nil {
		_t1888 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1888})
	}
	if msg.SyntaxDelim != nil {
		_t1889 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1889})
	}
	if msg.SyntaxQuotechar != nil {
		_t1890 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1890})
	}
	if msg.SyntaxEscapechar != nil {
		_t1891 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1891})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1892 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1892
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1893 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1893
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1894 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1894
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1895 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1895})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1896 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1896})
	}
	if msg.GetCompression() != "" {
		_t1897 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1897})
	}
	var _t1898 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1898
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1899 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1899
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
	flat856 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat856 != nil {
		p.write(*flat856)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1694 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1694 = _dollar_dollar.GetConfigure()
		}
		var _t1695 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1695 = _dollar_dollar.GetSync()
		}
		fields847 := []interface{}{_t1694, _t1695, _dollar_dollar.GetEpochs()}
		unwrapped_fields848 := fields847
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field849 := unwrapped_fields848[0].(*pb.Configure)
		if field849 != nil {
			p.newline()
			opt_val850 := field849
			p.pretty_configure(opt_val850)
		}
		field851 := unwrapped_fields848[1].(*pb.Sync)
		if field851 != nil {
			p.newline()
			opt_val852 := field851
			p.pretty_sync(opt_val852)
		}
		field853 := unwrapped_fields848[2].([]*pb.Epoch)
		if !(len(field853) == 0) {
			p.newline()
			for i855, elem854 := range field853 {
				if (i855 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem854)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat859 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat859 != nil {
		p.write(*flat859)
		return nil
	} else {
		_dollar_dollar := msg
		_t1696 := p.deconstruct_configure(_dollar_dollar)
		fields857 := _t1696
		unwrapped_fields858 := fields857
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields858)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat863 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat863 != nil {
		p.write(*flat863)
		return nil
	} else {
		fields860 := msg
		p.write("{")
		p.indent()
		if !(len(fields860) == 0) {
			p.newline()
			for i862, elem861 := range fields860 {
				if (i862 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem861)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat868 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat868 != nil {
		p.write(*flat868)
		return nil
	} else {
		_dollar_dollar := msg
		fields864 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields865 := fields864
		p.write(":")
		field866 := unwrapped_fields865[0].(string)
		p.write(field866)
		p.write(" ")
		field867 := unwrapped_fields865[1].(*pb.Value)
		p.pretty_raw_value(field867)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat894 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat894 != nil {
		p.write(*flat894)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1697 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1697 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result892 := _t1697
		if deconstruct_result892 != nil {
			unwrapped893 := deconstruct_result892
			p.pretty_raw_date(unwrapped893)
		} else {
			_dollar_dollar := msg
			var _t1698 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1698 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result890 := _t1698
			if deconstruct_result890 != nil {
				unwrapped891 := deconstruct_result890
				p.pretty_raw_datetime(unwrapped891)
			} else {
				_dollar_dollar := msg
				var _t1699 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1699 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result888 := _t1699
				if deconstruct_result888 != nil {
					unwrapped889 := *deconstruct_result888
					p.write(p.formatStringValue(unwrapped889))
				} else {
					_dollar_dollar := msg
					var _t1700 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1700 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result886 := _t1700
					if deconstruct_result886 != nil {
						unwrapped887 := *deconstruct_result886
						p.write(fmt.Sprintf("%di32", unwrapped887))
					} else {
						_dollar_dollar := msg
						var _t1701 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1701 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result884 := _t1701
						if deconstruct_result884 != nil {
							unwrapped885 := *deconstruct_result884
							p.write(fmt.Sprintf("%d", unwrapped885))
						} else {
							_dollar_dollar := msg
							var _t1702 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1702 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result882 := _t1702
							if deconstruct_result882 != nil {
								unwrapped883 := *deconstruct_result882
								p.write(formatFloat32(unwrapped883))
							} else {
								_dollar_dollar := msg
								var _t1703 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1703 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result880 := _t1703
								if deconstruct_result880 != nil {
									unwrapped881 := *deconstruct_result880
									p.write(formatFloat64(unwrapped881))
								} else {
									_dollar_dollar := msg
									var _t1704 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1704 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result878 := _t1704
									if deconstruct_result878 != nil {
										unwrapped879 := *deconstruct_result878
										p.write(fmt.Sprintf("%du32", unwrapped879))
									} else {
										_dollar_dollar := msg
										var _t1705 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1705 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result876 := _t1705
										if deconstruct_result876 != nil {
											unwrapped877 := deconstruct_result876
											p.write(p.formatUint128(unwrapped877))
										} else {
											_dollar_dollar := msg
											var _t1706 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1706 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result874 := _t1706
											if deconstruct_result874 != nil {
												unwrapped875 := deconstruct_result874
												p.write(p.formatInt128(unwrapped875))
											} else {
												_dollar_dollar := msg
												var _t1707 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1707 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result872 := _t1707
												if deconstruct_result872 != nil {
													unwrapped873 := deconstruct_result872
													p.write(p.formatDecimal(unwrapped873))
												} else {
													_dollar_dollar := msg
													var _t1708 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1708 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result870 := _t1708
													if deconstruct_result870 != nil {
														unwrapped871 := *deconstruct_result870
														p.pretty_boolean_value(unwrapped871)
													} else {
														fields869 := msg
														_ = fields869
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
	flat900 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat900 != nil {
		p.write(*flat900)
		return nil
	} else {
		_dollar_dollar := msg
		fields895 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields896 := fields895
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field897 := unwrapped_fields896[0].(int64)
		p.write(fmt.Sprintf("%d", field897))
		p.newline()
		field898 := unwrapped_fields896[1].(int64)
		p.write(fmt.Sprintf("%d", field898))
		p.newline()
		field899 := unwrapped_fields896[2].(int64)
		p.write(fmt.Sprintf("%d", field899))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat911 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat911 != nil {
		p.write(*flat911)
		return nil
	} else {
		_dollar_dollar := msg
		fields901 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields902 := fields901
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field903 := unwrapped_fields902[0].(int64)
		p.write(fmt.Sprintf("%d", field903))
		p.newline()
		field904 := unwrapped_fields902[1].(int64)
		p.write(fmt.Sprintf("%d", field904))
		p.newline()
		field905 := unwrapped_fields902[2].(int64)
		p.write(fmt.Sprintf("%d", field905))
		p.newline()
		field906 := unwrapped_fields902[3].(int64)
		p.write(fmt.Sprintf("%d", field906))
		p.newline()
		field907 := unwrapped_fields902[4].(int64)
		p.write(fmt.Sprintf("%d", field907))
		p.newline()
		field908 := unwrapped_fields902[5].(int64)
		p.write(fmt.Sprintf("%d", field908))
		field909 := unwrapped_fields902[6].(*int64)
		if field909 != nil {
			p.newline()
			opt_val910 := *field909
			p.write(fmt.Sprintf("%d", opt_val910))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1709 []interface{}
	if _dollar_dollar {
		_t1709 = []interface{}{}
	}
	deconstruct_result914 := _t1709
	if deconstruct_result914 != nil {
		unwrapped915 := deconstruct_result914
		_ = unwrapped915
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1710 []interface{}
		if !(_dollar_dollar) {
			_t1710 = []interface{}{}
		}
		deconstruct_result912 := _t1710
		if deconstruct_result912 != nil {
			unwrapped913 := deconstruct_result912
			_ = unwrapped913
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat920 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat920 != nil {
		p.write(*flat920)
		return nil
	} else {
		_dollar_dollar := msg
		fields916 := _dollar_dollar.GetFragments()
		unwrapped_fields917 := fields916
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields917) == 0) {
			p.newline()
			for i919, elem918 := range unwrapped_fields917 {
				if (i919 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem918)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat923 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat923 != nil {
		p.write(*flat923)
		return nil
	} else {
		_dollar_dollar := msg
		fields921 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields922 := fields921
		p.write(":")
		p.write(unwrapped_fields922)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat930 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat930 != nil {
		p.write(*flat930)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1711 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1711 = _dollar_dollar.GetWrites()
		}
		var _t1712 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1712 = _dollar_dollar.GetReads()
		}
		fields924 := []interface{}{_t1711, _t1712}
		unwrapped_fields925 := fields924
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field926 := unwrapped_fields925[0].([]*pb.Write)
		if field926 != nil {
			p.newline()
			opt_val927 := field926
			p.pretty_epoch_writes(opt_val927)
		}
		field928 := unwrapped_fields925[1].([]*pb.Read)
		if field928 != nil {
			p.newline()
			opt_val929 := field928
			p.pretty_epoch_reads(opt_val929)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat934 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat934 != nil {
		p.write(*flat934)
		return nil
	} else {
		fields931 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields931) == 0) {
			p.newline()
			for i933, elem932 := range fields931 {
				if (i933 > 0) {
					p.newline()
				}
				p.pretty_write(elem932)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat943 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat943 != nil {
		p.write(*flat943)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1713 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1713 = _dollar_dollar.GetDefine()
		}
		deconstruct_result941 := _t1713
		if deconstruct_result941 != nil {
			unwrapped942 := deconstruct_result941
			p.pretty_define(unwrapped942)
		} else {
			_dollar_dollar := msg
			var _t1714 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1714 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result939 := _t1714
			if deconstruct_result939 != nil {
				unwrapped940 := deconstruct_result939
				p.pretty_undefine(unwrapped940)
			} else {
				_dollar_dollar := msg
				var _t1715 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1715 = _dollar_dollar.GetContext()
				}
				deconstruct_result937 := _t1715
				if deconstruct_result937 != nil {
					unwrapped938 := deconstruct_result937
					p.pretty_context(unwrapped938)
				} else {
					_dollar_dollar := msg
					var _t1716 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1716 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result935 := _t1716
					if deconstruct_result935 != nil {
						unwrapped936 := deconstruct_result935
						p.pretty_snapshot(unwrapped936)
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
	flat946 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat946 != nil {
		p.write(*flat946)
		return nil
	} else {
		_dollar_dollar := msg
		fields944 := _dollar_dollar.GetFragment()
		unwrapped_fields945 := fields944
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields945)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat953 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat953 != nil {
		p.write(*flat953)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields947 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields948 := fields947
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field949 := unwrapped_fields948[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field949)
		field950 := unwrapped_fields948[1].([]*pb.Declaration)
		if !(len(field950) == 0) {
			p.newline()
			for i952, elem951 := range field950 {
				if (i952 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem951)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat955 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat955 != nil {
		p.write(*flat955)
		return nil
	} else {
		fields954 := msg
		p.pretty_fragment_id(fields954)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat964 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat964 != nil {
		p.write(*flat964)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1717 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1717 = _dollar_dollar.GetDef()
		}
		deconstruct_result962 := _t1717
		if deconstruct_result962 != nil {
			unwrapped963 := deconstruct_result962
			p.pretty_def(unwrapped963)
		} else {
			_dollar_dollar := msg
			var _t1718 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1718 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result960 := _t1718
			if deconstruct_result960 != nil {
				unwrapped961 := deconstruct_result960
				p.pretty_algorithm(unwrapped961)
			} else {
				_dollar_dollar := msg
				var _t1719 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1719 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result958 := _t1719
				if deconstruct_result958 != nil {
					unwrapped959 := deconstruct_result958
					p.pretty_constraint(unwrapped959)
				} else {
					_dollar_dollar := msg
					var _t1720 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1720 = _dollar_dollar.GetData()
					}
					deconstruct_result956 := _t1720
					if deconstruct_result956 != nil {
						unwrapped957 := deconstruct_result956
						p.pretty_data(unwrapped957)
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
	flat971 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat971 != nil {
		p.write(*flat971)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1721 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1721 = _dollar_dollar.GetAttrs()
		}
		fields965 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1721}
		unwrapped_fields966 := fields965
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field967 := unwrapped_fields966[0].(*pb.RelationId)
		p.pretty_relation_id(field967)
		p.newline()
		field968 := unwrapped_fields966[1].(*pb.Abstraction)
		p.pretty_abstraction(field968)
		field969 := unwrapped_fields966[2].([]*pb.Attribute)
		if field969 != nil {
			p.newline()
			opt_val970 := field969
			p.pretty_attrs(opt_val970)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat976 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat976 != nil {
		p.write(*flat976)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1722 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1723 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1722 = ptr(_t1723)
		}
		deconstruct_result974 := _t1722
		if deconstruct_result974 != nil {
			unwrapped975 := *deconstruct_result974
			p.write(":")
			p.write(unwrapped975)
		} else {
			_dollar_dollar := msg
			_t1724 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result972 := _t1724
			if deconstruct_result972 != nil {
				unwrapped973 := deconstruct_result972
				p.write(p.formatUint128(unwrapped973))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat981 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat981 != nil {
		p.write(*flat981)
		return nil
	} else {
		_dollar_dollar := msg
		_t1725 := p.deconstruct_bindings(_dollar_dollar)
		fields977 := []interface{}{_t1725, _dollar_dollar.GetValue()}
		unwrapped_fields978 := fields977
		p.write("(")
		p.indent()
		field979 := unwrapped_fields978[0].([]interface{})
		p.pretty_bindings(field979)
		p.newline()
		field980 := unwrapped_fields978[1].(*pb.Formula)
		p.pretty_formula(field980)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat989 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat989 != nil {
		p.write(*flat989)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1726 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1726 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields982 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1726}
		unwrapped_fields983 := fields982
		p.write("[")
		p.indent()
		field984 := unwrapped_fields983[0].([]*pb.Binding)
		for i986, elem985 := range field984 {
			if (i986 > 0) {
				p.newline()
			}
			p.pretty_binding(elem985)
		}
		field987 := unwrapped_fields983[1].([]*pb.Binding)
		if field987 != nil {
			p.newline()
			opt_val988 := field987
			p.pretty_value_bindings(opt_val988)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat994 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat994 != nil {
		p.write(*flat994)
		return nil
	} else {
		_dollar_dollar := msg
		fields990 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields991 := fields990
		field992 := unwrapped_fields991[0].(string)
		p.write(field992)
		p.write("::")
		field993 := unwrapped_fields991[1].(*pb.Type)
		p.pretty_type(field993)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat1023 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat1023 != nil {
		p.write(*flat1023)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1727 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1727 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result1021 := _t1727
		if deconstruct_result1021 != nil {
			unwrapped1022 := deconstruct_result1021
			p.pretty_unspecified_type(unwrapped1022)
		} else {
			_dollar_dollar := msg
			var _t1728 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1728 = _dollar_dollar.GetStringType()
			}
			deconstruct_result1019 := _t1728
			if deconstruct_result1019 != nil {
				unwrapped1020 := deconstruct_result1019
				p.pretty_string_type(unwrapped1020)
			} else {
				_dollar_dollar := msg
				var _t1729 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1729 = _dollar_dollar.GetIntType()
				}
				deconstruct_result1017 := _t1729
				if deconstruct_result1017 != nil {
					unwrapped1018 := deconstruct_result1017
					p.pretty_int_type(unwrapped1018)
				} else {
					_dollar_dollar := msg
					var _t1730 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1730 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result1015 := _t1730
					if deconstruct_result1015 != nil {
						unwrapped1016 := deconstruct_result1015
						p.pretty_float_type(unwrapped1016)
					} else {
						_dollar_dollar := msg
						var _t1731 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1731 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result1013 := _t1731
						if deconstruct_result1013 != nil {
							unwrapped1014 := deconstruct_result1013
							p.pretty_uint128_type(unwrapped1014)
						} else {
							_dollar_dollar := msg
							var _t1732 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1732 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result1011 := _t1732
							if deconstruct_result1011 != nil {
								unwrapped1012 := deconstruct_result1011
								p.pretty_int128_type(unwrapped1012)
							} else {
								_dollar_dollar := msg
								var _t1733 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1733 = _dollar_dollar.GetDateType()
								}
								deconstruct_result1009 := _t1733
								if deconstruct_result1009 != nil {
									unwrapped1010 := deconstruct_result1009
									p.pretty_date_type(unwrapped1010)
								} else {
									_dollar_dollar := msg
									var _t1734 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1734 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result1007 := _t1734
									if deconstruct_result1007 != nil {
										unwrapped1008 := deconstruct_result1007
										p.pretty_datetime_type(unwrapped1008)
									} else {
										_dollar_dollar := msg
										var _t1735 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1735 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result1005 := _t1735
										if deconstruct_result1005 != nil {
											unwrapped1006 := deconstruct_result1005
											p.pretty_missing_type(unwrapped1006)
										} else {
											_dollar_dollar := msg
											var _t1736 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1736 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result1003 := _t1736
											if deconstruct_result1003 != nil {
												unwrapped1004 := deconstruct_result1003
												p.pretty_decimal_type(unwrapped1004)
											} else {
												_dollar_dollar := msg
												var _t1737 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1737 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result1001 := _t1737
												if deconstruct_result1001 != nil {
													unwrapped1002 := deconstruct_result1001
													p.pretty_boolean_type(unwrapped1002)
												} else {
													_dollar_dollar := msg
													var _t1738 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1738 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result999 := _t1738
													if deconstruct_result999 != nil {
														unwrapped1000 := deconstruct_result999
														p.pretty_int32_type(unwrapped1000)
													} else {
														_dollar_dollar := msg
														var _t1739 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1739 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result997 := _t1739
														if deconstruct_result997 != nil {
															unwrapped998 := deconstruct_result997
															p.pretty_float32_type(unwrapped998)
														} else {
															_dollar_dollar := msg
															var _t1740 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1740 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result995 := _t1740
															if deconstruct_result995 != nil {
																unwrapped996 := deconstruct_result995
																p.pretty_uint32_type(unwrapped996)
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
	fields1024 := msg
	_ = fields1024
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields1025 := msg
	_ = fields1025
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields1026 := msg
	_ = fields1026
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields1027 := msg
	_ = fields1027
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields1028 := msg
	_ = fields1028
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields1029 := msg
	_ = fields1029
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields1030 := msg
	_ = fields1030
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields1031 := msg
	_ = fields1031
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields1032 := msg
	_ = fields1032
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat1037 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat1037 != nil {
		p.write(*flat1037)
		return nil
	} else {
		_dollar_dollar := msg
		fields1033 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields1034 := fields1033
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field1035 := unwrapped_fields1034[0].(int64)
		p.write(fmt.Sprintf("%d", field1035))
		p.newline()
		field1036 := unwrapped_fields1034[1].(int64)
		p.write(fmt.Sprintf("%d", field1036))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields1038 := msg
	_ = fields1038
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields1039 := msg
	_ = fields1039
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields1040 := msg
	_ = fields1040
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields1041 := msg
	_ = fields1041
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat1045 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat1045 != nil {
		p.write(*flat1045)
		return nil
	} else {
		fields1042 := msg
		p.write("|")
		if !(len(fields1042) == 0) {
			p.write(" ")
			for i1044, elem1043 := range fields1042 {
				if (i1044 > 0) {
					p.newline()
				}
				p.pretty_binding(elem1043)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1072 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1072 != nil {
		p.write(*flat1072)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1741 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1741 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1070 := _t1741
		if deconstruct_result1070 != nil {
			unwrapped1071 := deconstruct_result1070
			p.pretty_true(unwrapped1071)
		} else {
			_dollar_dollar := msg
			var _t1742 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1742 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1068 := _t1742
			if deconstruct_result1068 != nil {
				unwrapped1069 := deconstruct_result1068
				p.pretty_false(unwrapped1069)
			} else {
				_dollar_dollar := msg
				var _t1743 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1743 = _dollar_dollar.GetExists()
				}
				deconstruct_result1066 := _t1743
				if deconstruct_result1066 != nil {
					unwrapped1067 := deconstruct_result1066
					p.pretty_exists(unwrapped1067)
				} else {
					_dollar_dollar := msg
					var _t1744 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1744 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1064 := _t1744
					if deconstruct_result1064 != nil {
						unwrapped1065 := deconstruct_result1064
						p.pretty_reduce(unwrapped1065)
					} else {
						_dollar_dollar := msg
						var _t1745 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1745 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1062 := _t1745
						if deconstruct_result1062 != nil {
							unwrapped1063 := deconstruct_result1062
							p.pretty_conjunction(unwrapped1063)
						} else {
							_dollar_dollar := msg
							var _t1746 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1746 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1060 := _t1746
							if deconstruct_result1060 != nil {
								unwrapped1061 := deconstruct_result1060
								p.pretty_disjunction(unwrapped1061)
							} else {
								_dollar_dollar := msg
								var _t1747 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1747 = _dollar_dollar.GetNot()
								}
								deconstruct_result1058 := _t1747
								if deconstruct_result1058 != nil {
									unwrapped1059 := deconstruct_result1058
									p.pretty_not(unwrapped1059)
								} else {
									_dollar_dollar := msg
									var _t1748 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1748 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1056 := _t1748
									if deconstruct_result1056 != nil {
										unwrapped1057 := deconstruct_result1056
										p.pretty_ffi(unwrapped1057)
									} else {
										_dollar_dollar := msg
										var _t1749 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1749 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1054 := _t1749
										if deconstruct_result1054 != nil {
											unwrapped1055 := deconstruct_result1054
											p.pretty_atom(unwrapped1055)
										} else {
											_dollar_dollar := msg
											var _t1750 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1750 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1052 := _t1750
											if deconstruct_result1052 != nil {
												unwrapped1053 := deconstruct_result1052
												p.pretty_pragma(unwrapped1053)
											} else {
												_dollar_dollar := msg
												var _t1751 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1751 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1050 := _t1751
												if deconstruct_result1050 != nil {
													unwrapped1051 := deconstruct_result1050
													p.pretty_primitive(unwrapped1051)
												} else {
													_dollar_dollar := msg
													var _t1752 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1752 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1048 := _t1752
													if deconstruct_result1048 != nil {
														unwrapped1049 := deconstruct_result1048
														p.pretty_rel_atom(unwrapped1049)
													} else {
														_dollar_dollar := msg
														var _t1753 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1753 = _dollar_dollar.GetCast()
														}
														deconstruct_result1046 := _t1753
														if deconstruct_result1046 != nil {
															unwrapped1047 := deconstruct_result1046
															p.pretty_cast(unwrapped1047)
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
	fields1073 := msg
	_ = fields1073
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1074 := msg
	_ = fields1074
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1079 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1079 != nil {
		p.write(*flat1079)
		return nil
	} else {
		_dollar_dollar := msg
		_t1754 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1075 := []interface{}{_t1754, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1076 := fields1075
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1077 := unwrapped_fields1076[0].([]interface{})
		p.pretty_bindings(field1077)
		p.newline()
		field1078 := unwrapped_fields1076[1].(*pb.Formula)
		p.pretty_formula(field1078)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1085 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1085 != nil {
		p.write(*flat1085)
		return nil
	} else {
		_dollar_dollar := msg
		fields1080 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1081 := fields1080
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1082 := unwrapped_fields1081[0].(*pb.Abstraction)
		p.pretty_abstraction(field1082)
		p.newline()
		field1083 := unwrapped_fields1081[1].(*pb.Abstraction)
		p.pretty_abstraction(field1083)
		p.newline()
		field1084 := unwrapped_fields1081[2].([]*pb.Term)
		p.pretty_terms(field1084)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1089 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1089 != nil {
		p.write(*flat1089)
		return nil
	} else {
		fields1086 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1086) == 0) {
			p.newline()
			for i1088, elem1087 := range fields1086 {
				if (i1088 > 0) {
					p.newline()
				}
				p.pretty_term(elem1087)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1094 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1094 != nil {
		p.write(*flat1094)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1755 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1755 = _dollar_dollar.GetVar()
		}
		deconstruct_result1092 := _t1755
		if deconstruct_result1092 != nil {
			unwrapped1093 := deconstruct_result1092
			p.pretty_var(unwrapped1093)
		} else {
			_dollar_dollar := msg
			var _t1756 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1756 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1090 := _t1756
			if deconstruct_result1090 != nil {
				unwrapped1091 := deconstruct_result1090
				p.pretty_value(unwrapped1091)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1097 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1097 != nil {
		p.write(*flat1097)
		return nil
	} else {
		_dollar_dollar := msg
		fields1095 := _dollar_dollar.GetName()
		unwrapped_fields1096 := fields1095
		p.write(unwrapped_fields1096)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1123 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1123 != nil {
		p.write(*flat1123)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1757 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1757 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1121 := _t1757
		if deconstruct_result1121 != nil {
			unwrapped1122 := deconstruct_result1121
			p.pretty_date(unwrapped1122)
		} else {
			_dollar_dollar := msg
			var _t1758 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1758 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1119 := _t1758
			if deconstruct_result1119 != nil {
				unwrapped1120 := deconstruct_result1119
				p.pretty_datetime(unwrapped1120)
			} else {
				_dollar_dollar := msg
				var _t1759 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1759 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1117 := _t1759
				if deconstruct_result1117 != nil {
					unwrapped1118 := *deconstruct_result1117
					p.write(p.formatStringValue(unwrapped1118))
				} else {
					_dollar_dollar := msg
					var _t1760 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1760 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1115 := _t1760
					if deconstruct_result1115 != nil {
						unwrapped1116 := *deconstruct_result1115
						p.write(fmt.Sprintf("%di32", unwrapped1116))
					} else {
						_dollar_dollar := msg
						var _t1761 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1761 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1113 := _t1761
						if deconstruct_result1113 != nil {
							unwrapped1114 := *deconstruct_result1113
							p.write(fmt.Sprintf("%d", unwrapped1114))
						} else {
							_dollar_dollar := msg
							var _t1762 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1762 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1111 := _t1762
							if deconstruct_result1111 != nil {
								unwrapped1112 := *deconstruct_result1111
								p.write(formatFloat32(unwrapped1112))
							} else {
								_dollar_dollar := msg
								var _t1763 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1763 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1109 := _t1763
								if deconstruct_result1109 != nil {
									unwrapped1110 := *deconstruct_result1109
									p.write(formatFloat64(unwrapped1110))
								} else {
									_dollar_dollar := msg
									var _t1764 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1764 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1107 := _t1764
									if deconstruct_result1107 != nil {
										unwrapped1108 := *deconstruct_result1107
										p.write(fmt.Sprintf("%du32", unwrapped1108))
									} else {
										_dollar_dollar := msg
										var _t1765 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1765 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1105 := _t1765
										if deconstruct_result1105 != nil {
											unwrapped1106 := deconstruct_result1105
											p.write(p.formatUint128(unwrapped1106))
										} else {
											_dollar_dollar := msg
											var _t1766 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1766 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1103 := _t1766
											if deconstruct_result1103 != nil {
												unwrapped1104 := deconstruct_result1103
												p.write(p.formatInt128(unwrapped1104))
											} else {
												_dollar_dollar := msg
												var _t1767 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1767 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1101 := _t1767
												if deconstruct_result1101 != nil {
													unwrapped1102 := deconstruct_result1101
													p.write(p.formatDecimal(unwrapped1102))
												} else {
													_dollar_dollar := msg
													var _t1768 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1768 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1099 := _t1768
													if deconstruct_result1099 != nil {
														unwrapped1100 := *deconstruct_result1099
														p.pretty_boolean_value(unwrapped1100)
													} else {
														fields1098 := msg
														_ = fields1098
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
	flat1129 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1129 != nil {
		p.write(*flat1129)
		return nil
	} else {
		_dollar_dollar := msg
		fields1124 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1125 := fields1124
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1126 := unwrapped_fields1125[0].(int64)
		p.write(fmt.Sprintf("%d", field1126))
		p.newline()
		field1127 := unwrapped_fields1125[1].(int64)
		p.write(fmt.Sprintf("%d", field1127))
		p.newline()
		field1128 := unwrapped_fields1125[2].(int64)
		p.write(fmt.Sprintf("%d", field1128))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1140 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1140 != nil {
		p.write(*flat1140)
		return nil
	} else {
		_dollar_dollar := msg
		fields1130 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1131 := fields1130
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1132 := unwrapped_fields1131[0].(int64)
		p.write(fmt.Sprintf("%d", field1132))
		p.newline()
		field1133 := unwrapped_fields1131[1].(int64)
		p.write(fmt.Sprintf("%d", field1133))
		p.newline()
		field1134 := unwrapped_fields1131[2].(int64)
		p.write(fmt.Sprintf("%d", field1134))
		p.newline()
		field1135 := unwrapped_fields1131[3].(int64)
		p.write(fmt.Sprintf("%d", field1135))
		p.newline()
		field1136 := unwrapped_fields1131[4].(int64)
		p.write(fmt.Sprintf("%d", field1136))
		p.newline()
		field1137 := unwrapped_fields1131[5].(int64)
		p.write(fmt.Sprintf("%d", field1137))
		field1138 := unwrapped_fields1131[6].(*int64)
		if field1138 != nil {
			p.newline()
			opt_val1139 := *field1138
			p.write(fmt.Sprintf("%d", opt_val1139))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1145 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1145 != nil {
		p.write(*flat1145)
		return nil
	} else {
		_dollar_dollar := msg
		fields1141 := _dollar_dollar.GetArgs()
		unwrapped_fields1142 := fields1141
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1142) == 0) {
			p.newline()
			for i1144, elem1143 := range unwrapped_fields1142 {
				if (i1144 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1143)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1150 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1150 != nil {
		p.write(*flat1150)
		return nil
	} else {
		_dollar_dollar := msg
		fields1146 := _dollar_dollar.GetArgs()
		unwrapped_fields1147 := fields1146
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1147) == 0) {
			p.newline()
			for i1149, elem1148 := range unwrapped_fields1147 {
				if (i1149 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1148)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1153 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1153 != nil {
		p.write(*flat1153)
		return nil
	} else {
		_dollar_dollar := msg
		fields1151 := _dollar_dollar.GetArg()
		unwrapped_fields1152 := fields1151
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1152)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1159 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1159 != nil {
		p.write(*flat1159)
		return nil
	} else {
		_dollar_dollar := msg
		fields1154 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1155 := fields1154
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1156 := unwrapped_fields1155[0].(string)
		p.pretty_name(field1156)
		p.newline()
		field1157 := unwrapped_fields1155[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1157)
		p.newline()
		field1158 := unwrapped_fields1155[2].([]*pb.Term)
		p.pretty_terms(field1158)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1161 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1161 != nil {
		p.write(*flat1161)
		return nil
	} else {
		fields1160 := msg
		p.write(":")
		p.write(fields1160)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1165 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1165 != nil {
		p.write(*flat1165)
		return nil
	} else {
		fields1162 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1162) == 0) {
			p.newline()
			for i1164, elem1163 := range fields1162 {
				if (i1164 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1163)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1172 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1172 != nil {
		p.write(*flat1172)
		return nil
	} else {
		_dollar_dollar := msg
		fields1166 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1167 := fields1166
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1168 := unwrapped_fields1167[0].(*pb.RelationId)
		p.pretty_relation_id(field1168)
		field1169 := unwrapped_fields1167[1].([]*pb.Term)
		if !(len(field1169) == 0) {
			p.newline()
			for i1171, elem1170 := range field1169 {
				if (i1171 > 0) {
					p.newline()
				}
				p.pretty_term(elem1170)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		_dollar_dollar := msg
		fields1173 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1174 := fields1173
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1175 := unwrapped_fields1174[0].(string)
		p.pretty_name(field1175)
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

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1195 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1195 != nil {
		p.write(*flat1195)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1769 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1769 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1194 := _t1769
		if guard_result1194 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1770 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1770 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1193 := _t1770
			if guard_result1193 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1771 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1771 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1192 := _t1771
				if guard_result1192 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1772 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1772 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1191 := _t1772
					if guard_result1191 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1773 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1773 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1190 := _t1773
						if guard_result1190 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1774 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1774 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1189 := _t1774
							if guard_result1189 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1775 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1775 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1188 := _t1775
								if guard_result1188 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1776 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1776 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1187 := _t1776
									if guard_result1187 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1777 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1777 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1186 := _t1777
										if guard_result1186 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1180 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1181 := fields1180
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1182 := unwrapped_fields1181[0].(string)
											p.pretty_name(field1182)
											field1183 := unwrapped_fields1181[1].([]*pb.RelTerm)
											if !(len(field1183) == 0) {
												p.newline()
												for i1185, elem1184 := range field1183 {
													if (i1185 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1184)
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
	flat1200 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1200 != nil {
		p.write(*flat1200)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1778 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1778 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1196 := _t1778
		unwrapped_fields1197 := fields1196
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1198 := unwrapped_fields1197[0].(*pb.Term)
		p.pretty_term(field1198)
		p.newline()
		field1199 := unwrapped_fields1197[1].(*pb.Term)
		p.pretty_term(field1199)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1205 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1205 != nil {
		p.write(*flat1205)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1779 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1779 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1201 := _t1779
		unwrapped_fields1202 := fields1201
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1203 := unwrapped_fields1202[0].(*pb.Term)
		p.pretty_term(field1203)
		p.newline()
		field1204 := unwrapped_fields1202[1].(*pb.Term)
		p.pretty_term(field1204)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1210 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1210 != nil {
		p.write(*flat1210)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1780 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1780 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1206 := _t1780
		unwrapped_fields1207 := fields1206
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1208 := unwrapped_fields1207[0].(*pb.Term)
		p.pretty_term(field1208)
		p.newline()
		field1209 := unwrapped_fields1207[1].(*pb.Term)
		p.pretty_term(field1209)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1215 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1215 != nil {
		p.write(*flat1215)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1781 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1781 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1211 := _t1781
		unwrapped_fields1212 := fields1211
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1213 := unwrapped_fields1212[0].(*pb.Term)
		p.pretty_term(field1213)
		p.newline()
		field1214 := unwrapped_fields1212[1].(*pb.Term)
		p.pretty_term(field1214)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1220 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1220 != nil {
		p.write(*flat1220)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1782 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1782 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1216 := _t1782
		unwrapped_fields1217 := fields1216
		p.write("(")
		p.write(">=")
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

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1226 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1226 != nil {
		p.write(*flat1226)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1783 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1783 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1221 := _t1783
		unwrapped_fields1222 := fields1221
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1223 := unwrapped_fields1222[0].(*pb.Term)
		p.pretty_term(field1223)
		p.newline()
		field1224 := unwrapped_fields1222[1].(*pb.Term)
		p.pretty_term(field1224)
		p.newline()
		field1225 := unwrapped_fields1222[2].(*pb.Term)
		p.pretty_term(field1225)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1232 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1232 != nil {
		p.write(*flat1232)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1784 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1784 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1227 := _t1784
		unwrapped_fields1228 := fields1227
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1229 := unwrapped_fields1228[0].(*pb.Term)
		p.pretty_term(field1229)
		p.newline()
		field1230 := unwrapped_fields1228[1].(*pb.Term)
		p.pretty_term(field1230)
		p.newline()
		field1231 := unwrapped_fields1228[2].(*pb.Term)
		p.pretty_term(field1231)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1238 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1238 != nil {
		p.write(*flat1238)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1785 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1785 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1233 := _t1785
		unwrapped_fields1234 := fields1233
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1235 := unwrapped_fields1234[0].(*pb.Term)
		p.pretty_term(field1235)
		p.newline()
		field1236 := unwrapped_fields1234[1].(*pb.Term)
		p.pretty_term(field1236)
		p.newline()
		field1237 := unwrapped_fields1234[2].(*pb.Term)
		p.pretty_term(field1237)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1244 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1244 != nil {
		p.write(*flat1244)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1786 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1786 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1239 := _t1786
		unwrapped_fields1240 := fields1239
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1241 := unwrapped_fields1240[0].(*pb.Term)
		p.pretty_term(field1241)
		p.newline()
		field1242 := unwrapped_fields1240[1].(*pb.Term)
		p.pretty_term(field1242)
		p.newline()
		field1243 := unwrapped_fields1240[2].(*pb.Term)
		p.pretty_term(field1243)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1249 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1249 != nil {
		p.write(*flat1249)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1787 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1787 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1247 := _t1787
		if deconstruct_result1247 != nil {
			unwrapped1248 := deconstruct_result1247
			p.pretty_specialized_value(unwrapped1248)
		} else {
			_dollar_dollar := msg
			var _t1788 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1788 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1245 := _t1788
			if deconstruct_result1245 != nil {
				unwrapped1246 := deconstruct_result1245
				p.pretty_term(unwrapped1246)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1251 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1251 != nil {
		p.write(*flat1251)
		return nil
	} else {
		fields1250 := msg
		p.write("#")
		p.pretty_raw_value(fields1250)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1258 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1258 != nil {
		p.write(*flat1258)
		return nil
	} else {
		_dollar_dollar := msg
		fields1252 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1253 := fields1252
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1254 := unwrapped_fields1253[0].(string)
		p.pretty_name(field1254)
		field1255 := unwrapped_fields1253[1].([]*pb.RelTerm)
		if !(len(field1255) == 0) {
			p.newline()
			for i1257, elem1256 := range field1255 {
				if (i1257 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1256)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1263 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1263 != nil {
		p.write(*flat1263)
		return nil
	} else {
		_dollar_dollar := msg
		fields1259 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1260 := fields1259
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1261 := unwrapped_fields1260[0].(*pb.Term)
		p.pretty_term(field1261)
		p.newline()
		field1262 := unwrapped_fields1260[1].(*pb.Term)
		p.pretty_term(field1262)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1267 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1267 != nil {
		p.write(*flat1267)
		return nil
	} else {
		fields1264 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1264) == 0) {
			p.newline()
			for i1266, elem1265 := range fields1264 {
				if (i1266 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1265)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1274 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1274 != nil {
		p.write(*flat1274)
		return nil
	} else {
		_dollar_dollar := msg
		fields1268 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1269 := fields1268
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1270 := unwrapped_fields1269[0].(string)
		p.pretty_name(field1270)
		field1271 := unwrapped_fields1269[1].([]*pb.Value)
		if !(len(field1271) == 0) {
			p.newline()
			for i1273, elem1272 := range field1271 {
				if (i1273 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1272)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1283 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1283 != nil {
		p.write(*flat1283)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1789 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1789 = _dollar_dollar.GetAttrs()
		}
		fields1275 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1789}
		unwrapped_fields1276 := fields1275
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1277 := unwrapped_fields1276[0].([]*pb.RelationId)
		if !(len(field1277) == 0) {
			p.newline()
			for i1279, elem1278 := range field1277 {
				if (i1279 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1278)
			}
		}
		p.newline()
		field1280 := unwrapped_fields1276[1].(*pb.Script)
		p.pretty_script(field1280)
		field1281 := unwrapped_fields1276[2].([]*pb.Attribute)
		if field1281 != nil {
			p.newline()
			opt_val1282 := field1281
			p.pretty_attrs(opt_val1282)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1288 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1288 != nil {
		p.write(*flat1288)
		return nil
	} else {
		_dollar_dollar := msg
		fields1284 := _dollar_dollar.GetConstructs()
		unwrapped_fields1285 := fields1284
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1285) == 0) {
			p.newline()
			for i1287, elem1286 := range unwrapped_fields1285 {
				if (i1287 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1286)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1293 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1293 != nil {
		p.write(*flat1293)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1790 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1790 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1291 := _t1790
		if deconstruct_result1291 != nil {
			unwrapped1292 := deconstruct_result1291
			p.pretty_loop(unwrapped1292)
		} else {
			_dollar_dollar := msg
			var _t1791 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1791 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1289 := _t1791
			if deconstruct_result1289 != nil {
				unwrapped1290 := deconstruct_result1289
				p.pretty_instruction(unwrapped1290)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1300 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1300 != nil {
		p.write(*flat1300)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1792 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1792 = _dollar_dollar.GetAttrs()
		}
		fields1294 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1792}
		unwrapped_fields1295 := fields1294
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1296 := unwrapped_fields1295[0].([]*pb.Instruction)
		p.pretty_init(field1296)
		p.newline()
		field1297 := unwrapped_fields1295[1].(*pb.Script)
		p.pretty_script(field1297)
		field1298 := unwrapped_fields1295[2].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1304 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1304 != nil {
		p.write(*flat1304)
		return nil
	} else {
		fields1301 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1301) == 0) {
			p.newline()
			for i1303, elem1302 := range fields1301 {
				if (i1303 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1302)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1315 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1315 != nil {
		p.write(*flat1315)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1793 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1793 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1313 := _t1793
		if deconstruct_result1313 != nil {
			unwrapped1314 := deconstruct_result1313
			p.pretty_assign(unwrapped1314)
		} else {
			_dollar_dollar := msg
			var _t1794 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1794 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1311 := _t1794
			if deconstruct_result1311 != nil {
				unwrapped1312 := deconstruct_result1311
				p.pretty_upsert(unwrapped1312)
			} else {
				_dollar_dollar := msg
				var _t1795 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1795 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1309 := _t1795
				if deconstruct_result1309 != nil {
					unwrapped1310 := deconstruct_result1309
					p.pretty_break(unwrapped1310)
				} else {
					_dollar_dollar := msg
					var _t1796 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1796 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1307 := _t1796
					if deconstruct_result1307 != nil {
						unwrapped1308 := deconstruct_result1307
						p.pretty_monoid_def(unwrapped1308)
					} else {
						_dollar_dollar := msg
						var _t1797 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1797 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1305 := _t1797
						if deconstruct_result1305 != nil {
							unwrapped1306 := deconstruct_result1305
							p.pretty_monus_def(unwrapped1306)
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
	flat1322 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1322 != nil {
		p.write(*flat1322)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1798 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1798 = _dollar_dollar.GetAttrs()
		}
		fields1316 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1798}
		unwrapped_fields1317 := fields1316
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1318 := unwrapped_fields1317[0].(*pb.RelationId)
		p.pretty_relation_id(field1318)
		p.newline()
		field1319 := unwrapped_fields1317[1].(*pb.Abstraction)
		p.pretty_abstraction(field1319)
		field1320 := unwrapped_fields1317[2].([]*pb.Attribute)
		if field1320 != nil {
			p.newline()
			opt_val1321 := field1320
			p.pretty_attrs(opt_val1321)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1329 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1329 != nil {
		p.write(*flat1329)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1799 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1799 = _dollar_dollar.GetAttrs()
		}
		fields1323 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1799}
		unwrapped_fields1324 := fields1323
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1325 := unwrapped_fields1324[0].(*pb.RelationId)
		p.pretty_relation_id(field1325)
		p.newline()
		field1326 := unwrapped_fields1324[1].([]interface{})
		p.pretty_abstraction_with_arity(field1326)
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

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1334 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1334 != nil {
		p.write(*flat1334)
		return nil
	} else {
		_dollar_dollar := msg
		_t1800 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1330 := []interface{}{_t1800, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1331 := fields1330
		p.write("(")
		p.indent()
		field1332 := unwrapped_fields1331[0].([]interface{})
		p.pretty_bindings(field1332)
		p.newline()
		field1333 := unwrapped_fields1331[1].(*pb.Formula)
		p.pretty_formula(field1333)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1341 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1341 != nil {
		p.write(*flat1341)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1801 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1801 = _dollar_dollar.GetAttrs()
		}
		fields1335 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1801}
		unwrapped_fields1336 := fields1335
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1337 := unwrapped_fields1336[0].(*pb.RelationId)
		p.pretty_relation_id(field1337)
		p.newline()
		field1338 := unwrapped_fields1336[1].(*pb.Abstraction)
		p.pretty_abstraction(field1338)
		field1339 := unwrapped_fields1336[2].([]*pb.Attribute)
		if field1339 != nil {
			p.newline()
			opt_val1340 := field1339
			p.pretty_attrs(opt_val1340)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1349 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1349 != nil {
		p.write(*flat1349)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1802 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1802 = _dollar_dollar.GetAttrs()
		}
		fields1342 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1802}
		unwrapped_fields1343 := fields1342
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1344 := unwrapped_fields1343[0].(*pb.Monoid)
		p.pretty_monoid(field1344)
		p.newline()
		field1345 := unwrapped_fields1343[1].(*pb.RelationId)
		p.pretty_relation_id(field1345)
		p.newline()
		field1346 := unwrapped_fields1343[2].([]interface{})
		p.pretty_abstraction_with_arity(field1346)
		field1347 := unwrapped_fields1343[3].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1358 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1358 != nil {
		p.write(*flat1358)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1803 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1803 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1356 := _t1803
		if deconstruct_result1356 != nil {
			unwrapped1357 := deconstruct_result1356
			p.pretty_or_monoid(unwrapped1357)
		} else {
			_dollar_dollar := msg
			var _t1804 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1804 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1354 := _t1804
			if deconstruct_result1354 != nil {
				unwrapped1355 := deconstruct_result1354
				p.pretty_min_monoid(unwrapped1355)
			} else {
				_dollar_dollar := msg
				var _t1805 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1805 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1352 := _t1805
				if deconstruct_result1352 != nil {
					unwrapped1353 := deconstruct_result1352
					p.pretty_max_monoid(unwrapped1353)
				} else {
					_dollar_dollar := msg
					var _t1806 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1806 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1350 := _t1806
					if deconstruct_result1350 != nil {
						unwrapped1351 := deconstruct_result1350
						p.pretty_sum_monoid(unwrapped1351)
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
	fields1359 := msg
	_ = fields1359
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1362 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1362 != nil {
		p.write(*flat1362)
		return nil
	} else {
		_dollar_dollar := msg
		fields1360 := _dollar_dollar.GetType()
		unwrapped_fields1361 := fields1360
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1361)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1365 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1365 != nil {
		p.write(*flat1365)
		return nil
	} else {
		_dollar_dollar := msg
		fields1363 := _dollar_dollar.GetType()
		unwrapped_fields1364 := fields1363
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1364)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1368 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1368 != nil {
		p.write(*flat1368)
		return nil
	} else {
		_dollar_dollar := msg
		fields1366 := _dollar_dollar.GetType()
		unwrapped_fields1367 := fields1366
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1367)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1376 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1376 != nil {
		p.write(*flat1376)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1807 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1807 = _dollar_dollar.GetAttrs()
		}
		fields1369 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1807}
		unwrapped_fields1370 := fields1369
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1371 := unwrapped_fields1370[0].(*pb.Monoid)
		p.pretty_monoid(field1371)
		p.newline()
		field1372 := unwrapped_fields1370[1].(*pb.RelationId)
		p.pretty_relation_id(field1372)
		p.newline()
		field1373 := unwrapped_fields1370[2].([]interface{})
		p.pretty_abstraction_with_arity(field1373)
		field1374 := unwrapped_fields1370[3].([]*pb.Attribute)
		if field1374 != nil {
			p.newline()
			opt_val1375 := field1374
			p.pretty_attrs(opt_val1375)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1383 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1383 != nil {
		p.write(*flat1383)
		return nil
	} else {
		_dollar_dollar := msg
		fields1377 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1378 := fields1377
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1379 := unwrapped_fields1378[0].(*pb.RelationId)
		p.pretty_relation_id(field1379)
		p.newline()
		field1380 := unwrapped_fields1378[1].(*pb.Abstraction)
		p.pretty_abstraction(field1380)
		p.newline()
		field1381 := unwrapped_fields1378[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1381)
		p.newline()
		field1382 := unwrapped_fields1378[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1382)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1387 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1387 != nil {
		p.write(*flat1387)
		return nil
	} else {
		fields1384 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1384) == 0) {
			p.newline()
			for i1386, elem1385 := range fields1384 {
				if (i1386 > 0) {
					p.newline()
				}
				p.pretty_var(elem1385)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1391 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1391 != nil {
		p.write(*flat1391)
		return nil
	} else {
		fields1388 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1388) == 0) {
			p.newline()
			for i1390, elem1389 := range fields1388 {
				if (i1390 > 0) {
					p.newline()
				}
				p.pretty_var(elem1389)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1400 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1400 != nil {
		p.write(*flat1400)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1808 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1808 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1398 := _t1808
		if deconstruct_result1398 != nil {
			unwrapped1399 := deconstruct_result1398
			p.pretty_edb(unwrapped1399)
		} else {
			_dollar_dollar := msg
			var _t1809 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1809 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1396 := _t1809
			if deconstruct_result1396 != nil {
				unwrapped1397 := deconstruct_result1396
				p.pretty_betree_relation(unwrapped1397)
			} else {
				_dollar_dollar := msg
				var _t1810 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1810 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1394 := _t1810
				if deconstruct_result1394 != nil {
					unwrapped1395 := deconstruct_result1394
					p.pretty_csv_data(unwrapped1395)
				} else {
					_dollar_dollar := msg
					var _t1811 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1811 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1392 := _t1811
					if deconstruct_result1392 != nil {
						unwrapped1393 := deconstruct_result1392
						p.pretty_iceberg_data(unwrapped1393)
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
	flat1406 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1406 != nil {
		p.write(*flat1406)
		return nil
	} else {
		_dollar_dollar := msg
		fields1401 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1402 := fields1401
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1403 := unwrapped_fields1402[0].(*pb.RelationId)
		p.pretty_relation_id(field1403)
		p.newline()
		field1404 := unwrapped_fields1402[1].([]string)
		p.pretty_edb_path(field1404)
		p.newline()
		field1405 := unwrapped_fields1402[2].([]*pb.Type)
		p.pretty_edb_types(field1405)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1410 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1410 != nil {
		p.write(*flat1410)
		return nil
	} else {
		fields1407 := msg
		p.write("[")
		p.indent()
		for i1409, elem1408 := range fields1407 {
			if (i1409 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1408))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1414 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1414 != nil {
		p.write(*flat1414)
		return nil
	} else {
		fields1411 := msg
		p.write("[")
		p.indent()
		for i1413, elem1412 := range fields1411 {
			if (i1413 > 0) {
				p.newline()
			}
			p.pretty_type(elem1412)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1419 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1419 != nil {
		p.write(*flat1419)
		return nil
	} else {
		_dollar_dollar := msg
		fields1415 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1416 := fields1415
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1417 := unwrapped_fields1416[0].(*pb.RelationId)
		p.pretty_relation_id(field1417)
		p.newline()
		field1418 := unwrapped_fields1416[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1418)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1425 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1425 != nil {
		p.write(*flat1425)
		return nil
	} else {
		_dollar_dollar := msg
		_t1812 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1420 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1812}
		unwrapped_fields1421 := fields1420
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1422 := unwrapped_fields1421[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1422)
		p.newline()
		field1423 := unwrapped_fields1421[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1423)
		p.newline()
		field1424 := unwrapped_fields1421[2].([][]interface{})
		p.pretty_config_dict(field1424)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1429 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1429 != nil {
		p.write(*flat1429)
		return nil
	} else {
		fields1426 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1426) == 0) {
			p.newline()
			for i1428, elem1427 := range fields1426 {
				if (i1428 > 0) {
					p.newline()
				}
				p.pretty_type(elem1427)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1433 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1433 != nil {
		p.write(*flat1433)
		return nil
	} else {
		fields1430 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1430) == 0) {
			p.newline()
			for i1432, elem1431 := range fields1430 {
				if (i1432 > 0) {
					p.newline()
				}
				p.pretty_type(elem1431)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1443 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1443 != nil {
		p.write(*flat1443)
		return nil
	} else {
		_dollar_dollar := msg
		_t1813 := p.deconstruct_csv_data_columns_optional(_dollar_dollar)
		_t1814 := p.deconstruct_csv_data_relations_optional(_dollar_dollar)
		fields1434 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _t1813, _t1814, _dollar_dollar.GetAsof()}
		unwrapped_fields1435 := fields1434
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1436 := unwrapped_fields1435[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1436)
		p.newline()
		field1437 := unwrapped_fields1435[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1437)
		field1438 := unwrapped_fields1435[2].([]*pb.GNFColumn)
		if field1438 != nil {
			p.newline()
			opt_val1439 := field1438
			p.pretty_gnf_columns(opt_val1439)
		}
		field1440 := unwrapped_fields1435[3].(*pb.TargetRelations)
		if field1440 != nil {
			p.newline()
			opt_val1441 := field1440
			p.pretty_target_relations(opt_val1441)
		}
		p.newline()
		field1442 := unwrapped_fields1435[4].(string)
		p.pretty_csv_asof(field1442)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1450 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1450 != nil {
		p.write(*flat1450)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1815 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1815 = _dollar_dollar.GetPaths()
		}
		var _t1816 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1816 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1444 := []interface{}{_t1815, _t1816}
		unwrapped_fields1445 := fields1444
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1446 := unwrapped_fields1445[0].([]string)
		if field1446 != nil {
			p.newline()
			opt_val1447 := field1446
			p.pretty_csv_locator_paths(opt_val1447)
		}
		field1448 := unwrapped_fields1445[1].(*string)
		if field1448 != nil {
			p.newline()
			opt_val1449 := *field1448
			p.pretty_csv_locator_inline_data(opt_val1449)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1454 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1454 != nil {
		p.write(*flat1454)
		return nil
	} else {
		fields1451 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1451) == 0) {
			p.newline()
			for i1453, elem1452 := range fields1451 {
				if (i1453 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1452))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1456 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1456 != nil {
		p.write(*flat1456)
		return nil
	} else {
		fields1455 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1455))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1462 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1462 != nil {
		p.write(*flat1462)
		return nil
	} else {
		_dollar_dollar := msg
		_t1817 := p.deconstruct_csv_config(_dollar_dollar)
		_t1818 := p.deconstruct_csv_storage_integration_optional(_dollar_dollar)
		fields1457 := []interface{}{_t1817, _t1818}
		unwrapped_fields1458 := fields1457
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		field1459 := unwrapped_fields1458[0].([][]interface{})
		p.pretty_config_dict(field1459)
		field1460 := unwrapped_fields1458[1].([][]interface{})
		if field1460 != nil {
			p.newline()
			opt_val1461 := field1460
			p.pretty__storage_integration(opt_val1461)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty__storage_integration(msg [][]interface{}) interface{} {
	flat1464 := p.tryFlat(msg, func() { p.pretty__storage_integration(msg) })
	if flat1464 != nil {
		p.write(*flat1464)
		return nil
	} else {
		fields1463 := msg
		p.write("(")
		p.write("storage_integration")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(fields1463)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1468 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1468 != nil {
		p.write(*flat1468)
		return nil
	} else {
		fields1465 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1465) == 0) {
			p.newline()
			for i1467, elem1466 := range fields1465 {
				if (i1467 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1466)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1477 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1477 != nil {
		p.write(*flat1477)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1819 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1819 = _dollar_dollar.GetTargetId()
		}
		fields1469 := []interface{}{_dollar_dollar.GetColumnPath(), _t1819, _dollar_dollar.GetTypes()}
		unwrapped_fields1470 := fields1469
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1471 := unwrapped_fields1470[0].([]string)
		p.pretty_gnf_column_path(field1471)
		field1472 := unwrapped_fields1470[1].(*pb.RelationId)
		if field1472 != nil {
			p.newline()
			opt_val1473 := field1472
			p.pretty_relation_id(opt_val1473)
		}
		p.newline()
		p.write("[")
		field1474 := unwrapped_fields1470[2].([]*pb.Type)
		for i1476, elem1475 := range field1474 {
			if (i1476 > 0) {
				p.newline()
			}
			p.pretty_type(elem1475)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1484 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1484 != nil {
		p.write(*flat1484)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1820 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1820 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1482 := _t1820
		if deconstruct_result1482 != nil {
			unwrapped1483 := *deconstruct_result1482
			p.write(p.formatStringValue(unwrapped1483))
		} else {
			_dollar_dollar := msg
			var _t1821 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1821 = _dollar_dollar
			}
			deconstruct_result1478 := _t1821
			if deconstruct_result1478 != nil {
				unwrapped1479 := deconstruct_result1478
				p.write("[")
				p.indent()
				for i1481, elem1480 := range unwrapped1479 {
					if (i1481 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1480))
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
	flat1489 := p.tryFlat(msg, func() { p.pretty_target_relations(msg) })
	if flat1489 != nil {
		p.write(*flat1489)
		return nil
	} else {
		_dollar_dollar := msg
		fields1485 := []interface{}{_dollar_dollar.GetKeys(), _dollar_dollar}
		unwrapped_fields1486 := fields1485
		p.write("(")
		p.write("relations")
		p.indentSexp()
		p.newline()
		field1487 := unwrapped_fields1486[0].([]*pb.NamedColumn)
		p.pretty_relation_keys(field1487)
		p.newline()
		field1488 := unwrapped_fields1486[1].(*pb.TargetRelations)
		p.pretty_relation_body(field1488)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_keys(msg []*pb.NamedColumn) interface{} {
	flat1493 := p.tryFlat(msg, func() { p.pretty_relation_keys(msg) })
	if flat1493 != nil {
		p.write(*flat1493)
		return nil
	} else {
		fields1490 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1490) == 0) {
			p.newline()
			for i1492, elem1491 := range fields1490 {
				if (i1492 > 0) {
					p.newline()
				}
				p.pretty_named_column(elem1491)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_named_column(msg *pb.NamedColumn) interface{} {
	flat1498 := p.tryFlat(msg, func() { p.pretty_named_column(msg) })
	if flat1498 != nil {
		p.write(*flat1498)
		return nil
	} else {
		_dollar_dollar := msg
		fields1494 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetType()}
		unwrapped_fields1495 := fields1494
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1496 := unwrapped_fields1495[0].(string)
		p.write(p.formatStringValue(field1496))
		p.newline()
		field1497 := unwrapped_fields1495[1].(*pb.Type)
		p.pretty_type(field1497)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_body(msg *pb.TargetRelations) interface{} {
	flat1505 := p.tryFlat(msg, func() { p.pretty_relation_body(msg) })
	if flat1505 != nil {
		p.write(*flat1505)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1822 []*pb.TargetRelation
		if hasProtoField(_dollar_dollar, "plain") {
			_t1822 = _dollar_dollar.GetPlain().GetTargets()
		}
		deconstruct_result1503 := _t1822
		if deconstruct_result1503 != nil {
			unwrapped1504 := deconstruct_result1503
			p.pretty_non_cdc_relations(unwrapped1504)
		} else {
			_dollar_dollar := msg
			var _t1823 []interface{}
			if hasProtoField(_dollar_dollar, "cdc") {
				_t1823 = []interface{}{_dollar_dollar.GetCdc().GetInserts(), _dollar_dollar.GetCdc().GetDeletes()}
			}
			deconstruct_result1499 := _t1823
			if deconstruct_result1499 != nil {
				unwrapped1500 := deconstruct_result1499
				field1501 := unwrapped1500[0].([]*pb.TargetRelation)
				p.pretty_cdc_inserts(field1501)
				p.write(" ")
				field1502 := unwrapped1500[1].([]*pb.TargetRelation)
				p.pretty_cdc_deletes(field1502)
			} else {
				panic(ParseError{msg: "No matching rule for relation_body"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_non_cdc_relations(msg []*pb.TargetRelation) interface{} {
	flat1509 := p.tryFlat(msg, func() { p.pretty_non_cdc_relations(msg) })
	if flat1509 != nil {
		p.write(*flat1509)
		return nil
	} else {
		fields1506 := msg
		for i1508, elem1507 := range fields1506 {
			if (i1508 > 0) {
				p.newline()
			}
			p.pretty_target_relation(elem1507)
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_target_relation(msg *pb.TargetRelation) interface{} {
	flat1516 := p.tryFlat(msg, func() { p.pretty_target_relation(msg) })
	if flat1516 != nil {
		p.write(*flat1516)
		return nil
	} else {
		_dollar_dollar := msg
		fields1510 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetValues()}
		unwrapped_fields1511 := fields1510
		p.write("(")
		p.write("relation")
		p.indentSexp()
		p.newline()
		field1512 := unwrapped_fields1511[0].(*pb.RelationId)
		p.pretty_relation_id(field1512)
		field1513 := unwrapped_fields1511[1].([]*pb.NamedColumn)
		if !(len(field1513) == 0) {
			p.newline()
			for i1515, elem1514 := range field1513 {
				if (i1515 > 0) {
					p.newline()
				}
				p.pretty_named_column(elem1514)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_inserts(msg []*pb.TargetRelation) interface{} {
	flat1520 := p.tryFlat(msg, func() { p.pretty_cdc_inserts(msg) })
	if flat1520 != nil {
		p.write(*flat1520)
		return nil
	} else {
		fields1517 := msg
		p.write("(")
		p.write("inserts")
		p.indentSexp()
		if !(len(fields1517) == 0) {
			p.newline()
			for i1519, elem1518 := range fields1517 {
				if (i1519 > 0) {
					p.newline()
				}
				p.pretty_target_relation(elem1518)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cdc_deletes(msg []*pb.TargetRelation) interface{} {
	flat1524 := p.tryFlat(msg, func() { p.pretty_cdc_deletes(msg) })
	if flat1524 != nil {
		p.write(*flat1524)
		return nil
	} else {
		fields1521 := msg
		p.write("(")
		p.write("deletes")
		p.indentSexp()
		if !(len(fields1521) == 0) {
			p.newline()
			for i1523, elem1522 := range fields1521 {
				if (i1523 > 0) {
					p.newline()
				}
				p.pretty_target_relation(elem1522)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1526 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1526 != nil {
		p.write(*flat1526)
		return nil
	} else {
		fields1525 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1525))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1537 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1537 != nil {
		p.write(*flat1537)
		return nil
	} else {
		_dollar_dollar := msg
		_t1824 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1825 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1527 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1824, _t1825, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1528 := fields1527
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1529 := unwrapped_fields1528[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1529)
		p.newline()
		field1530 := unwrapped_fields1528[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1530)
		p.newline()
		field1531 := unwrapped_fields1528[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1531)
		field1532 := unwrapped_fields1528[3].(*string)
		if field1532 != nil {
			p.newline()
			opt_val1533 := *field1532
			p.pretty_iceberg_from_snapshot(opt_val1533)
		}
		field1534 := unwrapped_fields1528[4].(*string)
		if field1534 != nil {
			p.newline()
			opt_val1535 := *field1534
			p.pretty_iceberg_to_snapshot(opt_val1535)
		}
		p.newline()
		field1536 := unwrapped_fields1528[5].(bool)
		p.pretty_boolean_value(field1536)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1543 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1543 != nil {
		p.write(*flat1543)
		return nil
	} else {
		_dollar_dollar := msg
		fields1538 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1539 := fields1538
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1540 := unwrapped_fields1539[0].(string)
		p.pretty_iceberg_locator_table_name(field1540)
		p.newline()
		field1541 := unwrapped_fields1539[1].([]string)
		p.pretty_iceberg_locator_namespace(field1541)
		p.newline()
		field1542 := unwrapped_fields1539[2].(string)
		p.pretty_iceberg_locator_warehouse(field1542)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1545 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1545 != nil {
		p.write(*flat1545)
		return nil
	} else {
		fields1544 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1544))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1549 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1549 != nil {
		p.write(*flat1549)
		return nil
	} else {
		fields1546 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1546) == 0) {
			p.newline()
			for i1548, elem1547 := range fields1546 {
				if (i1548 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1547))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1551 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1551 != nil {
		p.write(*flat1551)
		return nil
	} else {
		fields1550 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1550))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1559 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1559 != nil {
		p.write(*flat1559)
		return nil
	} else {
		_dollar_dollar := msg
		_t1826 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1552 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1826, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1553 := fields1552
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1554 := unwrapped_fields1553[0].(string)
		p.pretty_iceberg_catalog_uri(field1554)
		field1555 := unwrapped_fields1553[1].(*string)
		if field1555 != nil {
			p.newline()
			opt_val1556 := *field1555
			p.pretty_iceberg_catalog_config_scope(opt_val1556)
		}
		p.newline()
		field1557 := unwrapped_fields1553[2].([][]interface{})
		p.pretty_iceberg_properties(field1557)
		p.newline()
		field1558 := unwrapped_fields1553[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1558)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1561 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1561 != nil {
		p.write(*flat1561)
		return nil
	} else {
		fields1560 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1560))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1563 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1563 != nil {
		p.write(*flat1563)
		return nil
	} else {
		fields1562 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1562))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1567 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1567 != nil {
		p.write(*flat1567)
		return nil
	} else {
		fields1564 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1564) == 0) {
			p.newline()
			for i1566, elem1565 := range fields1564 {
				if (i1566 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1565)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1572 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1572 != nil {
		p.write(*flat1572)
		return nil
	} else {
		_dollar_dollar := msg
		fields1568 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1569 := fields1568
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1570 := unwrapped_fields1569[0].(string)
		p.write(p.formatStringValue(field1570))
		p.newline()
		field1571 := unwrapped_fields1569[1].(string)
		p.write(p.formatStringValue(field1571))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1576 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1576 != nil {
		p.write(*flat1576)
		return nil
	} else {
		fields1573 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1573) == 0) {
			p.newline()
			for i1575, elem1574 := range fields1573 {
				if (i1575 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1574)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1581 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1581 != nil {
		p.write(*flat1581)
		return nil
	} else {
		_dollar_dollar := msg
		_t1827 := p.mask_secret_value(_dollar_dollar)
		fields1577 := []interface{}{_dollar_dollar[0].(string), _t1827}
		unwrapped_fields1578 := fields1577
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1579 := unwrapped_fields1578[0].(string)
		p.write(p.formatStringValue(field1579))
		p.newline()
		field1580 := unwrapped_fields1578[1].(string)
		p.write(p.formatStringValue(field1580))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1583 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1583 != nil {
		p.write(*flat1583)
		return nil
	} else {
		fields1582 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1582))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1585 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1585 != nil {
		p.write(*flat1585)
		return nil
	} else {
		fields1584 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1584))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1588 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1588 != nil {
		p.write(*flat1588)
		return nil
	} else {
		_dollar_dollar := msg
		fields1586 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1587 := fields1586
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1587)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1593 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1593 != nil {
		p.write(*flat1593)
		return nil
	} else {
		_dollar_dollar := msg
		fields1589 := _dollar_dollar.GetRelations()
		unwrapped_fields1590 := fields1589
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1590) == 0) {
			p.newline()
			for i1592, elem1591 := range unwrapped_fields1590 {
				if (i1592 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1591)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1600 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1600 != nil {
		p.write(*flat1600)
		return nil
	} else {
		_dollar_dollar := msg
		fields1594 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1595 := fields1594
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1596 := unwrapped_fields1595[0].([]string)
		p.pretty_edb_path(field1596)
		field1597 := unwrapped_fields1595[1].([]*pb.SnapshotMapping)
		if !(len(field1597) == 0) {
			p.newline()
			for i1599, elem1598 := range field1597 {
				if (i1599 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1598)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1605 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1605 != nil {
		p.write(*flat1605)
		return nil
	} else {
		_dollar_dollar := msg
		fields1601 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1602 := fields1601
		field1603 := unwrapped_fields1602[0].([]string)
		p.pretty_edb_path(field1603)
		p.write(" ")
		field1604 := unwrapped_fields1602[1].(*pb.RelationId)
		p.pretty_relation_id(field1604)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1609 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1609 != nil {
		p.write(*flat1609)
		return nil
	} else {
		fields1606 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1606) == 0) {
			p.newline()
			for i1608, elem1607 := range fields1606 {
				if (i1608 > 0) {
					p.newline()
				}
				p.pretty_read(elem1607)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1620 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1620 != nil {
		p.write(*flat1620)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1828 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1828 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1618 := _t1828
		if deconstruct_result1618 != nil {
			unwrapped1619 := deconstruct_result1618
			p.pretty_demand(unwrapped1619)
		} else {
			_dollar_dollar := msg
			var _t1829 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1829 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1616 := _t1829
			if deconstruct_result1616 != nil {
				unwrapped1617 := deconstruct_result1616
				p.pretty_output(unwrapped1617)
			} else {
				_dollar_dollar := msg
				var _t1830 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1830 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1614 := _t1830
				if deconstruct_result1614 != nil {
					unwrapped1615 := deconstruct_result1614
					p.pretty_what_if(unwrapped1615)
				} else {
					_dollar_dollar := msg
					var _t1831 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1831 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1612 := _t1831
					if deconstruct_result1612 != nil {
						unwrapped1613 := deconstruct_result1612
						p.pretty_abort(unwrapped1613)
					} else {
						_dollar_dollar := msg
						var _t1832 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1832 = _dollar_dollar.GetExport()
						}
						deconstruct_result1610 := _t1832
						if deconstruct_result1610 != nil {
							unwrapped1611 := deconstruct_result1610
							p.pretty_export(unwrapped1611)
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
	flat1623 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1623 != nil {
		p.write(*flat1623)
		return nil
	} else {
		_dollar_dollar := msg
		fields1621 := _dollar_dollar.GetRelationId()
		unwrapped_fields1622 := fields1621
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1622)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1628 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1628 != nil {
		p.write(*flat1628)
		return nil
	} else {
		_dollar_dollar := msg
		fields1624 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1625 := fields1624
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1626 := unwrapped_fields1625[0].(string)
		p.pretty_name(field1626)
		p.newline()
		field1627 := unwrapped_fields1625[1].(*pb.RelationId)
		p.pretty_relation_id(field1627)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1633 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1633 != nil {
		p.write(*flat1633)
		return nil
	} else {
		_dollar_dollar := msg
		fields1629 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1630 := fields1629
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1631 := unwrapped_fields1630[0].(string)
		p.pretty_name(field1631)
		p.newline()
		field1632 := unwrapped_fields1630[1].(*pb.Epoch)
		p.pretty_epoch(field1632)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1639 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1639 != nil {
		p.write(*flat1639)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1833 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1833 = ptr(_dollar_dollar.GetName())
		}
		fields1634 := []interface{}{_t1833, _dollar_dollar.GetRelationId()}
		unwrapped_fields1635 := fields1634
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1636 := unwrapped_fields1635[0].(*string)
		if field1636 != nil {
			p.newline()
			opt_val1637 := *field1636
			p.pretty_name(opt_val1637)
		}
		p.newline()
		field1638 := unwrapped_fields1635[1].(*pb.RelationId)
		p.pretty_relation_id(field1638)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1644 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1644 != nil {
		p.write(*flat1644)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1834 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1834 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1642 := _t1834
		if deconstruct_result1642 != nil {
			unwrapped1643 := deconstruct_result1642
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1643)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1835 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1835 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1640 := _t1835
			if deconstruct_result1640 != nil {
				unwrapped1641 := deconstruct_result1640
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1641)
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
	flat1655 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1655 != nil {
		p.write(*flat1655)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1836 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1837 := p.deconstruct_export_csv_output_location(_dollar_dollar)
			_t1836 = []interface{}{_t1837, _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1650 := _t1836
		if deconstruct_result1650 != nil {
			unwrapped1651 := deconstruct_result1650
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1652 := unwrapped1651[0].([]interface{})
			p.pretty_export_csv_output_location(field1652)
			p.newline()
			field1653 := unwrapped1651[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1653)
			p.newline()
			field1654 := unwrapped1651[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1654)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1838 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1839 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1838 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1839}
			}
			deconstruct_result1645 := _t1838
			if deconstruct_result1645 != nil {
				unwrapped1646 := deconstruct_result1645
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1647 := unwrapped1646[0].(string)
				p.pretty_export_csv_path(field1647)
				p.newline()
				field1648 := unwrapped1646[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1648)
				p.newline()
				field1649 := unwrapped1646[2].([][]interface{})
				p.pretty_config_dict(field1649)
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
	flat1660 := p.tryFlat(msg, func() { p.pretty_export_csv_output_location(msg) })
	if flat1660 != nil {
		p.write(*flat1660)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1840 *string
		if _dollar_dollar[0].(string) != "" {
			_t1840 = ptr(_dollar_dollar[0].(string))
		}
		deconstruct_result1658 := _t1840
		if deconstruct_result1658 != nil {
			unwrapped1659 := *deconstruct_result1658
			p.write("(")
			p.write("path")
			p.indentSexp()
			p.newline()
			p.write(p.formatStringValue(unwrapped1659))
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1841 *string
			if _dollar_dollar[1].(string) != "" {
				_t1841 = ptr(_dollar_dollar[1].(string))
			}
			deconstruct_result1656 := _t1841
			if deconstruct_result1656 != nil {
				unwrapped1657 := *deconstruct_result1656
				p.write("(")
				p.write("transaction_output_name")
				p.indentSexp()
				p.newline()
				p.pretty_name(unwrapped1657)
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
	flat1667 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1667 != nil {
		p.write(*flat1667)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1842 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1842 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1663 := _t1842
		if deconstruct_result1663 != nil {
			unwrapped1664 := deconstruct_result1663
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1664) == 0) {
				p.newline()
				for i1666, elem1665 := range unwrapped1664 {
					if (i1666 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1665)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1843 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1843 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1661 := _t1843
			if deconstruct_result1661 != nil {
				unwrapped1662 := deconstruct_result1661
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1662)
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
	flat1672 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1672 != nil {
		p.write(*flat1672)
		return nil
	} else {
		_dollar_dollar := msg
		fields1668 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1669 := fields1668
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1670 := unwrapped_fields1669[0].(string)
		p.write(p.formatStringValue(field1670))
		p.newline()
		field1671 := unwrapped_fields1669[1].(*pb.RelationId)
		p.pretty_relation_id(field1671)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1674 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1674 != nil {
		p.write(*flat1674)
		return nil
	} else {
		fields1673 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1673))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1678 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1678 != nil {
		p.write(*flat1678)
		return nil
	} else {
		fields1675 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1675) == 0) {
			p.newline()
			for i1677, elem1676 := range fields1675 {
				if (i1677 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1676)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1687 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1687 != nil {
		p.write(*flat1687)
		return nil
	} else {
		_dollar_dollar := msg
		_t1844 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1679 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1844}
		unwrapped_fields1680 := fields1679
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1681 := unwrapped_fields1680[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1681)
		p.newline()
		field1682 := unwrapped_fields1680[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1682)
		p.newline()
		field1683 := unwrapped_fields1680[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1683)
		p.newline()
		field1684 := unwrapped_fields1680[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1684)
		field1685 := unwrapped_fields1680[4].([][]interface{})
		if field1685 != nil {
			p.newline()
			opt_val1686 := field1685
			p.pretty_config_dict(opt_val1686)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1689 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1689 != nil {
		p.write(*flat1689)
		return nil
	} else {
		fields1688 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1688)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1693 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1693 != nil {
		p.write(*flat1693)
		return nil
	} else {
		fields1690 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1690) == 0) {
			p.newline()
			for i1692, elem1691 := range fields1690 {
				if (i1692 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1691)
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
		_t1900 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1900)
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

func (p *PrettyPrinter) pretty_ast_size_limit(msg *pb.ASTSizeLimit) interface{} {
	p.write("(ast_size_limit")
	p.indentSexp()
	p.newline()
	p.write(":warning_limit ")
	p.write(fmt.Sprintf("%d", msg.GetWarningLimit()))
	p.newline()
	p.write(":exception_limit ")
	p.write(fmt.Sprintf("%d", msg.GetExceptionLimit()))
	p.write(")")
	p.dedent()
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
	case []*pb.NamedColumn:
		p.pretty_relation_keys(m)
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
	case *pb.ASTSizeLimit:
		p.pretty_ast_size_limit(m)
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
