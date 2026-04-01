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
	_t1737 := &pb.Value{}
	_t1737.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1737
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1738 := &pb.Value{}
	_t1738.Value = &pb.Value_IntValue{IntValue: v}
	return _t1738
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1739 := &pb.Value{}
	_t1739.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1739
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1740 := &pb.Value{}
	_t1740.Value = &pb.Value_StringValue{StringValue: v}
	return _t1740
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1741 := &pb.Value{}
	_t1741.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1741
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1742 := &pb.Value{}
	_t1742.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1742
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1743 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1743})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1744 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1744})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1745 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1745})
			}
		}
	}
	_t1746 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1746})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1747 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1747})
	_t1748 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1748})
	if msg.GetNewLine() != "" {
		_t1749 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1749})
	}
	_t1750 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1750})
	_t1751 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1751})
	_t1752 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1752})
	if msg.GetComment() != "" {
		_t1753 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1753})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1754 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1754})
	}
	_t1755 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1755})
	_t1756 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1756})
	_t1757 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1757})
	if msg.GetPartitionSizeMb() != 0 {
		_t1758 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1758})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1759 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1759})
	_t1760 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1760})
	_t1761 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1761})
	_t1762 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1762})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1763 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1763})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1764 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1764})
		}
	}
	_t1765 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1765})
	_t1766 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1766})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1767 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1767})
	}
	if msg.Compression != nil {
		_t1768 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1768})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1769 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1769})
	}
	if msg.SyntaxMissingString != nil {
		_t1770 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1770})
	}
	if msg.SyntaxDelim != nil {
		_t1771 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1771})
	}
	if msg.SyntaxQuotechar != nil {
		_t1772 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1772})
	}
	if msg.SyntaxEscapechar != nil {
		_t1773 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1773})
	}
	return listSort(result)
}

func (p *PrettyPrinter) mask_secret_value(pair []interface{}) string {
	return "***"
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1774 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1774
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_from_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1775 interface{}
	if *msg.FromSnapshot != "" {
		return ptr(*msg.FromSnapshot)
	}
	_ = _t1775
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1776 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1776
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1777 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1777})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1778 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1778})
	}
	if msg.GetCompression() != "" {
		_t1779 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1779})
	}
	var _t1780 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1780
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1781 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1781
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
	flat807 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat807 != nil {
		p.write(*flat807)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1596 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1596 = _dollar_dollar.GetConfigure()
		}
		var _t1597 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1597 = _dollar_dollar.GetSync()
		}
		fields798 := []interface{}{_t1596, _t1597, _dollar_dollar.GetEpochs()}
		unwrapped_fields799 := fields798
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field800 := unwrapped_fields799[0].(*pb.Configure)
		if field800 != nil {
			p.newline()
			opt_val801 := field800
			p.pretty_configure(opt_val801)
		}
		field802 := unwrapped_fields799[1].(*pb.Sync)
		if field802 != nil {
			p.newline()
			opt_val803 := field802
			p.pretty_sync(opt_val803)
		}
		field804 := unwrapped_fields799[2].([]*pb.Epoch)
		if !(len(field804) == 0) {
			p.newline()
			for i806, elem805 := range field804 {
				if (i806 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem805)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat810 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat810 != nil {
		p.write(*flat810)
		return nil
	} else {
		_dollar_dollar := msg
		_t1598 := p.deconstruct_configure(_dollar_dollar)
		fields808 := _t1598
		unwrapped_fields809 := fields808
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields809)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat814 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat814 != nil {
		p.write(*flat814)
		return nil
	} else {
		fields811 := msg
		p.write("{")
		p.indent()
		if !(len(fields811) == 0) {
			p.newline()
			for i813, elem812 := range fields811 {
				if (i813 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem812)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat819 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat819 != nil {
		p.write(*flat819)
		return nil
	} else {
		_dollar_dollar := msg
		fields815 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields816 := fields815
		p.write(":")
		field817 := unwrapped_fields816[0].(string)
		p.write(field817)
		p.write(" ")
		field818 := unwrapped_fields816[1].(*pb.Value)
		p.pretty_raw_value(field818)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat845 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat845 != nil {
		p.write(*flat845)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1599 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1599 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result843 := _t1599
		if deconstruct_result843 != nil {
			unwrapped844 := deconstruct_result843
			p.pretty_raw_date(unwrapped844)
		} else {
			_dollar_dollar := msg
			var _t1600 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1600 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result841 := _t1600
			if deconstruct_result841 != nil {
				unwrapped842 := deconstruct_result841
				p.pretty_raw_datetime(unwrapped842)
			} else {
				_dollar_dollar := msg
				var _t1601 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1601 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result839 := _t1601
				if deconstruct_result839 != nil {
					unwrapped840 := *deconstruct_result839
					p.write(p.formatStringValue(unwrapped840))
				} else {
					_dollar_dollar := msg
					var _t1602 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1602 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result837 := _t1602
					if deconstruct_result837 != nil {
						unwrapped838 := *deconstruct_result837
						p.write(fmt.Sprintf("%di32", unwrapped838))
					} else {
						_dollar_dollar := msg
						var _t1603 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1603 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result835 := _t1603
						if deconstruct_result835 != nil {
							unwrapped836 := *deconstruct_result835
							p.write(fmt.Sprintf("%d", unwrapped836))
						} else {
							_dollar_dollar := msg
							var _t1604 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1604 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result833 := _t1604
							if deconstruct_result833 != nil {
								unwrapped834 := *deconstruct_result833
								p.write(formatFloat32(unwrapped834))
							} else {
								_dollar_dollar := msg
								var _t1605 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1605 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result831 := _t1605
								if deconstruct_result831 != nil {
									unwrapped832 := *deconstruct_result831
									p.write(formatFloat64(unwrapped832))
								} else {
									_dollar_dollar := msg
									var _t1606 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1606 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result829 := _t1606
									if deconstruct_result829 != nil {
										unwrapped830 := *deconstruct_result829
										p.write(fmt.Sprintf("%du32", unwrapped830))
									} else {
										_dollar_dollar := msg
										var _t1607 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1607 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result827 := _t1607
										if deconstruct_result827 != nil {
											unwrapped828 := deconstruct_result827
											p.write(p.formatUint128(unwrapped828))
										} else {
											_dollar_dollar := msg
											var _t1608 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1608 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result825 := _t1608
											if deconstruct_result825 != nil {
												unwrapped826 := deconstruct_result825
												p.write(p.formatInt128(unwrapped826))
											} else {
												_dollar_dollar := msg
												var _t1609 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1609 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result823 := _t1609
												if deconstruct_result823 != nil {
													unwrapped824 := deconstruct_result823
													p.write(p.formatDecimal(unwrapped824))
												} else {
													_dollar_dollar := msg
													var _t1610 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1610 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result821 := _t1610
													if deconstruct_result821 != nil {
														unwrapped822 := *deconstruct_result821
														p.pretty_boolean_value(unwrapped822)
													} else {
														fields820 := msg
														_ = fields820
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
	flat851 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat851 != nil {
		p.write(*flat851)
		return nil
	} else {
		_dollar_dollar := msg
		fields846 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields847 := fields846
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field848 := unwrapped_fields847[0].(int64)
		p.write(fmt.Sprintf("%d", field848))
		p.newline()
		field849 := unwrapped_fields847[1].(int64)
		p.write(fmt.Sprintf("%d", field849))
		p.newline()
		field850 := unwrapped_fields847[2].(int64)
		p.write(fmt.Sprintf("%d", field850))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat862 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat862 != nil {
		p.write(*flat862)
		return nil
	} else {
		_dollar_dollar := msg
		fields852 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields853 := fields852
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field854 := unwrapped_fields853[0].(int64)
		p.write(fmt.Sprintf("%d", field854))
		p.newline()
		field855 := unwrapped_fields853[1].(int64)
		p.write(fmt.Sprintf("%d", field855))
		p.newline()
		field856 := unwrapped_fields853[2].(int64)
		p.write(fmt.Sprintf("%d", field856))
		p.newline()
		field857 := unwrapped_fields853[3].(int64)
		p.write(fmt.Sprintf("%d", field857))
		p.newline()
		field858 := unwrapped_fields853[4].(int64)
		p.write(fmt.Sprintf("%d", field858))
		p.newline()
		field859 := unwrapped_fields853[5].(int64)
		p.write(fmt.Sprintf("%d", field859))
		field860 := unwrapped_fields853[6].(*int64)
		if field860 != nil {
			p.newline()
			opt_val861 := *field860
			p.write(fmt.Sprintf("%d", opt_val861))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1611 []interface{}
	if _dollar_dollar {
		_t1611 = []interface{}{}
	}
	deconstruct_result865 := _t1611
	if deconstruct_result865 != nil {
		unwrapped866 := deconstruct_result865
		_ = unwrapped866
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1612 []interface{}
		if !(_dollar_dollar) {
			_t1612 = []interface{}{}
		}
		deconstruct_result863 := _t1612
		if deconstruct_result863 != nil {
			unwrapped864 := deconstruct_result863
			_ = unwrapped864
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat871 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat871 != nil {
		p.write(*flat871)
		return nil
	} else {
		_dollar_dollar := msg
		fields867 := _dollar_dollar.GetFragments()
		unwrapped_fields868 := fields867
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields868) == 0) {
			p.newline()
			for i870, elem869 := range unwrapped_fields868 {
				if (i870 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem869)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat874 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat874 != nil {
		p.write(*flat874)
		return nil
	} else {
		_dollar_dollar := msg
		fields872 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields873 := fields872
		p.write(":")
		p.write(unwrapped_fields873)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat881 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat881 != nil {
		p.write(*flat881)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1613 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1613 = _dollar_dollar.GetWrites()
		}
		var _t1614 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1614 = _dollar_dollar.GetReads()
		}
		fields875 := []interface{}{_t1613, _t1614}
		unwrapped_fields876 := fields875
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field877 := unwrapped_fields876[0].([]*pb.Write)
		if field877 != nil {
			p.newline()
			opt_val878 := field877
			p.pretty_epoch_writes(opt_val878)
		}
		field879 := unwrapped_fields876[1].([]*pb.Read)
		if field879 != nil {
			p.newline()
			opt_val880 := field879
			p.pretty_epoch_reads(opt_val880)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat885 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat885 != nil {
		p.write(*flat885)
		return nil
	} else {
		fields882 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields882) == 0) {
			p.newline()
			for i884, elem883 := range fields882 {
				if (i884 > 0) {
					p.newline()
				}
				p.pretty_write(elem883)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat894 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat894 != nil {
		p.write(*flat894)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1615 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1615 = _dollar_dollar.GetDefine()
		}
		deconstruct_result892 := _t1615
		if deconstruct_result892 != nil {
			unwrapped893 := deconstruct_result892
			p.pretty_define(unwrapped893)
		} else {
			_dollar_dollar := msg
			var _t1616 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1616 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result890 := _t1616
			if deconstruct_result890 != nil {
				unwrapped891 := deconstruct_result890
				p.pretty_undefine(unwrapped891)
			} else {
				_dollar_dollar := msg
				var _t1617 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1617 = _dollar_dollar.GetContext()
				}
				deconstruct_result888 := _t1617
				if deconstruct_result888 != nil {
					unwrapped889 := deconstruct_result888
					p.pretty_context(unwrapped889)
				} else {
					_dollar_dollar := msg
					var _t1618 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1618 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result886 := _t1618
					if deconstruct_result886 != nil {
						unwrapped887 := deconstruct_result886
						p.pretty_snapshot(unwrapped887)
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
	flat897 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat897 != nil {
		p.write(*flat897)
		return nil
	} else {
		_dollar_dollar := msg
		fields895 := _dollar_dollar.GetFragment()
		unwrapped_fields896 := fields895
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields896)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat904 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat904 != nil {
		p.write(*flat904)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields898 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields899 := fields898
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field900 := unwrapped_fields899[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field900)
		field901 := unwrapped_fields899[1].([]*pb.Declaration)
		if !(len(field901) == 0) {
			p.newline()
			for i903, elem902 := range field901 {
				if (i903 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem902)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat906 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat906 != nil {
		p.write(*flat906)
		return nil
	} else {
		fields905 := msg
		p.pretty_fragment_id(fields905)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat915 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat915 != nil {
		p.write(*flat915)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1619 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1619 = _dollar_dollar.GetDef()
		}
		deconstruct_result913 := _t1619
		if deconstruct_result913 != nil {
			unwrapped914 := deconstruct_result913
			p.pretty_def(unwrapped914)
		} else {
			_dollar_dollar := msg
			var _t1620 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1620 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result911 := _t1620
			if deconstruct_result911 != nil {
				unwrapped912 := deconstruct_result911
				p.pretty_algorithm(unwrapped912)
			} else {
				_dollar_dollar := msg
				var _t1621 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1621 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result909 := _t1621
				if deconstruct_result909 != nil {
					unwrapped910 := deconstruct_result909
					p.pretty_constraint(unwrapped910)
				} else {
					_dollar_dollar := msg
					var _t1622 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1622 = _dollar_dollar.GetData()
					}
					deconstruct_result907 := _t1622
					if deconstruct_result907 != nil {
						unwrapped908 := deconstruct_result907
						p.pretty_data(unwrapped908)
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
	flat922 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat922 != nil {
		p.write(*flat922)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1623 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1623 = _dollar_dollar.GetAttrs()
		}
		fields916 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1623}
		unwrapped_fields917 := fields916
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field918 := unwrapped_fields917[0].(*pb.RelationId)
		p.pretty_relation_id(field918)
		p.newline()
		field919 := unwrapped_fields917[1].(*pb.Abstraction)
		p.pretty_abstraction(field919)
		field920 := unwrapped_fields917[2].([]*pb.Attribute)
		if field920 != nil {
			p.newline()
			opt_val921 := field920
			p.pretty_attrs(opt_val921)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat927 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat927 != nil {
		p.write(*flat927)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1624 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1625 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1624 = ptr(_t1625)
		}
		deconstruct_result925 := _t1624
		if deconstruct_result925 != nil {
			unwrapped926 := *deconstruct_result925
			p.write(":")
			p.write(unwrapped926)
		} else {
			_dollar_dollar := msg
			_t1626 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result923 := _t1626
			if deconstruct_result923 != nil {
				unwrapped924 := deconstruct_result923
				p.write(p.formatUint128(unwrapped924))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat932 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat932 != nil {
		p.write(*flat932)
		return nil
	} else {
		_dollar_dollar := msg
		_t1627 := p.deconstruct_bindings(_dollar_dollar)
		fields928 := []interface{}{_t1627, _dollar_dollar.GetValue()}
		unwrapped_fields929 := fields928
		p.write("(")
		p.indent()
		field930 := unwrapped_fields929[0].([]interface{})
		p.pretty_bindings(field930)
		p.newline()
		field931 := unwrapped_fields929[1].(*pb.Formula)
		p.pretty_formula(field931)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat940 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat940 != nil {
		p.write(*flat940)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1628 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1628 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields933 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1628}
		unwrapped_fields934 := fields933
		p.write("[")
		p.indent()
		field935 := unwrapped_fields934[0].([]*pb.Binding)
		for i937, elem936 := range field935 {
			if (i937 > 0) {
				p.newline()
			}
			p.pretty_binding(elem936)
		}
		field938 := unwrapped_fields934[1].([]*pb.Binding)
		if field938 != nil {
			p.newline()
			opt_val939 := field938
			p.pretty_value_bindings(opt_val939)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat945 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat945 != nil {
		p.write(*flat945)
		return nil
	} else {
		_dollar_dollar := msg
		fields941 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields942 := fields941
		field943 := unwrapped_fields942[0].(string)
		p.write(field943)
		p.write("::")
		field944 := unwrapped_fields942[1].(*pb.Type)
		p.pretty_type(field944)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat974 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat974 != nil {
		p.write(*flat974)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1629 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1629 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result972 := _t1629
		if deconstruct_result972 != nil {
			unwrapped973 := deconstruct_result972
			p.pretty_unspecified_type(unwrapped973)
		} else {
			_dollar_dollar := msg
			var _t1630 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1630 = _dollar_dollar.GetStringType()
			}
			deconstruct_result970 := _t1630
			if deconstruct_result970 != nil {
				unwrapped971 := deconstruct_result970
				p.pretty_string_type(unwrapped971)
			} else {
				_dollar_dollar := msg
				var _t1631 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1631 = _dollar_dollar.GetIntType()
				}
				deconstruct_result968 := _t1631
				if deconstruct_result968 != nil {
					unwrapped969 := deconstruct_result968
					p.pretty_int_type(unwrapped969)
				} else {
					_dollar_dollar := msg
					var _t1632 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1632 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result966 := _t1632
					if deconstruct_result966 != nil {
						unwrapped967 := deconstruct_result966
						p.pretty_float_type(unwrapped967)
					} else {
						_dollar_dollar := msg
						var _t1633 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1633 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result964 := _t1633
						if deconstruct_result964 != nil {
							unwrapped965 := deconstruct_result964
							p.pretty_uint128_type(unwrapped965)
						} else {
							_dollar_dollar := msg
							var _t1634 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1634 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result962 := _t1634
							if deconstruct_result962 != nil {
								unwrapped963 := deconstruct_result962
								p.pretty_int128_type(unwrapped963)
							} else {
								_dollar_dollar := msg
								var _t1635 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1635 = _dollar_dollar.GetDateType()
								}
								deconstruct_result960 := _t1635
								if deconstruct_result960 != nil {
									unwrapped961 := deconstruct_result960
									p.pretty_date_type(unwrapped961)
								} else {
									_dollar_dollar := msg
									var _t1636 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1636 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result958 := _t1636
									if deconstruct_result958 != nil {
										unwrapped959 := deconstruct_result958
										p.pretty_datetime_type(unwrapped959)
									} else {
										_dollar_dollar := msg
										var _t1637 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1637 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result956 := _t1637
										if deconstruct_result956 != nil {
											unwrapped957 := deconstruct_result956
											p.pretty_missing_type(unwrapped957)
										} else {
											_dollar_dollar := msg
											var _t1638 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1638 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result954 := _t1638
											if deconstruct_result954 != nil {
												unwrapped955 := deconstruct_result954
												p.pretty_decimal_type(unwrapped955)
											} else {
												_dollar_dollar := msg
												var _t1639 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1639 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result952 := _t1639
												if deconstruct_result952 != nil {
													unwrapped953 := deconstruct_result952
													p.pretty_boolean_type(unwrapped953)
												} else {
													_dollar_dollar := msg
													var _t1640 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1640 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result950 := _t1640
													if deconstruct_result950 != nil {
														unwrapped951 := deconstruct_result950
														p.pretty_int32_type(unwrapped951)
													} else {
														_dollar_dollar := msg
														var _t1641 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1641 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result948 := _t1641
														if deconstruct_result948 != nil {
															unwrapped949 := deconstruct_result948
															p.pretty_float32_type(unwrapped949)
														} else {
															_dollar_dollar := msg
															var _t1642 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1642 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result946 := _t1642
															if deconstruct_result946 != nil {
																unwrapped947 := deconstruct_result946
																p.pretty_uint32_type(unwrapped947)
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
	fields975 := msg
	_ = fields975
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields976 := msg
	_ = fields976
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields977 := msg
	_ = fields977
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields978 := msg
	_ = fields978
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields979 := msg
	_ = fields979
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields980 := msg
	_ = fields980
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields981 := msg
	_ = fields981
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields982 := msg
	_ = fields982
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields983 := msg
	_ = fields983
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat988 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat988 != nil {
		p.write(*flat988)
		return nil
	} else {
		_dollar_dollar := msg
		fields984 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields985 := fields984
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field986 := unwrapped_fields985[0].(int64)
		p.write(fmt.Sprintf("%d", field986))
		p.newline()
		field987 := unwrapped_fields985[1].(int64)
		p.write(fmt.Sprintf("%d", field987))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields989 := msg
	_ = fields989
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields990 := msg
	_ = fields990
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields991 := msg
	_ = fields991
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields992 := msg
	_ = fields992
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat996 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat996 != nil {
		p.write(*flat996)
		return nil
	} else {
		fields993 := msg
		p.write("|")
		if !(len(fields993) == 0) {
			p.write(" ")
			for i995, elem994 := range fields993 {
				if (i995 > 0) {
					p.newline()
				}
				p.pretty_binding(elem994)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat1023 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat1023 != nil {
		p.write(*flat1023)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1643 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1643 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result1021 := _t1643
		if deconstruct_result1021 != nil {
			unwrapped1022 := deconstruct_result1021
			p.pretty_true(unwrapped1022)
		} else {
			_dollar_dollar := msg
			var _t1644 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1644 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result1019 := _t1644
			if deconstruct_result1019 != nil {
				unwrapped1020 := deconstruct_result1019
				p.pretty_false(unwrapped1020)
			} else {
				_dollar_dollar := msg
				var _t1645 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1645 = _dollar_dollar.GetExists()
				}
				deconstruct_result1017 := _t1645
				if deconstruct_result1017 != nil {
					unwrapped1018 := deconstruct_result1017
					p.pretty_exists(unwrapped1018)
				} else {
					_dollar_dollar := msg
					var _t1646 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1646 = _dollar_dollar.GetReduce()
					}
					deconstruct_result1015 := _t1646
					if deconstruct_result1015 != nil {
						unwrapped1016 := deconstruct_result1015
						p.pretty_reduce(unwrapped1016)
					} else {
						_dollar_dollar := msg
						var _t1647 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1647 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result1013 := _t1647
						if deconstruct_result1013 != nil {
							unwrapped1014 := deconstruct_result1013
							p.pretty_conjunction(unwrapped1014)
						} else {
							_dollar_dollar := msg
							var _t1648 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1648 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result1011 := _t1648
							if deconstruct_result1011 != nil {
								unwrapped1012 := deconstruct_result1011
								p.pretty_disjunction(unwrapped1012)
							} else {
								_dollar_dollar := msg
								var _t1649 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1649 = _dollar_dollar.GetNot()
								}
								deconstruct_result1009 := _t1649
								if deconstruct_result1009 != nil {
									unwrapped1010 := deconstruct_result1009
									p.pretty_not(unwrapped1010)
								} else {
									_dollar_dollar := msg
									var _t1650 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1650 = _dollar_dollar.GetFfi()
									}
									deconstruct_result1007 := _t1650
									if deconstruct_result1007 != nil {
										unwrapped1008 := deconstruct_result1007
										p.pretty_ffi(unwrapped1008)
									} else {
										_dollar_dollar := msg
										var _t1651 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1651 = _dollar_dollar.GetAtom()
										}
										deconstruct_result1005 := _t1651
										if deconstruct_result1005 != nil {
											unwrapped1006 := deconstruct_result1005
											p.pretty_atom(unwrapped1006)
										} else {
											_dollar_dollar := msg
											var _t1652 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1652 = _dollar_dollar.GetPragma()
											}
											deconstruct_result1003 := _t1652
											if deconstruct_result1003 != nil {
												unwrapped1004 := deconstruct_result1003
												p.pretty_pragma(unwrapped1004)
											} else {
												_dollar_dollar := msg
												var _t1653 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1653 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result1001 := _t1653
												if deconstruct_result1001 != nil {
													unwrapped1002 := deconstruct_result1001
													p.pretty_primitive(unwrapped1002)
												} else {
													_dollar_dollar := msg
													var _t1654 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1654 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result999 := _t1654
													if deconstruct_result999 != nil {
														unwrapped1000 := deconstruct_result999
														p.pretty_rel_atom(unwrapped1000)
													} else {
														_dollar_dollar := msg
														var _t1655 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1655 = _dollar_dollar.GetCast()
														}
														deconstruct_result997 := _t1655
														if deconstruct_result997 != nil {
															unwrapped998 := deconstruct_result997
															p.pretty_cast(unwrapped998)
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
	fields1024 := msg
	_ = fields1024
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields1025 := msg
	_ = fields1025
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1030 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1030 != nil {
		p.write(*flat1030)
		return nil
	} else {
		_dollar_dollar := msg
		_t1656 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields1026 := []interface{}{_t1656, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1027 := fields1026
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1028 := unwrapped_fields1027[0].([]interface{})
		p.pretty_bindings(field1028)
		p.newline()
		field1029 := unwrapped_fields1027[1].(*pb.Formula)
		p.pretty_formula(field1029)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1036 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1036 != nil {
		p.write(*flat1036)
		return nil
	} else {
		_dollar_dollar := msg
		fields1031 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1032 := fields1031
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1033 := unwrapped_fields1032[0].(*pb.Abstraction)
		p.pretty_abstraction(field1033)
		p.newline()
		field1034 := unwrapped_fields1032[1].(*pb.Abstraction)
		p.pretty_abstraction(field1034)
		p.newline()
		field1035 := unwrapped_fields1032[2].([]*pb.Term)
		p.pretty_terms(field1035)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1040 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1040 != nil {
		p.write(*flat1040)
		return nil
	} else {
		fields1037 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1037) == 0) {
			p.newline()
			for i1039, elem1038 := range fields1037 {
				if (i1039 > 0) {
					p.newline()
				}
				p.pretty_term(elem1038)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1045 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1045 != nil {
		p.write(*flat1045)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1657 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1657 = _dollar_dollar.GetVar()
		}
		deconstruct_result1043 := _t1657
		if deconstruct_result1043 != nil {
			unwrapped1044 := deconstruct_result1043
			p.pretty_var(unwrapped1044)
		} else {
			_dollar_dollar := msg
			var _t1658 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1658 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1041 := _t1658
			if deconstruct_result1041 != nil {
				unwrapped1042 := deconstruct_result1041
				p.pretty_value(unwrapped1042)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1048 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1048 != nil {
		p.write(*flat1048)
		return nil
	} else {
		_dollar_dollar := msg
		fields1046 := _dollar_dollar.GetName()
		unwrapped_fields1047 := fields1046
		p.write(unwrapped_fields1047)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1074 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1074 != nil {
		p.write(*flat1074)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1659 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1659 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1072 := _t1659
		if deconstruct_result1072 != nil {
			unwrapped1073 := deconstruct_result1072
			p.pretty_date(unwrapped1073)
		} else {
			_dollar_dollar := msg
			var _t1660 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1660 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1070 := _t1660
			if deconstruct_result1070 != nil {
				unwrapped1071 := deconstruct_result1070
				p.pretty_datetime(unwrapped1071)
			} else {
				_dollar_dollar := msg
				var _t1661 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1661 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1068 := _t1661
				if deconstruct_result1068 != nil {
					unwrapped1069 := *deconstruct_result1068
					p.write(p.formatStringValue(unwrapped1069))
				} else {
					_dollar_dollar := msg
					var _t1662 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1662 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1066 := _t1662
					if deconstruct_result1066 != nil {
						unwrapped1067 := *deconstruct_result1066
						p.write(fmt.Sprintf("%di32", unwrapped1067))
					} else {
						_dollar_dollar := msg
						var _t1663 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1663 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1064 := _t1663
						if deconstruct_result1064 != nil {
							unwrapped1065 := *deconstruct_result1064
							p.write(fmt.Sprintf("%d", unwrapped1065))
						} else {
							_dollar_dollar := msg
							var _t1664 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1664 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1062 := _t1664
							if deconstruct_result1062 != nil {
								unwrapped1063 := *deconstruct_result1062
								p.write(formatFloat32(unwrapped1063))
							} else {
								_dollar_dollar := msg
								var _t1665 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1665 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1060 := _t1665
								if deconstruct_result1060 != nil {
									unwrapped1061 := *deconstruct_result1060
									p.write(formatFloat64(unwrapped1061))
								} else {
									_dollar_dollar := msg
									var _t1666 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1666 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1058 := _t1666
									if deconstruct_result1058 != nil {
										unwrapped1059 := *deconstruct_result1058
										p.write(fmt.Sprintf("%du32", unwrapped1059))
									} else {
										_dollar_dollar := msg
										var _t1667 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1667 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1056 := _t1667
										if deconstruct_result1056 != nil {
											unwrapped1057 := deconstruct_result1056
											p.write(p.formatUint128(unwrapped1057))
										} else {
											_dollar_dollar := msg
											var _t1668 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1668 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1054 := _t1668
											if deconstruct_result1054 != nil {
												unwrapped1055 := deconstruct_result1054
												p.write(p.formatInt128(unwrapped1055))
											} else {
												_dollar_dollar := msg
												var _t1669 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1669 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1052 := _t1669
												if deconstruct_result1052 != nil {
													unwrapped1053 := deconstruct_result1052
													p.write(p.formatDecimal(unwrapped1053))
												} else {
													_dollar_dollar := msg
													var _t1670 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1670 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1050 := _t1670
													if deconstruct_result1050 != nil {
														unwrapped1051 := *deconstruct_result1050
														p.pretty_boolean_value(unwrapped1051)
													} else {
														fields1049 := msg
														_ = fields1049
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
	flat1080 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1080 != nil {
		p.write(*flat1080)
		return nil
	} else {
		_dollar_dollar := msg
		fields1075 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1076 := fields1075
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1077 := unwrapped_fields1076[0].(int64)
		p.write(fmt.Sprintf("%d", field1077))
		p.newline()
		field1078 := unwrapped_fields1076[1].(int64)
		p.write(fmt.Sprintf("%d", field1078))
		p.newline()
		field1079 := unwrapped_fields1076[2].(int64)
		p.write(fmt.Sprintf("%d", field1079))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1091 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1091 != nil {
		p.write(*flat1091)
		return nil
	} else {
		_dollar_dollar := msg
		fields1081 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1082 := fields1081
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1083 := unwrapped_fields1082[0].(int64)
		p.write(fmt.Sprintf("%d", field1083))
		p.newline()
		field1084 := unwrapped_fields1082[1].(int64)
		p.write(fmt.Sprintf("%d", field1084))
		p.newline()
		field1085 := unwrapped_fields1082[2].(int64)
		p.write(fmt.Sprintf("%d", field1085))
		p.newline()
		field1086 := unwrapped_fields1082[3].(int64)
		p.write(fmt.Sprintf("%d", field1086))
		p.newline()
		field1087 := unwrapped_fields1082[4].(int64)
		p.write(fmt.Sprintf("%d", field1087))
		p.newline()
		field1088 := unwrapped_fields1082[5].(int64)
		p.write(fmt.Sprintf("%d", field1088))
		field1089 := unwrapped_fields1082[6].(*int64)
		if field1089 != nil {
			p.newline()
			opt_val1090 := *field1089
			p.write(fmt.Sprintf("%d", opt_val1090))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1096 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1096 != nil {
		p.write(*flat1096)
		return nil
	} else {
		_dollar_dollar := msg
		fields1092 := _dollar_dollar.GetArgs()
		unwrapped_fields1093 := fields1092
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1093) == 0) {
			p.newline()
			for i1095, elem1094 := range unwrapped_fields1093 {
				if (i1095 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1094)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1101 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1101 != nil {
		p.write(*flat1101)
		return nil
	} else {
		_dollar_dollar := msg
		fields1097 := _dollar_dollar.GetArgs()
		unwrapped_fields1098 := fields1097
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1098) == 0) {
			p.newline()
			for i1100, elem1099 := range unwrapped_fields1098 {
				if (i1100 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1099)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1104 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1104 != nil {
		p.write(*flat1104)
		return nil
	} else {
		_dollar_dollar := msg
		fields1102 := _dollar_dollar.GetArg()
		unwrapped_fields1103 := fields1102
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1103)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1110 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1110 != nil {
		p.write(*flat1110)
		return nil
	} else {
		_dollar_dollar := msg
		fields1105 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1106 := fields1105
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1107 := unwrapped_fields1106[0].(string)
		p.pretty_name(field1107)
		p.newline()
		field1108 := unwrapped_fields1106[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1108)
		p.newline()
		field1109 := unwrapped_fields1106[2].([]*pb.Term)
		p.pretty_terms(field1109)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1112 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1112 != nil {
		p.write(*flat1112)
		return nil
	} else {
		fields1111 := msg
		p.write(":")
		p.write(fields1111)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1116 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1116 != nil {
		p.write(*flat1116)
		return nil
	} else {
		fields1113 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1113) == 0) {
			p.newline()
			for i1115, elem1114 := range fields1113 {
				if (i1115 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1114)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1123 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1123 != nil {
		p.write(*flat1123)
		return nil
	} else {
		_dollar_dollar := msg
		fields1117 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1118 := fields1117
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1119 := unwrapped_fields1118[0].(*pb.RelationId)
		p.pretty_relation_id(field1119)
		field1120 := unwrapped_fields1118[1].([]*pb.Term)
		if !(len(field1120) == 0) {
			p.newline()
			for i1122, elem1121 := range field1120 {
				if (i1122 > 0) {
					p.newline()
				}
				p.pretty_term(elem1121)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1130 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1130 != nil {
		p.write(*flat1130)
		return nil
	} else {
		_dollar_dollar := msg
		fields1124 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1125 := fields1124
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1126 := unwrapped_fields1125[0].(string)
		p.pretty_name(field1126)
		field1127 := unwrapped_fields1125[1].([]*pb.Term)
		if !(len(field1127) == 0) {
			p.newline()
			for i1129, elem1128 := range field1127 {
				if (i1129 > 0) {
					p.newline()
				}
				p.pretty_term(elem1128)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1146 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1146 != nil {
		p.write(*flat1146)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1671 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1671 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1145 := _t1671
		if guard_result1145 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1672 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1672 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1144 := _t1672
			if guard_result1144 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1673 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1673 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1143 := _t1673
				if guard_result1143 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1674 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1674 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1142 := _t1674
					if guard_result1142 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1675 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1675 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1141 := _t1675
						if guard_result1141 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1676 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1676 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1140 := _t1676
							if guard_result1140 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1677 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1677 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1139 := _t1677
								if guard_result1139 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1678 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1678 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1138 := _t1678
									if guard_result1138 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1679 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1679 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1137 := _t1679
										if guard_result1137 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1131 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1132 := fields1131
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1133 := unwrapped_fields1132[0].(string)
											p.pretty_name(field1133)
											field1134 := unwrapped_fields1132[1].([]*pb.RelTerm)
											if !(len(field1134) == 0) {
												p.newline()
												for i1136, elem1135 := range field1134 {
													if (i1136 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1135)
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
	flat1151 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1151 != nil {
		p.write(*flat1151)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1680 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1680 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1147 := _t1680
		unwrapped_fields1148 := fields1147
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1149 := unwrapped_fields1148[0].(*pb.Term)
		p.pretty_term(field1149)
		p.newline()
		field1150 := unwrapped_fields1148[1].(*pb.Term)
		p.pretty_term(field1150)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1156 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1156 != nil {
		p.write(*flat1156)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1681 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1681 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1152 := _t1681
		unwrapped_fields1153 := fields1152
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1154 := unwrapped_fields1153[0].(*pb.Term)
		p.pretty_term(field1154)
		p.newline()
		field1155 := unwrapped_fields1153[1].(*pb.Term)
		p.pretty_term(field1155)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1161 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1161 != nil {
		p.write(*flat1161)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1682 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1682 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1157 := _t1682
		unwrapped_fields1158 := fields1157
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1159 := unwrapped_fields1158[0].(*pb.Term)
		p.pretty_term(field1159)
		p.newline()
		field1160 := unwrapped_fields1158[1].(*pb.Term)
		p.pretty_term(field1160)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1166 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1166 != nil {
		p.write(*flat1166)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1683 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1683 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1162 := _t1683
		unwrapped_fields1163 := fields1162
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1164 := unwrapped_fields1163[0].(*pb.Term)
		p.pretty_term(field1164)
		p.newline()
		field1165 := unwrapped_fields1163[1].(*pb.Term)
		p.pretty_term(field1165)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1171 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1171 != nil {
		p.write(*flat1171)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1684 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1684 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1167 := _t1684
		unwrapped_fields1168 := fields1167
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1169 := unwrapped_fields1168[0].(*pb.Term)
		p.pretty_term(field1169)
		p.newline()
		field1170 := unwrapped_fields1168[1].(*pb.Term)
		p.pretty_term(field1170)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1177 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1177 != nil {
		p.write(*flat1177)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1685 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1685 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1172 := _t1685
		unwrapped_fields1173 := fields1172
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1174 := unwrapped_fields1173[0].(*pb.Term)
		p.pretty_term(field1174)
		p.newline()
		field1175 := unwrapped_fields1173[1].(*pb.Term)
		p.pretty_term(field1175)
		p.newline()
		field1176 := unwrapped_fields1173[2].(*pb.Term)
		p.pretty_term(field1176)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1183 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1183 != nil {
		p.write(*flat1183)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1686 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1686 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1178 := _t1686
		unwrapped_fields1179 := fields1178
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1180 := unwrapped_fields1179[0].(*pb.Term)
		p.pretty_term(field1180)
		p.newline()
		field1181 := unwrapped_fields1179[1].(*pb.Term)
		p.pretty_term(field1181)
		p.newline()
		field1182 := unwrapped_fields1179[2].(*pb.Term)
		p.pretty_term(field1182)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1189 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1189 != nil {
		p.write(*flat1189)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1687 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1687 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1184 := _t1687
		unwrapped_fields1185 := fields1184
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1186 := unwrapped_fields1185[0].(*pb.Term)
		p.pretty_term(field1186)
		p.newline()
		field1187 := unwrapped_fields1185[1].(*pb.Term)
		p.pretty_term(field1187)
		p.newline()
		field1188 := unwrapped_fields1185[2].(*pb.Term)
		p.pretty_term(field1188)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1195 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1195 != nil {
		p.write(*flat1195)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1688 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1688 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1190 := _t1688
		unwrapped_fields1191 := fields1190
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1192 := unwrapped_fields1191[0].(*pb.Term)
		p.pretty_term(field1192)
		p.newline()
		field1193 := unwrapped_fields1191[1].(*pb.Term)
		p.pretty_term(field1193)
		p.newline()
		field1194 := unwrapped_fields1191[2].(*pb.Term)
		p.pretty_term(field1194)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1200 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1200 != nil {
		p.write(*flat1200)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1689 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1689 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1198 := _t1689
		if deconstruct_result1198 != nil {
			unwrapped1199 := deconstruct_result1198
			p.pretty_specialized_value(unwrapped1199)
		} else {
			_dollar_dollar := msg
			var _t1690 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1690 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1196 := _t1690
			if deconstruct_result1196 != nil {
				unwrapped1197 := deconstruct_result1196
				p.pretty_term(unwrapped1197)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1202 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1202 != nil {
		p.write(*flat1202)
		return nil
	} else {
		fields1201 := msg
		p.write("#")
		p.pretty_raw_value(fields1201)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1209 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1209 != nil {
		p.write(*flat1209)
		return nil
	} else {
		_dollar_dollar := msg
		fields1203 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1204 := fields1203
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1205 := unwrapped_fields1204[0].(string)
		p.pretty_name(field1205)
		field1206 := unwrapped_fields1204[1].([]*pb.RelTerm)
		if !(len(field1206) == 0) {
			p.newline()
			for i1208, elem1207 := range field1206 {
				if (i1208 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1207)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1214 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1214 != nil {
		p.write(*flat1214)
		return nil
	} else {
		_dollar_dollar := msg
		fields1210 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1211 := fields1210
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1212 := unwrapped_fields1211[0].(*pb.Term)
		p.pretty_term(field1212)
		p.newline()
		field1213 := unwrapped_fields1211[1].(*pb.Term)
		p.pretty_term(field1213)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1218 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1218 != nil {
		p.write(*flat1218)
		return nil
	} else {
		fields1215 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1215) == 0) {
			p.newline()
			for i1217, elem1216 := range fields1215 {
				if (i1217 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1216)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1225 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1225 != nil {
		p.write(*flat1225)
		return nil
	} else {
		_dollar_dollar := msg
		fields1219 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1220 := fields1219
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1221 := unwrapped_fields1220[0].(string)
		p.pretty_name(field1221)
		field1222 := unwrapped_fields1220[1].([]*pb.Value)
		if !(len(field1222) == 0) {
			p.newline()
			for i1224, elem1223 := range field1222 {
				if (i1224 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1223)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1232 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1232 != nil {
		p.write(*flat1232)
		return nil
	} else {
		_dollar_dollar := msg
		fields1226 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1227 := fields1226
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1228 := unwrapped_fields1227[0].([]*pb.RelationId)
		if !(len(field1228) == 0) {
			p.newline()
			for i1230, elem1229 := range field1228 {
				if (i1230 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1229)
			}
		}
		p.newline()
		field1231 := unwrapped_fields1227[1].(*pb.Script)
		p.pretty_script(field1231)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1237 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1237 != nil {
		p.write(*flat1237)
		return nil
	} else {
		_dollar_dollar := msg
		fields1233 := _dollar_dollar.GetConstructs()
		unwrapped_fields1234 := fields1233
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1234) == 0) {
			p.newline()
			for i1236, elem1235 := range unwrapped_fields1234 {
				if (i1236 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1235)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1242 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1242 != nil {
		p.write(*flat1242)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1691 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1691 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1240 := _t1691
		if deconstruct_result1240 != nil {
			unwrapped1241 := deconstruct_result1240
			p.pretty_loop(unwrapped1241)
		} else {
			_dollar_dollar := msg
			var _t1692 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1692 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1238 := _t1692
			if deconstruct_result1238 != nil {
				unwrapped1239 := deconstruct_result1238
				p.pretty_instruction(unwrapped1239)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1247 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1247 != nil {
		p.write(*flat1247)
		return nil
	} else {
		_dollar_dollar := msg
		fields1243 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1244 := fields1243
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1245 := unwrapped_fields1244[0].([]*pb.Instruction)
		p.pretty_init(field1245)
		p.newline()
		field1246 := unwrapped_fields1244[1].(*pb.Script)
		p.pretty_script(field1246)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1251 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1251 != nil {
		p.write(*flat1251)
		return nil
	} else {
		fields1248 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1248) == 0) {
			p.newline()
			for i1250, elem1249 := range fields1248 {
				if (i1250 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1249)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1262 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1262 != nil {
		p.write(*flat1262)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1693 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1693 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1260 := _t1693
		if deconstruct_result1260 != nil {
			unwrapped1261 := deconstruct_result1260
			p.pretty_assign(unwrapped1261)
		} else {
			_dollar_dollar := msg
			var _t1694 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1694 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1258 := _t1694
			if deconstruct_result1258 != nil {
				unwrapped1259 := deconstruct_result1258
				p.pretty_upsert(unwrapped1259)
			} else {
				_dollar_dollar := msg
				var _t1695 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1695 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1256 := _t1695
				if deconstruct_result1256 != nil {
					unwrapped1257 := deconstruct_result1256
					p.pretty_break(unwrapped1257)
				} else {
					_dollar_dollar := msg
					var _t1696 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1696 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1254 := _t1696
					if deconstruct_result1254 != nil {
						unwrapped1255 := deconstruct_result1254
						p.pretty_monoid_def(unwrapped1255)
					} else {
						_dollar_dollar := msg
						var _t1697 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1697 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1252 := _t1697
						if deconstruct_result1252 != nil {
							unwrapped1253 := deconstruct_result1252
							p.pretty_monus_def(unwrapped1253)
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
	flat1269 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1269 != nil {
		p.write(*flat1269)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1698 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1698 = _dollar_dollar.GetAttrs()
		}
		fields1263 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1698}
		unwrapped_fields1264 := fields1263
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1265 := unwrapped_fields1264[0].(*pb.RelationId)
		p.pretty_relation_id(field1265)
		p.newline()
		field1266 := unwrapped_fields1264[1].(*pb.Abstraction)
		p.pretty_abstraction(field1266)
		field1267 := unwrapped_fields1264[2].([]*pb.Attribute)
		if field1267 != nil {
			p.newline()
			opt_val1268 := field1267
			p.pretty_attrs(opt_val1268)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1276 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1276 != nil {
		p.write(*flat1276)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1699 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1699 = _dollar_dollar.GetAttrs()
		}
		fields1270 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1699}
		unwrapped_fields1271 := fields1270
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1272 := unwrapped_fields1271[0].(*pb.RelationId)
		p.pretty_relation_id(field1272)
		p.newline()
		field1273 := unwrapped_fields1271[1].([]interface{})
		p.pretty_abstraction_with_arity(field1273)
		field1274 := unwrapped_fields1271[2].([]*pb.Attribute)
		if field1274 != nil {
			p.newline()
			opt_val1275 := field1274
			p.pretty_attrs(opt_val1275)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1281 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1281 != nil {
		p.write(*flat1281)
		return nil
	} else {
		_dollar_dollar := msg
		_t1700 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1277 := []interface{}{_t1700, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1278 := fields1277
		p.write("(")
		p.indent()
		field1279 := unwrapped_fields1278[0].([]interface{})
		p.pretty_bindings(field1279)
		p.newline()
		field1280 := unwrapped_fields1278[1].(*pb.Formula)
		p.pretty_formula(field1280)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1288 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1288 != nil {
		p.write(*flat1288)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1701 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1701 = _dollar_dollar.GetAttrs()
		}
		fields1282 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1701}
		unwrapped_fields1283 := fields1282
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1284 := unwrapped_fields1283[0].(*pb.RelationId)
		p.pretty_relation_id(field1284)
		p.newline()
		field1285 := unwrapped_fields1283[1].(*pb.Abstraction)
		p.pretty_abstraction(field1285)
		field1286 := unwrapped_fields1283[2].([]*pb.Attribute)
		if field1286 != nil {
			p.newline()
			opt_val1287 := field1286
			p.pretty_attrs(opt_val1287)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1296 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1296 != nil {
		p.write(*flat1296)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1702 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1702 = _dollar_dollar.GetAttrs()
		}
		fields1289 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1702}
		unwrapped_fields1290 := fields1289
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1291 := unwrapped_fields1290[0].(*pb.Monoid)
		p.pretty_monoid(field1291)
		p.newline()
		field1292 := unwrapped_fields1290[1].(*pb.RelationId)
		p.pretty_relation_id(field1292)
		p.newline()
		field1293 := unwrapped_fields1290[2].([]interface{})
		p.pretty_abstraction_with_arity(field1293)
		field1294 := unwrapped_fields1290[3].([]*pb.Attribute)
		if field1294 != nil {
			p.newline()
			opt_val1295 := field1294
			p.pretty_attrs(opt_val1295)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1305 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1305 != nil {
		p.write(*flat1305)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1703 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1703 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1303 := _t1703
		if deconstruct_result1303 != nil {
			unwrapped1304 := deconstruct_result1303
			p.pretty_or_monoid(unwrapped1304)
		} else {
			_dollar_dollar := msg
			var _t1704 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1704 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1301 := _t1704
			if deconstruct_result1301 != nil {
				unwrapped1302 := deconstruct_result1301
				p.pretty_min_monoid(unwrapped1302)
			} else {
				_dollar_dollar := msg
				var _t1705 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1705 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1299 := _t1705
				if deconstruct_result1299 != nil {
					unwrapped1300 := deconstruct_result1299
					p.pretty_max_monoid(unwrapped1300)
				} else {
					_dollar_dollar := msg
					var _t1706 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1706 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1297 := _t1706
					if deconstruct_result1297 != nil {
						unwrapped1298 := deconstruct_result1297
						p.pretty_sum_monoid(unwrapped1298)
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
	fields1306 := msg
	_ = fields1306
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1309 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1309 != nil {
		p.write(*flat1309)
		return nil
	} else {
		_dollar_dollar := msg
		fields1307 := _dollar_dollar.GetType()
		unwrapped_fields1308 := fields1307
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1308)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1312 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1312 != nil {
		p.write(*flat1312)
		return nil
	} else {
		_dollar_dollar := msg
		fields1310 := _dollar_dollar.GetType()
		unwrapped_fields1311 := fields1310
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1311)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1315 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1315 != nil {
		p.write(*flat1315)
		return nil
	} else {
		_dollar_dollar := msg
		fields1313 := _dollar_dollar.GetType()
		unwrapped_fields1314 := fields1313
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1314)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1323 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1323 != nil {
		p.write(*flat1323)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1707 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1707 = _dollar_dollar.GetAttrs()
		}
		fields1316 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1707}
		unwrapped_fields1317 := fields1316
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1318 := unwrapped_fields1317[0].(*pb.Monoid)
		p.pretty_monoid(field1318)
		p.newline()
		field1319 := unwrapped_fields1317[1].(*pb.RelationId)
		p.pretty_relation_id(field1319)
		p.newline()
		field1320 := unwrapped_fields1317[2].([]interface{})
		p.pretty_abstraction_with_arity(field1320)
		field1321 := unwrapped_fields1317[3].([]*pb.Attribute)
		if field1321 != nil {
			p.newline()
			opt_val1322 := field1321
			p.pretty_attrs(opt_val1322)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1330 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1330 != nil {
		p.write(*flat1330)
		return nil
	} else {
		_dollar_dollar := msg
		fields1324 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1325 := fields1324
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1326 := unwrapped_fields1325[0].(*pb.RelationId)
		p.pretty_relation_id(field1326)
		p.newline()
		field1327 := unwrapped_fields1325[1].(*pb.Abstraction)
		p.pretty_abstraction(field1327)
		p.newline()
		field1328 := unwrapped_fields1325[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1328)
		p.newline()
		field1329 := unwrapped_fields1325[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1329)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1334 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1334 != nil {
		p.write(*flat1334)
		return nil
	} else {
		fields1331 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1331) == 0) {
			p.newline()
			for i1333, elem1332 := range fields1331 {
				if (i1333 > 0) {
					p.newline()
				}
				p.pretty_var(elem1332)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1338 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1338 != nil {
		p.write(*flat1338)
		return nil
	} else {
		fields1335 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1335) == 0) {
			p.newline()
			for i1337, elem1336 := range fields1335 {
				if (i1337 > 0) {
					p.newline()
				}
				p.pretty_var(elem1336)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1347 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1347 != nil {
		p.write(*flat1347)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1708 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1708 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1345 := _t1708
		if deconstruct_result1345 != nil {
			unwrapped1346 := deconstruct_result1345
			p.pretty_edb(unwrapped1346)
		} else {
			_dollar_dollar := msg
			var _t1709 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1709 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1343 := _t1709
			if deconstruct_result1343 != nil {
				unwrapped1344 := deconstruct_result1343
				p.pretty_betree_relation(unwrapped1344)
			} else {
				_dollar_dollar := msg
				var _t1710 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1710 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1341 := _t1710
				if deconstruct_result1341 != nil {
					unwrapped1342 := deconstruct_result1341
					p.pretty_csv_data(unwrapped1342)
				} else {
					_dollar_dollar := msg
					var _t1711 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1711 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1339 := _t1711
					if deconstruct_result1339 != nil {
						unwrapped1340 := deconstruct_result1339
						p.pretty_iceberg_data(unwrapped1340)
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
	flat1353 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1353 != nil {
		p.write(*flat1353)
		return nil
	} else {
		_dollar_dollar := msg
		fields1348 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1349 := fields1348
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1350 := unwrapped_fields1349[0].(*pb.RelationId)
		p.pretty_relation_id(field1350)
		p.newline()
		field1351 := unwrapped_fields1349[1].([]string)
		p.pretty_edb_path(field1351)
		p.newline()
		field1352 := unwrapped_fields1349[2].([]*pb.Type)
		p.pretty_edb_types(field1352)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1357 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1357 != nil {
		p.write(*flat1357)
		return nil
	} else {
		fields1354 := msg
		p.write("[")
		p.indent()
		for i1356, elem1355 := range fields1354 {
			if (i1356 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1355))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1361 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1361 != nil {
		p.write(*flat1361)
		return nil
	} else {
		fields1358 := msg
		p.write("[")
		p.indent()
		for i1360, elem1359 := range fields1358 {
			if (i1360 > 0) {
				p.newline()
			}
			p.pretty_type(elem1359)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1366 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1366 != nil {
		p.write(*flat1366)
		return nil
	} else {
		_dollar_dollar := msg
		fields1362 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1363 := fields1362
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1364 := unwrapped_fields1363[0].(*pb.RelationId)
		p.pretty_relation_id(field1364)
		p.newline()
		field1365 := unwrapped_fields1363[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1365)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1372 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1372 != nil {
		p.write(*flat1372)
		return nil
	} else {
		_dollar_dollar := msg
		_t1712 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1367 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1712}
		unwrapped_fields1368 := fields1367
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1369 := unwrapped_fields1368[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1369)
		p.newline()
		field1370 := unwrapped_fields1368[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1370)
		p.newline()
		field1371 := unwrapped_fields1368[2].([][]interface{})
		p.pretty_config_dict(field1371)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1376 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1376 != nil {
		p.write(*flat1376)
		return nil
	} else {
		fields1373 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1373) == 0) {
			p.newline()
			for i1375, elem1374 := range fields1373 {
				if (i1375 > 0) {
					p.newline()
				}
				p.pretty_type(elem1374)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1380 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1380 != nil {
		p.write(*flat1380)
		return nil
	} else {
		fields1377 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1377) == 0) {
			p.newline()
			for i1379, elem1378 := range fields1377 {
				if (i1379 > 0) {
					p.newline()
				}
				p.pretty_type(elem1378)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1387 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1387 != nil {
		p.write(*flat1387)
		return nil
	} else {
		_dollar_dollar := msg
		fields1381 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1382 := fields1381
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1383 := unwrapped_fields1382[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1383)
		p.newline()
		field1384 := unwrapped_fields1382[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1384)
		p.newline()
		field1385 := unwrapped_fields1382[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1385)
		p.newline()
		field1386 := unwrapped_fields1382[3].(string)
		p.pretty_csv_asof(field1386)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1394 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1394 != nil {
		p.write(*flat1394)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1713 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1713 = _dollar_dollar.GetPaths()
		}
		var _t1714 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1714 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1388 := []interface{}{_t1713, _t1714}
		unwrapped_fields1389 := fields1388
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1390 := unwrapped_fields1389[0].([]string)
		if field1390 != nil {
			p.newline()
			opt_val1391 := field1390
			p.pretty_csv_locator_paths(opt_val1391)
		}
		field1392 := unwrapped_fields1389[1].(*string)
		if field1392 != nil {
			p.newline()
			opt_val1393 := *field1392
			p.pretty_csv_locator_inline_data(opt_val1393)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1398 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1398 != nil {
		p.write(*flat1398)
		return nil
	} else {
		fields1395 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1395) == 0) {
			p.newline()
			for i1397, elem1396 := range fields1395 {
				if (i1397 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1396))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1400 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1400 != nil {
		p.write(*flat1400)
		return nil
	} else {
		fields1399 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1399))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1403 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1403 != nil {
		p.write(*flat1403)
		return nil
	} else {
		_dollar_dollar := msg
		_t1715 := p.deconstruct_csv_config(_dollar_dollar)
		fields1401 := _t1715
		unwrapped_fields1402 := fields1401
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1402)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1407 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1407 != nil {
		p.write(*flat1407)
		return nil
	} else {
		fields1404 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1404) == 0) {
			p.newline()
			for i1406, elem1405 := range fields1404 {
				if (i1406 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1405)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1416 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1416 != nil {
		p.write(*flat1416)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1716 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1716 = _dollar_dollar.GetTargetId()
		}
		fields1408 := []interface{}{_dollar_dollar.GetColumnPath(), _t1716, _dollar_dollar.GetTypes()}
		unwrapped_fields1409 := fields1408
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1410 := unwrapped_fields1409[0].([]string)
		p.pretty_gnf_column_path(field1410)
		field1411 := unwrapped_fields1409[1].(*pb.RelationId)
		if field1411 != nil {
			p.newline()
			opt_val1412 := field1411
			p.pretty_relation_id(opt_val1412)
		}
		p.newline()
		p.write("[")
		field1413 := unwrapped_fields1409[2].([]*pb.Type)
		for i1415, elem1414 := range field1413 {
			if (i1415 > 0) {
				p.newline()
			}
			p.pretty_type(elem1414)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1423 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1423 != nil {
		p.write(*flat1423)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1717 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1717 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1421 := _t1717
		if deconstruct_result1421 != nil {
			unwrapped1422 := *deconstruct_result1421
			p.write(p.formatStringValue(unwrapped1422))
		} else {
			_dollar_dollar := msg
			var _t1718 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1718 = _dollar_dollar
			}
			deconstruct_result1417 := _t1718
			if deconstruct_result1417 != nil {
				unwrapped1418 := deconstruct_result1417
				p.write("[")
				p.indent()
				for i1420, elem1419 := range unwrapped1418 {
					if (i1420 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1419))
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
	flat1425 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1425 != nil {
		p.write(*flat1425)
		return nil
	} else {
		fields1424 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1424))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1436 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1436 != nil {
		p.write(*flat1436)
		return nil
	} else {
		_dollar_dollar := msg
		_t1719 := p.deconstruct_iceberg_data_from_snapshot_optional(_dollar_dollar)
		_t1720 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1426 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1719, _t1720, _dollar_dollar.GetReturnsDelta()}
		unwrapped_fields1427 := fields1426
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1428 := unwrapped_fields1427[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1428)
		p.newline()
		field1429 := unwrapped_fields1427[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1429)
		p.newline()
		field1430 := unwrapped_fields1427[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1430)
		field1431 := unwrapped_fields1427[3].(*string)
		if field1431 != nil {
			p.newline()
			opt_val1432 := *field1431
			p.pretty_iceberg_from_snapshot(opt_val1432)
		}
		field1433 := unwrapped_fields1427[4].(*string)
		if field1433 != nil {
			p.newline()
			opt_val1434 := *field1433
			p.pretty_iceberg_to_snapshot(opt_val1434)
		}
		p.newline()
		field1435 := unwrapped_fields1427[5].(bool)
		p.pretty_boolean_value(field1435)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1442 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1442 != nil {
		p.write(*flat1442)
		return nil
	} else {
		_dollar_dollar := msg
		fields1437 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1438 := fields1437
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		field1439 := unwrapped_fields1438[0].(string)
		p.pretty_iceberg_locator_table_name(field1439)
		p.newline()
		field1440 := unwrapped_fields1438[1].([]string)
		p.pretty_iceberg_locator_namespace(field1440)
		p.newline()
		field1441 := unwrapped_fields1438[2].(string)
		p.pretty_iceberg_locator_warehouse(field1441)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_table_name(msg string) interface{} {
	flat1444 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_table_name(msg) })
	if flat1444 != nil {
		p.write(*flat1444)
		return nil
	} else {
		fields1443 := msg
		p.write("(")
		p.write("table_name")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1443))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_namespace(msg []string) interface{} {
	flat1448 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_namespace(msg) })
	if flat1448 != nil {
		p.write(*flat1448)
		return nil
	} else {
		fields1445 := msg
		p.write("(")
		p.write("namespace")
		p.indentSexp()
		if !(len(fields1445) == 0) {
			p.newline()
			for i1447, elem1446 := range fields1445 {
				if (i1447 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1446))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator_warehouse(msg string) interface{} {
	flat1450 := p.tryFlat(msg, func() { p.pretty_iceberg_locator_warehouse(msg) })
	if flat1450 != nil {
		p.write(*flat1450)
		return nil
	} else {
		fields1449 := msg
		p.write("(")
		p.write("warehouse")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1449))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1458 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1458 != nil {
		p.write(*flat1458)
		return nil
	} else {
		_dollar_dollar := msg
		_t1721 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1451 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1721, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1452 := fields1451
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		field1453 := unwrapped_fields1452[0].(string)
		p.pretty_iceberg_catalog_uri(field1453)
		field1454 := unwrapped_fields1452[1].(*string)
		if field1454 != nil {
			p.newline()
			opt_val1455 := *field1454
			p.pretty_iceberg_catalog_config_scope(opt_val1455)
		}
		p.newline()
		field1456 := unwrapped_fields1452[2].([][]interface{})
		p.pretty_iceberg_properties(field1456)
		p.newline()
		field1457 := unwrapped_fields1452[3].([][]interface{})
		p.pretty_iceberg_auth_properties(field1457)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_uri(msg string) interface{} {
	flat1460 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_uri(msg) })
	if flat1460 != nil {
		p.write(*flat1460)
		return nil
	} else {
		fields1459 := msg
		p.write("(")
		p.write("catalog_uri")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1459))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1462 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1462 != nil {
		p.write(*flat1462)
		return nil
	} else {
		fields1461 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1461))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_properties(msg [][]interface{}) interface{} {
	flat1466 := p.tryFlat(msg, func() { p.pretty_iceberg_properties(msg) })
	if flat1466 != nil {
		p.write(*flat1466)
		return nil
	} else {
		fields1463 := msg
		p.write("(")
		p.write("properties")
		p.indentSexp()
		if !(len(fields1463) == 0) {
			p.newline()
			for i1465, elem1464 := range fields1463 {
				if (i1465 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1464)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1471 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1471 != nil {
		p.write(*flat1471)
		return nil
	} else {
		_dollar_dollar := msg
		fields1467 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1468 := fields1467
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1469 := unwrapped_fields1468[0].(string)
		p.write(p.formatStringValue(field1469))
		p.newline()
		field1470 := unwrapped_fields1468[1].(string)
		p.write(p.formatStringValue(field1470))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_auth_properties(msg [][]interface{}) interface{} {
	flat1475 := p.tryFlat(msg, func() { p.pretty_iceberg_auth_properties(msg) })
	if flat1475 != nil {
		p.write(*flat1475)
		return nil
	} else {
		fields1472 := msg
		p.write("(")
		p.write("auth_properties")
		p.indentSexp()
		if !(len(fields1472) == 0) {
			p.newline()
			for i1474, elem1473 := range fields1472 {
				if (i1474 > 0) {
					p.newline()
				}
				p.pretty_iceberg_masked_property_entry(elem1473)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_masked_property_entry(msg []interface{}) interface{} {
	flat1480 := p.tryFlat(msg, func() { p.pretty_iceberg_masked_property_entry(msg) })
	if flat1480 != nil {
		p.write(*flat1480)
		return nil
	} else {
		_dollar_dollar := msg
		_t1722 := p.mask_secret_value(_dollar_dollar)
		fields1476 := []interface{}{_dollar_dollar[0].(string), _t1722}
		unwrapped_fields1477 := fields1476
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1478 := unwrapped_fields1477[0].(string)
		p.write(p.formatStringValue(field1478))
		p.newline()
		field1479 := unwrapped_fields1477[1].(string)
		p.write(p.formatStringValue(field1479))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_from_snapshot(msg string) interface{} {
	flat1482 := p.tryFlat(msg, func() { p.pretty_iceberg_from_snapshot(msg) })
	if flat1482 != nil {
		p.write(*flat1482)
		return nil
	} else {
		fields1481 := msg
		p.write("(")
		p.write("from_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1481))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1484 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1484 != nil {
		p.write(*flat1484)
		return nil
	} else {
		fields1483 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1483))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1487 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1487 != nil {
		p.write(*flat1487)
		return nil
	} else {
		_dollar_dollar := msg
		fields1485 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1486 := fields1485
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1486)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1492 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1492 != nil {
		p.write(*flat1492)
		return nil
	} else {
		_dollar_dollar := msg
		fields1488 := _dollar_dollar.GetRelations()
		unwrapped_fields1489 := fields1488
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1489) == 0) {
			p.newline()
			for i1491, elem1490 := range unwrapped_fields1489 {
				if (i1491 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1490)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1497 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1497 != nil {
		p.write(*flat1497)
		return nil
	} else {
		_dollar_dollar := msg
		fields1493 := _dollar_dollar.GetMappings()
		unwrapped_fields1494 := fields1493
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1494) == 0) {
			p.newline()
			for i1496, elem1495 := range unwrapped_fields1494 {
				if (i1496 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1495)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1502 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1502 != nil {
		p.write(*flat1502)
		return nil
	} else {
		_dollar_dollar := msg
		fields1498 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1499 := fields1498
		field1500 := unwrapped_fields1499[0].([]string)
		p.pretty_edb_path(field1500)
		p.write(" ")
		field1501 := unwrapped_fields1499[1].(*pb.RelationId)
		p.pretty_relation_id(field1501)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1506 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1506 != nil {
		p.write(*flat1506)
		return nil
	} else {
		fields1503 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1503) == 0) {
			p.newline()
			for i1505, elem1504 := range fields1503 {
				if (i1505 > 0) {
					p.newline()
				}
				p.pretty_read(elem1504)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1517 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1517 != nil {
		p.write(*flat1517)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1723 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1723 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1515 := _t1723
		if deconstruct_result1515 != nil {
			unwrapped1516 := deconstruct_result1515
			p.pretty_demand(unwrapped1516)
		} else {
			_dollar_dollar := msg
			var _t1724 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1724 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1513 := _t1724
			if deconstruct_result1513 != nil {
				unwrapped1514 := deconstruct_result1513
				p.pretty_output(unwrapped1514)
			} else {
				_dollar_dollar := msg
				var _t1725 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1725 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1511 := _t1725
				if deconstruct_result1511 != nil {
					unwrapped1512 := deconstruct_result1511
					p.pretty_what_if(unwrapped1512)
				} else {
					_dollar_dollar := msg
					var _t1726 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1726 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1509 := _t1726
					if deconstruct_result1509 != nil {
						unwrapped1510 := deconstruct_result1509
						p.pretty_abort(unwrapped1510)
					} else {
						_dollar_dollar := msg
						var _t1727 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1727 = _dollar_dollar.GetExport()
						}
						deconstruct_result1507 := _t1727
						if deconstruct_result1507 != nil {
							unwrapped1508 := deconstruct_result1507
							p.pretty_export(unwrapped1508)
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
	flat1520 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1520 != nil {
		p.write(*flat1520)
		return nil
	} else {
		_dollar_dollar := msg
		fields1518 := _dollar_dollar.GetRelationId()
		unwrapped_fields1519 := fields1518
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1519)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1525 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1525 != nil {
		p.write(*flat1525)
		return nil
	} else {
		_dollar_dollar := msg
		fields1521 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1522 := fields1521
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1523 := unwrapped_fields1522[0].(string)
		p.pretty_name(field1523)
		p.newline()
		field1524 := unwrapped_fields1522[1].(*pb.RelationId)
		p.pretty_relation_id(field1524)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1530 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1530 != nil {
		p.write(*flat1530)
		return nil
	} else {
		_dollar_dollar := msg
		fields1526 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1527 := fields1526
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1528 := unwrapped_fields1527[0].(string)
		p.pretty_name(field1528)
		p.newline()
		field1529 := unwrapped_fields1527[1].(*pb.Epoch)
		p.pretty_epoch(field1529)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1536 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1536 != nil {
		p.write(*flat1536)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1728 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1728 = ptr(_dollar_dollar.GetName())
		}
		fields1531 := []interface{}{_t1728, _dollar_dollar.GetRelationId()}
		unwrapped_fields1532 := fields1531
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1533 := unwrapped_fields1532[0].(*string)
		if field1533 != nil {
			p.newline()
			opt_val1534 := *field1533
			p.pretty_name(opt_val1534)
		}
		p.newline()
		field1535 := unwrapped_fields1532[1].(*pb.RelationId)
		p.pretty_relation_id(field1535)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1541 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1541 != nil {
		p.write(*flat1541)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1729 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1729 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1539 := _t1729
		if deconstruct_result1539 != nil {
			unwrapped1540 := deconstruct_result1539
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1540)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1730 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1730 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1537 := _t1730
			if deconstruct_result1537 != nil {
				unwrapped1538 := deconstruct_result1537
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1538)
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
	flat1552 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1552 != nil {
		p.write(*flat1552)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1731 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1731 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1547 := _t1731
		if deconstruct_result1547 != nil {
			unwrapped1548 := deconstruct_result1547
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1549 := unwrapped1548[0].(string)
			p.pretty_export_csv_path(field1549)
			p.newline()
			field1550 := unwrapped1548[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1550)
			p.newline()
			field1551 := unwrapped1548[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1551)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1732 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1733 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1732 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1733}
			}
			deconstruct_result1542 := _t1732
			if deconstruct_result1542 != nil {
				unwrapped1543 := deconstruct_result1542
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1544 := unwrapped1543[0].(string)
				p.pretty_export_csv_path(field1544)
				p.newline()
				field1545 := unwrapped1543[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1545)
				p.newline()
				field1546 := unwrapped1543[2].([][]interface{})
				p.pretty_config_dict(field1546)
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
	flat1554 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1554 != nil {
		p.write(*flat1554)
		return nil
	} else {
		fields1553 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1553))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1561 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1561 != nil {
		p.write(*flat1561)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1734 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1734 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1557 := _t1734
		if deconstruct_result1557 != nil {
			unwrapped1558 := deconstruct_result1557
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1558) == 0) {
				p.newline()
				for i1560, elem1559 := range unwrapped1558 {
					if (i1560 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1559)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1735 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1735 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1555 := _t1735
			if deconstruct_result1555 != nil {
				unwrapped1556 := deconstruct_result1555
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1556)
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
	flat1566 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1566 != nil {
		p.write(*flat1566)
		return nil
	} else {
		_dollar_dollar := msg
		fields1562 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1563 := fields1562
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1564 := unwrapped_fields1563[0].(string)
		p.write(p.formatStringValue(field1564))
		p.newline()
		field1565 := unwrapped_fields1563[1].(*pb.RelationId)
		p.pretty_relation_id(field1565)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1570 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1570 != nil {
		p.write(*flat1570)
		return nil
	} else {
		fields1567 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1567) == 0) {
			p.newline()
			for i1569, elem1568 := range fields1567 {
				if (i1569 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1568)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1580 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1580 != nil {
		p.write(*flat1580)
		return nil
	} else {
		_dollar_dollar := msg
		_t1736 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1571 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetTableDef(), _dollar_dollar.GetColumns(), dictToPairs(_dollar_dollar.GetTableProperties()), _t1736}
		unwrapped_fields1572 := fields1571
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1573 := unwrapped_fields1572[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1573)
		p.newline()
		field1574 := unwrapped_fields1572[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1574)
		p.newline()
		field1575 := unwrapped_fields1572[2].(*pb.RelationId)
		p.pretty_export_iceberg_table_def(field1575)
		p.newline()
		field1576 := unwrapped_fields1572[3].([]*pb.ExportColumn)
		p.pretty_export_iceberg_columns(field1576)
		p.newline()
		field1577 := unwrapped_fields1572[4].([][]interface{})
		p.pretty_iceberg_table_properties(field1577)
		field1578 := unwrapped_fields1572[5].([][]interface{})
		if field1578 != nil {
			p.newline()
			opt_val1579 := field1578
			p.pretty_config_dict(opt_val1579)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_table_def(msg *pb.RelationId) interface{} {
	flat1582 := p.tryFlat(msg, func() { p.pretty_export_iceberg_table_def(msg) })
	if flat1582 != nil {
		p.write(*flat1582)
		return nil
	} else {
		fields1581 := msg
		p.write("(")
		p.write("table_def")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(fields1581)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_columns(msg []*pb.ExportColumn) interface{} {
	flat1586 := p.tryFlat(msg, func() { p.pretty_export_iceberg_columns(msg) })
	if flat1586 != nil {
		p.write(*flat1586)
		return nil
	} else {
		fields1583 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1583) == 0) {
			p.newline()
			for i1585, elem1584 := range fields1583 {
				if (i1585 > 0) {
					p.newline()
				}
				p.pretty_export_iceberg_column(elem1584)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_column(msg *pb.ExportColumn) interface{} {
	flat1591 := p.tryFlat(msg, func() { p.pretty_export_iceberg_column(msg) })
	if flat1591 != nil {
		p.write(*flat1591)
		return nil
	} else {
		_dollar_dollar := msg
		fields1587 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetNullable()}
		unwrapped_fields1588 := fields1587
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1589 := unwrapped_fields1588[0].(string)
		p.write(p.formatStringValue(field1589))
		p.newline()
		field1590 := unwrapped_fields1588[1].(bool)
		p.pretty_boolean_value(field1590)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_table_properties(msg [][]interface{}) interface{} {
	flat1595 := p.tryFlat(msg, func() { p.pretty_iceberg_table_properties(msg) })
	if flat1595 != nil {
		p.write(*flat1595)
		return nil
	} else {
		fields1592 := msg
		p.write("(")
		p.write("table_properties")
		p.indentSexp()
		if !(len(fields1592) == 0) {
			p.newline()
			for i1594, elem1593 := range fields1592 {
				if (i1594 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1593)
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
		_t1782 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1782)
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
	case []*pb.ExportColumn:
		p.pretty_export_iceberg_columns(m)
	case *pb.ExportColumn:
		p.pretty_export_iceberg_column(m)
	case *pb.DebugInfo:
		p.pretty_debug_info(m)
	case *pb.BeTreeConfig:
		p.pretty_be_tree_config(m)
	case *pb.BeTreeLocator:
		p.pretty_be_tree_locator(m)
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
