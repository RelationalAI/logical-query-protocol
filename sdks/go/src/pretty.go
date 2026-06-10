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

func (p *PrettyPrinter) _make_value_int32(v int32) *pb.Value {
	_t1742 := &pb.Value{}
	_t1742.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1742
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1743 := &pb.Value{}
	_t1743.Value = &pb.Value_IntValue{IntValue: v}
	return _t1743
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1744 := &pb.Value{}
	_t1744.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1744
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1745 := &pb.Value{}
	_t1745.Value = &pb.Value_StringValue{StringValue: v}
	return _t1745
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1746 := &pb.Value{}
	_t1746.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1746
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1747 := &pb.Value{}
	_t1747.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1747
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1748 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1748})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1749 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1749})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1750 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1750})
			}
		}
	}
	_t1751 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1751})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1752 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1752})
	_t1753 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1753})
	if msg.GetNewLine() != "" {
		_t1754 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1754})
	}
	_t1755 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1755})
	_t1756 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1756})
	_t1757 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1757})
	if msg.GetComment() != "" {
		_t1758 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1758})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1759 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1759})
	}
	_t1760 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1760})
	_t1761 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1761})
	_t1762 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1762})
	if msg.GetPartitionSizeMb() != 0 {
		_t1763 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1763})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_storage_integration_optional(msg *pb.CSVConfig) [][]interface{} {
	var _t1764 interface{}
	if !(hasProtoField(msg, "storage_integration")) {
		return nil
	}
	_ = _t1764
	si := msg.GetStorageIntegration()
	result := [][]interface{}{}
	if si.GetProvider() != "" {
		_t1765 := p._make_value_string(si.GetProvider())
		result = append(result, []interface{}{"provider", _t1765})
	}
	if si.GetAzureSasToken() != "" {
		_t1766 := p._make_value_string("***")
		result = append(result, []interface{}{"azure_sas_token", _t1766})
	}
	if si.GetS3Region() != "" {
		_t1767 := p._make_value_string(si.GetS3Region())
		result = append(result, []interface{}{"s3_region", _t1767})
	}
	if si.GetS3AccessKeyId() != "" {
		_t1768 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_access_key_id", _t1768})
	}
	if si.GetS3SecretAccessKey() != "" {
		_t1769 := p._make_value_string("***")
		result = append(result, []interface{}{"s3_secret_access_key", _t1769})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1770 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1770})
	_t1771 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1771})
	_t1772 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1772})
	_t1773 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1773})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1774 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1774})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1775 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1775})
		}
	}
	_t1776 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1776})
	_t1777 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1777})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1778 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1778})
	}
	if msg.Compression != nil {
		_t1779 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1779})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1780 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1780})
	}
	if msg.SyntaxMissingString != nil {
		_t1781 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1781})
	}
	if msg.SyntaxDelim != nil {
		_t1782 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1782})
	}
	if msg.SyntaxQuotechar != nil {
		_t1783 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1783})
	}
	if msg.SyntaxEscapechar != nil {
		_t1784 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1784})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1785 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1785
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1786 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1786
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1787 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1787
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1788 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1788})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1789 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1789})
	}
	if msg.GetCompression() != "" {
		_t1790 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1790})
	}
	var _t1791 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1791
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1792 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1792
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
	flat808 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat808 != nil {
		p.write(*flat808)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1598 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1598 = _dollar_dollar.GetConfigure()
		}
		var _t1599 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1599 = _dollar_dollar.GetSync()
		}
		fields799 := []interface{}{_t1598, _t1599, _dollar_dollar.GetEpochs()}
		unwrapped_fields800 := fields799
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field801 := unwrapped_fields800[0].(*pb.Configure)
		if field801 != nil {
			p.newline()
			opt_val802 := field801
			p.pretty_configure(opt_val802)
		}
		field803 := unwrapped_fields800[1].(*pb.Sync)
		if field803 != nil {
			p.newline()
			opt_val804 := field803
			p.pretty_sync(opt_val804)
		}
		field805 := unwrapped_fields800[2].([]*pb.Epoch)
		if !(len(field805) == 0) {
			p.newline()
			for i807, elem806 := range field805 {
				if (i807 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem806)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat811 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat811 != nil {
		p.write(*flat811)
		return nil
	} else {
		_dollar_dollar := msg
		_t1600 := p.deconstruct_configure(_dollar_dollar)
		fields809 := _t1600
		unwrapped_fields810 := fields809
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields810)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat815 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat815 != nil {
		p.write(*flat815)
		return nil
	} else {
		fields812 := msg
		p.write("{")
		p.indent()
		if !(len(fields812) == 0) {
			p.newline()
			for i814, elem813 := range fields812 {
				if (i814 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem813)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat820 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat820 != nil {
		p.write(*flat820)
		return nil
	} else {
		_dollar_dollar := msg
		fields816 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields817 := fields816
		p.write(":")
		field818 := unwrapped_fields817[0].(string)
		p.write(field818)
		p.write(" ")
		field819 := unwrapped_fields817[1].(*pb.Value)
		p.pretty_raw_value(field819)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat846 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat846 != nil {
		p.write(*flat846)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1601 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1601 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result844 := _t1601
		if deconstruct_result844 != nil {
			unwrapped845 := deconstruct_result844
			p.pretty_raw_date(unwrapped845)
		} else {
			_dollar_dollar := msg
			var _t1602 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1602 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result842 := _t1602
			if deconstruct_result842 != nil {
				unwrapped843 := deconstruct_result842
				p.pretty_raw_datetime(unwrapped843)
			} else {
				_dollar_dollar := msg
				var _t1603 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1603 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result840 := _t1603
				if deconstruct_result840 != nil {
					unwrapped841 := *deconstruct_result840
					p.write(p.formatStringValue(unwrapped841))
				} else {
					_dollar_dollar := msg
					var _t1604 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1604 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result838 := _t1604
					if deconstruct_result838 != nil {
						unwrapped839 := *deconstruct_result838
						p.write(fmt.Sprintf("%di32", unwrapped839))
					} else {
						_dollar_dollar := msg
						var _t1605 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1605 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result836 := _t1605
						if deconstruct_result836 != nil {
							unwrapped837 := *deconstruct_result836
							p.write(fmt.Sprintf("%d", unwrapped837))
						} else {
							_dollar_dollar := msg
							var _t1606 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1606 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result834 := _t1606
							if deconstruct_result834 != nil {
								unwrapped835 := *deconstruct_result834
								p.write(formatFloat32(unwrapped835))
							} else {
								_dollar_dollar := msg
								var _t1607 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1607 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result832 := _t1607
								if deconstruct_result832 != nil {
									unwrapped833 := *deconstruct_result832
									p.write(formatFloat64(unwrapped833))
								} else {
									_dollar_dollar := msg
									var _t1608 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1608 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result830 := _t1608
									if deconstruct_result830 != nil {
										unwrapped831 := *deconstruct_result830
										p.write(fmt.Sprintf("%du32", unwrapped831))
									} else {
										_dollar_dollar := msg
										var _t1609 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1609 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result828 := _t1609
										if deconstruct_result828 != nil {
											unwrapped829 := deconstruct_result828
											p.write(p.formatUint128(unwrapped829))
										} else {
											_dollar_dollar := msg
											var _t1610 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1610 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result826 := _t1610
											if deconstruct_result826 != nil {
												unwrapped827 := deconstruct_result826
												p.write(p.formatInt128(unwrapped827))
											} else {
												_dollar_dollar := msg
												var _t1611 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1611 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result824 := _t1611
												if deconstruct_result824 != nil {
													unwrapped825 := deconstruct_result824
													p.write(p.formatDecimal(unwrapped825))
												} else {
													_dollar_dollar := msg
													var _t1612 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1612 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result822 := _t1612
													if deconstruct_result822 != nil {
														unwrapped823 := *deconstruct_result822
														p.pretty_boolean_value(unwrapped823)
													} else {
														fields821 := msg
														_ = fields821
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
	flat852 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat852 != nil {
		p.write(*flat852)
		return nil
	} else {
		_dollar_dollar := msg
		fields847 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields848 := fields847
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field849 := unwrapped_fields848[0].(int64)
		p.write(fmt.Sprintf("%d", field849))
		p.newline()
		field850 := unwrapped_fields848[1].(int64)
		p.write(fmt.Sprintf("%d", field850))
		p.newline()
		field851 := unwrapped_fields848[2].(int64)
		p.write(fmt.Sprintf("%d", field851))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat863 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat863 != nil {
		p.write(*flat863)
		return nil
	} else {
		_dollar_dollar := msg
		fields853 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields854 := fields853
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field855 := unwrapped_fields854[0].(int64)
		p.write(fmt.Sprintf("%d", field855))
		p.newline()
		field856 := unwrapped_fields854[1].(int64)
		p.write(fmt.Sprintf("%d", field856))
		p.newline()
		field857 := unwrapped_fields854[2].(int64)
		p.write(fmt.Sprintf("%d", field857))
		p.newline()
		field858 := unwrapped_fields854[3].(int64)
		p.write(fmt.Sprintf("%d", field858))
		p.newline()
		field859 := unwrapped_fields854[4].(int64)
		p.write(fmt.Sprintf("%d", field859))
		p.newline()
		field860 := unwrapped_fields854[5].(int64)
		p.write(fmt.Sprintf("%d", field860))
		field861 := unwrapped_fields854[6].(*int64)
		if field861 != nil {
			p.newline()
			opt_val862 := *field861
			p.write(fmt.Sprintf("%d", opt_val862))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1613 []interface{}
	if _dollar_dollar {
		_t1613 = []interface{}{}
	}
	deconstruct_result866 := _t1613
	if deconstruct_result866 != nil {
		unwrapped867 := deconstruct_result866
		_ = unwrapped867
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1614 []interface{}
		if !(_dollar_dollar) {
			_t1614 = []interface{}{}
		}
		deconstruct_result864 := _t1614
		if deconstruct_result864 != nil {
			unwrapped865 := deconstruct_result864
			_ = unwrapped865
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat872 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat872 != nil {
		p.write(*flat872)
		return nil
	} else {
		_dollar_dollar := msg
		fields868 := _dollar_dollar.GetFragments()
		unwrapped_fields869 := fields868
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields869) == 0) {
			p.newline()
			for i871, elem870 := range unwrapped_fields869 {
				if (i871 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem870)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat875 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat875 != nil {
		p.write(*flat875)
		return nil
	} else {
		_dollar_dollar := msg
		fields873 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields874 := fields873
		p.write(":")
		p.write(unwrapped_fields874)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat882 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat882 != nil {
		p.write(*flat882)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1615 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1615 = _dollar_dollar.GetWrites()
		}
		var _t1616 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1616 = _dollar_dollar.GetReads()
		}
		fields876 := []interface{}{_t1615, _t1616}
		unwrapped_fields877 := fields876
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field878 := unwrapped_fields877[0].([]*pb.Write)
		if field878 != nil {
			p.newline()
			opt_val879 := field878
			p.pretty_epoch_writes(opt_val879)
		}
		field880 := unwrapped_fields877[1].([]*pb.Read)
		if field880 != nil {
			p.newline()
			opt_val881 := field880
			p.pretty_epoch_reads(opt_val881)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat886 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat886 != nil {
		p.write(*flat886)
		return nil
	} else {
		fields883 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields883) == 0) {
			p.newline()
			for i885, elem884 := range fields883 {
				if (i885 > 0) {
					p.newline()
				}
				p.pretty_write(elem884)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat895 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat895 != nil {
		p.write(*flat895)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1617 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1617 = _dollar_dollar.GetDefine()
		}
		deconstruct_result893 := _t1617
		if deconstruct_result893 != nil {
			unwrapped894 := deconstruct_result893
			p.pretty_define(unwrapped894)
		} else {
			_dollar_dollar := msg
			var _t1618 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1618 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result891 := _t1618
			if deconstruct_result891 != nil {
				unwrapped892 := deconstruct_result891
				p.pretty_undefine(unwrapped892)
			} else {
				_dollar_dollar := msg
				var _t1619 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1619 = _dollar_dollar.GetContext()
				}
				deconstruct_result889 := _t1619
				if deconstruct_result889 != nil {
					unwrapped890 := deconstruct_result889
					p.pretty_context(unwrapped890)
				} else {
					_dollar_dollar := msg
					var _t1620 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1620 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result887 := _t1620
					if deconstruct_result887 != nil {
						unwrapped888 := deconstruct_result887
						p.pretty_snapshot(unwrapped888)
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
	flat898 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat898 != nil {
		p.write(*flat898)
		return nil
	} else {
		_dollar_dollar := msg
		fields896 := _dollar_dollar.GetFragment()
		unwrapped_fields897 := fields896
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields897)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat905 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat905 != nil {
		p.write(*flat905)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields899 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields900 := fields899
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field901 := unwrapped_fields900[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field901)
		field902 := unwrapped_fields900[1].([]*pb.Declaration)
		if !(len(field902) == 0) {
			p.newline()
			for i904, elem903 := range field902 {
				if (i904 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem903)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat907 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat907 != nil {
		p.write(*flat907)
		return nil
	} else {
		fields906 := msg
		p.pretty_fragment_id(fields906)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat916 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat916 != nil {
		p.write(*flat916)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1621 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1621 = _dollar_dollar.GetDef()
		}
		deconstruct_result914 := _t1621
		if deconstruct_result914 != nil {
			unwrapped915 := deconstruct_result914
			p.pretty_def(unwrapped915)
		} else {
			_dollar_dollar := msg
			var _t1622 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1622 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result912 := _t1622
			if deconstruct_result912 != nil {
				unwrapped913 := deconstruct_result912
				p.pretty_algorithm(unwrapped913)
			} else {
				_dollar_dollar := msg
				var _t1623 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1623 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result910 := _t1623
				if deconstruct_result910 != nil {
					unwrapped911 := deconstruct_result910
					p.pretty_constraint(unwrapped911)
				} else {
					_dollar_dollar := msg
					var _t1624 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1624 = _dollar_dollar.GetData()
					}
					deconstruct_result908 := _t1624
					if deconstruct_result908 != nil {
						unwrapped909 := deconstruct_result908
						p.pretty_data(unwrapped909)
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
	flat923 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat923 != nil {
		p.write(*flat923)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1625 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1625 = _dollar_dollar.GetAttrs()
		}
		fields917 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1625}
		unwrapped_fields918 := fields917
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field919 := unwrapped_fields918[0].(*pb.RelationId)
		p.pretty_relation_id(field919)
		p.newline()
		field920 := unwrapped_fields918[1].(*pb.Abstraction)
		p.pretty_abstraction(field920)
		field921 := unwrapped_fields918[2].([]*pb.Attribute)
		if field921 != nil {
			p.newline()
			opt_val922 := field921
			p.pretty_attrs(opt_val922)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat928 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat928 != nil {
		p.write(*flat928)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1626 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1627 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1626 = ptr(_t1627)
		}
		deconstruct_result926 := _t1626
		if deconstruct_result926 != nil {
			unwrapped927 := *deconstruct_result926
			p.write(":")
			p.write(unwrapped927)
		} else {
			_dollar_dollar := msg
			_t1628 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result924 := _t1628
			if deconstruct_result924 != nil {
				unwrapped925 := deconstruct_result924
				p.write(p.formatUint128(unwrapped925))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat933 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat933 != nil {
		p.write(*flat933)
		return nil
	} else {
		_dollar_dollar := msg
		_t1629 := p.deconstruct_bindings(_dollar_dollar)
		fields929 := []interface{}{_t1629, _dollar_dollar.GetValue()}
		unwrapped_fields930 := fields929
		p.write("(")
		p.indent()
		field931 := unwrapped_fields930[0].([]interface{})
		p.pretty_bindings(field931)
		p.newline()
		field932 := unwrapped_fields930[1].(*pb.Formula)
		p.pretty_formula(field932)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat941 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat941 != nil {
		p.write(*flat941)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1630 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1630 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields934 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1630}
		unwrapped_fields935 := fields934
		p.write("[")
		p.indent()
		field936 := unwrapped_fields935[0].([]*pb.Binding)
		for i938, elem937 := range field936 {
			if (i938 > 0) {
				p.newline()
			}
			p.pretty_binding(elem937)
		}
		field939 := unwrapped_fields935[1].([]*pb.Binding)
		if field939 != nil {
			p.newline()
			opt_val940 := field939
			p.pretty_value_bindings(opt_val940)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat946 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat946 != nil {
		p.write(*flat946)
		return nil
	} else {
		_dollar_dollar := msg
		fields942 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields943 := fields942
		field944 := unwrapped_fields943[0].(string)
		p.write(field944)
		p.write("::")
		field945 := unwrapped_fields943[1].(*pb.Type)
		p.pretty_type(field945)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat975 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat975 != nil {
		p.write(*flat975)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1631 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1631 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result973 := _t1631
		if deconstruct_result973 != nil {
			unwrapped974 := deconstruct_result973
			p.pretty_unspecified_type(unwrapped974)
		} else {
			_dollar_dollar := msg
			var _t1632 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1632 = _dollar_dollar.GetStringType()
			}
			deconstruct_result971 := _t1632
			if deconstruct_result971 != nil {
				unwrapped972 := deconstruct_result971
				p.pretty_string_type(unwrapped972)
			} else {
				_dollar_dollar := msg
				var _t1633 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1633 = _dollar_dollar.GetIntType()
				}
				deconstruct_result969 := _t1633
				if deconstruct_result969 != nil {
					unwrapped970 := deconstruct_result969
					p.pretty_int_type(unwrapped970)
				} else {
					_dollar_dollar := msg
					var _t1634 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1634 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result967 := _t1634
					if deconstruct_result967 != nil {
						unwrapped968 := deconstruct_result967
						p.pretty_float_type(unwrapped968)
					} else {
						_dollar_dollar := msg
						var _t1635 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1635 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result965 := _t1635
						if deconstruct_result965 != nil {
							unwrapped966 := deconstruct_result965
							p.pretty_uint128_type(unwrapped966)
						} else {
							_dollar_dollar := msg
							var _t1636 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1636 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result963 := _t1636
							if deconstruct_result963 != nil {
								unwrapped964 := deconstruct_result963
								p.pretty_int128_type(unwrapped964)
							} else {
								_dollar_dollar := msg
								var _t1637 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1637 = _dollar_dollar.GetDateType()
								}
								deconstruct_result961 := _t1637
								if deconstruct_result961 != nil {
									unwrapped962 := deconstruct_result961
									p.pretty_date_type(unwrapped962)
								} else {
									_dollar_dollar := msg
									var _t1638 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1638 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result959 := _t1638
									if deconstruct_result959 != nil {
										unwrapped960 := deconstruct_result959
										p.pretty_datetime_type(unwrapped960)
									} else {
										_dollar_dollar := msg
										var _t1639 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1639 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result957 := _t1639
										if deconstruct_result957 != nil {
											unwrapped958 := deconstruct_result957
											p.pretty_missing_type(unwrapped958)
										} else {
											_dollar_dollar := msg
											var _t1640 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1640 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result955 := _t1640
											if deconstruct_result955 != nil {
												unwrapped956 := deconstruct_result955
												p.pretty_decimal_type(unwrapped956)
											} else {
												_dollar_dollar := msg
												var _t1641 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1641 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result953 := _t1641
												if deconstruct_result953 != nil {
													unwrapped954 := deconstruct_result953
													p.pretty_boolean_type(unwrapped954)
												} else {
													_dollar_dollar := msg
													var _t1642 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1642 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result951 := _t1642
													if deconstruct_result951 != nil {
														unwrapped952 := deconstruct_result951
														p.pretty_int32_type(unwrapped952)
													} else {
														_dollar_dollar := msg
														var _t1643 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1643 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result949 := _t1643
														if deconstruct_result949 != nil {
															unwrapped950 := deconstruct_result949
															p.pretty_float32_type(unwrapped950)
														} else {
															_dollar_dollar := msg
															var _t1644 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1644 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result947 := _t1644
															if deconstruct_result947 != nil {
																unwrapped948 := deconstruct_result947
																p.pretty_uint32_type(unwrapped948)
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
	fields976 := msg
	_ = fields976
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields977 := msg
	_ = fields977
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields978 := msg
	_ = fields978
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields979 := msg
	_ = fields979
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields980 := msg
	_ = fields980
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields981 := msg
	_ = fields981
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields982 := msg
	_ = fields982
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields983 := msg
	_ = fields983
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields984 := msg
	_ = fields984
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat989 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat989 != nil {
		p.write(*flat989)
		return nil
	} else {
		_dollar_dollar := msg
		fields985 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields986 := fields985
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field987 := unwrapped_fields986[0].(int64)
		p.write(fmt.Sprintf("%d", field987))
		p.newline()
		field988 := unwrapped_fields986[1].(int64)
		p.write(fmt.Sprintf("%d", field988))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields990 := msg
	_ = fields990
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields991 := msg
	_ = fields991
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields992 := msg
	_ = fields992
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields993 := msg
	_ = fields993
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat997 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat997 != nil {
		p.write(*flat997)
		return nil
	} else {
		fields994 := msg
		p.write("|")
		if !(len(fields994) == 0) {
			p.write(" ")
			for i996, elem995 := range fields994 {
				if (i996 > 0) {
					p.newline()
				}
				p.pretty_binding(elem995)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1024 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1024 != nil {
		p.write(*flat1024)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1645 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1645 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1022 := _t1645
		if deconstruct_result1022 != nil {
			unwrapped1023 := deconstruct_result1022
			p.pretty_true(unwrapped1023)
		} else {
			_dollar_dollar := msg
			var _t1646 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1646 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1020 := _t1646
			if deconstruct_result1020 != nil {
				unwrapped1021 := deconstruct_result1020
				p.pretty_false(unwrapped1021)
			} else {
				_dollar_dollar := msg
				var _t1647 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1647 = _dollar_dollar.GetExists()
				}
				deconstruct_result1018 := _t1647
				if deconstruct_result1018 != nil {
					unwrapped1019 := deconstruct_result1018
					p.pretty_exists(unwrapped1019)
				} else {
					_dollar_dollar := msg
					var _t1648 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1648 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1016 := _t1648
					if deconstruct_result1016 != nil {
						unwrapped1017 := deconstruct_result1016
						p.pretty_reduce(unwrapped1017)
					} else {
						_dollar_dollar := msg
						var _t1649 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1649 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1014 := _t1649
						if deconstruct_result1014 != nil {
							unwrapped1015 := deconstruct_result1014
							p.pretty_conjunction(unwrapped1015)
						} else {
							_dollar_dollar := msg
							var _t1650 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1650 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1012 := _t1650
							if deconstruct_result1012 != nil {
								unwrapped1013 := deconstruct_result1012
								p.pretty_disjunction(unwrapped1013)
							} else {
								_dollar_dollar := msg
								var _t1651 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1651 = _dollar_dollar.GetNot()
								}
								deconstruct_result1010 := _t1651
								if deconstruct_result1010 != nil {
									unwrapped1011 := deconstruct_result1010
									p.pretty_not(unwrapped1011)
								} else {
									_dollar_dollar := msg
									var _t1652 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1652 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1008 := _t1652
									if deconstruct_result1008 != nil {
										unwrapped1009 := deconstruct_result1008
										p.pretty_ffi(unwrapped1009)
									} else {
										_dollar_dollar := msg
										var _t1653 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1653 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1006 := _t1653
										if deconstruct_result1006 != nil {
											unwrapped1007 := deconstruct_result1006
											p.pretty_atom(unwrapped1007)
										} else {
											_dollar_dollar := msg
											var _t1654 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1654 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1004 := _t1654
											if deconstruct_result1004 != nil {
												unwrapped1005 := deconstruct_result1004
												p.pretty_pragma(unwrapped1005)
											} else {
												_dollar_dollar := msg
												var _t1655 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1655 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1002 := _t1655
												if deconstruct_result1002 != nil {
													unwrapped1003 := deconstruct_result1002
													p.pretty_primitive(unwrapped1003)
												} else {
													_dollar_dollar := msg
													var _t1656 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1656 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result1000 := _t1656
													if deconstruct_result1000 != nil {
														unwrapped1001 := deconstruct_result1000
														p.pretty_rel_atom(unwrapped1001)
													} else {
														_dollar_dollar := msg
														var _t1657 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1657 = _dollar_dollar.GetCast()
														}
														deconstruct_result998 := _t1657
														if deconstruct_result998 != nil {
															unwrapped999 := deconstruct_result998
															p.pretty_cast(unwrapped999)
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
	fields1025 := msg
	_ = fields1025
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1026 := msg
	_ = fields1026
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1031 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1031 != nil {
		p.write(*flat1031)
		return nil
	} else {
		_dollar_dollar := msg
		_t1658 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1027 := []interface{}{_t1658, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1028 := fields1027
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1029 := unwrapped_fields1028[0].([]interface{})
		p.pretty_bindings(field1029)
		p.newline()
		field1030 := unwrapped_fields1028[1].(*pb.Formula)
		p.pretty_formula(field1030)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1037 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1037 != nil {
		p.write(*flat1037)
		return nil
	} else {
		_dollar_dollar := msg
		fields1032 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1033 := fields1032
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1034 := unwrapped_fields1033[0].(*pb.Abstraction)
		p.pretty_abstraction(field1034)
		p.newline()
		field1035 := unwrapped_fields1033[1].(*pb.Abstraction)
		p.pretty_abstraction(field1035)
		p.newline()
		field1036 := unwrapped_fields1033[2].([]*pb.Term)
		p.pretty_terms(field1036)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1041 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1041 != nil {
		p.write(*flat1041)
		return nil
	} else {
		fields1038 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1038) == 0) {
			p.newline()
			for i1040, elem1039 := range fields1038 {
				if (i1040 > 0) {
					p.newline()
				}
				p.pretty_term(elem1039)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1046 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1046 != nil {
		p.write(*flat1046)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1659 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1659 = _dollar_dollar.GetVar()
		}
		deconstruct_result1044 := _t1659
		if deconstruct_result1044 != nil {
			unwrapped1045 := deconstruct_result1044
			p.pretty_var(unwrapped1045)
		} else {
			_dollar_dollar := msg
			var _t1660 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1660 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1042 := _t1660
			if deconstruct_result1042 != nil {
				unwrapped1043 := deconstruct_result1042
				p.pretty_value(unwrapped1043)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1049 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1049 != nil {
		p.write(*flat1049)
		return nil
	} else {
		_dollar_dollar := msg
		fields1047 := _dollar_dollar.GetName()
		unwrapped_fields1048 := fields1047
		p.write(unwrapped_fields1048)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1075 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1075 != nil {
		p.write(*flat1075)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1661 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1661 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1073 := _t1661
		if deconstruct_result1073 != nil {
			unwrapped1074 := deconstruct_result1073
			p.pretty_date(unwrapped1074)
		} else {
			_dollar_dollar := msg
			var _t1662 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1662 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1071 := _t1662
			if deconstruct_result1071 != nil {
				unwrapped1072 := deconstruct_result1071
				p.pretty_datetime(unwrapped1072)
			} else {
				_dollar_dollar := msg
				var _t1663 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1663 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1069 := _t1663
				if deconstruct_result1069 != nil {
					unwrapped1070 := *deconstruct_result1069
					p.write(p.formatStringValue(unwrapped1070))
				} else {
					_dollar_dollar := msg
					var _t1664 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1664 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1067 := _t1664
					if deconstruct_result1067 != nil {
						unwrapped1068 := *deconstruct_result1067
						p.write(fmt.Sprintf("%di32", unwrapped1068))
					} else {
						_dollar_dollar := msg
						var _t1665 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1665 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1065 := _t1665
						if deconstruct_result1065 != nil {
							unwrapped1066 := *deconstruct_result1065
							p.write(fmt.Sprintf("%d", unwrapped1066))
						} else {
							_dollar_dollar := msg
							var _t1666 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1666 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1063 := _t1666
							if deconstruct_result1063 != nil {
								unwrapped1064 := *deconstruct_result1063
								p.write(formatFloat32(unwrapped1064))
							} else {
								_dollar_dollar := msg
								var _t1667 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1667 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1061 := _t1667
								if deconstruct_result1061 != nil {
									unwrapped1062 := *deconstruct_result1061
									p.write(formatFloat64(unwrapped1062))
								} else {
									_dollar_dollar := msg
									var _t1668 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1668 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1059 := _t1668
									if deconstruct_result1059 != nil {
										unwrapped1060 := *deconstruct_result1059
										p.write(fmt.Sprintf("%du32", unwrapped1060))
									} else {
										_dollar_dollar := msg
										var _t1669 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1669 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1057 := _t1669
										if deconstruct_result1057 != nil {
											unwrapped1058 := deconstruct_result1057
											p.write(p.formatUint128(unwrapped1058))
										} else {
											_dollar_dollar := msg
											var _t1670 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1670 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1055 := _t1670
											if deconstruct_result1055 != nil {
												unwrapped1056 := deconstruct_result1055
												p.write(p.formatInt128(unwrapped1056))
											} else {
												_dollar_dollar := msg
												var _t1671 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1671 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1053 := _t1671
												if deconstruct_result1053 != nil {
													unwrapped1054 := deconstruct_result1053
													p.write(p.formatDecimal(unwrapped1054))
												} else {
													_dollar_dollar := msg
													var _t1672 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1672 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1051 := _t1672
													if deconstruct_result1051 != nil {
														unwrapped1052 := *deconstruct_result1051
														p.pretty_boolean_value(unwrapped1052)
													} else {
														fields1050 := msg
														_ = fields1050
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
	flat1081 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1081 != nil {
		p.write(*flat1081)
		return nil
	} else {
		_dollar_dollar := msg
		fields1076 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1077 := fields1076
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1078 := unwrapped_fields1077[0].(int64)
		p.write(fmt.Sprintf("%d", field1078))
		p.newline()
		field1079 := unwrapped_fields1077[1].(int64)
		p.write(fmt.Sprintf("%d", field1079))
		p.newline()
		field1080 := unwrapped_fields1077[2].(int64)
		p.write(fmt.Sprintf("%d", field1080))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1092 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1092 != nil {
		p.write(*flat1092)
		return nil
	} else {
		_dollar_dollar := msg
		fields1082 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1083 := fields1082
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1084 := unwrapped_fields1083[0].(int64)
		p.write(fmt.Sprintf("%d", field1084))
		p.newline()
		field1085 := unwrapped_fields1083[1].(int64)
		p.write(fmt.Sprintf("%d", field1085))
		p.newline()
		field1086 := unwrapped_fields1083[2].(int64)
		p.write(fmt.Sprintf("%d", field1086))
		p.newline()
		field1087 := unwrapped_fields1083[3].(int64)
		p.write(fmt.Sprintf("%d", field1087))
		p.newline()
		field1088 := unwrapped_fields1083[4].(int64)
		p.write(fmt.Sprintf("%d", field1088))
		p.newline()
		field1089 := unwrapped_fields1083[5].(int64)
		p.write(fmt.Sprintf("%d", field1089))
		field1090 := unwrapped_fields1083[6].(*int64)
		if field1090 != nil {
			p.newline()
			opt_val1091 := *field1090
			p.write(fmt.Sprintf("%d", opt_val1091))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1097 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1097 != nil {
		p.write(*flat1097)
		return nil
	} else {
		_dollar_dollar := msg
		fields1093 := _dollar_dollar.GetArgs()
		unwrapped_fields1094 := fields1093
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1094) == 0) {
			p.newline()
			for i1096, elem1095 := range unwrapped_fields1094 {
				if (i1096 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1095)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1102 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1102 != nil {
		p.write(*flat1102)
		return nil
	} else {
		_dollar_dollar := msg
		fields1098 := _dollar_dollar.GetArgs()
		unwrapped_fields1099 := fields1098
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1099) == 0) {
			p.newline()
			for i1101, elem1100 := range unwrapped_fields1099 {
				if (i1101 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1100)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1105 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1105 != nil {
		p.write(*flat1105)
		return nil
	} else {
		_dollar_dollar := msg
		fields1103 := _dollar_dollar.GetArg()
		unwrapped_fields1104 := fields1103
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1104)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1111 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1111 != nil {
		p.write(*flat1111)
		return nil
	} else {
		_dollar_dollar := msg
		fields1106 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1107 := fields1106
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1108 := unwrapped_fields1107[0].(string)
		p.pretty_name(field1108)
		p.newline()
		field1109 := unwrapped_fields1107[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1109)
		p.newline()
		field1110 := unwrapped_fields1107[2].([]*pb.Term)
		p.pretty_terms(field1110)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1113 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1113 != nil {
		p.write(*flat1113)
		return nil
	} else {
		fields1112 := msg
		p.write(":")
		p.write(fields1112)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1117 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1117 != nil {
		p.write(*flat1117)
		return nil
	} else {
		fields1114 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1114) == 0) {
			p.newline()
			for i1116, elem1115 := range fields1114 {
				if (i1116 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1115)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1124 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1124 != nil {
		p.write(*flat1124)
		return nil
	} else {
		_dollar_dollar := msg
		fields1118 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1119 := fields1118
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1120 := unwrapped_fields1119[0].(*pb.RelationId)
		p.pretty_relation_id(field1120)
		field1121 := unwrapped_fields1119[1].([]*pb.Term)
		if !(len(field1121) == 0) {
			p.newline()
			for i1123, elem1122 := range field1121 {
				if (i1123 > 0) {
					p.newline()
				}
				p.pretty_term(elem1122)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1131 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1131 != nil {
		p.write(*flat1131)
		return nil
	} else {
		_dollar_dollar := msg
		fields1125 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1126 := fields1125
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1127 := unwrapped_fields1126[0].(string)
		p.pretty_name(field1127)
		field1128 := unwrapped_fields1126[1].([]*pb.Term)
		if !(len(field1128) == 0) {
			p.newline()
			for i1130, elem1129 := range field1128 {
				if (i1130 > 0) {
					p.newline()
				}
				p.pretty_term(elem1129)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1147 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1147 != nil {
		p.write(*flat1147)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1673 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1673 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1146 := _t1673
		if guard_result1146 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1674 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1674 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1145 := _t1674
			if guard_result1145 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1675 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1675 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1144 := _t1675
				if guard_result1144 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1676 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1676 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1143 := _t1676
					if guard_result1143 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1677 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1677 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1142 := _t1677
						if guard_result1142 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1678 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1678 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1141 := _t1678
							if guard_result1141 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1679 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1679 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1140 := _t1679
								if guard_result1140 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1680 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1680 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1139 := _t1680
									if guard_result1139 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1681 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1681 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1138 := _t1681
										if guard_result1138 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1132 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1133 := fields1132
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1134 := unwrapped_fields1133[0].(string)
											p.pretty_name(field1134)
											field1135 := unwrapped_fields1133[1].([]*pb.RelTerm)
											if !(len(field1135) == 0) {
												p.newline()
												for i1137, elem1136 := range field1135 {
													if (i1137 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1136)
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
	flat1152 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1152 != nil {
		p.write(*flat1152)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1682 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1682 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1148 := _t1682
		unwrapped_fields1149 := fields1148
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1150 := unwrapped_fields1149[0].(*pb.Term)
		p.pretty_term(field1150)
		p.newline()
		field1151 := unwrapped_fields1149[1].(*pb.Term)
		p.pretty_term(field1151)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1157 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1157 != nil {
		p.write(*flat1157)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1683 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1683 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1153 := _t1683
		unwrapped_fields1154 := fields1153
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1155 := unwrapped_fields1154[0].(*pb.Term)
		p.pretty_term(field1155)
		p.newline()
		field1156 := unwrapped_fields1154[1].(*pb.Term)
		p.pretty_term(field1156)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1162 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1162 != nil {
		p.write(*flat1162)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1684 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1684 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1158 := _t1684
		unwrapped_fields1159 := fields1158
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1160 := unwrapped_fields1159[0].(*pb.Term)
		p.pretty_term(field1160)
		p.newline()
		field1161 := unwrapped_fields1159[1].(*pb.Term)
		p.pretty_term(field1161)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1167 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1167 != nil {
		p.write(*flat1167)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1685 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1685 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1163 := _t1685
		unwrapped_fields1164 := fields1163
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1165 := unwrapped_fields1164[0].(*pb.Term)
		p.pretty_term(field1165)
		p.newline()
		field1166 := unwrapped_fields1164[1].(*pb.Term)
		p.pretty_term(field1166)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1172 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1172 != nil {
		p.write(*flat1172)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1686 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1686 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1168 := _t1686
		unwrapped_fields1169 := fields1168
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1170 := unwrapped_fields1169[0].(*pb.Term)
		p.pretty_term(field1170)
		p.newline()
		field1171 := unwrapped_fields1169[1].(*pb.Term)
		p.pretty_term(field1171)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1178 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1178 != nil {
		p.write(*flat1178)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1687 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1687 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1173 := _t1687
		unwrapped_fields1174 := fields1173
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1175 := unwrapped_fields1174[0].(*pb.Term)
		p.pretty_term(field1175)
		p.newline()
		field1176 := unwrapped_fields1174[1].(*pb.Term)
		p.pretty_term(field1176)
		p.newline()
		field1177 := unwrapped_fields1174[2].(*pb.Term)
		p.pretty_term(field1177)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1184 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1184 != nil {
		p.write(*flat1184)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1688 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1688 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1179 := _t1688
		unwrapped_fields1180 := fields1179
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1181 := unwrapped_fields1180[0].(*pb.Term)
		p.pretty_term(field1181)
		p.newline()
		field1182 := unwrapped_fields1180[1].(*pb.Term)
		p.pretty_term(field1182)
		p.newline()
		field1183 := unwrapped_fields1180[2].(*pb.Term)
		p.pretty_term(field1183)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1190 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1190 != nil {
		p.write(*flat1190)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1689 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1689 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1185 := _t1689
		unwrapped_fields1186 := fields1185
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1187 := unwrapped_fields1186[0].(*pb.Term)
		p.pretty_term(field1187)
		p.newline()
		field1188 := unwrapped_fields1186[1].(*pb.Term)
		p.pretty_term(field1188)
		p.newline()
		field1189 := unwrapped_fields1186[2].(*pb.Term)
		p.pretty_term(field1189)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1196 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1196 != nil {
		p.write(*flat1196)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1690 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1690 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1191 := _t1690
		unwrapped_fields1192 := fields1191
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1193 := unwrapped_fields1192[0].(*pb.Term)
		p.pretty_term(field1193)
		p.newline()
		field1194 := unwrapped_fields1192[1].(*pb.Term)
		p.pretty_term(field1194)
		p.newline()
		field1195 := unwrapped_fields1192[2].(*pb.Term)
		p.pretty_term(field1195)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1201 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1201 != nil {
		p.write(*flat1201)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1691 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1691 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1199 := _t1691
		if deconstruct_result1199 != nil {
			unwrapped1200 := deconstruct_result1199
			p.pretty_specialized_value(unwrapped1200)
		} else {
			_dollar_dollar := msg
			var _t1692 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1692 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1197 := _t1692
			if deconstruct_result1197 != nil {
				unwrapped1198 := deconstruct_result1197
				p.pretty_term(unwrapped1198)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1203 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1203 != nil {
		p.write(*flat1203)
		return nil
	} else {
		fields1202 := msg
		p.write("#")
		p.pretty_raw_value(fields1202)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1210 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1210 != nil {
		p.write(*flat1210)
		return nil
	} else {
		_dollar_dollar := msg
		fields1204 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1205 := fields1204
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1206 := unwrapped_fields1205[0].(string)
		p.pretty_name(field1206)
		field1207 := unwrapped_fields1205[1].([]*pb.RelTerm)
		if !(len(field1207) == 0) {
			p.newline()
			for i1209, elem1208 := range field1207 {
				if (i1209 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1208)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1215 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1215 != nil {
		p.write(*flat1215)
		return nil
	} else {
		_dollar_dollar := msg
		fields1211 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1212 := fields1211
		p.write("(")
		p.write("cast")
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

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1219 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1219 != nil {
		p.write(*flat1219)
		return nil
	} else {
		fields1216 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1216) == 0) {
			p.newline()
			for i1218, elem1217 := range fields1216 {
				if (i1218 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1217)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1226 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1226 != nil {
		p.write(*flat1226)
		return nil
	} else {
		_dollar_dollar := msg
		fields1220 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1221 := fields1220
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1222 := unwrapped_fields1221[0].(string)
		p.pretty_name(field1222)
		field1223 := unwrapped_fields1221[1].([]*pb.Value)
		if !(len(field1223) == 0) {
			p.newline()
			for i1225, elem1224 := range field1223 {
				if (i1225 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1224)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1235 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1235 != nil {
		p.write(*flat1235)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1693 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1693 = _dollar_dollar.GetAttrs()
		}
		fields1227 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody(), _t1693}
		unwrapped_fields1228 := fields1227
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1229 := unwrapped_fields1228[0].([]*pb.RelationId)
		if !(len(field1229) == 0) {
			p.newline()
			for i1231, elem1230 := range field1229 {
				if (i1231 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1230)
			}
		}
		p.newline()
		field1232 := unwrapped_fields1228[1].(*pb.Script)
		p.pretty_script(field1232)
		field1233 := unwrapped_fields1228[2].([]*pb.Attribute)
		if field1233 != nil {
			p.newline()
			opt_val1234 := field1233
			p.pretty_attrs(opt_val1234)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1240 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1240 != nil {
		p.write(*flat1240)
		return nil
	} else {
		_dollar_dollar := msg
		fields1236 := _dollar_dollar.GetConstructs()
		unwrapped_fields1237 := fields1236
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1237) == 0) {
			p.newline()
			for i1239, elem1238 := range unwrapped_fields1237 {
				if (i1239 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1238)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1245 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1245 != nil {
		p.write(*flat1245)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1694 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1694 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1243 := _t1694
		if deconstruct_result1243 != nil {
			unwrapped1244 := deconstruct_result1243
			p.pretty_loop(unwrapped1244)
		} else {
			_dollar_dollar := msg
			var _t1695 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1695 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1241 := _t1695
			if deconstruct_result1241 != nil {
				unwrapped1242 := deconstruct_result1241
				p.pretty_instruction(unwrapped1242)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1252 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1252 != nil {
		p.write(*flat1252)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1696 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1696 = _dollar_dollar.GetAttrs()
		}
		fields1246 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody(), _t1696}
		unwrapped_fields1247 := fields1246
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1248 := unwrapped_fields1247[0].([]*pb.Instruction)
		p.pretty_init(field1248)
		p.newline()
		field1249 := unwrapped_fields1247[1].(*pb.Script)
		p.pretty_script(field1249)
		field1250 := unwrapped_fields1247[2].([]*pb.Attribute)
		if field1250 != nil {
			p.newline()
			opt_val1251 := field1250
			p.pretty_attrs(opt_val1251)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1256 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1256 != nil {
		p.write(*flat1256)
		return nil
	} else {
		fields1253 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1253) == 0) {
			p.newline()
			for i1255, elem1254 := range fields1253 {
				if (i1255 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1254)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1267 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1267 != nil {
		p.write(*flat1267)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1697 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1697 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1265 := _t1697
		if deconstruct_result1265 != nil {
			unwrapped1266 := deconstruct_result1265
			p.pretty_assign(unwrapped1266)
		} else {
			_dollar_dollar := msg
			var _t1698 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1698 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1263 := _t1698
			if deconstruct_result1263 != nil {
				unwrapped1264 := deconstruct_result1263
				p.pretty_upsert(unwrapped1264)
			} else {
				_dollar_dollar := msg
				var _t1699 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1699 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1261 := _t1699
				if deconstruct_result1261 != nil {
					unwrapped1262 := deconstruct_result1261
					p.pretty_break(unwrapped1262)
				} else {
					_dollar_dollar := msg
					var _t1700 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1700 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1259 := _t1700
					if deconstruct_result1259 != nil {
						unwrapped1260 := deconstruct_result1259
						p.pretty_monoid_def(unwrapped1260)
					} else {
						_dollar_dollar := msg
						var _t1701 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1701 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1257 := _t1701
						if deconstruct_result1257 != nil {
							unwrapped1258 := deconstruct_result1257
							p.pretty_monus_def(unwrapped1258)
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
	flat1274 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1274 != nil {
		p.write(*flat1274)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1702 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1702 = _dollar_dollar.GetAttrs()
		}
		fields1268 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1702}
		unwrapped_fields1269 := fields1268
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1270 := unwrapped_fields1269[0].(*pb.RelationId)
		p.pretty_relation_id(field1270)
		p.newline()
		field1271 := unwrapped_fields1269[1].(*pb.Abstraction)
		p.pretty_abstraction(field1271)
		field1272 := unwrapped_fields1269[2].([]*pb.Attribute)
		if field1272 != nil {
			p.newline()
			opt_val1273 := field1272
			p.pretty_attrs(opt_val1273)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1281 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1281 != nil {
		p.write(*flat1281)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1703 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1703 = _dollar_dollar.GetAttrs()
		}
		fields1275 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1703}
		unwrapped_fields1276 := fields1275
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1277 := unwrapped_fields1276[0].(*pb.RelationId)
		p.pretty_relation_id(field1277)
		p.newline()
		field1278 := unwrapped_fields1276[1].([]interface{})
		p.pretty_abstraction_with_arity(field1278)
		field1279 := unwrapped_fields1276[2].([]*pb.Attribute)
		if field1279 != nil {
			p.newline()
			opt_val1280 := field1279
			p.pretty_attrs(opt_val1280)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1286 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1286 != nil {
		p.write(*flat1286)
		return nil
	} else {
		_dollar_dollar := msg
		_t1704 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1282 := []interface{}{_t1704, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1283 := fields1282
		p.write("(")
		p.indent()
		field1284 := unwrapped_fields1283[0].([]interface{})
		p.pretty_bindings(field1284)
		p.newline()
		field1285 := unwrapped_fields1283[1].(*pb.Formula)
		p.pretty_formula(field1285)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1293 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1293 != nil {
		p.write(*flat1293)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1705 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1705 = _dollar_dollar.GetAttrs()
		}
		fields1287 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1705}
		unwrapped_fields1288 := fields1287
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1289 := unwrapped_fields1288[0].(*pb.RelationId)
		p.pretty_relation_id(field1289)
		p.newline()
		field1290 := unwrapped_fields1288[1].(*pb.Abstraction)
		p.pretty_abstraction(field1290)
		field1291 := unwrapped_fields1288[2].([]*pb.Attribute)
		if field1291 != nil {
			p.newline()
			opt_val1292 := field1291
			p.pretty_attrs(opt_val1292)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1301 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1301 != nil {
		p.write(*flat1301)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1706 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1706 = _dollar_dollar.GetAttrs()
		}
		fields1294 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1706}
		unwrapped_fields1295 := fields1294
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1296 := unwrapped_fields1295[0].(*pb.Monoid)
		p.pretty_monoid(field1296)
		p.newline()
		field1297 := unwrapped_fields1295[1].(*pb.RelationId)
		p.pretty_relation_id(field1297)
		p.newline()
		field1298 := unwrapped_fields1295[2].([]interface{})
		p.pretty_abstraction_with_arity(field1298)
		field1299 := unwrapped_fields1295[3].([]*pb.Attribute)
		if field1299 != nil {
			p.newline()
			opt_val1300 := field1299
			p.pretty_attrs(opt_val1300)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1310 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1310 != nil {
		p.write(*flat1310)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1707 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1707 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1308 := _t1707
		if deconstruct_result1308 != nil {
			unwrapped1309 := deconstruct_result1308
			p.pretty_or_monoid(unwrapped1309)
		} else {
			_dollar_dollar := msg
			var _t1708 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1708 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1306 := _t1708
			if deconstruct_result1306 != nil {
				unwrapped1307 := deconstruct_result1306
				p.pretty_min_monoid(unwrapped1307)
			} else {
				_dollar_dollar := msg
				var _t1709 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1709 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1304 := _t1709
				if deconstruct_result1304 != nil {
					unwrapped1305 := deconstruct_result1304
					p.pretty_max_monoid(unwrapped1305)
				} else {
					_dollar_dollar := msg
					var _t1710 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1710 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1302 := _t1710
					if deconstruct_result1302 != nil {
						unwrapped1303 := deconstruct_result1302
						p.pretty_sum_monoid(unwrapped1303)
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
	fields1311 := msg
	_ = fields1311
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1314 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1314 != nil {
		p.write(*flat1314)
		return nil
	} else {
		_dollar_dollar := msg
		fields1312 := _dollar_dollar.GetType()
		unwrapped_fields1313 := fields1312
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1313)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1317 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1317 != nil {
		p.write(*flat1317)
		return nil
	} else {
		_dollar_dollar := msg
		fields1315 := _dollar_dollar.GetType()
		unwrapped_fields1316 := fields1315
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1316)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1320 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1320 != nil {
		p.write(*flat1320)
		return nil
	} else {
		_dollar_dollar := msg
		fields1318 := _dollar_dollar.GetType()
		unwrapped_fields1319 := fields1318
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1319)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1328 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1328 != nil {
		p.write(*flat1328)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1711 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1711 = _dollar_dollar.GetAttrs()
		}
		fields1321 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1711}
		unwrapped_fields1322 := fields1321
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1323 := unwrapped_fields1322[0].(*pb.Monoid)
		p.pretty_monoid(field1323)
		p.newline()
		field1324 := unwrapped_fields1322[1].(*pb.RelationId)
		p.pretty_relation_id(field1324)
		p.newline()
		field1325 := unwrapped_fields1322[2].([]interface{})
		p.pretty_abstraction_with_arity(field1325)
		field1326 := unwrapped_fields1322[3].([]*pb.Attribute)
		if field1326 != nil {
			p.newline()
			opt_val1327 := field1326
			p.pretty_attrs(opt_val1327)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1335 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1335 != nil {
		p.write(*flat1335)
		return nil
	} else {
		_dollar_dollar := msg
		fields1329 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1330 := fields1329
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1331 := unwrapped_fields1330[0].(*pb.RelationId)
		p.pretty_relation_id(field1331)
		p.newline()
		field1332 := unwrapped_fields1330[1].(*pb.Abstraction)
		p.pretty_abstraction(field1332)
		p.newline()
		field1333 := unwrapped_fields1330[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1333)
		p.newline()
		field1334 := unwrapped_fields1330[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1334)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1339 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1339 != nil {
		p.write(*flat1339)
		return nil
	} else {
		fields1336 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1336) == 0) {
			p.newline()
			for i1338, elem1337 := range fields1336 {
				if (i1338 > 0) {
					p.newline()
				}
				p.pretty_var(elem1337)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1343 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1343 != nil {
		p.write(*flat1343)
		return nil
	} else {
		fields1340 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1340) == 0) {
			p.newline()
			for i1342, elem1341 := range fields1340 {
				if (i1342 > 0) {
					p.newline()
				}
				p.pretty_var(elem1341)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1352 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1352 != nil {
		p.write(*flat1352)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1712 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1712 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1350 := _t1712
		if deconstruct_result1350 != nil {
			unwrapped1351 := deconstruct_result1350
			p.pretty_edb(unwrapped1351)
		} else {
			_dollar_dollar := msg
			var _t1713 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1713 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1348 := _t1713
			if deconstruct_result1348 != nil {
				unwrapped1349 := deconstruct_result1348
				p.pretty_betree_relation(unwrapped1349)
			} else {
				_dollar_dollar := msg
				var _t1714 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1714 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1346 := _t1714
				if deconstruct_result1346 != nil {
					unwrapped1347 := deconstruct_result1346
					p.pretty_csv_data(unwrapped1347)
				} else {
					_dollar_dollar := msg
					var _t1715 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1715 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1344 := _t1715
					if deconstruct_result1344 != nil {
						unwrapped1345 := deconstruct_result1344
						p.pretty_iceberg_data(unwrapped1345)
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
	flat1358 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1358 != nil {
		p.write(*flat1358)
		return nil
	} else {
		_dollar_dollar := msg
		fields1353 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1354 := fields1353
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1355 := unwrapped_fields1354[0].(*pb.RelationId)
		p.pretty_relation_id(field1355)
		p.newline()
		field1356 := unwrapped_fields1354[1].([]string)
		p.pretty_edb_path(field1356)
		p.newline()
		field1357 := unwrapped_fields1354[2].([]*pb.Type)
		p.pretty_edb_types(field1357)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1362 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1362 != nil {
		p.write(*flat1362)
		return nil
	} else {
		fields1359 := msg
		p.write("[")
		p.indent()
		for i1361, elem1360 := range fields1359 {
			if (i1361 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1360))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1366 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1366 != nil {
		p.write(*flat1366)
		return nil
	} else {
		fields1363 := msg
		p.write("[")
		p.indent()
		for i1365, elem1364 := range fields1363 {
			if (i1365 > 0) {
				p.newline()
			}
			p.pretty_type(elem1364)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1371 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1371 != nil {
		p.write(*flat1371)
		return nil
	} else {
		_dollar_dollar := msg
		fields1367 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1368 := fields1367
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1369 := unwrapped_fields1368[0].(*pb.RelationId)
		p.pretty_relation_id(field1369)
		p.newline()
		field1370 := unwrapped_fields1368[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1370)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1377 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1377 != nil {
		p.write(*flat1377)
		return nil
	} else {
		_dollar_dollar := msg
		_t1716 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1372 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1716}
		unwrapped_fields1373 := fields1372
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1374 := unwrapped_fields1373[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1374)
		p.newline()
		field1375 := unwrapped_fields1373[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1375)
		p.newline()
		field1376 := unwrapped_fields1373[2].([][]interface{})
		p.pretty_config_dict(field1376)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1381 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1381 != nil {
		p.write(*flat1381)
		return nil
	} else {
		fields1378 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1378) == 0) {
			p.newline()
			for i1380, elem1379 := range fields1378 {
				if (i1380 > 0) {
					p.newline()
				}
				p.pretty_type(elem1379)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1385 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1385 != nil {
		p.write(*flat1385)
		return nil
	} else {
		fields1382 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1382) == 0) {
			p.newline()
			for i1384, elem1383 := range fields1382 {
				if (i1384 > 0) {
					p.newline()
				}
				p.pretty_type(elem1383)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1392 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1392 != nil {
		p.write(*flat1392)
		return nil
	} else {
		_dollar_dollar := msg
		fields1386 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1387 := fields1386
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1388 := unwrapped_fields1387[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1388)
		p.newline()
		field1389 := unwrapped_fields1387[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1389)
		p.newline()
		field1390 := unwrapped_fields1387[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1390)
		p.newline()
		field1391 := unwrapped_fields1387[3].(string)
		p.pretty_csv_asof(field1391)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1399 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1399 != nil {
		p.write(*flat1399)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1717 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1717 = _dollar_dollar.GetPaths()
		}
		var _t1718 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1718 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1393 := []interface{}{_t1717, _t1718}
		unwrapped_fields1394 := fields1393
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1395 := unwrapped_fields1394[0].([]string)
		if field1395 != nil {
			p.newline()
			opt_val1396 := field1395
			p.pretty_csv_locator_paths(opt_val1396)
		}
		field1397 := unwrapped_fields1394[1].(*string)
		if field1397 != nil {
			p.newline()
			opt_val1398 := *field1397
			p.pretty_csv_locator_inline_data(opt_val1398)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1403 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1403 != nil {
		p.write(*flat1403)
		return nil
	} else {
		fields1400 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1400) == 0) {
			p.newline()
			for i1402, elem1401 := range fields1400 {
				if (i1402 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1401))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1405 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1405 != nil {
		p.write(*flat1405)
		return nil
	} else {
		fields1404 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1404))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1411 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1411 != nil {
		p.write(*flat1411)
		return nil
	} else {
		_dollar_dollar := msg
		_t1719 := p.deconstruct_csv_config(_dollar_dollar)
		_t1720 := p.deconstruct_csv_storage_integration_optional(_dollar_dollar)
		fields1406 := []interface{}{_t1719, _t1720}
		unwrapped_fields1407 := fields1406
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		field1408 := unwrapped_fields1407[0].([][]interface{})
		p.pretty_config_dict(field1408)
		field1409 := unwrapped_fields1407[1].([][]interface{})
		if field1409 != nil {
			p.newline()
			opt_val1410 := field1409
			p.pretty_csv_storage_integration(opt_val1410)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_storage_integration(msg [][]interface{}) interface{} {
	flat1413 := p.tryFlat(msg, func() { p.pretty_csv_storage_integration(msg) })
	if flat1413 != nil {
		p.write(*flat1413)
		return nil
	} else {
		fields1412 := msg
		p.write("(")
		p.write("storage_integration")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(fields1412)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1417 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1417 != nil {
		p.write(*flat1417)
		return nil
	} else {
		fields1414 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1414) == 0) {
			p.newline()
			for i1416, elem1415 := range fields1414 {
				if (i1416 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1415)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1426 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1426 != nil {
		p.write(*flat1426)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1721 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1721 = _dollar_dollar.GetTargetId()
		}
		fields1418 := []interface{}{_dollar_dollar.GetColumnPath(), _t1721, _dollar_dollar.GetTypes()}
		unwrapped_fields1419 := fields1418
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1420 := unwrapped_fields1419[0].([]string)
		p.pretty_gnf_column_path(field1420)
		field1421 := unwrapped_fields1419[1].(*pb.RelationId)
		if field1421 != nil {
			p.newline()
			opt_val1422 := field1421
			p.pretty_relation_id(opt_val1422)
		}
		p.newline()
		p.write("[")
		field1423 := unwrapped_fields1419[2].([]*pb.Type)
		for i1425, elem1424 := range field1423 {
			if (i1425 > 0) {
				p.newline()
			}
			p.pretty_type(elem1424)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1433 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1433 != nil {
		p.write(*flat1433)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1722 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1722 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1431 := _t1722
		if deconstruct_result1431 != nil {
			unwrapped1432 := *deconstruct_result1431
			p.write(p.formatStringValue(unwrapped1432))
		} else {
			_dollar_dollar := msg
			var _t1723 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1723 = _dollar_dollar
			}
			deconstruct_result1427 := _t1723
			if deconstruct_result1427 != nil {
				unwrapped1428 := deconstruct_result1427
				p.write("[")
				p.indent()
				for i1430, elem1429 := range unwrapped1428 {
					if (i1430 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1429))
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

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1435 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1435 != nil {
		p.write(*flat1435)
		return nil
	} else {
		fields1434 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1434))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1446 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1446 != nil {
		p.write(*flat1446)
		return nil
	} else {
		_dollar_dollar := msg
		_t1724 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1725 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1436 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1724, _t1725, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1437 := fields1436
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1438 := unwrapped_fields1437[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1438)
		p.newline()
		field1439 := unwrapped_fields1437[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1439)
		p.newline()
		field1440 := unwrapped_fields1437[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1440)
		field1441 := unwrapped_fields1437[3].(*string)
		if field1441 != nil {
			p.newline()
			opt_val1442 := *field1441
			p.pretty_iceberg_from_snapshot(opt_val1442)
		}
		field1443 := unwrapped_fields1437[4].(*string)
		if field1443 != nil {
			p.newline()
			opt_val1444 := *field1443
			p.pretty_iceberg_to_snapshot(opt_val1444)
		}
		p.newline()
		field1445 := unwrapped_fields1437[5].(bool)
		p.pretty_boolean_value(field1445)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1452 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1452 != nil {
		p.write(*flat1452)
		return nil
	} else {
		_dollar_dollar := msg
		fields1447 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1448 := fields1447
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1449 := unwrapped_fields1448[0].(string)
		p.pretty_iceberg_locator_table_name(field1449)
		p.newline()
		field1450 := unwrapped_fields1448[1].([]string)
		p.pretty_iceberg_locator_namespace(field1450)
		p.newline()
		field1451 := unwrapped_fields1448[2].(string)
		p.pretty_iceberg_locator_warehouse(field1451)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1454 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1454 != nil {
		p.write(*flat1454)
		return nil
	} else {
		fields1453 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1453))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1458 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1458 != nil {
		p.write(*flat1458)
		return nil
	} else {
		fields1455 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1455) == 0) {
			p.newline()
			for i1457, elem1456 := range fields1455 {
				if (i1457 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1456))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1460 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1460 != nil {
		p.write(*flat1460)
		return nil
	} else {
		fields1459 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1459))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1468 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1468 != nil {
		p.write(*flat1468)
		return nil
	} else {
		_dollar_dollar := msg
		_t1726 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1461 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1726, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1462 := fields1461
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1463 := unwrapped_fields1462[0].(string)
		p.pretty_iceberg_catalog_uri(field1463)
		field1464 := unwrapped_fields1462[1].(*string)
		if field1464 != nil {
			p.newline()
			opt_val1465 := *field1464
			p.pretty_iceberg_catalog_config_scope(opt_val1465)
		}
		p.newline()
		field1466 := unwrapped_fields1462[2].([][]interface{})
		p.pretty_iceberg_properties(field1466)
		p.newline()
		field1467 := unwrapped_fields1462[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1467)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1470 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1470 != nil {
		p.write(*flat1470)
		return nil
	} else {
		fields1469 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1469))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1472 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1472 != nil {
		p.write(*flat1472)
		return nil
	} else {
		fields1471 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1471))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1476 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1476 != nil {
		p.write(*flat1476)
		return nil
	} else {
		fields1473 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1473) == 0) {
			p.newline()
			for i1475, elem1474 := range fields1473 {
				if (i1475 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1474)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1481 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1481 != nil {
		p.write(*flat1481)
		return nil
	} else {
		_dollar_dollar := msg
		fields1477 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1478 := fields1477
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1479 := unwrapped_fields1478[0].(string)
		p.write(p.formatStringValue(field1479))
		p.newline()
		field1480 := unwrapped_fields1478[1].(string)
		p.write(p.formatStringValue(field1480))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1485 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1485 != nil {
		p.write(*flat1485)
		return nil
	} else {
		fields1482 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1482) == 0) {
			p.newline()
			for i1484, elem1483 := range fields1482 {
				if (i1484 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1483)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1490 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1490 != nil {
		p.write(*flat1490)
		return nil
	} else {
		_dollar_dollar := msg
		_t1727 := p.mask_secret_value(_dollar_dollar)
		fields1486 := []interface{}{_dollar_dollar[0].(string), _t1727}
		unwrapped_fields1487 := fields1486
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1488 := unwrapped_fields1487[0].(string)
		p.write(p.formatStringValue(field1488))
		p.newline()
		field1489 := unwrapped_fields1487[1].(string)
		p.write(p.formatStringValue(field1489))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1492 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1492 != nil {
		p.write(*flat1492)
		return nil
	} else {
		fields1491 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1491))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1494 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1494 != nil {
		p.write(*flat1494)
		return nil
	} else {
		fields1493 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1493))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1497 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1497 != nil {
		p.write(*flat1497)
		return nil
	} else {
		_dollar_dollar := msg
		fields1495 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1496 := fields1495
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1496)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1502 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1502 != nil {
		p.write(*flat1502)
		return nil
	} else {
		_dollar_dollar := msg
		fields1498 := _dollar_dollar.GetRelations()
		unwrapped_fields1499 := fields1498
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1499) == 0) {
			p.newline()
			for i1501, elem1500 := range unwrapped_fields1499 {
				if (i1501 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1500)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1509 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1509 != nil {
		p.write(*flat1509)
		return nil
	} else {
		_dollar_dollar := msg
		fields1503 := []interface{}{_dollar_dollar.GetPrefix(), _dollar_dollar.GetMappings()}
		unwrapped_fields1504 := fields1503
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1505 := unwrapped_fields1504[0].([]string)
		p.pretty_edb_path(field1505)
		field1506 := unwrapped_fields1504[1].([]*pb.SnapshotMapping)
		if !(len(field1506) == 0) {
			p.newline()
			for i1508, elem1507 := range field1506 {
				if (i1508 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1507)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1514 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1514 != nil {
		p.write(*flat1514)
		return nil
	} else {
		_dollar_dollar := msg
		fields1510 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1511 := fields1510
		field1512 := unwrapped_fields1511[0].([]string)
		p.pretty_edb_path(field1512)
		p.write(" ")
		field1513 := unwrapped_fields1511[1].(*pb.RelationId)
		p.pretty_relation_id(field1513)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1518 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1518 != nil {
		p.write(*flat1518)
		return nil
	} else {
		fields1515 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1515) == 0) {
			p.newline()
			for i1517, elem1516 := range fields1515 {
				if (i1517 > 0) {
					p.newline()
				}
				p.pretty_read(elem1516)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1529 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1529 != nil {
		p.write(*flat1529)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1728 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1728 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1527 := _t1728
		if deconstruct_result1527 != nil {
			unwrapped1528 := deconstruct_result1527
			p.pretty_demand(unwrapped1528)
		} else {
			_dollar_dollar := msg
			var _t1729 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1729 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1525 := _t1729
			if deconstruct_result1525 != nil {
				unwrapped1526 := deconstruct_result1525
				p.pretty_output(unwrapped1526)
			} else {
				_dollar_dollar := msg
				var _t1730 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1730 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1523 := _t1730
				if deconstruct_result1523 != nil {
					unwrapped1524 := deconstruct_result1523
					p.pretty_what_if(unwrapped1524)
				} else {
					_dollar_dollar := msg
					var _t1731 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1731 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1521 := _t1731
					if deconstruct_result1521 != nil {
						unwrapped1522 := deconstruct_result1521
						p.pretty_abort(unwrapped1522)
					} else {
						_dollar_dollar := msg
						var _t1732 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1732 = _dollar_dollar.GetExport()
						}
						deconstruct_result1519 := _t1732
						if deconstruct_result1519 != nil {
							unwrapped1520 := deconstruct_result1519
							p.pretty_export(unwrapped1520)
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
	flat1532 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1532 != nil {
		p.write(*flat1532)
		return nil
	} else {
		_dollar_dollar := msg
		fields1530 := _dollar_dollar.GetRelationId()
		unwrapped_fields1531 := fields1530
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1531)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1537 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1537 != nil {
		p.write(*flat1537)
		return nil
	} else {
		_dollar_dollar := msg
		fields1533 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1534 := fields1533
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1535 := unwrapped_fields1534[0].(string)
		p.pretty_name(field1535)
		p.newline()
		field1536 := unwrapped_fields1534[1].(*pb.RelationId)
		p.pretty_relation_id(field1536)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1542 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1542 != nil {
		p.write(*flat1542)
		return nil
	} else {
		_dollar_dollar := msg
		fields1538 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1539 := fields1538
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1540 := unwrapped_fields1539[0].(string)
		p.pretty_name(field1540)
		p.newline()
		field1541 := unwrapped_fields1539[1].(*pb.Epoch)
		p.pretty_epoch(field1541)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1548 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1548 != nil {
		p.write(*flat1548)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1733 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1733 = ptr(_dollar_dollar.GetName())
		}
		fields1543 := []interface{}{_t1733, _dollar_dollar.GetRelationId()}
		unwrapped_fields1544 := fields1543
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1545 := unwrapped_fields1544[0].(*string)
		if field1545 != nil {
			p.newline()
			opt_val1546 := *field1545
			p.pretty_name(opt_val1546)
		}
		p.newline()
		field1547 := unwrapped_fields1544[1].(*pb.RelationId)
		p.pretty_relation_id(field1547)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1553 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1553 != nil {
		p.write(*flat1553)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1734 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1734 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1551 := _t1734
		if deconstruct_result1551 != nil {
			unwrapped1552 := deconstruct_result1551
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1552)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1735 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1735 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1549 := _t1735
			if deconstruct_result1549 != nil {
				unwrapped1550 := deconstruct_result1549
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1550)
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
	flat1564 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1564 != nil {
		p.write(*flat1564)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1736 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1736 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1559 := _t1736
		if deconstruct_result1559 != nil {
			unwrapped1560 := deconstruct_result1559
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1561 := unwrapped1560[0].(string)
			p.pretty_export_csv_path(field1561)
			p.newline()
			field1562 := unwrapped1560[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1562)
			p.newline()
			field1563 := unwrapped1560[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1563)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1737 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1738 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1737 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1738}
			}
			deconstruct_result1554 := _t1737
			if deconstruct_result1554 != nil {
				unwrapped1555 := deconstruct_result1554
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1556 := unwrapped1555[0].(string)
				p.pretty_export_csv_path(field1556)
				p.newline()
				field1557 := unwrapped1555[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1557)
				p.newline()
				field1558 := unwrapped1555[2].([][]interface{})
				p.pretty_config_dict(field1558)
				p.dedent()
				p.write(")")
			} else {
				panic(ParseError{msg: "No matching rule for export_csv_config"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1566 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1566 != nil {
		p.write(*flat1566)
		return nil
	} else {
		fields1565 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1565))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1573 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1573 != nil {
		p.write(*flat1573)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1739 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1739 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1569 := _t1739
		if deconstruct_result1569 != nil {
			unwrapped1570 := deconstruct_result1569
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1570) == 0) {
				p.newline()
				for i1572, elem1571 := range unwrapped1570 {
					if (i1572 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1571)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1740 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1740 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1567 := _t1740
			if deconstruct_result1567 != nil {
				unwrapped1568 := deconstruct_result1567
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1568)
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
	flat1578 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1578 != nil {
		p.write(*flat1578)
		return nil
	} else {
		_dollar_dollar := msg
		fields1574 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1575 := fields1574
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1576 := unwrapped_fields1575[0].(string)
		p.write(p.formatStringValue(field1576))
		p.newline()
		field1577 := unwrapped_fields1575[1].(*pb.RelationId)
		p.pretty_relation_id(field1577)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1582 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1582 != nil {
		p.write(*flat1582)
		return nil
	} else {
		fields1579 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1579) == 0) {
			p.newline()
			for i1581, elem1580 := range fields1579 {
				if (i1581 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1580)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1591 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1591 != nil {
		p.write(*flat1591)
		return nil
	} else {
		_dollar_dollar := msg
		_t1741 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1583 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1741}
		unwrapped_fields1584 := fields1583
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1585 := unwrapped_fields1584[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1585)
		p.newline()
		field1586 := unwrapped_fields1584[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1586)
		p.newline()
		field1587 := unwrapped_fields1584[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1587)
		p.newline()
		field1588 := unwrapped_fields1584[3].([][]interface{})
		p.pretty_iceberg_table_properties(field1588)
		field1589 := unwrapped_fields1584[4].([][]interface{})
		if field1589 != nil {
			p.newline()
			opt_val1590 := field1589
			p.pretty_config_dict(opt_val1590)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1593 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1593 != nil {
		p.write(*flat1593)
		return nil
	} else {
		fields1592 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1592)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1597 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1597 != nil {
		p.write(*flat1597)
		return nil
	} else {
		fields1594 := msg
		p.write("(")
		p.write("table_properties")
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


// --- Auto-generated printers for uncovered proto types ---

func (p *PrettyPrinter) pretty_debug_info(msg *pb.DebugInfo) interface{} {
	p.write("(debug_info")
	p.indentSexp()
	for _idx, _rid := range msg.GetIds() {
		p.newline()
		p.write("(")
		_t1793 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1793)
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

func (p *PrettyPrinter) pretty_csv_storage_integration(msg *pb.CSVStorageIntegration) interface{} {
	p.write("(csv_storage_integration")
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
	case *pb.CSVStorageIntegration:
		p.pretty_csv_storage_integration(m)
	case *pb.DecimalValue:
		p.pretty_decimal_value(m)
	case *pb.FunctionalDependency:
		p.pretty_functional_dependency(m)
	case *pb.Int128Value:
		p.pretty_int128_value(m)
	case *pb.MissingValue:
		p.pretty_missing_value(m)
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
