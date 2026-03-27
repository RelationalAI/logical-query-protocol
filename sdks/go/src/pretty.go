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
	_t1681 := &pb.Value{}
	_t1681.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1681
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1682 := &pb.Value{}
	_t1682.Value = &pb.Value_IntValue{IntValue: v}
	return _t1682
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1683 := &pb.Value{}
	_t1683.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1683
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1684 := &pb.Value{}
	_t1684.Value = &pb.Value_StringValue{StringValue: v}
	return _t1684
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1685 := &pb.Value{}
	_t1685.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1685
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1686 := &pb.Value{}
	_t1686.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1686
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1687 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1687})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1688 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1688})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1689 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1689})
			}
		}
	}
	_t1690 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1690})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1691 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1691})
	_t1692 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1692})
	if msg.GetNewLine() != "" {
		_t1693 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1693})
	}
	_t1694 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1694})
	_t1695 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1695})
	_t1696 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1696})
	if msg.GetComment() != "" {
		_t1697 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1697})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1698 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1698})
	}
	_t1699 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1699})
	_t1700 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1700})
	_t1701 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1701})
	if msg.GetPartitionSizeMb() != 0 {
		_t1702 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1702})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1703 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1703})
	_t1704 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1704})
	_t1705 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1705})
	_t1706 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1706})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1707 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1707})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1708 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1708})
		}
	}
	_t1709 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1709})
	_t1710 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1710})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1711 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1711})
	}
	if msg.Compression != nil {
		_t1712 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1712})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1713 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1713})
	}
	if msg.SyntaxMissingString != nil {
		_t1714 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1714})
	}
	if msg.SyntaxDelim != nil {
		_t1715 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1715})
	}
	if msg.SyntaxQuotechar != nil {
		_t1716 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1716})
	}
	if msg.SyntaxEscapechar != nil {
		_t1717 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1717})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_iceberg_catalog_config_scope_optional(msg *pb.IcebergCatalogConfig) *string {
	var _t1718 interface{}
	if *msg.Scope != "" {
		return ptr(*msg.Scope)
	}
	_ = _t1718
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1719 interface{}
	if *msg.ToSnapshot != "" {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1719
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1720 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1720})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1721 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1721})
	}
	if msg.GetCompression() != "" {
		_t1722 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1722})
	}
	var _t1723 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1723
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1724 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1724
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
	flat780 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat780 != nil {
		p.write(*flat780)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1542 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1542 = _dollar_dollar.GetConfigure()
		}
		var _t1543 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1543 = _dollar_dollar.GetSync()
		}
		fields771 := []interface{}{_t1542, _t1543, _dollar_dollar.GetEpochs()}
		unwrapped_fields772 := fields771
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field773 := unwrapped_fields772[0].(*pb.Configure)
		if field773 != nil {
			p.newline()
			opt_val774 := field773
			p.pretty_configure(opt_val774)
		}
		field775 := unwrapped_fields772[1].(*pb.Sync)
		if field775 != nil {
			p.newline()
			opt_val776 := field775
			p.pretty_sync(opt_val776)
		}
		field777 := unwrapped_fields772[2].([]*pb.Epoch)
		if !(len(field777) == 0) {
			p.newline()
			for i779, elem778 := range field777 {
				if (i779 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem778)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat783 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat783 != nil {
		p.write(*flat783)
		return nil
	} else {
		_dollar_dollar := msg
		_t1544 := p.deconstruct_configure(_dollar_dollar)
		fields781 := _t1544
		unwrapped_fields782 := fields781
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields782)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat787 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat787 != nil {
		p.write(*flat787)
		return nil
	} else {
		fields784 := msg
		p.write("{")
		p.indent()
		if !(len(fields784) == 0) {
			p.newline()
			for i786, elem785 := range fields784 {
				if (i786 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem785)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat792 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat792 != nil {
		p.write(*flat792)
		return nil
	} else {
		_dollar_dollar := msg
		fields788 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields789 := fields788
		p.write(":")
		field790 := unwrapped_fields789[0].(string)
		p.write(field790)
		p.write(" ")
		field791 := unwrapped_fields789[1].(*pb.Value)
		p.pretty_raw_value(field791)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat818 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat818 != nil {
		p.write(*flat818)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1545 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1545 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result816 := _t1545
		if deconstruct_result816 != nil {
			unwrapped817 := deconstruct_result816
			p.pretty_raw_date(unwrapped817)
		} else {
			_dollar_dollar := msg
			var _t1546 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1546 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result814 := _t1546
			if deconstruct_result814 != nil {
				unwrapped815 := deconstruct_result814
				p.pretty_raw_datetime(unwrapped815)
			} else {
				_dollar_dollar := msg
				var _t1547 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1547 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result812 := _t1547
				if deconstruct_result812 != nil {
					unwrapped813 := *deconstruct_result812
					p.write(p.formatStringValue(unwrapped813))
				} else {
					_dollar_dollar := msg
					var _t1548 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1548 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result810 := _t1548
					if deconstruct_result810 != nil {
						unwrapped811 := *deconstruct_result810
						p.write(fmt.Sprintf("%di32", unwrapped811))
					} else {
						_dollar_dollar := msg
						var _t1549 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1549 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result808 := _t1549
						if deconstruct_result808 != nil {
							unwrapped809 := *deconstruct_result808
							p.write(fmt.Sprintf("%d", unwrapped809))
						} else {
							_dollar_dollar := msg
							var _t1550 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1550 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result806 := _t1550
							if deconstruct_result806 != nil {
								unwrapped807 := *deconstruct_result806
								p.write(formatFloat32(unwrapped807))
							} else {
								_dollar_dollar := msg
								var _t1551 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1551 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result804 := _t1551
								if deconstruct_result804 != nil {
									unwrapped805 := *deconstruct_result804
									p.write(formatFloat64(unwrapped805))
								} else {
									_dollar_dollar := msg
									var _t1552 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1552 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result802 := _t1552
									if deconstruct_result802 != nil {
										unwrapped803 := *deconstruct_result802
										p.write(fmt.Sprintf("%du32", unwrapped803))
									} else {
										_dollar_dollar := msg
										var _t1553 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1553 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result800 := _t1553
										if deconstruct_result800 != nil {
											unwrapped801 := deconstruct_result800
											p.write(p.formatUint128(unwrapped801))
										} else {
											_dollar_dollar := msg
											var _t1554 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1554 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result798 := _t1554
											if deconstruct_result798 != nil {
												unwrapped799 := deconstruct_result798
												p.write(p.formatInt128(unwrapped799))
											} else {
												_dollar_dollar := msg
												var _t1555 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1555 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result796 := _t1555
												if deconstruct_result796 != nil {
													unwrapped797 := deconstruct_result796
													p.write(p.formatDecimal(unwrapped797))
												} else {
													_dollar_dollar := msg
													var _t1556 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1556 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result794 := _t1556
													if deconstruct_result794 != nil {
														unwrapped795 := *deconstruct_result794
														p.pretty_boolean_value(unwrapped795)
													} else {
														fields793 := msg
														_ = fields793
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
	flat824 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat824 != nil {
		p.write(*flat824)
		return nil
	} else {
		_dollar_dollar := msg
		fields819 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields820 := fields819
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field821 := unwrapped_fields820[0].(int64)
		p.write(fmt.Sprintf("%d", field821))
		p.newline()
		field822 := unwrapped_fields820[1].(int64)
		p.write(fmt.Sprintf("%d", field822))
		p.newline()
		field823 := unwrapped_fields820[2].(int64)
		p.write(fmt.Sprintf("%d", field823))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat835 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat835 != nil {
		p.write(*flat835)
		return nil
	} else {
		_dollar_dollar := msg
		fields825 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields826 := fields825
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field827 := unwrapped_fields826[0].(int64)
		p.write(fmt.Sprintf("%d", field827))
		p.newline()
		field828 := unwrapped_fields826[1].(int64)
		p.write(fmt.Sprintf("%d", field828))
		p.newline()
		field829 := unwrapped_fields826[2].(int64)
		p.write(fmt.Sprintf("%d", field829))
		p.newline()
		field830 := unwrapped_fields826[3].(int64)
		p.write(fmt.Sprintf("%d", field830))
		p.newline()
		field831 := unwrapped_fields826[4].(int64)
		p.write(fmt.Sprintf("%d", field831))
		p.newline()
		field832 := unwrapped_fields826[5].(int64)
		p.write(fmt.Sprintf("%d", field832))
		field833 := unwrapped_fields826[6].(*int64)
		if field833 != nil {
			p.newline()
			opt_val834 := *field833
			p.write(fmt.Sprintf("%d", opt_val834))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1557 []interface{}
	if _dollar_dollar {
		_t1557 = []interface{}{}
	}
	deconstruct_result838 := _t1557
	if deconstruct_result838 != nil {
		unwrapped839 := deconstruct_result838
		_ = unwrapped839
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1558 []interface{}
		if !(_dollar_dollar) {
			_t1558 = []interface{}{}
		}
		deconstruct_result836 := _t1558
		if deconstruct_result836 != nil {
			unwrapped837 := deconstruct_result836
			_ = unwrapped837
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat844 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat844 != nil {
		p.write(*flat844)
		return nil
	} else {
		_dollar_dollar := msg
		fields840 := _dollar_dollar.GetFragments()
		unwrapped_fields841 := fields840
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields841) == 0) {
			p.newline()
			for i843, elem842 := range unwrapped_fields841 {
				if (i843 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem842)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat847 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat847 != nil {
		p.write(*flat847)
		return nil
	} else {
		_dollar_dollar := msg
		fields845 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields846 := fields845
		p.write(":")
		p.write(unwrapped_fields846)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat854 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat854 != nil {
		p.write(*flat854)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1559 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1559 = _dollar_dollar.GetWrites()
		}
		var _t1560 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1560 = _dollar_dollar.GetReads()
		}
		fields848 := []interface{}{_t1559, _t1560}
		unwrapped_fields849 := fields848
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field850 := unwrapped_fields849[0].([]*pb.Write)
		if field850 != nil {
			p.newline()
			opt_val851 := field850
			p.pretty_epoch_writes(opt_val851)
		}
		field852 := unwrapped_fields849[1].([]*pb.Read)
		if field852 != nil {
			p.newline()
			opt_val853 := field852
			p.pretty_epoch_reads(opt_val853)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat858 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat858 != nil {
		p.write(*flat858)
		return nil
	} else {
		fields855 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields855) == 0) {
			p.newline()
			for i857, elem856 := range fields855 {
				if (i857 > 0) {
					p.newline()
				}
				p.pretty_write(elem856)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat867 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat867 != nil {
		p.write(*flat867)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1561 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1561 = _dollar_dollar.GetDefine()
		}
		deconstruct_result865 := _t1561
		if deconstruct_result865 != nil {
			unwrapped866 := deconstruct_result865
			p.pretty_define(unwrapped866)
		} else {
			_dollar_dollar := msg
			var _t1562 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1562 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result863 := _t1562
			if deconstruct_result863 != nil {
				unwrapped864 := deconstruct_result863
				p.pretty_undefine(unwrapped864)
			} else {
				_dollar_dollar := msg
				var _t1563 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1563 = _dollar_dollar.GetContext()
				}
				deconstruct_result861 := _t1563
				if deconstruct_result861 != nil {
					unwrapped862 := deconstruct_result861
					p.pretty_context(unwrapped862)
				} else {
					_dollar_dollar := msg
					var _t1564 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1564 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result859 := _t1564
					if deconstruct_result859 != nil {
						unwrapped860 := deconstruct_result859
						p.pretty_snapshot(unwrapped860)
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
	flat870 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat870 != nil {
		p.write(*flat870)
		return nil
	} else {
		_dollar_dollar := msg
		fields868 := _dollar_dollar.GetFragment()
		unwrapped_fields869 := fields868
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields869)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat877 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat877 != nil {
		p.write(*flat877)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields871 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields872 := fields871
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field873 := unwrapped_fields872[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field873)
		field874 := unwrapped_fields872[1].([]*pb.Declaration)
		if !(len(field874) == 0) {
			p.newline()
			for i876, elem875 := range field874 {
				if (i876 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem875)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat879 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat879 != nil {
		p.write(*flat879)
		return nil
	} else {
		fields878 := msg
		p.pretty_fragment_id(fields878)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat888 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat888 != nil {
		p.write(*flat888)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1565 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1565 = _dollar_dollar.GetDef()
		}
		deconstruct_result886 := _t1565
		if deconstruct_result886 != nil {
			unwrapped887 := deconstruct_result886
			p.pretty_def(unwrapped887)
		} else {
			_dollar_dollar := msg
			var _t1566 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1566 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result884 := _t1566
			if deconstruct_result884 != nil {
				unwrapped885 := deconstruct_result884
				p.pretty_algorithm(unwrapped885)
			} else {
				_dollar_dollar := msg
				var _t1567 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1567 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result882 := _t1567
				if deconstruct_result882 != nil {
					unwrapped883 := deconstruct_result882
					p.pretty_constraint(unwrapped883)
				} else {
					_dollar_dollar := msg
					var _t1568 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1568 = _dollar_dollar.GetData()
					}
					deconstruct_result880 := _t1568
					if deconstruct_result880 != nil {
						unwrapped881 := deconstruct_result880
						p.pretty_data(unwrapped881)
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
	flat895 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat895 != nil {
		p.write(*flat895)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1569 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1569 = _dollar_dollar.GetAttrs()
		}
		fields889 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1569}
		unwrapped_fields890 := fields889
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field891 := unwrapped_fields890[0].(*pb.RelationId)
		p.pretty_relation_id(field891)
		p.newline()
		field892 := unwrapped_fields890[1].(*pb.Abstraction)
		p.pretty_abstraction(field892)
		field893 := unwrapped_fields890[2].([]*pb.Attribute)
		if field893 != nil {
			p.newline()
			opt_val894 := field893
			p.pretty_attrs(opt_val894)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat900 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat900 != nil {
		p.write(*flat900)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1570 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1571 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1570 = ptr(_t1571)
		}
		deconstruct_result898 := _t1570
		if deconstruct_result898 != nil {
			unwrapped899 := *deconstruct_result898
			p.write(":")
			p.write(unwrapped899)
		} else {
			_dollar_dollar := msg
			_t1572 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result896 := _t1572
			if deconstruct_result896 != nil {
				unwrapped897 := deconstruct_result896
				p.write(p.formatUint128(unwrapped897))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat905 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat905 != nil {
		p.write(*flat905)
		return nil
	} else {
		_dollar_dollar := msg
		_t1573 := p.deconstruct_bindings(_dollar_dollar)
		fields901 := []interface{}{_t1573, _dollar_dollar.GetValue()}
		unwrapped_fields902 := fields901
		p.write("(")
		p.indent()
		field903 := unwrapped_fields902[0].([]interface{})
		p.pretty_bindings(field903)
		p.newline()
		field904 := unwrapped_fields902[1].(*pb.Formula)
		p.pretty_formula(field904)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat913 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat913 != nil {
		p.write(*flat913)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1574 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1574 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields906 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1574}
		unwrapped_fields907 := fields906
		p.write("[")
		p.indent()
		field908 := unwrapped_fields907[0].([]*pb.Binding)
		for i910, elem909 := range field908 {
			if (i910 > 0) {
				p.newline()
			}
			p.pretty_binding(elem909)
		}
		field911 := unwrapped_fields907[1].([]*pb.Binding)
		if field911 != nil {
			p.newline()
			opt_val912 := field911
			p.pretty_value_bindings(opt_val912)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat918 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat918 != nil {
		p.write(*flat918)
		return nil
	} else {
		_dollar_dollar := msg
		fields914 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields915 := fields914
		field916 := unwrapped_fields915[0].(string)
		p.write(field916)
		p.write("::")
		field917 := unwrapped_fields915[1].(*pb.Type)
		p.pretty_type(field917)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat947 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat947 != nil {
		p.write(*flat947)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1575 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1575 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result945 := _t1575
		if deconstruct_result945 != nil {
			unwrapped946 := deconstruct_result945
			p.pretty_unspecified_type(unwrapped946)
		} else {
			_dollar_dollar := msg
			var _t1576 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1576 = _dollar_dollar.GetStringType()
			}
			deconstruct_result943 := _t1576
			if deconstruct_result943 != nil {
				unwrapped944 := deconstruct_result943
				p.pretty_string_type(unwrapped944)
			} else {
				_dollar_dollar := msg
				var _t1577 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1577 = _dollar_dollar.GetIntType()
				}
				deconstruct_result941 := _t1577
				if deconstruct_result941 != nil {
					unwrapped942 := deconstruct_result941
					p.pretty_int_type(unwrapped942)
				} else {
					_dollar_dollar := msg
					var _t1578 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1578 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result939 := _t1578
					if deconstruct_result939 != nil {
						unwrapped940 := deconstruct_result939
						p.pretty_float_type(unwrapped940)
					} else {
						_dollar_dollar := msg
						var _t1579 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1579 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result937 := _t1579
						if deconstruct_result937 != nil {
							unwrapped938 := deconstruct_result937
							p.pretty_uint128_type(unwrapped938)
						} else {
							_dollar_dollar := msg
							var _t1580 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1580 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result935 := _t1580
							if deconstruct_result935 != nil {
								unwrapped936 := deconstruct_result935
								p.pretty_int128_type(unwrapped936)
							} else {
								_dollar_dollar := msg
								var _t1581 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1581 = _dollar_dollar.GetDateType()
								}
								deconstruct_result933 := _t1581
								if deconstruct_result933 != nil {
									unwrapped934 := deconstruct_result933
									p.pretty_date_type(unwrapped934)
								} else {
									_dollar_dollar := msg
									var _t1582 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1582 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result931 := _t1582
									if deconstruct_result931 != nil {
										unwrapped932 := deconstruct_result931
										p.pretty_datetime_type(unwrapped932)
									} else {
										_dollar_dollar := msg
										var _t1583 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1583 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result929 := _t1583
										if deconstruct_result929 != nil {
											unwrapped930 := deconstruct_result929
											p.pretty_missing_type(unwrapped930)
										} else {
											_dollar_dollar := msg
											var _t1584 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1584 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result927 := _t1584
											if deconstruct_result927 != nil {
												unwrapped928 := deconstruct_result927
												p.pretty_decimal_type(unwrapped928)
											} else {
												_dollar_dollar := msg
												var _t1585 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1585 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result925 := _t1585
												if deconstruct_result925 != nil {
													unwrapped926 := deconstruct_result925
													p.pretty_boolean_type(unwrapped926)
												} else {
													_dollar_dollar := msg
													var _t1586 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1586 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result923 := _t1586
													if deconstruct_result923 != nil {
														unwrapped924 := deconstruct_result923
														p.pretty_int32_type(unwrapped924)
													} else {
														_dollar_dollar := msg
														var _t1587 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1587 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result921 := _t1587
														if deconstruct_result921 != nil {
															unwrapped922 := deconstruct_result921
															p.pretty_float32_type(unwrapped922)
														} else {
															_dollar_dollar := msg
															var _t1588 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1588 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result919 := _t1588
															if deconstruct_result919 != nil {
																unwrapped920 := deconstruct_result919
																p.pretty_uint32_type(unwrapped920)
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
	fields948 := msg
	_ = fields948
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields949 := msg
	_ = fields949
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields950 := msg
	_ = fields950
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields951 := msg
	_ = fields951
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields952 := msg
	_ = fields952
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields953 := msg
	_ = fields953
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields954 := msg
	_ = fields954
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields955 := msg
	_ = fields955
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields956 := msg
	_ = fields956
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat961 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat961 != nil {
		p.write(*flat961)
		return nil
	} else {
		_dollar_dollar := msg
		fields957 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields958 := fields957
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field959 := unwrapped_fields958[0].(int64)
		p.write(fmt.Sprintf("%d", field959))
		p.newline()
		field960 := unwrapped_fields958[1].(int64)
		p.write(fmt.Sprintf("%d", field960))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields962 := msg
	_ = fields962
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields963 := msg
	_ = fields963
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields964 := msg
	_ = fields964
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields965 := msg
	_ = fields965
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat969 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat969 != nil {
		p.write(*flat969)
		return nil
	} else {
		fields966 := msg
		p.write("|")
		if !(len(fields966) == 0) {
			p.write(" ")
			for i968, elem967 := range fields966 {
				if (i968 > 0) {
					p.newline()
				}
				p.pretty_binding(elem967)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat996 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat996 != nil {
		p.write(*flat996)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1589 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1589 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result994 := _t1589
		if deconstruct_result994 != nil {
			unwrapped995 := deconstruct_result994
			p.pretty_true(unwrapped995)
		} else {
			_dollar_dollar := msg
			var _t1590 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1590 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result992 := _t1590
			if deconstruct_result992 != nil {
				unwrapped993 := deconstruct_result992
				p.pretty_false(unwrapped993)
			} else {
				_dollar_dollar := msg
				var _t1591 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1591 = _dollar_dollar.GetExists()
				}
				deconstruct_result990 := _t1591
				if deconstruct_result990 != nil {
					unwrapped991 := deconstruct_result990
					p.pretty_exists(unwrapped991)
				} else {
					_dollar_dollar := msg
					var _t1592 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1592 = _dollar_dollar.GetReduce()
					}
					deconstruct_result988 := _t1592
					if deconstruct_result988 != nil {
						unwrapped989 := deconstruct_result988
						p.pretty_reduce(unwrapped989)
					} else {
						_dollar_dollar := msg
						var _t1593 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1593 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result986 := _t1593
						if deconstruct_result986 != nil {
							unwrapped987 := deconstruct_result986
							p.pretty_conjunction(unwrapped987)
						} else {
							_dollar_dollar := msg
							var _t1594 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1594 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result984 := _t1594
							if deconstruct_result984 != nil {
								unwrapped985 := deconstruct_result984
								p.pretty_disjunction(unwrapped985)
							} else {
								_dollar_dollar := msg
								var _t1595 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1595 = _dollar_dollar.GetNot()
								}
								deconstruct_result982 := _t1595
								if deconstruct_result982 != nil {
									unwrapped983 := deconstruct_result982
									p.pretty_not(unwrapped983)
								} else {
									_dollar_dollar := msg
									var _t1596 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1596 = _dollar_dollar.GetFfi()
									}
									deconstruct_result980 := _t1596
									if deconstruct_result980 != nil {
										unwrapped981 := deconstruct_result980
										p.pretty_ffi(unwrapped981)
									} else {
										_dollar_dollar := msg
										var _t1597 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1597 = _dollar_dollar.GetAtom()
										}
										deconstruct_result978 := _t1597
										if deconstruct_result978 != nil {
											unwrapped979 := deconstruct_result978
											p.pretty_atom(unwrapped979)
										} else {
											_dollar_dollar := msg
											var _t1598 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1598 = _dollar_dollar.GetPragma()
											}
											deconstruct_result976 := _t1598
											if deconstruct_result976 != nil {
												unwrapped977 := deconstruct_result976
												p.pretty_pragma(unwrapped977)
											} else {
												_dollar_dollar := msg
												var _t1599 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1599 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result974 := _t1599
												if deconstruct_result974 != nil {
													unwrapped975 := deconstruct_result974
													p.pretty_primitive(unwrapped975)
												} else {
													_dollar_dollar := msg
													var _t1600 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1600 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result972 := _t1600
													if deconstruct_result972 != nil {
														unwrapped973 := deconstruct_result972
														p.pretty_rel_atom(unwrapped973)
													} else {
														_dollar_dollar := msg
														var _t1601 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1601 = _dollar_dollar.GetCast()
														}
														deconstruct_result970 := _t1601
														if deconstruct_result970 != nil {
															unwrapped971 := deconstruct_result970
															p.pretty_cast(unwrapped971)
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
	fields997 := msg
	_ = fields997
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields998 := msg
	_ = fields998
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat1003 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat1003 != nil {
		p.write(*flat1003)
		return nil
	} else {
		_dollar_dollar := msg
		_t1602 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields999 := []interface{}{_t1602, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields1000 := fields999
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field1001 := unwrapped_fields1000[0].([]interface{})
		p.pretty_bindings(field1001)
		p.newline()
		field1002 := unwrapped_fields1000[1].(*pb.Formula)
		p.pretty_formula(field1002)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1009 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1009 != nil {
		p.write(*flat1009)
		return nil
	} else {
		_dollar_dollar := msg
		fields1004 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1005 := fields1004
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1006 := unwrapped_fields1005[0].(*pb.Abstraction)
		p.pretty_abstraction(field1006)
		p.newline()
		field1007 := unwrapped_fields1005[1].(*pb.Abstraction)
		p.pretty_abstraction(field1007)
		p.newline()
		field1008 := unwrapped_fields1005[2].([]*pb.Term)
		p.pretty_terms(field1008)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1013 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1013 != nil {
		p.write(*flat1013)
		return nil
	} else {
		fields1010 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1010) == 0) {
			p.newline()
			for i1012, elem1011 := range fields1010 {
				if (i1012 > 0) {
					p.newline()
				}
				p.pretty_term(elem1011)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1018 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1018 != nil {
		p.write(*flat1018)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1603 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1603 = _dollar_dollar.GetVar()
		}
		deconstruct_result1016 := _t1603
		if deconstruct_result1016 != nil {
			unwrapped1017 := deconstruct_result1016
			p.pretty_var(unwrapped1017)
		} else {
			_dollar_dollar := msg
			var _t1604 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1604 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1014 := _t1604
			if deconstruct_result1014 != nil {
				unwrapped1015 := deconstruct_result1014
				p.pretty_value(unwrapped1015)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1021 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1021 != nil {
		p.write(*flat1021)
		return nil
	} else {
		_dollar_dollar := msg
		fields1019 := _dollar_dollar.GetName()
		unwrapped_fields1020 := fields1019
		p.write(unwrapped_fields1020)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1047 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1047 != nil {
		p.write(*flat1047)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1605 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1605 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1045 := _t1605
		if deconstruct_result1045 != nil {
			unwrapped1046 := deconstruct_result1045
			p.pretty_date(unwrapped1046)
		} else {
			_dollar_dollar := msg
			var _t1606 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1606 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1043 := _t1606
			if deconstruct_result1043 != nil {
				unwrapped1044 := deconstruct_result1043
				p.pretty_datetime(unwrapped1044)
			} else {
				_dollar_dollar := msg
				var _t1607 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1607 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1041 := _t1607
				if deconstruct_result1041 != nil {
					unwrapped1042 := *deconstruct_result1041
					p.write(p.formatStringValue(unwrapped1042))
				} else {
					_dollar_dollar := msg
					var _t1608 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1608 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1039 := _t1608
					if deconstruct_result1039 != nil {
						unwrapped1040 := *deconstruct_result1039
						p.write(fmt.Sprintf("%di32", unwrapped1040))
					} else {
						_dollar_dollar := msg
						var _t1609 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1609 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1037 := _t1609
						if deconstruct_result1037 != nil {
							unwrapped1038 := *deconstruct_result1037
							p.write(fmt.Sprintf("%d", unwrapped1038))
						} else {
							_dollar_dollar := msg
							var _t1610 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1610 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1035 := _t1610
							if deconstruct_result1035 != nil {
								unwrapped1036 := *deconstruct_result1035
								p.write(formatFloat32(unwrapped1036))
							} else {
								_dollar_dollar := msg
								var _t1611 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1611 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1033 := _t1611
								if deconstruct_result1033 != nil {
									unwrapped1034 := *deconstruct_result1033
									p.write(formatFloat64(unwrapped1034))
								} else {
									_dollar_dollar := msg
									var _t1612 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1612 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1031 := _t1612
									if deconstruct_result1031 != nil {
										unwrapped1032 := *deconstruct_result1031
										p.write(fmt.Sprintf("%du32", unwrapped1032))
									} else {
										_dollar_dollar := msg
										var _t1613 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1613 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1029 := _t1613
										if deconstruct_result1029 != nil {
											unwrapped1030 := deconstruct_result1029
											p.write(p.formatUint128(unwrapped1030))
										} else {
											_dollar_dollar := msg
											var _t1614 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1614 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1027 := _t1614
											if deconstruct_result1027 != nil {
												unwrapped1028 := deconstruct_result1027
												p.write(p.formatInt128(unwrapped1028))
											} else {
												_dollar_dollar := msg
												var _t1615 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1615 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1025 := _t1615
												if deconstruct_result1025 != nil {
													unwrapped1026 := deconstruct_result1025
													p.write(p.formatDecimal(unwrapped1026))
												} else {
													_dollar_dollar := msg
													var _t1616 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1616 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1023 := _t1616
													if deconstruct_result1023 != nil {
														unwrapped1024 := *deconstruct_result1023
														p.pretty_boolean_value(unwrapped1024)
													} else {
														fields1022 := msg
														_ = fields1022
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
	flat1053 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1053 != nil {
		p.write(*flat1053)
		return nil
	} else {
		_dollar_dollar := msg
		fields1048 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1049 := fields1048
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1050 := unwrapped_fields1049[0].(int64)
		p.write(fmt.Sprintf("%d", field1050))
		p.newline()
		field1051 := unwrapped_fields1049[1].(int64)
		p.write(fmt.Sprintf("%d", field1051))
		p.newline()
		field1052 := unwrapped_fields1049[2].(int64)
		p.write(fmt.Sprintf("%d", field1052))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1064 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1064 != nil {
		p.write(*flat1064)
		return nil
	} else {
		_dollar_dollar := msg
		fields1054 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1055 := fields1054
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1056 := unwrapped_fields1055[0].(int64)
		p.write(fmt.Sprintf("%d", field1056))
		p.newline()
		field1057 := unwrapped_fields1055[1].(int64)
		p.write(fmt.Sprintf("%d", field1057))
		p.newline()
		field1058 := unwrapped_fields1055[2].(int64)
		p.write(fmt.Sprintf("%d", field1058))
		p.newline()
		field1059 := unwrapped_fields1055[3].(int64)
		p.write(fmt.Sprintf("%d", field1059))
		p.newline()
		field1060 := unwrapped_fields1055[4].(int64)
		p.write(fmt.Sprintf("%d", field1060))
		p.newline()
		field1061 := unwrapped_fields1055[5].(int64)
		p.write(fmt.Sprintf("%d", field1061))
		field1062 := unwrapped_fields1055[6].(*int64)
		if field1062 != nil {
			p.newline()
			opt_val1063 := *field1062
			p.write(fmt.Sprintf("%d", opt_val1063))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1069 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1069 != nil {
		p.write(*flat1069)
		return nil
	} else {
		_dollar_dollar := msg
		fields1065 := _dollar_dollar.GetArgs()
		unwrapped_fields1066 := fields1065
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1066) == 0) {
			p.newline()
			for i1068, elem1067 := range unwrapped_fields1066 {
				if (i1068 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1067)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1074 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1074 != nil {
		p.write(*flat1074)
		return nil
	} else {
		_dollar_dollar := msg
		fields1070 := _dollar_dollar.GetArgs()
		unwrapped_fields1071 := fields1070
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1071) == 0) {
			p.newline()
			for i1073, elem1072 := range unwrapped_fields1071 {
				if (i1073 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1072)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1077 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1077 != nil {
		p.write(*flat1077)
		return nil
	} else {
		_dollar_dollar := msg
		fields1075 := _dollar_dollar.GetArg()
		unwrapped_fields1076 := fields1075
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1076)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1083 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1083 != nil {
		p.write(*flat1083)
		return nil
	} else {
		_dollar_dollar := msg
		fields1078 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1079 := fields1078
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1080 := unwrapped_fields1079[0].(string)
		p.pretty_name(field1080)
		p.newline()
		field1081 := unwrapped_fields1079[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1081)
		p.newline()
		field1082 := unwrapped_fields1079[2].([]*pb.Term)
		p.pretty_terms(field1082)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1085 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1085 != nil {
		p.write(*flat1085)
		return nil
	} else {
		fields1084 := msg
		p.write(":")
		p.write(fields1084)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1089 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1089 != nil {
		p.write(*flat1089)
		return nil
	} else {
		fields1086 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1086) == 0) {
			p.newline()
			for i1088, elem1087 := range fields1086 {
				if (i1088 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1087)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1096 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1096 != nil {
		p.write(*flat1096)
		return nil
	} else {
		_dollar_dollar := msg
		fields1090 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1091 := fields1090
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1092 := unwrapped_fields1091[0].(*pb.RelationId)
		p.pretty_relation_id(field1092)
		field1093 := unwrapped_fields1091[1].([]*pb.Term)
		if !(len(field1093) == 0) {
			p.newline()
			for i1095, elem1094 := range field1093 {
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

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1103 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1103 != nil {
		p.write(*flat1103)
		return nil
	} else {
		_dollar_dollar := msg
		fields1097 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1098 := fields1097
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1099 := unwrapped_fields1098[0].(string)
		p.pretty_name(field1099)
		field1100 := unwrapped_fields1098[1].([]*pb.Term)
		if !(len(field1100) == 0) {
			p.newline()
			for i1102, elem1101 := range field1100 {
				if (i1102 > 0) {
					p.newline()
				}
				p.pretty_term(elem1101)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1119 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1119 != nil {
		p.write(*flat1119)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1617 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1617 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1118 := _t1617
		if guard_result1118 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1618 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1618 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1117 := _t1618
			if guard_result1117 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1619 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1619 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1116 := _t1619
				if guard_result1116 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1620 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1620 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1115 := _t1620
					if guard_result1115 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1621 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1621 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1114 := _t1621
						if guard_result1114 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1622 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1622 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1113 := _t1622
							if guard_result1113 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1623 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1623 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1112 := _t1623
								if guard_result1112 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1624 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1624 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1111 := _t1624
									if guard_result1111 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1625 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1625 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1110 := _t1625
										if guard_result1110 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1104 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1105 := fields1104
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1106 := unwrapped_fields1105[0].(string)
											p.pretty_name(field1106)
											field1107 := unwrapped_fields1105[1].([]*pb.RelTerm)
											if !(len(field1107) == 0) {
												p.newline()
												for i1109, elem1108 := range field1107 {
													if (i1109 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1108)
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
	flat1124 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1124 != nil {
		p.write(*flat1124)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1626 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1626 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1120 := _t1626
		unwrapped_fields1121 := fields1120
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1122 := unwrapped_fields1121[0].(*pb.Term)
		p.pretty_term(field1122)
		p.newline()
		field1123 := unwrapped_fields1121[1].(*pb.Term)
		p.pretty_term(field1123)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1129 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1129 != nil {
		p.write(*flat1129)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1627 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1627 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1125 := _t1627
		unwrapped_fields1126 := fields1125
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1127 := unwrapped_fields1126[0].(*pb.Term)
		p.pretty_term(field1127)
		p.newline()
		field1128 := unwrapped_fields1126[1].(*pb.Term)
		p.pretty_term(field1128)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1134 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1134 != nil {
		p.write(*flat1134)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1628 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1628 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1130 := _t1628
		unwrapped_fields1131 := fields1130
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1132 := unwrapped_fields1131[0].(*pb.Term)
		p.pretty_term(field1132)
		p.newline()
		field1133 := unwrapped_fields1131[1].(*pb.Term)
		p.pretty_term(field1133)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1139 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1139 != nil {
		p.write(*flat1139)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1629 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1629 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1135 := _t1629
		unwrapped_fields1136 := fields1135
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1137 := unwrapped_fields1136[0].(*pb.Term)
		p.pretty_term(field1137)
		p.newline()
		field1138 := unwrapped_fields1136[1].(*pb.Term)
		p.pretty_term(field1138)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1144 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1144 != nil {
		p.write(*flat1144)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1630 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1630 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1140 := _t1630
		unwrapped_fields1141 := fields1140
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1142 := unwrapped_fields1141[0].(*pb.Term)
		p.pretty_term(field1142)
		p.newline()
		field1143 := unwrapped_fields1141[1].(*pb.Term)
		p.pretty_term(field1143)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1150 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1150 != nil {
		p.write(*flat1150)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1631 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1631 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1145 := _t1631
		unwrapped_fields1146 := fields1145
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1147 := unwrapped_fields1146[0].(*pb.Term)
		p.pretty_term(field1147)
		p.newline()
		field1148 := unwrapped_fields1146[1].(*pb.Term)
		p.pretty_term(field1148)
		p.newline()
		field1149 := unwrapped_fields1146[2].(*pb.Term)
		p.pretty_term(field1149)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1156 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1156 != nil {
		p.write(*flat1156)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1632 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1632 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1151 := _t1632
		unwrapped_fields1152 := fields1151
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1153 := unwrapped_fields1152[0].(*pb.Term)
		p.pretty_term(field1153)
		p.newline()
		field1154 := unwrapped_fields1152[1].(*pb.Term)
		p.pretty_term(field1154)
		p.newline()
		field1155 := unwrapped_fields1152[2].(*pb.Term)
		p.pretty_term(field1155)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1162 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1162 != nil {
		p.write(*flat1162)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1633 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1633 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1157 := _t1633
		unwrapped_fields1158 := fields1157
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1159 := unwrapped_fields1158[0].(*pb.Term)
		p.pretty_term(field1159)
		p.newline()
		field1160 := unwrapped_fields1158[1].(*pb.Term)
		p.pretty_term(field1160)
		p.newline()
		field1161 := unwrapped_fields1158[2].(*pb.Term)
		p.pretty_term(field1161)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1168 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1168 != nil {
		p.write(*flat1168)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1634 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1634 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1163 := _t1634
		unwrapped_fields1164 := fields1163
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1165 := unwrapped_fields1164[0].(*pb.Term)
		p.pretty_term(field1165)
		p.newline()
		field1166 := unwrapped_fields1164[1].(*pb.Term)
		p.pretty_term(field1166)
		p.newline()
		field1167 := unwrapped_fields1164[2].(*pb.Term)
		p.pretty_term(field1167)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1173 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1173 != nil {
		p.write(*flat1173)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1635 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1635 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1171 := _t1635
		if deconstruct_result1171 != nil {
			unwrapped1172 := deconstruct_result1171
			p.pretty_specialized_value(unwrapped1172)
		} else {
			_dollar_dollar := msg
			var _t1636 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1636 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1169 := _t1636
			if deconstruct_result1169 != nil {
				unwrapped1170 := deconstruct_result1169
				p.pretty_term(unwrapped1170)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1175 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1175 != nil {
		p.write(*flat1175)
		return nil
	} else {
		fields1174 := msg
		p.write("#")
		p.pretty_raw_value(fields1174)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1182 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1182 != nil {
		p.write(*flat1182)
		return nil
	} else {
		_dollar_dollar := msg
		fields1176 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1177 := fields1176
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1178 := unwrapped_fields1177[0].(string)
		p.pretty_name(field1178)
		field1179 := unwrapped_fields1177[1].([]*pb.RelTerm)
		if !(len(field1179) == 0) {
			p.newline()
			for i1181, elem1180 := range field1179 {
				if (i1181 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1180)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1187 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1187 != nil {
		p.write(*flat1187)
		return nil
	} else {
		_dollar_dollar := msg
		fields1183 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1184 := fields1183
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1185 := unwrapped_fields1184[0].(*pb.Term)
		p.pretty_term(field1185)
		p.newline()
		field1186 := unwrapped_fields1184[1].(*pb.Term)
		p.pretty_term(field1186)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1191 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1191 != nil {
		p.write(*flat1191)
		return nil
	} else {
		fields1188 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1188) == 0) {
			p.newline()
			for i1190, elem1189 := range fields1188 {
				if (i1190 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1189)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1198 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1198 != nil {
		p.write(*flat1198)
		return nil
	} else {
		_dollar_dollar := msg
		fields1192 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1193 := fields1192
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1194 := unwrapped_fields1193[0].(string)
		p.pretty_name(field1194)
		field1195 := unwrapped_fields1193[1].([]*pb.Value)
		if !(len(field1195) == 0) {
			p.newline()
			for i1197, elem1196 := range field1195 {
				if (i1197 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1196)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1205 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1205 != nil {
		p.write(*flat1205)
		return nil
	} else {
		_dollar_dollar := msg
		fields1199 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1200 := fields1199
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1201 := unwrapped_fields1200[0].([]*pb.RelationId)
		if !(len(field1201) == 0) {
			p.newline()
			for i1203, elem1202 := range field1201 {
				if (i1203 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1202)
			}
		}
		p.newline()
		field1204 := unwrapped_fields1200[1].(*pb.Script)
		p.pretty_script(field1204)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1210 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1210 != nil {
		p.write(*flat1210)
		return nil
	} else {
		_dollar_dollar := msg
		fields1206 := _dollar_dollar.GetConstructs()
		unwrapped_fields1207 := fields1206
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1207) == 0) {
			p.newline()
			for i1209, elem1208 := range unwrapped_fields1207 {
				if (i1209 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1208)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1215 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1215 != nil {
		p.write(*flat1215)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1637 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1637 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1213 := _t1637
		if deconstruct_result1213 != nil {
			unwrapped1214 := deconstruct_result1213
			p.pretty_loop(unwrapped1214)
		} else {
			_dollar_dollar := msg
			var _t1638 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1638 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1211 := _t1638
			if deconstruct_result1211 != nil {
				unwrapped1212 := deconstruct_result1211
				p.pretty_instruction(unwrapped1212)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1220 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1220 != nil {
		p.write(*flat1220)
		return nil
	} else {
		_dollar_dollar := msg
		fields1216 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1217 := fields1216
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1218 := unwrapped_fields1217[0].([]*pb.Instruction)
		p.pretty_init(field1218)
		p.newline()
		field1219 := unwrapped_fields1217[1].(*pb.Script)
		p.pretty_script(field1219)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1224 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1224 != nil {
		p.write(*flat1224)
		return nil
	} else {
		fields1221 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1221) == 0) {
			p.newline()
			for i1223, elem1222 := range fields1221 {
				if (i1223 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1222)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1235 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1235 != nil {
		p.write(*flat1235)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1639 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1639 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1233 := _t1639
		if deconstruct_result1233 != nil {
			unwrapped1234 := deconstruct_result1233
			p.pretty_assign(unwrapped1234)
		} else {
			_dollar_dollar := msg
			var _t1640 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1640 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1231 := _t1640
			if deconstruct_result1231 != nil {
				unwrapped1232 := deconstruct_result1231
				p.pretty_upsert(unwrapped1232)
			} else {
				_dollar_dollar := msg
				var _t1641 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1641 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1229 := _t1641
				if deconstruct_result1229 != nil {
					unwrapped1230 := deconstruct_result1229
					p.pretty_break(unwrapped1230)
				} else {
					_dollar_dollar := msg
					var _t1642 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1642 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1227 := _t1642
					if deconstruct_result1227 != nil {
						unwrapped1228 := deconstruct_result1227
						p.pretty_monoid_def(unwrapped1228)
					} else {
						_dollar_dollar := msg
						var _t1643 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1643 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1225 := _t1643
						if deconstruct_result1225 != nil {
							unwrapped1226 := deconstruct_result1225
							p.pretty_monus_def(unwrapped1226)
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
	flat1242 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1242 != nil {
		p.write(*flat1242)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1644 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1644 = _dollar_dollar.GetAttrs()
		}
		fields1236 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1644}
		unwrapped_fields1237 := fields1236
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1238 := unwrapped_fields1237[0].(*pb.RelationId)
		p.pretty_relation_id(field1238)
		p.newline()
		field1239 := unwrapped_fields1237[1].(*pb.Abstraction)
		p.pretty_abstraction(field1239)
		field1240 := unwrapped_fields1237[2].([]*pb.Attribute)
		if field1240 != nil {
			p.newline()
			opt_val1241 := field1240
			p.pretty_attrs(opt_val1241)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1249 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1249 != nil {
		p.write(*flat1249)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1645 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1645 = _dollar_dollar.GetAttrs()
		}
		fields1243 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1645}
		unwrapped_fields1244 := fields1243
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1245 := unwrapped_fields1244[0].(*pb.RelationId)
		p.pretty_relation_id(field1245)
		p.newline()
		field1246 := unwrapped_fields1244[1].([]interface{})
		p.pretty_abstraction_with_arity(field1246)
		field1247 := unwrapped_fields1244[2].([]*pb.Attribute)
		if field1247 != nil {
			p.newline()
			opt_val1248 := field1247
			p.pretty_attrs(opt_val1248)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1254 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1254 != nil {
		p.write(*flat1254)
		return nil
	} else {
		_dollar_dollar := msg
		_t1646 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1250 := []interface{}{_t1646, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1251 := fields1250
		p.write("(")
		p.indent()
		field1252 := unwrapped_fields1251[0].([]interface{})
		p.pretty_bindings(field1252)
		p.newline()
		field1253 := unwrapped_fields1251[1].(*pb.Formula)
		p.pretty_formula(field1253)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1261 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1261 != nil {
		p.write(*flat1261)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1647 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1647 = _dollar_dollar.GetAttrs()
		}
		fields1255 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1647}
		unwrapped_fields1256 := fields1255
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1257 := unwrapped_fields1256[0].(*pb.RelationId)
		p.pretty_relation_id(field1257)
		p.newline()
		field1258 := unwrapped_fields1256[1].(*pb.Abstraction)
		p.pretty_abstraction(field1258)
		field1259 := unwrapped_fields1256[2].([]*pb.Attribute)
		if field1259 != nil {
			p.newline()
			opt_val1260 := field1259
			p.pretty_attrs(opt_val1260)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1269 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1269 != nil {
		p.write(*flat1269)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1648 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1648 = _dollar_dollar.GetAttrs()
		}
		fields1262 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1648}
		unwrapped_fields1263 := fields1262
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1264 := unwrapped_fields1263[0].(*pb.Monoid)
		p.pretty_monoid(field1264)
		p.newline()
		field1265 := unwrapped_fields1263[1].(*pb.RelationId)
		p.pretty_relation_id(field1265)
		p.newline()
		field1266 := unwrapped_fields1263[2].([]interface{})
		p.pretty_abstraction_with_arity(field1266)
		field1267 := unwrapped_fields1263[3].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1278 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1278 != nil {
		p.write(*flat1278)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1649 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1649 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1276 := _t1649
		if deconstruct_result1276 != nil {
			unwrapped1277 := deconstruct_result1276
			p.pretty_or_monoid(unwrapped1277)
		} else {
			_dollar_dollar := msg
			var _t1650 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1650 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1274 := _t1650
			if deconstruct_result1274 != nil {
				unwrapped1275 := deconstruct_result1274
				p.pretty_min_monoid(unwrapped1275)
			} else {
				_dollar_dollar := msg
				var _t1651 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1651 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1272 := _t1651
				if deconstruct_result1272 != nil {
					unwrapped1273 := deconstruct_result1272
					p.pretty_max_monoid(unwrapped1273)
				} else {
					_dollar_dollar := msg
					var _t1652 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1652 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1270 := _t1652
					if deconstruct_result1270 != nil {
						unwrapped1271 := deconstruct_result1270
						p.pretty_sum_monoid(unwrapped1271)
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
	fields1279 := msg
	_ = fields1279
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1282 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1282 != nil {
		p.write(*flat1282)
		return nil
	} else {
		_dollar_dollar := msg
		fields1280 := _dollar_dollar.GetType()
		unwrapped_fields1281 := fields1280
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1281)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1285 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1285 != nil {
		p.write(*flat1285)
		return nil
	} else {
		_dollar_dollar := msg
		fields1283 := _dollar_dollar.GetType()
		unwrapped_fields1284 := fields1283
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1284)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1288 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1288 != nil {
		p.write(*flat1288)
		return nil
	} else {
		_dollar_dollar := msg
		fields1286 := _dollar_dollar.GetType()
		unwrapped_fields1287 := fields1286
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1287)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1296 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1296 != nil {
		p.write(*flat1296)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1653 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1653 = _dollar_dollar.GetAttrs()
		}
		fields1289 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1653}
		unwrapped_fields1290 := fields1289
		p.write("(")
		p.write("monus")
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

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1303 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1303 != nil {
		p.write(*flat1303)
		return nil
	} else {
		_dollar_dollar := msg
		fields1297 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1298 := fields1297
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1299 := unwrapped_fields1298[0].(*pb.RelationId)
		p.pretty_relation_id(field1299)
		p.newline()
		field1300 := unwrapped_fields1298[1].(*pb.Abstraction)
		p.pretty_abstraction(field1300)
		p.newline()
		field1301 := unwrapped_fields1298[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1301)
		p.newline()
		field1302 := unwrapped_fields1298[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1302)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1307 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1307 != nil {
		p.write(*flat1307)
		return nil
	} else {
		fields1304 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1304) == 0) {
			p.newline()
			for i1306, elem1305 := range fields1304 {
				if (i1306 > 0) {
					p.newline()
				}
				p.pretty_var(elem1305)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1311 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1311 != nil {
		p.write(*flat1311)
		return nil
	} else {
		fields1308 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1308) == 0) {
			p.newline()
			for i1310, elem1309 := range fields1308 {
				if (i1310 > 0) {
					p.newline()
				}
				p.pretty_var(elem1309)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1320 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1320 != nil {
		p.write(*flat1320)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1654 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1654 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1318 := _t1654
		if deconstruct_result1318 != nil {
			unwrapped1319 := deconstruct_result1318
			p.pretty_edb(unwrapped1319)
		} else {
			_dollar_dollar := msg
			var _t1655 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1655 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1316 := _t1655
			if deconstruct_result1316 != nil {
				unwrapped1317 := deconstruct_result1316
				p.pretty_betree_relation(unwrapped1317)
			} else {
				_dollar_dollar := msg
				var _t1656 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1656 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1314 := _t1656
				if deconstruct_result1314 != nil {
					unwrapped1315 := deconstruct_result1314
					p.pretty_csv_data(unwrapped1315)
				} else {
					_dollar_dollar := msg
					var _t1657 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1657 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1312 := _t1657
					if deconstruct_result1312 != nil {
						unwrapped1313 := deconstruct_result1312
						p.pretty_iceberg_data(unwrapped1313)
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
	flat1326 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1326 != nil {
		p.write(*flat1326)
		return nil
	} else {
		_dollar_dollar := msg
		fields1321 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1322 := fields1321
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1323 := unwrapped_fields1322[0].(*pb.RelationId)
		p.pretty_relation_id(field1323)
		p.newline()
		field1324 := unwrapped_fields1322[1].([]string)
		p.pretty_edb_path(field1324)
		p.newline()
		field1325 := unwrapped_fields1322[2].([]*pb.Type)
		p.pretty_edb_types(field1325)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1330 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1330 != nil {
		p.write(*flat1330)
		return nil
	} else {
		fields1327 := msg
		p.write("[")
		p.indent()
		for i1329, elem1328 := range fields1327 {
			if (i1329 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1328))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1334 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1334 != nil {
		p.write(*flat1334)
		return nil
	} else {
		fields1331 := msg
		p.write("[")
		p.indent()
		for i1333, elem1332 := range fields1331 {
			if (i1333 > 0) {
				p.newline()
			}
			p.pretty_type(elem1332)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1339 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1339 != nil {
		p.write(*flat1339)
		return nil
	} else {
		_dollar_dollar := msg
		fields1335 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1336 := fields1335
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1337 := unwrapped_fields1336[0].(*pb.RelationId)
		p.pretty_relation_id(field1337)
		p.newline()
		field1338 := unwrapped_fields1336[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1338)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1345 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1345 != nil {
		p.write(*flat1345)
		return nil
	} else {
		_dollar_dollar := msg
		_t1658 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1340 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1658}
		unwrapped_fields1341 := fields1340
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1342 := unwrapped_fields1341[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1342)
		p.newline()
		field1343 := unwrapped_fields1341[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1343)
		p.newline()
		field1344 := unwrapped_fields1341[2].([][]interface{})
		p.pretty_config_dict(field1344)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1349 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1349 != nil {
		p.write(*flat1349)
		return nil
	} else {
		fields1346 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1346) == 0) {
			p.newline()
			for i1348, elem1347 := range fields1346 {
				if (i1348 > 0) {
					p.newline()
				}
				p.pretty_type(elem1347)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1353 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1353 != nil {
		p.write(*flat1353)
		return nil
	} else {
		fields1350 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1350) == 0) {
			p.newline()
			for i1352, elem1351 := range fields1350 {
				if (i1352 > 0) {
					p.newline()
				}
				p.pretty_type(elem1351)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1360 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1360 != nil {
		p.write(*flat1360)
		return nil
	} else {
		_dollar_dollar := msg
		fields1354 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1355 := fields1354
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1356 := unwrapped_fields1355[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1356)
		p.newline()
		field1357 := unwrapped_fields1355[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1357)
		p.newline()
		field1358 := unwrapped_fields1355[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1358)
		p.newline()
		field1359 := unwrapped_fields1355[3].(string)
		p.pretty_csv_asof(field1359)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1367 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1367 != nil {
		p.write(*flat1367)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1659 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1659 = _dollar_dollar.GetPaths()
		}
		var _t1660 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1660 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1361 := []interface{}{_t1659, _t1660}
		unwrapped_fields1362 := fields1361
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1363 := unwrapped_fields1362[0].([]string)
		if field1363 != nil {
			p.newline()
			opt_val1364 := field1363
			p.pretty_csv_locator_paths(opt_val1364)
		}
		field1365 := unwrapped_fields1362[1].(*string)
		if field1365 != nil {
			p.newline()
			opt_val1366 := *field1365
			p.pretty_csv_locator_inline_data(opt_val1366)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1371 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1371 != nil {
		p.write(*flat1371)
		return nil
	} else {
		fields1368 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1368) == 0) {
			p.newline()
			for i1370, elem1369 := range fields1368 {
				if (i1370 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1369))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1373 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1373 != nil {
		p.write(*flat1373)
		return nil
	} else {
		fields1372 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1372))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1376 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1376 != nil {
		p.write(*flat1376)
		return nil
	} else {
		_dollar_dollar := msg
		_t1661 := p.deconstruct_csv_config(_dollar_dollar)
		fields1374 := _t1661
		unwrapped_fields1375 := fields1374
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1375)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1380 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1380 != nil {
		p.write(*flat1380)
		return nil
	} else {
		fields1377 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1377) == 0) {
			p.newline()
			for i1379, elem1378 := range fields1377 {
				if (i1379 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1378)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1389 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1389 != nil {
		p.write(*flat1389)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1662 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1662 = _dollar_dollar.GetTargetId()
		}
		fields1381 := []interface{}{_dollar_dollar.GetColumnPath(), _t1662, _dollar_dollar.GetTypes()}
		unwrapped_fields1382 := fields1381
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1383 := unwrapped_fields1382[0].([]string)
		p.pretty_gnf_column_path(field1383)
		field1384 := unwrapped_fields1382[1].(*pb.RelationId)
		if field1384 != nil {
			p.newline()
			opt_val1385 := field1384
			p.pretty_relation_id(opt_val1385)
		}
		p.newline()
		p.write("[")
		field1386 := unwrapped_fields1382[2].([]*pb.Type)
		for i1388, elem1387 := range field1386 {
			if (i1388 > 0) {
				p.newline()
			}
			p.pretty_type(elem1387)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1396 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1396 != nil {
		p.write(*flat1396)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1663 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1663 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1394 := _t1663
		if deconstruct_result1394 != nil {
			unwrapped1395 := *deconstruct_result1394
			p.write(p.formatStringValue(unwrapped1395))
		} else {
			_dollar_dollar := msg
			var _t1664 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1664 = _dollar_dollar
			}
			deconstruct_result1390 := _t1664
			if deconstruct_result1390 != nil {
				unwrapped1391 := deconstruct_result1390
				p.write("[")
				p.indent()
				for i1393, elem1392 := range unwrapped1391 {
					if (i1393 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1392))
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
	flat1398 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1398 != nil {
		p.write(*flat1398)
		return nil
	} else {
		fields1397 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1397))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1406 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1406 != nil {
		p.write(*flat1406)
		return nil
	} else {
		_dollar_dollar := msg
		_t1665 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1399 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1665}
		unwrapped_fields1400 := fields1399
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1401 := unwrapped_fields1400[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1401)
		p.newline()
		field1402 := unwrapped_fields1400[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1402)
		p.newline()
		field1403 := unwrapped_fields1400[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1403)
		field1404 := unwrapped_fields1400[3].(*string)
		if field1404 != nil {
			p.newline()
			opt_val1405 := *field1404
			p.pretty_iceberg_to_snapshot(opt_val1405)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1414 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1414 != nil {
		p.write(*flat1414)
		return nil
	} else {
		_dollar_dollar := msg
		fields1407 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1408 := fields1407
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_name")
		p.newline()
		field1409 := unwrapped_fields1408[0].(string)
		p.write(p.formatStringValue(field1409))
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("namespace")
		field1410 := unwrapped_fields1408[1].([]string)
		if !(len(field1410) == 0) {
			p.newline()
			for i1412, elem1411 := range field1410 {
				if (i1412 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1411))
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("warehouse")
		p.newline()
		field1413 := unwrapped_fields1408[2].(string)
		p.write(p.formatStringValue(field1413))
		p.dedent()
		p.write(")")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config(msg *pb.IcebergCatalogConfig) interface{} {
	flat1426 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config(msg) })
	if flat1426 != nil {
		p.write(*flat1426)
		return nil
	} else {
		_dollar_dollar := msg
		_t1666 := p.deconstruct_iceberg_catalog_config_scope_optional(_dollar_dollar)
		fields1415 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1666, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1416 := fields1415
		p.write("(")
		p.write("iceberg_catalog_config")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("catalog_uri")
		p.newline()
		field1417 := unwrapped_fields1416[0].(string)
		p.write(p.formatStringValue(field1417))
		p.dedent()
		p.write(")")
		field1418 := unwrapped_fields1416[1].(*string)
		if field1418 != nil {
			p.newline()
			opt_val1419 := *field1418
			p.pretty_iceberg_catalog_config_scope(opt_val1419)
		}
		p.newline()
		p.write("(")
		p.newline()
		p.write("properties")
		field1420 := unwrapped_fields1416[2].([][]interface{})
		if !(len(field1420) == 0) {
			p.newline()
			for i1422, elem1421 := range field1420 {
				if (i1422 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1421)
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("auth_properties")
		field1423 := unwrapped_fields1416[3].([][]interface{})
		if !(len(field1423) == 0) {
			p.newline()
			for i1425, elem1424 := range field1423 {
				if (i1425 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1424)
			}
		}
		p.dedent()
		p.write(")")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_catalog_config_scope(msg string) interface{} {
	flat1428 := p.tryFlat(msg, func() { p.pretty_iceberg_catalog_config_scope(msg) })
	if flat1428 != nil {
		p.write(*flat1428)
		return nil
	} else {
		fields1427 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1427))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1433 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1433 != nil {
		p.write(*flat1433)
		return nil
	} else {
		_dollar_dollar := msg
		fields1429 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1430 := fields1429
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1431 := unwrapped_fields1430[0].(string)
		p.write(p.formatStringValue(field1431))
		p.newline()
		field1432 := unwrapped_fields1430[1].(string)
		p.write(p.formatStringValue(field1432))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1435 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1435 != nil {
		p.write(*flat1435)
		return nil
	} else {
		fields1434 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1434))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1438 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1438 != nil {
		p.write(*flat1438)
		return nil
	} else {
		_dollar_dollar := msg
		fields1436 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1437 := fields1436
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1437)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1443 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1443 != nil {
		p.write(*flat1443)
		return nil
	} else {
		_dollar_dollar := msg
		fields1439 := _dollar_dollar.GetRelations()
		unwrapped_fields1440 := fields1439
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1440) == 0) {
			p.newline()
			for i1442, elem1441 := range unwrapped_fields1440 {
				if (i1442 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1441)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1448 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1448 != nil {
		p.write(*flat1448)
		return nil
	} else {
		_dollar_dollar := msg
		fields1444 := _dollar_dollar.GetMappings()
		unwrapped_fields1445 := fields1444
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1445) == 0) {
			p.newline()
			for i1447, elem1446 := range unwrapped_fields1445 {
				if (i1447 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1446)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1453 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1453 != nil {
		p.write(*flat1453)
		return nil
	} else {
		_dollar_dollar := msg
		fields1449 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1450 := fields1449
		field1451 := unwrapped_fields1450[0].([]string)
		p.pretty_edb_path(field1451)
		p.write(" ")
		field1452 := unwrapped_fields1450[1].(*pb.RelationId)
		p.pretty_relation_id(field1452)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1457 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1457 != nil {
		p.write(*flat1457)
		return nil
	} else {
		fields1454 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1454) == 0) {
			p.newline()
			for i1456, elem1455 := range fields1454 {
				if (i1456 > 0) {
					p.newline()
				}
				p.pretty_read(elem1455)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1468 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1468 != nil {
		p.write(*flat1468)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1667 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1667 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1466 := _t1667
		if deconstruct_result1466 != nil {
			unwrapped1467 := deconstruct_result1466
			p.pretty_demand(unwrapped1467)
		} else {
			_dollar_dollar := msg
			var _t1668 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1668 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1464 := _t1668
			if deconstruct_result1464 != nil {
				unwrapped1465 := deconstruct_result1464
				p.pretty_output(unwrapped1465)
			} else {
				_dollar_dollar := msg
				var _t1669 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1669 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1462 := _t1669
				if deconstruct_result1462 != nil {
					unwrapped1463 := deconstruct_result1462
					p.pretty_what_if(unwrapped1463)
				} else {
					_dollar_dollar := msg
					var _t1670 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1670 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1460 := _t1670
					if deconstruct_result1460 != nil {
						unwrapped1461 := deconstruct_result1460
						p.pretty_abort(unwrapped1461)
					} else {
						_dollar_dollar := msg
						var _t1671 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1671 = _dollar_dollar.GetExport()
						}
						deconstruct_result1458 := _t1671
						if deconstruct_result1458 != nil {
							unwrapped1459 := deconstruct_result1458
							p.pretty_export(unwrapped1459)
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
	flat1471 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1471 != nil {
		p.write(*flat1471)
		return nil
	} else {
		_dollar_dollar := msg
		fields1469 := _dollar_dollar.GetRelationId()
		unwrapped_fields1470 := fields1469
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1470)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1476 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1476 != nil {
		p.write(*flat1476)
		return nil
	} else {
		_dollar_dollar := msg
		fields1472 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1473 := fields1472
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1474 := unwrapped_fields1473[0].(string)
		p.pretty_name(field1474)
		p.newline()
		field1475 := unwrapped_fields1473[1].(*pb.RelationId)
		p.pretty_relation_id(field1475)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1481 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1481 != nil {
		p.write(*flat1481)
		return nil
	} else {
		_dollar_dollar := msg
		fields1477 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1478 := fields1477
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1479 := unwrapped_fields1478[0].(string)
		p.pretty_name(field1479)
		p.newline()
		field1480 := unwrapped_fields1478[1].(*pb.Epoch)
		p.pretty_epoch(field1480)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1487 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1487 != nil {
		p.write(*flat1487)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1672 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1672 = ptr(_dollar_dollar.GetName())
		}
		fields1482 := []interface{}{_t1672, _dollar_dollar.GetRelationId()}
		unwrapped_fields1483 := fields1482
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1484 := unwrapped_fields1483[0].(*string)
		if field1484 != nil {
			p.newline()
			opt_val1485 := *field1484
			p.pretty_name(opt_val1485)
		}
		p.newline()
		field1486 := unwrapped_fields1483[1].(*pb.RelationId)
		p.pretty_relation_id(field1486)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1492 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1492 != nil {
		p.write(*flat1492)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1673 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1673 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1490 := _t1673
		if deconstruct_result1490 != nil {
			unwrapped1491 := deconstruct_result1490
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1491)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1674 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1674 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1488 := _t1674
			if deconstruct_result1488 != nil {
				unwrapped1489 := deconstruct_result1488
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1489)
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
	flat1503 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1503 != nil {
		p.write(*flat1503)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1675 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1675 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1498 := _t1675
		if deconstruct_result1498 != nil {
			unwrapped1499 := deconstruct_result1498
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1500 := unwrapped1499[0].(string)
			p.pretty_export_csv_path(field1500)
			p.newline()
			field1501 := unwrapped1499[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1501)
			p.newline()
			field1502 := unwrapped1499[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1502)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1676 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1677 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1676 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1677}
			}
			deconstruct_result1493 := _t1676
			if deconstruct_result1493 != nil {
				unwrapped1494 := deconstruct_result1493
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1495 := unwrapped1494[0].(string)
				p.pretty_export_csv_path(field1495)
				p.newline()
				field1496 := unwrapped1494[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1496)
				p.newline()
				field1497 := unwrapped1494[2].([][]interface{})
				p.pretty_config_dict(field1497)
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
	flat1505 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1505 != nil {
		p.write(*flat1505)
		return nil
	} else {
		fields1504 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1504))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1512 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1512 != nil {
		p.write(*flat1512)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1678 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1678 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1508 := _t1678
		if deconstruct_result1508 != nil {
			unwrapped1509 := deconstruct_result1508
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1509) == 0) {
				p.newline()
				for i1511, elem1510 := range unwrapped1509 {
					if (i1511 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1510)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1679 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1679 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1506 := _t1679
			if deconstruct_result1506 != nil {
				unwrapped1507 := deconstruct_result1506
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1507)
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
	flat1517 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1517 != nil {
		p.write(*flat1517)
		return nil
	} else {
		_dollar_dollar := msg
		fields1513 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1514 := fields1513
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1515 := unwrapped_fields1514[0].(string)
		p.write(p.formatStringValue(field1515))
		p.newline()
		field1516 := unwrapped_fields1514[1].(*pb.RelationId)
		p.pretty_relation_id(field1516)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1521 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1521 != nil {
		p.write(*flat1521)
		return nil
	} else {
		fields1518 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1518) == 0) {
			p.newline()
			for i1520, elem1519 := range fields1518 {
				if (i1520 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1519)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1534 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1534 != nil {
		p.write(*flat1534)
		return nil
	} else {
		_dollar_dollar := msg
		_t1680 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1522 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), dictToPairs(_dollar_dollar.GetCreateTableProperties()), _t1680}
		unwrapped_fields1523 := fields1522
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1524 := unwrapped_fields1523[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1524)
		p.newline()
		field1525 := unwrapped_fields1523[1].(*pb.IcebergCatalogConfig)
		p.pretty_iceberg_catalog_config(field1525)
		p.newline()
		p.write("(")
		p.newline()
		p.write("columns")
		field1526 := unwrapped_fields1523[2].([]*pb.ExportIcebergColumn)
		if !(len(field1526) == 0) {
			p.newline()
			for i1528, elem1527 := range field1526 {
				if (i1528 > 0) {
					p.newline()
				}
				p.pretty_iceberg_export_column(elem1527)
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("create_table_properties")
		field1529 := unwrapped_fields1523[3].([][]interface{})
		if !(len(field1529) == 0) {
			p.newline()
			for i1531, elem1530 := range field1529 {
				if (i1531 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1530)
			}
		}
		p.dedent()
		p.write(")")
		field1532 := unwrapped_fields1523[4].([][]interface{})
		if field1532 != nil {
			p.newline()
			opt_val1533 := field1532
			p.pretty_config_dict(opt_val1533)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_export_column(msg *pb.ExportIcebergColumn) interface{} {
	flat1541 := p.tryFlat(msg, func() { p.pretty_iceberg_export_column(msg) })
	if flat1541 != nil {
		p.write(*flat1541)
		return nil
	} else {
		_dollar_dollar := msg
		fields1535 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetColumnData(), _dollar_dollar.GetType(), _dollar_dollar.GetNullable()}
		unwrapped_fields1536 := fields1535
		p.write("(")
		p.write("iceberg_column")
		p.indentSexp()
		p.newline()
		field1537 := unwrapped_fields1536[0].(string)
		p.write(p.formatStringValue(field1537))
		p.newline()
		field1538 := unwrapped_fields1536[1].(*pb.RelationId)
		p.pretty_relation_id(field1538)
		p.newline()
		field1539 := unwrapped_fields1536[2].(*pb.Type)
		p.pretty_type(field1539)
		p.newline()
		field1540 := unwrapped_fields1536[3].(bool)
		p.pretty_boolean_value(field1540)
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
		_t1725 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1725)
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
	case *pb.ExportIcebergColumn:
		p.pretty_iceberg_export_column(m)
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
