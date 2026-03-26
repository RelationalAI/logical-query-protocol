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
	_t1673 := &pb.Value{}
	_t1673.Value = &pb.Value_Int32Value{Int32Value: v}
	return _t1673
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1674 := &pb.Value{}
	_t1674.Value = &pb.Value_IntValue{IntValue: v}
	return _t1674
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1675 := &pb.Value{}
	_t1675.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1675
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1676 := &pb.Value{}
	_t1676.Value = &pb.Value_StringValue{StringValue: v}
	return _t1676
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1677 := &pb.Value{}
	_t1677.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1677
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1678 := &pb.Value{}
	_t1678.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1678
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1679 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1679})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1680 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1680})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1681 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1681})
			}
		}
	}
	_t1682 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1682})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1683 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1683})
	_t1684 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1684})
	if msg.GetNewLine() != "" {
		_t1685 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1685})
	}
	_t1686 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1686})
	_t1687 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1687})
	_t1688 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1688})
	if msg.GetComment() != "" {
		_t1689 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1689})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1690 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1690})
	}
	_t1691 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1691})
	_t1692 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1692})
	_t1693 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1693})
	if msg.GetPartitionSizeMb() != 0 {
		_t1694 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1694})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1695 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1695})
	_t1696 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1696})
	_t1697 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1697})
	_t1698 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1698})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1699 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1699})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1700 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1700})
		}
	}
	_t1701 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1701})
	_t1702 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1702})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1703 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1703})
	}
	if msg.Compression != nil {
		_t1704 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1704})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1705 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1705})
	}
	if msg.SyntaxMissingString != nil {
		_t1706 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1706})
	}
	if msg.SyntaxDelim != nil {
		_t1707 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1707})
	}
	if msg.SyntaxQuotechar != nil {
		_t1708 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1708})
	}
	if msg.SyntaxEscapechar != nil {
		_t1709 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1709})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_iceberg_config_scope_optional(msg *pb.IcebergConfig) *string {
	var _t1710 interface{}
	if hasProtoField(msg, "scope") {
		return ptr(*msg.Scope)
	}
	_ = _t1710
	return nil
}

func (p *PrettyPrinter) deconstruct_iceberg_data_to_snapshot_optional(msg *pb.IcebergData) *string {
	var _t1711 interface{}
	if hasProtoField(msg, "to_snapshot") {
		return ptr(*msg.ToSnapshot)
	}
	_ = _t1711
	return nil
}

func (p *PrettyPrinter) deconstruct_export_iceberg_config_optional(msg *pb.ExportIcebergConfig) [][]interface{} {
	result := [][]interface{}{}
	if *msg.Prefix != "" {
		_t1712 := p._make_value_string(*msg.Prefix)
		result = append(result, []interface{}{"prefix", _t1712})
	}
	if *msg.TargetFileSizeBytes != 0 {
		_t1713 := p._make_value_int64(*msg.TargetFileSizeBytes)
		result = append(result, []interface{}{"target_file_size_bytes", _t1713})
	}
	if msg.GetCompression() != "" {
		_t1714 := p._make_value_string(msg.GetCompression())
		result = append(result, []interface{}{"compression", _t1714})
	}
	var _t1715 interface{}
	if int64(len(result)) == 0 {
		return nil
	}
	_ = _t1715
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1716 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1716
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
	flat776 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat776 != nil {
		p.write(*flat776)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1534 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1534 = _dollar_dollar.GetConfigure()
		}
		var _t1535 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1535 = _dollar_dollar.GetSync()
		}
		fields767 := []interface{}{_t1534, _t1535, _dollar_dollar.GetEpochs()}
		unwrapped_fields768 := fields767
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field769 := unwrapped_fields768[0].(*pb.Configure)
		if field769 != nil {
			p.newline()
			opt_val770 := field769
			p.pretty_configure(opt_val770)
		}
		field771 := unwrapped_fields768[1].(*pb.Sync)
		if field771 != nil {
			p.newline()
			opt_val772 := field771
			p.pretty_sync(opt_val772)
		}
		field773 := unwrapped_fields768[2].([]*pb.Epoch)
		if !(len(field773) == 0) {
			p.newline()
			for i775, elem774 := range field773 {
				if (i775 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem774)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat779 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat779 != nil {
		p.write(*flat779)
		return nil
	} else {
		_dollar_dollar := msg
		_t1536 := p.deconstruct_configure(_dollar_dollar)
		fields777 := _t1536
		unwrapped_fields778 := fields777
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields778)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat783 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat783 != nil {
		p.write(*flat783)
		return nil
	} else {
		fields780 := msg
		p.write("{")
		p.indent()
		if !(len(fields780) == 0) {
			p.newline()
			for i782, elem781 := range fields780 {
				if (i782 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem781)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat788 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat788 != nil {
		p.write(*flat788)
		return nil
	} else {
		_dollar_dollar := msg
		fields784 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields785 := fields784
		p.write(":")
		field786 := unwrapped_fields785[0].(string)
		p.write(field786)
		p.write(" ")
		field787 := unwrapped_fields785[1].(*pb.Value)
		p.pretty_raw_value(field787)
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_value(msg *pb.Value) interface{} {
	flat814 := p.tryFlat(msg, func() { p.pretty_raw_value(msg) })
	if flat814 != nil {
		p.write(*flat814)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1537 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1537 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result812 := _t1537
		if deconstruct_result812 != nil {
			unwrapped813 := deconstruct_result812
			p.pretty_raw_date(unwrapped813)
		} else {
			_dollar_dollar := msg
			var _t1538 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1538 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result810 := _t1538
			if deconstruct_result810 != nil {
				unwrapped811 := deconstruct_result810
				p.pretty_raw_datetime(unwrapped811)
			} else {
				_dollar_dollar := msg
				var _t1539 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1539 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result808 := _t1539
				if deconstruct_result808 != nil {
					unwrapped809 := *deconstruct_result808
					p.write(p.formatStringValue(unwrapped809))
				} else {
					_dollar_dollar := msg
					var _t1540 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1540 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result806 := _t1540
					if deconstruct_result806 != nil {
						unwrapped807 := *deconstruct_result806
						p.write(fmt.Sprintf("%di32", unwrapped807))
					} else {
						_dollar_dollar := msg
						var _t1541 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1541 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result804 := _t1541
						if deconstruct_result804 != nil {
							unwrapped805 := *deconstruct_result804
							p.write(fmt.Sprintf("%d", unwrapped805))
						} else {
							_dollar_dollar := msg
							var _t1542 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1542 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result802 := _t1542
							if deconstruct_result802 != nil {
								unwrapped803 := *deconstruct_result802
								p.write(formatFloat32(unwrapped803))
							} else {
								_dollar_dollar := msg
								var _t1543 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1543 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result800 := _t1543
								if deconstruct_result800 != nil {
									unwrapped801 := *deconstruct_result800
									p.write(formatFloat64(unwrapped801))
								} else {
									_dollar_dollar := msg
									var _t1544 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1544 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result798 := _t1544
									if deconstruct_result798 != nil {
										unwrapped799 := *deconstruct_result798
										p.write(fmt.Sprintf("%du32", unwrapped799))
									} else {
										_dollar_dollar := msg
										var _t1545 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1545 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result796 := _t1545
										if deconstruct_result796 != nil {
											unwrapped797 := deconstruct_result796
											p.write(p.formatUint128(unwrapped797))
										} else {
											_dollar_dollar := msg
											var _t1546 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1546 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result794 := _t1546
											if deconstruct_result794 != nil {
												unwrapped795 := deconstruct_result794
												p.write(p.formatInt128(unwrapped795))
											} else {
												_dollar_dollar := msg
												var _t1547 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1547 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result792 := _t1547
												if deconstruct_result792 != nil {
													unwrapped793 := deconstruct_result792
													p.write(p.formatDecimal(unwrapped793))
												} else {
													_dollar_dollar := msg
													var _t1548 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1548 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result790 := _t1548
													if deconstruct_result790 != nil {
														unwrapped791 := *deconstruct_result790
														p.pretty_boolean_value(unwrapped791)
													} else {
														fields789 := msg
														_ = fields789
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
	flat820 := p.tryFlat(msg, func() { p.pretty_raw_date(msg) })
	if flat820 != nil {
		p.write(*flat820)
		return nil
	} else {
		_dollar_dollar := msg
		fields815 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields816 := fields815
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field817 := unwrapped_fields816[0].(int64)
		p.write(fmt.Sprintf("%d", field817))
		p.newline()
		field818 := unwrapped_fields816[1].(int64)
		p.write(fmt.Sprintf("%d", field818))
		p.newline()
		field819 := unwrapped_fields816[2].(int64)
		p.write(fmt.Sprintf("%d", field819))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_raw_datetime(msg *pb.DateTimeValue) interface{} {
	flat831 := p.tryFlat(msg, func() { p.pretty_raw_datetime(msg) })
	if flat831 != nil {
		p.write(*flat831)
		return nil
	} else {
		_dollar_dollar := msg
		fields821 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields822 := fields821
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field823 := unwrapped_fields822[0].(int64)
		p.write(fmt.Sprintf("%d", field823))
		p.newline()
		field824 := unwrapped_fields822[1].(int64)
		p.write(fmt.Sprintf("%d", field824))
		p.newline()
		field825 := unwrapped_fields822[2].(int64)
		p.write(fmt.Sprintf("%d", field825))
		p.newline()
		field826 := unwrapped_fields822[3].(int64)
		p.write(fmt.Sprintf("%d", field826))
		p.newline()
		field827 := unwrapped_fields822[4].(int64)
		p.write(fmt.Sprintf("%d", field827))
		p.newline()
		field828 := unwrapped_fields822[5].(int64)
		p.write(fmt.Sprintf("%d", field828))
		field829 := unwrapped_fields822[6].(*int64)
		if field829 != nil {
			p.newline()
			opt_val830 := *field829
			p.write(fmt.Sprintf("%d", opt_val830))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1549 []interface{}
	if _dollar_dollar {
		_t1549 = []interface{}{}
	}
	deconstruct_result834 := _t1549
	if deconstruct_result834 != nil {
		unwrapped835 := deconstruct_result834
		_ = unwrapped835
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1550 []interface{}
		if !(_dollar_dollar) {
			_t1550 = []interface{}{}
		}
		deconstruct_result832 := _t1550
		if deconstruct_result832 != nil {
			unwrapped833 := deconstruct_result832
			_ = unwrapped833
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat840 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat840 != nil {
		p.write(*flat840)
		return nil
	} else {
		_dollar_dollar := msg
		fields836 := _dollar_dollar.GetFragments()
		unwrapped_fields837 := fields836
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields837) == 0) {
			p.newline()
			for i839, elem838 := range unwrapped_fields837 {
				if (i839 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem838)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat843 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat843 != nil {
		p.write(*flat843)
		return nil
	} else {
		_dollar_dollar := msg
		fields841 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields842 := fields841
		p.write(":")
		p.write(unwrapped_fields842)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat850 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat850 != nil {
		p.write(*flat850)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1551 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1551 = _dollar_dollar.GetWrites()
		}
		var _t1552 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1552 = _dollar_dollar.GetReads()
		}
		fields844 := []interface{}{_t1551, _t1552}
		unwrapped_fields845 := fields844
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field846 := unwrapped_fields845[0].([]*pb.Write)
		if field846 != nil {
			p.newline()
			opt_val847 := field846
			p.pretty_epoch_writes(opt_val847)
		}
		field848 := unwrapped_fields845[1].([]*pb.Read)
		if field848 != nil {
			p.newline()
			opt_val849 := field848
			p.pretty_epoch_reads(opt_val849)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat854 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat854 != nil {
		p.write(*flat854)
		return nil
	} else {
		fields851 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields851) == 0) {
			p.newline()
			for i853, elem852 := range fields851 {
				if (i853 > 0) {
					p.newline()
				}
				p.pretty_write(elem852)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat863 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat863 != nil {
		p.write(*flat863)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1553 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1553 = _dollar_dollar.GetDefine()
		}
		deconstruct_result861 := _t1553
		if deconstruct_result861 != nil {
			unwrapped862 := deconstruct_result861
			p.pretty_define(unwrapped862)
		} else {
			_dollar_dollar := msg
			var _t1554 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1554 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result859 := _t1554
			if deconstruct_result859 != nil {
				unwrapped860 := deconstruct_result859
				p.pretty_undefine(unwrapped860)
			} else {
				_dollar_dollar := msg
				var _t1555 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1555 = _dollar_dollar.GetContext()
				}
				deconstruct_result857 := _t1555
				if deconstruct_result857 != nil {
					unwrapped858 := deconstruct_result857
					p.pretty_context(unwrapped858)
				} else {
					_dollar_dollar := msg
					var _t1556 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1556 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result855 := _t1556
					if deconstruct_result855 != nil {
						unwrapped856 := deconstruct_result855
						p.pretty_snapshot(unwrapped856)
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
	flat866 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat866 != nil {
		p.write(*flat866)
		return nil
	} else {
		_dollar_dollar := msg
		fields864 := _dollar_dollar.GetFragment()
		unwrapped_fields865 := fields864
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields865)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat873 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat873 != nil {
		p.write(*flat873)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields867 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields868 := fields867
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field869 := unwrapped_fields868[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field869)
		field870 := unwrapped_fields868[1].([]*pb.Declaration)
		if !(len(field870) == 0) {
			p.newline()
			for i872, elem871 := range field870 {
				if (i872 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem871)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat875 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat875 != nil {
		p.write(*flat875)
		return nil
	} else {
		fields874 := msg
		p.pretty_fragment_id(fields874)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat884 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat884 != nil {
		p.write(*flat884)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1557 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1557 = _dollar_dollar.GetDef()
		}
		deconstruct_result882 := _t1557
		if deconstruct_result882 != nil {
			unwrapped883 := deconstruct_result882
			p.pretty_def(unwrapped883)
		} else {
			_dollar_dollar := msg
			var _t1558 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1558 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result880 := _t1558
			if deconstruct_result880 != nil {
				unwrapped881 := deconstruct_result880
				p.pretty_algorithm(unwrapped881)
			} else {
				_dollar_dollar := msg
				var _t1559 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1559 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result878 := _t1559
				if deconstruct_result878 != nil {
					unwrapped879 := deconstruct_result878
					p.pretty_constraint(unwrapped879)
				} else {
					_dollar_dollar := msg
					var _t1560 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1560 = _dollar_dollar.GetData()
					}
					deconstruct_result876 := _t1560
					if deconstruct_result876 != nil {
						unwrapped877 := deconstruct_result876
						p.pretty_data(unwrapped877)
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
	flat891 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat891 != nil {
		p.write(*flat891)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1561 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1561 = _dollar_dollar.GetAttrs()
		}
		fields885 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1561}
		unwrapped_fields886 := fields885
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field887 := unwrapped_fields886[0].(*pb.RelationId)
		p.pretty_relation_id(field887)
		p.newline()
		field888 := unwrapped_fields886[1].(*pb.Abstraction)
		p.pretty_abstraction(field888)
		field889 := unwrapped_fields886[2].([]*pb.Attribute)
		if field889 != nil {
			p.newline()
			opt_val890 := field889
			p.pretty_attrs(opt_val890)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat896 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat896 != nil {
		p.write(*flat896)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1562 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1563 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1562 = ptr(_t1563)
		}
		deconstruct_result894 := _t1562
		if deconstruct_result894 != nil {
			unwrapped895 := *deconstruct_result894
			p.write(":")
			p.write(unwrapped895)
		} else {
			_dollar_dollar := msg
			_t1564 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result892 := _t1564
			if deconstruct_result892 != nil {
				unwrapped893 := deconstruct_result892
				p.write(p.formatUint128(unwrapped893))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat901 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat901 != nil {
		p.write(*flat901)
		return nil
	} else {
		_dollar_dollar := msg
		_t1565 := p.deconstruct_bindings(_dollar_dollar)
		fields897 := []interface{}{_t1565, _dollar_dollar.GetValue()}
		unwrapped_fields898 := fields897
		p.write("(")
		p.indent()
		field899 := unwrapped_fields898[0].([]interface{})
		p.pretty_bindings(field899)
		p.newline()
		field900 := unwrapped_fields898[1].(*pb.Formula)
		p.pretty_formula(field900)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat909 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat909 != nil {
		p.write(*flat909)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1566 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1566 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields902 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1566}
		unwrapped_fields903 := fields902
		p.write("[")
		p.indent()
		field904 := unwrapped_fields903[0].([]*pb.Binding)
		for i906, elem905 := range field904 {
			if (i906 > 0) {
				p.newline()
			}
			p.pretty_binding(elem905)
		}
		field907 := unwrapped_fields903[1].([]*pb.Binding)
		if field907 != nil {
			p.newline()
			opt_val908 := field907
			p.pretty_value_bindings(opt_val908)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat914 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat914 != nil {
		p.write(*flat914)
		return nil
	} else {
		_dollar_dollar := msg
		fields910 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields911 := fields910
		field912 := unwrapped_fields911[0].(string)
		p.write(field912)
		p.write("::")
		field913 := unwrapped_fields911[1].(*pb.Type)
		p.pretty_type(field913)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat943 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat943 != nil {
		p.write(*flat943)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1567 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1567 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result941 := _t1567
		if deconstruct_result941 != nil {
			unwrapped942 := deconstruct_result941
			p.pretty_unspecified_type(unwrapped942)
		} else {
			_dollar_dollar := msg
			var _t1568 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1568 = _dollar_dollar.GetStringType()
			}
			deconstruct_result939 := _t1568
			if deconstruct_result939 != nil {
				unwrapped940 := deconstruct_result939
				p.pretty_string_type(unwrapped940)
			} else {
				_dollar_dollar := msg
				var _t1569 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1569 = _dollar_dollar.GetIntType()
				}
				deconstruct_result937 := _t1569
				if deconstruct_result937 != nil {
					unwrapped938 := deconstruct_result937
					p.pretty_int_type(unwrapped938)
				} else {
					_dollar_dollar := msg
					var _t1570 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1570 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result935 := _t1570
					if deconstruct_result935 != nil {
						unwrapped936 := deconstruct_result935
						p.pretty_float_type(unwrapped936)
					} else {
						_dollar_dollar := msg
						var _t1571 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1571 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result933 := _t1571
						if deconstruct_result933 != nil {
							unwrapped934 := deconstruct_result933
							p.pretty_uint128_type(unwrapped934)
						} else {
							_dollar_dollar := msg
							var _t1572 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1572 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result931 := _t1572
							if deconstruct_result931 != nil {
								unwrapped932 := deconstruct_result931
								p.pretty_int128_type(unwrapped932)
							} else {
								_dollar_dollar := msg
								var _t1573 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1573 = _dollar_dollar.GetDateType()
								}
								deconstruct_result929 := _t1573
								if deconstruct_result929 != nil {
									unwrapped930 := deconstruct_result929
									p.pretty_date_type(unwrapped930)
								} else {
									_dollar_dollar := msg
									var _t1574 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1574 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result927 := _t1574
									if deconstruct_result927 != nil {
										unwrapped928 := deconstruct_result927
										p.pretty_datetime_type(unwrapped928)
									} else {
										_dollar_dollar := msg
										var _t1575 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1575 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result925 := _t1575
										if deconstruct_result925 != nil {
											unwrapped926 := deconstruct_result925
											p.pretty_missing_type(unwrapped926)
										} else {
											_dollar_dollar := msg
											var _t1576 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1576 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result923 := _t1576
											if deconstruct_result923 != nil {
												unwrapped924 := deconstruct_result923
												p.pretty_decimal_type(unwrapped924)
											} else {
												_dollar_dollar := msg
												var _t1577 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1577 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result921 := _t1577
												if deconstruct_result921 != nil {
													unwrapped922 := deconstruct_result921
													p.pretty_boolean_type(unwrapped922)
												} else {
													_dollar_dollar := msg
													var _t1578 *pb.Int32Type
													if hasProtoField(_dollar_dollar, "int32_type") {
														_t1578 = _dollar_dollar.GetInt32Type()
													}
													deconstruct_result919 := _t1578
													if deconstruct_result919 != nil {
														unwrapped920 := deconstruct_result919
														p.pretty_int32_type(unwrapped920)
													} else {
														_dollar_dollar := msg
														var _t1579 *pb.Float32Type
														if hasProtoField(_dollar_dollar, "float32_type") {
															_t1579 = _dollar_dollar.GetFloat32Type()
														}
														deconstruct_result917 := _t1579
														if deconstruct_result917 != nil {
															unwrapped918 := deconstruct_result917
															p.pretty_float32_type(unwrapped918)
														} else {
															_dollar_dollar := msg
															var _t1580 *pb.UInt32Type
															if hasProtoField(_dollar_dollar, "uint32_type") {
																_t1580 = _dollar_dollar.GetUint32Type()
															}
															deconstruct_result915 := _t1580
															if deconstruct_result915 != nil {
																unwrapped916 := deconstruct_result915
																p.pretty_uint32_type(unwrapped916)
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
	fields944 := msg
	_ = fields944
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields945 := msg
	_ = fields945
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields946 := msg
	_ = fields946
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields947 := msg
	_ = fields947
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields948 := msg
	_ = fields948
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields949 := msg
	_ = fields949
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields950 := msg
	_ = fields950
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields951 := msg
	_ = fields951
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields952 := msg
	_ = fields952
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat957 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat957 != nil {
		p.write(*flat957)
		return nil
	} else {
		_dollar_dollar := msg
		fields953 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields954 := fields953
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field955 := unwrapped_fields954[0].(int64)
		p.write(fmt.Sprintf("%d", field955))
		p.newline()
		field956 := unwrapped_fields954[1].(int64)
		p.write(fmt.Sprintf("%d", field956))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields958 := msg
	_ = fields958
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_int32_type(msg *pb.Int32Type) interface{} {
	fields959 := msg
	_ = fields959
	p.write("INT32")
	return nil
}

func (p *PrettyPrinter) pretty_float32_type(msg *pb.Float32Type) interface{} {
	fields960 := msg
	_ = fields960
	p.write("FLOAT32")
	return nil
}

func (p *PrettyPrinter) pretty_uint32_type(msg *pb.UInt32Type) interface{} {
	fields961 := msg
	_ = fields961
	p.write("UINT32")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat965 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat965 != nil {
		p.write(*flat965)
		return nil
	} else {
		fields962 := msg
		p.write("|")
		if !(len(fields962) == 0) {
			p.write(" ")
			for i964, elem963 := range fields962 {
				if (i964 > 0) {
					p.newline()
				}
				p.pretty_binding(elem963)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat992 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat992 != nil {
		p.write(*flat992)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1581 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1581 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result990 := _t1581
		if deconstruct_result990 != nil {
			unwrapped991 := deconstruct_result990
			p.pretty_true(unwrapped991)
		} else {
			_dollar_dollar := msg
			var _t1582 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1582 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result988 := _t1582
			if deconstruct_result988 != nil {
				unwrapped989 := deconstruct_result988
				p.pretty_false(unwrapped989)
			} else {
				_dollar_dollar := msg
				var _t1583 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1583 = _dollar_dollar.GetExists()
				}
				deconstruct_result986 := _t1583
				if deconstruct_result986 != nil {
					unwrapped987 := deconstruct_result986
					p.pretty_exists(unwrapped987)
				} else {
					_dollar_dollar := msg
					var _t1584 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1584 = _dollar_dollar.GetReduce()
					}
					deconstruct_result984 := _t1584
					if deconstruct_result984 != nil {
						unwrapped985 := deconstruct_result984
						p.pretty_reduce(unwrapped985)
					} else {
						_dollar_dollar := msg
						var _t1585 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1585 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result982 := _t1585
						if deconstruct_result982 != nil {
							unwrapped983 := deconstruct_result982
							p.pretty_conjunction(unwrapped983)
						} else {
							_dollar_dollar := msg
							var _t1586 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1586 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result980 := _t1586
							if deconstruct_result980 != nil {
								unwrapped981 := deconstruct_result980
								p.pretty_disjunction(unwrapped981)
							} else {
								_dollar_dollar := msg
								var _t1587 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1587 = _dollar_dollar.GetNot()
								}
								deconstruct_result978 := _t1587
								if deconstruct_result978 != nil {
									unwrapped979 := deconstruct_result978
									p.pretty_not(unwrapped979)
								} else {
									_dollar_dollar := msg
									var _t1588 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1588 = _dollar_dollar.GetFfi()
									}
									deconstruct_result976 := _t1588
									if deconstruct_result976 != nil {
										unwrapped977 := deconstruct_result976
										p.pretty_ffi(unwrapped977)
									} else {
										_dollar_dollar := msg
										var _t1589 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1589 = _dollar_dollar.GetAtom()
										}
										deconstruct_result974 := _t1589
										if deconstruct_result974 != nil {
											unwrapped975 := deconstruct_result974
											p.pretty_atom(unwrapped975)
										} else {
											_dollar_dollar := msg
											var _t1590 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1590 = _dollar_dollar.GetPragma()
											}
											deconstruct_result972 := _t1590
											if deconstruct_result972 != nil {
												unwrapped973 := deconstruct_result972
												p.pretty_pragma(unwrapped973)
											} else {
												_dollar_dollar := msg
												var _t1591 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1591 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result970 := _t1591
												if deconstruct_result970 != nil {
													unwrapped971 := deconstruct_result970
													p.pretty_primitive(unwrapped971)
												} else {
													_dollar_dollar := msg
													var _t1592 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1592 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result968 := _t1592
													if deconstruct_result968 != nil {
														unwrapped969 := deconstruct_result968
														p.pretty_rel_atom(unwrapped969)
													} else {
														_dollar_dollar := msg
														var _t1593 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1593 = _dollar_dollar.GetCast()
														}
														deconstruct_result966 := _t1593
														if deconstruct_result966 != nil {
															unwrapped967 := deconstruct_result966
															p.pretty_cast(unwrapped967)
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
	fields993 := msg
	_ = fields993
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields994 := msg
	_ = fields994
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat999 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat999 != nil {
		p.write(*flat999)
		return nil
	} else {
		_dollar_dollar := msg
		_t1594 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields995 := []interface{}{_t1594, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields996 := fields995
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field997 := unwrapped_fields996[0].([]interface{})
		p.pretty_bindings(field997)
		p.newline()
		field998 := unwrapped_fields996[1].(*pb.Formula)
		p.pretty_formula(field998)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat1005 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat1005 != nil {
		p.write(*flat1005)
		return nil
	} else {
		_dollar_dollar := msg
		fields1000 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields1001 := fields1000
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field1002 := unwrapped_fields1001[0].(*pb.Abstraction)
		p.pretty_abstraction(field1002)
		p.newline()
		field1003 := unwrapped_fields1001[1].(*pb.Abstraction)
		p.pretty_abstraction(field1003)
		p.newline()
		field1004 := unwrapped_fields1001[2].([]*pb.Term)
		p.pretty_terms(field1004)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat1009 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat1009 != nil {
		p.write(*flat1009)
		return nil
	} else {
		fields1006 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields1006) == 0) {
			p.newline()
			for i1008, elem1007 := range fields1006 {
				if (i1008 > 0) {
					p.newline()
				}
				p.pretty_term(elem1007)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat1014 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat1014 != nil {
		p.write(*flat1014)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1595 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1595 = _dollar_dollar.GetVar()
		}
		deconstruct_result1012 := _t1595
		if deconstruct_result1012 != nil {
			unwrapped1013 := deconstruct_result1012
			p.pretty_var(unwrapped1013)
		} else {
			_dollar_dollar := msg
			var _t1596 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1596 = _dollar_dollar.GetConstant()
			}
			deconstruct_result1010 := _t1596
			if deconstruct_result1010 != nil {
				unwrapped1011 := deconstruct_result1010
				p.pretty_value(unwrapped1011)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat1017 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat1017 != nil {
		p.write(*flat1017)
		return nil
	} else {
		_dollar_dollar := msg
		fields1015 := _dollar_dollar.GetName()
		unwrapped_fields1016 := fields1015
		p.write(unwrapped_fields1016)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat1043 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat1043 != nil {
		p.write(*flat1043)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1597 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1597 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result1041 := _t1597
		if deconstruct_result1041 != nil {
			unwrapped1042 := deconstruct_result1041
			p.pretty_date(unwrapped1042)
		} else {
			_dollar_dollar := msg
			var _t1598 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1598 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result1039 := _t1598
			if deconstruct_result1039 != nil {
				unwrapped1040 := deconstruct_result1039
				p.pretty_datetime(unwrapped1040)
			} else {
				_dollar_dollar := msg
				var _t1599 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1599 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result1037 := _t1599
				if deconstruct_result1037 != nil {
					unwrapped1038 := *deconstruct_result1037
					p.write(p.formatStringValue(unwrapped1038))
				} else {
					_dollar_dollar := msg
					var _t1600 *int32
					if hasProtoField(_dollar_dollar, "int32_value") {
						_t1600 = ptr(_dollar_dollar.GetInt32Value())
					}
					deconstruct_result1035 := _t1600
					if deconstruct_result1035 != nil {
						unwrapped1036 := *deconstruct_result1035
						p.write(fmt.Sprintf("%di32", unwrapped1036))
					} else {
						_dollar_dollar := msg
						var _t1601 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1601 = ptr(_dollar_dollar.GetIntValue())
						}
						deconstruct_result1033 := _t1601
						if deconstruct_result1033 != nil {
							unwrapped1034 := *deconstruct_result1033
							p.write(fmt.Sprintf("%d", unwrapped1034))
						} else {
							_dollar_dollar := msg
							var _t1602 *float32
							if hasProtoField(_dollar_dollar, "float32_value") {
								_t1602 = ptr(_dollar_dollar.GetFloat32Value())
							}
							deconstruct_result1031 := _t1602
							if deconstruct_result1031 != nil {
								unwrapped1032 := *deconstruct_result1031
								p.write(formatFloat32(unwrapped1032))
							} else {
								_dollar_dollar := msg
								var _t1603 *float64
								if hasProtoField(_dollar_dollar, "float_value") {
									_t1603 = ptr(_dollar_dollar.GetFloatValue())
								}
								deconstruct_result1029 := _t1603
								if deconstruct_result1029 != nil {
									unwrapped1030 := *deconstruct_result1029
									p.write(formatFloat64(unwrapped1030))
								} else {
									_dollar_dollar := msg
									var _t1604 *uint32
									if hasProtoField(_dollar_dollar, "uint32_value") {
										_t1604 = ptr(_dollar_dollar.GetUint32Value())
									}
									deconstruct_result1027 := _t1604
									if deconstruct_result1027 != nil {
										unwrapped1028 := *deconstruct_result1027
										p.write(fmt.Sprintf("%du32", unwrapped1028))
									} else {
										_dollar_dollar := msg
										var _t1605 *pb.UInt128Value
										if hasProtoField(_dollar_dollar, "uint128_value") {
											_t1605 = _dollar_dollar.GetUint128Value()
										}
										deconstruct_result1025 := _t1605
										if deconstruct_result1025 != nil {
											unwrapped1026 := deconstruct_result1025
											p.write(p.formatUint128(unwrapped1026))
										} else {
											_dollar_dollar := msg
											var _t1606 *pb.Int128Value
											if hasProtoField(_dollar_dollar, "int128_value") {
												_t1606 = _dollar_dollar.GetInt128Value()
											}
											deconstruct_result1023 := _t1606
											if deconstruct_result1023 != nil {
												unwrapped1024 := deconstruct_result1023
												p.write(p.formatInt128(unwrapped1024))
											} else {
												_dollar_dollar := msg
												var _t1607 *pb.DecimalValue
												if hasProtoField(_dollar_dollar, "decimal_value") {
													_t1607 = _dollar_dollar.GetDecimalValue()
												}
												deconstruct_result1021 := _t1607
												if deconstruct_result1021 != nil {
													unwrapped1022 := deconstruct_result1021
													p.write(p.formatDecimal(unwrapped1022))
												} else {
													_dollar_dollar := msg
													var _t1608 *bool
													if hasProtoField(_dollar_dollar, "boolean_value") {
														_t1608 = ptr(_dollar_dollar.GetBooleanValue())
													}
													deconstruct_result1019 := _t1608
													if deconstruct_result1019 != nil {
														unwrapped1020 := *deconstruct_result1019
														p.pretty_boolean_value(unwrapped1020)
													} else {
														fields1018 := msg
														_ = fields1018
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
	flat1049 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat1049 != nil {
		p.write(*flat1049)
		return nil
	} else {
		_dollar_dollar := msg
		fields1044 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields1045 := fields1044
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field1046 := unwrapped_fields1045[0].(int64)
		p.write(fmt.Sprintf("%d", field1046))
		p.newline()
		field1047 := unwrapped_fields1045[1].(int64)
		p.write(fmt.Sprintf("%d", field1047))
		p.newline()
		field1048 := unwrapped_fields1045[2].(int64)
		p.write(fmt.Sprintf("%d", field1048))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat1060 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat1060 != nil {
		p.write(*flat1060)
		return nil
	} else {
		_dollar_dollar := msg
		fields1050 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields1051 := fields1050
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field1052 := unwrapped_fields1051[0].(int64)
		p.write(fmt.Sprintf("%d", field1052))
		p.newline()
		field1053 := unwrapped_fields1051[1].(int64)
		p.write(fmt.Sprintf("%d", field1053))
		p.newline()
		field1054 := unwrapped_fields1051[2].(int64)
		p.write(fmt.Sprintf("%d", field1054))
		p.newline()
		field1055 := unwrapped_fields1051[3].(int64)
		p.write(fmt.Sprintf("%d", field1055))
		p.newline()
		field1056 := unwrapped_fields1051[4].(int64)
		p.write(fmt.Sprintf("%d", field1056))
		p.newline()
		field1057 := unwrapped_fields1051[5].(int64)
		p.write(fmt.Sprintf("%d", field1057))
		field1058 := unwrapped_fields1051[6].(*int64)
		if field1058 != nil {
			p.newline()
			opt_val1059 := *field1058
			p.write(fmt.Sprintf("%d", opt_val1059))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat1065 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat1065 != nil {
		p.write(*flat1065)
		return nil
	} else {
		_dollar_dollar := msg
		fields1061 := _dollar_dollar.GetArgs()
		unwrapped_fields1062 := fields1061
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields1062) == 0) {
			p.newline()
			for i1064, elem1063 := range unwrapped_fields1062 {
				if (i1064 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1063)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat1070 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat1070 != nil {
		p.write(*flat1070)
		return nil
	} else {
		_dollar_dollar := msg
		fields1066 := _dollar_dollar.GetArgs()
		unwrapped_fields1067 := fields1066
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields1067) == 0) {
			p.newline()
			for i1069, elem1068 := range unwrapped_fields1067 {
				if (i1069 > 0) {
					p.newline()
				}
				p.pretty_formula(elem1068)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat1073 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat1073 != nil {
		p.write(*flat1073)
		return nil
	} else {
		_dollar_dollar := msg
		fields1071 := _dollar_dollar.GetArg()
		unwrapped_fields1072 := fields1071
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields1072)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat1079 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat1079 != nil {
		p.write(*flat1079)
		return nil
	} else {
		_dollar_dollar := msg
		fields1074 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields1075 := fields1074
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field1076 := unwrapped_fields1075[0].(string)
		p.pretty_name(field1076)
		p.newline()
		field1077 := unwrapped_fields1075[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field1077)
		p.newline()
		field1078 := unwrapped_fields1075[2].([]*pb.Term)
		p.pretty_terms(field1078)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat1081 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat1081 != nil {
		p.write(*flat1081)
		return nil
	} else {
		fields1080 := msg
		p.write(":")
		p.write(fields1080)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat1085 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat1085 != nil {
		p.write(*flat1085)
		return nil
	} else {
		fields1082 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields1082) == 0) {
			p.newline()
			for i1084, elem1083 := range fields1082 {
				if (i1084 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem1083)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat1092 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat1092 != nil {
		p.write(*flat1092)
		return nil
	} else {
		_dollar_dollar := msg
		fields1086 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1087 := fields1086
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field1088 := unwrapped_fields1087[0].(*pb.RelationId)
		p.pretty_relation_id(field1088)
		field1089 := unwrapped_fields1087[1].([]*pb.Term)
		if !(len(field1089) == 0) {
			p.newline()
			for i1091, elem1090 := range field1089 {
				if (i1091 > 0) {
					p.newline()
				}
				p.pretty_term(elem1090)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat1099 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat1099 != nil {
		p.write(*flat1099)
		return nil
	} else {
		_dollar_dollar := msg
		fields1093 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1094 := fields1093
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field1095 := unwrapped_fields1094[0].(string)
		p.pretty_name(field1095)
		field1096 := unwrapped_fields1094[1].([]*pb.Term)
		if !(len(field1096) == 0) {
			p.newline()
			for i1098, elem1097 := range field1096 {
				if (i1098 > 0) {
					p.newline()
				}
				p.pretty_term(elem1097)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat1115 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat1115 != nil {
		p.write(*flat1115)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1609 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1609 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result1114 := _t1609
		if guard_result1114 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1610 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1610 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result1113 := _t1610
			if guard_result1113 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1611 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1611 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result1112 := _t1611
				if guard_result1112 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1612 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1612 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result1111 := _t1612
					if guard_result1111 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1613 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1613 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result1110 := _t1613
						if guard_result1110 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1614 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1614 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result1109 := _t1614
							if guard_result1109 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1615 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1615 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result1108 := _t1615
								if guard_result1108 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1616 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1616 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result1107 := _t1616
									if guard_result1107 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1617 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1617 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result1106 := _t1617
										if guard_result1106 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields1100 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields1101 := fields1100
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field1102 := unwrapped_fields1101[0].(string)
											p.pretty_name(field1102)
											field1103 := unwrapped_fields1101[1].([]*pb.RelTerm)
											if !(len(field1103) == 0) {
												p.newline()
												for i1105, elem1104 := range field1103 {
													if (i1105 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem1104)
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
	flat1120 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat1120 != nil {
		p.write(*flat1120)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1618 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1618 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1116 := _t1618
		unwrapped_fields1117 := fields1116
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field1118 := unwrapped_fields1117[0].(*pb.Term)
		p.pretty_term(field1118)
		p.newline()
		field1119 := unwrapped_fields1117[1].(*pb.Term)
		p.pretty_term(field1119)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat1125 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat1125 != nil {
		p.write(*flat1125)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1619 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1619 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1121 := _t1619
		unwrapped_fields1122 := fields1121
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field1123 := unwrapped_fields1122[0].(*pb.Term)
		p.pretty_term(field1123)
		p.newline()
		field1124 := unwrapped_fields1122[1].(*pb.Term)
		p.pretty_term(field1124)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat1130 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat1130 != nil {
		p.write(*flat1130)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1620 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1620 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1126 := _t1620
		unwrapped_fields1127 := fields1126
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field1128 := unwrapped_fields1127[0].(*pb.Term)
		p.pretty_term(field1128)
		p.newline()
		field1129 := unwrapped_fields1127[1].(*pb.Term)
		p.pretty_term(field1129)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat1135 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat1135 != nil {
		p.write(*flat1135)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1621 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1621 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1131 := _t1621
		unwrapped_fields1132 := fields1131
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field1133 := unwrapped_fields1132[0].(*pb.Term)
		p.pretty_term(field1133)
		p.newline()
		field1134 := unwrapped_fields1132[1].(*pb.Term)
		p.pretty_term(field1134)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat1140 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat1140 != nil {
		p.write(*flat1140)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1622 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1622 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields1136 := _t1622
		unwrapped_fields1137 := fields1136
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field1138 := unwrapped_fields1137[0].(*pb.Term)
		p.pretty_term(field1138)
		p.newline()
		field1139 := unwrapped_fields1137[1].(*pb.Term)
		p.pretty_term(field1139)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat1146 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat1146 != nil {
		p.write(*flat1146)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1623 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1623 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1141 := _t1623
		unwrapped_fields1142 := fields1141
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field1143 := unwrapped_fields1142[0].(*pb.Term)
		p.pretty_term(field1143)
		p.newline()
		field1144 := unwrapped_fields1142[1].(*pb.Term)
		p.pretty_term(field1144)
		p.newline()
		field1145 := unwrapped_fields1142[2].(*pb.Term)
		p.pretty_term(field1145)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat1152 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat1152 != nil {
		p.write(*flat1152)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1624 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1624 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1147 := _t1624
		unwrapped_fields1148 := fields1147
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field1149 := unwrapped_fields1148[0].(*pb.Term)
		p.pretty_term(field1149)
		p.newline()
		field1150 := unwrapped_fields1148[1].(*pb.Term)
		p.pretty_term(field1150)
		p.newline()
		field1151 := unwrapped_fields1148[2].(*pb.Term)
		p.pretty_term(field1151)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat1158 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat1158 != nil {
		p.write(*flat1158)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1625 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1625 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1153 := _t1625
		unwrapped_fields1154 := fields1153
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field1155 := unwrapped_fields1154[0].(*pb.Term)
		p.pretty_term(field1155)
		p.newline()
		field1156 := unwrapped_fields1154[1].(*pb.Term)
		p.pretty_term(field1156)
		p.newline()
		field1157 := unwrapped_fields1154[2].(*pb.Term)
		p.pretty_term(field1157)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat1164 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat1164 != nil {
		p.write(*flat1164)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1626 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1626 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields1159 := _t1626
		unwrapped_fields1160 := fields1159
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field1161 := unwrapped_fields1160[0].(*pb.Term)
		p.pretty_term(field1161)
		p.newline()
		field1162 := unwrapped_fields1160[1].(*pb.Term)
		p.pretty_term(field1162)
		p.newline()
		field1163 := unwrapped_fields1160[2].(*pb.Term)
		p.pretty_term(field1163)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1169 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1169 != nil {
		p.write(*flat1169)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1627 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1627 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result1167 := _t1627
		if deconstruct_result1167 != nil {
			unwrapped1168 := deconstruct_result1167
			p.pretty_specialized_value(unwrapped1168)
		} else {
			_dollar_dollar := msg
			var _t1628 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1628 = _dollar_dollar.GetTerm()
			}
			deconstruct_result1165 := _t1628
			if deconstruct_result1165 != nil {
				unwrapped1166 := deconstruct_result1165
				p.pretty_term(unwrapped1166)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1171 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1171 != nil {
		p.write(*flat1171)
		return nil
	} else {
		fields1170 := msg
		p.write("#")
		p.pretty_raw_value(fields1170)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1178 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1178 != nil {
		p.write(*flat1178)
		return nil
	} else {
		_dollar_dollar := msg
		fields1172 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1173 := fields1172
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1174 := unwrapped_fields1173[0].(string)
		p.pretty_name(field1174)
		field1175 := unwrapped_fields1173[1].([]*pb.RelTerm)
		if !(len(field1175) == 0) {
			p.newline()
			for i1177, elem1176 := range field1175 {
				if (i1177 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1176)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1183 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1183 != nil {
		p.write(*flat1183)
		return nil
	} else {
		_dollar_dollar := msg
		fields1179 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1180 := fields1179
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1181 := unwrapped_fields1180[0].(*pb.Term)
		p.pretty_term(field1181)
		p.newline()
		field1182 := unwrapped_fields1180[1].(*pb.Term)
		p.pretty_term(field1182)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1187 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1187 != nil {
		p.write(*flat1187)
		return nil
	} else {
		fields1184 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1184) == 0) {
			p.newline()
			for i1186, elem1185 := range fields1184 {
				if (i1186 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1185)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1194 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1194 != nil {
		p.write(*flat1194)
		return nil
	} else {
		_dollar_dollar := msg
		fields1188 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1189 := fields1188
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1190 := unwrapped_fields1189[0].(string)
		p.pretty_name(field1190)
		field1191 := unwrapped_fields1189[1].([]*pb.Value)
		if !(len(field1191) == 0) {
			p.newline()
			for i1193, elem1192 := range field1191 {
				if (i1193 > 0) {
					p.newline()
				}
				p.pretty_raw_value(elem1192)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1201 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1201 != nil {
		p.write(*flat1201)
		return nil
	} else {
		_dollar_dollar := msg
		fields1195 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1196 := fields1195
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1197 := unwrapped_fields1196[0].([]*pb.RelationId)
		if !(len(field1197) == 0) {
			p.newline()
			for i1199, elem1198 := range field1197 {
				if (i1199 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1198)
			}
		}
		p.newline()
		field1200 := unwrapped_fields1196[1].(*pb.Script)
		p.pretty_script(field1200)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1206 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1206 != nil {
		p.write(*flat1206)
		return nil
	} else {
		_dollar_dollar := msg
		fields1202 := _dollar_dollar.GetConstructs()
		unwrapped_fields1203 := fields1202
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1203) == 0) {
			p.newline()
			for i1205, elem1204 := range unwrapped_fields1203 {
				if (i1205 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1204)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1211 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1211 != nil {
		p.write(*flat1211)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1629 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1629 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1209 := _t1629
		if deconstruct_result1209 != nil {
			unwrapped1210 := deconstruct_result1209
			p.pretty_loop(unwrapped1210)
		} else {
			_dollar_dollar := msg
			var _t1630 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1630 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1207 := _t1630
			if deconstruct_result1207 != nil {
				unwrapped1208 := deconstruct_result1207
				p.pretty_instruction(unwrapped1208)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1216 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1216 != nil {
		p.write(*flat1216)
		return nil
	} else {
		_dollar_dollar := msg
		fields1212 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1213 := fields1212
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1214 := unwrapped_fields1213[0].([]*pb.Instruction)
		p.pretty_init(field1214)
		p.newline()
		field1215 := unwrapped_fields1213[1].(*pb.Script)
		p.pretty_script(field1215)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1220 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1220 != nil {
		p.write(*flat1220)
		return nil
	} else {
		fields1217 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1217) == 0) {
			p.newline()
			for i1219, elem1218 := range fields1217 {
				if (i1219 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1218)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1231 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1231 != nil {
		p.write(*flat1231)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1631 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1631 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1229 := _t1631
		if deconstruct_result1229 != nil {
			unwrapped1230 := deconstruct_result1229
			p.pretty_assign(unwrapped1230)
		} else {
			_dollar_dollar := msg
			var _t1632 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1632 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1227 := _t1632
			if deconstruct_result1227 != nil {
				unwrapped1228 := deconstruct_result1227
				p.pretty_upsert(unwrapped1228)
			} else {
				_dollar_dollar := msg
				var _t1633 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1633 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1225 := _t1633
				if deconstruct_result1225 != nil {
					unwrapped1226 := deconstruct_result1225
					p.pretty_break(unwrapped1226)
				} else {
					_dollar_dollar := msg
					var _t1634 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1634 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1223 := _t1634
					if deconstruct_result1223 != nil {
						unwrapped1224 := deconstruct_result1223
						p.pretty_monoid_def(unwrapped1224)
					} else {
						_dollar_dollar := msg
						var _t1635 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1635 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1221 := _t1635
						if deconstruct_result1221 != nil {
							unwrapped1222 := deconstruct_result1221
							p.pretty_monus_def(unwrapped1222)
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
	flat1238 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1238 != nil {
		p.write(*flat1238)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1636 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1636 = _dollar_dollar.GetAttrs()
		}
		fields1232 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1636}
		unwrapped_fields1233 := fields1232
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1234 := unwrapped_fields1233[0].(*pb.RelationId)
		p.pretty_relation_id(field1234)
		p.newline()
		field1235 := unwrapped_fields1233[1].(*pb.Abstraction)
		p.pretty_abstraction(field1235)
		field1236 := unwrapped_fields1233[2].([]*pb.Attribute)
		if field1236 != nil {
			p.newline()
			opt_val1237 := field1236
			p.pretty_attrs(opt_val1237)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1245 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1245 != nil {
		p.write(*flat1245)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1637 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1637 = _dollar_dollar.GetAttrs()
		}
		fields1239 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1637}
		unwrapped_fields1240 := fields1239
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1241 := unwrapped_fields1240[0].(*pb.RelationId)
		p.pretty_relation_id(field1241)
		p.newline()
		field1242 := unwrapped_fields1240[1].([]interface{})
		p.pretty_abstraction_with_arity(field1242)
		field1243 := unwrapped_fields1240[2].([]*pb.Attribute)
		if field1243 != nil {
			p.newline()
			opt_val1244 := field1243
			p.pretty_attrs(opt_val1244)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1250 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1250 != nil {
		p.write(*flat1250)
		return nil
	} else {
		_dollar_dollar := msg
		_t1638 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1246 := []interface{}{_t1638, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1247 := fields1246
		p.write("(")
		p.indent()
		field1248 := unwrapped_fields1247[0].([]interface{})
		p.pretty_bindings(field1248)
		p.newline()
		field1249 := unwrapped_fields1247[1].(*pb.Formula)
		p.pretty_formula(field1249)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1257 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1257 != nil {
		p.write(*flat1257)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1639 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1639 = _dollar_dollar.GetAttrs()
		}
		fields1251 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1639}
		unwrapped_fields1252 := fields1251
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1253 := unwrapped_fields1252[0].(*pb.RelationId)
		p.pretty_relation_id(field1253)
		p.newline()
		field1254 := unwrapped_fields1252[1].(*pb.Abstraction)
		p.pretty_abstraction(field1254)
		field1255 := unwrapped_fields1252[2].([]*pb.Attribute)
		if field1255 != nil {
			p.newline()
			opt_val1256 := field1255
			p.pretty_attrs(opt_val1256)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1265 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1265 != nil {
		p.write(*flat1265)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1640 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1640 = _dollar_dollar.GetAttrs()
		}
		fields1258 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1640}
		unwrapped_fields1259 := fields1258
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1260 := unwrapped_fields1259[0].(*pb.Monoid)
		p.pretty_monoid(field1260)
		p.newline()
		field1261 := unwrapped_fields1259[1].(*pb.RelationId)
		p.pretty_relation_id(field1261)
		p.newline()
		field1262 := unwrapped_fields1259[2].([]interface{})
		p.pretty_abstraction_with_arity(field1262)
		field1263 := unwrapped_fields1259[3].([]*pb.Attribute)
		if field1263 != nil {
			p.newline()
			opt_val1264 := field1263
			p.pretty_attrs(opt_val1264)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1274 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1274 != nil {
		p.write(*flat1274)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1641 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1641 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1272 := _t1641
		if deconstruct_result1272 != nil {
			unwrapped1273 := deconstruct_result1272
			p.pretty_or_monoid(unwrapped1273)
		} else {
			_dollar_dollar := msg
			var _t1642 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1642 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1270 := _t1642
			if deconstruct_result1270 != nil {
				unwrapped1271 := deconstruct_result1270
				p.pretty_min_monoid(unwrapped1271)
			} else {
				_dollar_dollar := msg
				var _t1643 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1643 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1268 := _t1643
				if deconstruct_result1268 != nil {
					unwrapped1269 := deconstruct_result1268
					p.pretty_max_monoid(unwrapped1269)
				} else {
					_dollar_dollar := msg
					var _t1644 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1644 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1266 := _t1644
					if deconstruct_result1266 != nil {
						unwrapped1267 := deconstruct_result1266
						p.pretty_sum_monoid(unwrapped1267)
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
	fields1275 := msg
	_ = fields1275
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1278 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1278 != nil {
		p.write(*flat1278)
		return nil
	} else {
		_dollar_dollar := msg
		fields1276 := _dollar_dollar.GetType()
		unwrapped_fields1277 := fields1276
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1277)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1281 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1281 != nil {
		p.write(*flat1281)
		return nil
	} else {
		_dollar_dollar := msg
		fields1279 := _dollar_dollar.GetType()
		unwrapped_fields1280 := fields1279
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1280)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1284 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1284 != nil {
		p.write(*flat1284)
		return nil
	} else {
		_dollar_dollar := msg
		fields1282 := _dollar_dollar.GetType()
		unwrapped_fields1283 := fields1282
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1283)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1292 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1292 != nil {
		p.write(*flat1292)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1645 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1645 = _dollar_dollar.GetAttrs()
		}
		fields1285 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1645}
		unwrapped_fields1286 := fields1285
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1287 := unwrapped_fields1286[0].(*pb.Monoid)
		p.pretty_monoid(field1287)
		p.newline()
		field1288 := unwrapped_fields1286[1].(*pb.RelationId)
		p.pretty_relation_id(field1288)
		p.newline()
		field1289 := unwrapped_fields1286[2].([]interface{})
		p.pretty_abstraction_with_arity(field1289)
		field1290 := unwrapped_fields1286[3].([]*pb.Attribute)
		if field1290 != nil {
			p.newline()
			opt_val1291 := field1290
			p.pretty_attrs(opt_val1291)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1299 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1299 != nil {
		p.write(*flat1299)
		return nil
	} else {
		_dollar_dollar := msg
		fields1293 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1294 := fields1293
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1295 := unwrapped_fields1294[0].(*pb.RelationId)
		p.pretty_relation_id(field1295)
		p.newline()
		field1296 := unwrapped_fields1294[1].(*pb.Abstraction)
		p.pretty_abstraction(field1296)
		p.newline()
		field1297 := unwrapped_fields1294[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1297)
		p.newline()
		field1298 := unwrapped_fields1294[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1298)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1303 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1303 != nil {
		p.write(*flat1303)
		return nil
	} else {
		fields1300 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1300) == 0) {
			p.newline()
			for i1302, elem1301 := range fields1300 {
				if (i1302 > 0) {
					p.newline()
				}
				p.pretty_var(elem1301)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1307 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1307 != nil {
		p.write(*flat1307)
		return nil
	} else {
		fields1304 := msg
		p.write("(")
		p.write("values")
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

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1316 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1316 != nil {
		p.write(*flat1316)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1646 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1646 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1314 := _t1646
		if deconstruct_result1314 != nil {
			unwrapped1315 := deconstruct_result1314
			p.pretty_edb(unwrapped1315)
		} else {
			_dollar_dollar := msg
			var _t1647 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1647 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1312 := _t1647
			if deconstruct_result1312 != nil {
				unwrapped1313 := deconstruct_result1312
				p.pretty_betree_relation(unwrapped1313)
			} else {
				_dollar_dollar := msg
				var _t1648 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1648 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1310 := _t1648
				if deconstruct_result1310 != nil {
					unwrapped1311 := deconstruct_result1310
					p.pretty_csv_data(unwrapped1311)
				} else {
					_dollar_dollar := msg
					var _t1649 *pb.IcebergData
					if hasProtoField(_dollar_dollar, "iceberg_data") {
						_t1649 = _dollar_dollar.GetIcebergData()
					}
					deconstruct_result1308 := _t1649
					if deconstruct_result1308 != nil {
						unwrapped1309 := deconstruct_result1308
						p.pretty_iceberg_data(unwrapped1309)
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
	flat1322 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1322 != nil {
		p.write(*flat1322)
		return nil
	} else {
		_dollar_dollar := msg
		fields1317 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1318 := fields1317
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1319 := unwrapped_fields1318[0].(*pb.RelationId)
		p.pretty_relation_id(field1319)
		p.newline()
		field1320 := unwrapped_fields1318[1].([]string)
		p.pretty_edb_path(field1320)
		p.newline()
		field1321 := unwrapped_fields1318[2].([]*pb.Type)
		p.pretty_edb_types(field1321)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1326 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1326 != nil {
		p.write(*flat1326)
		return nil
	} else {
		fields1323 := msg
		p.write("[")
		p.indent()
		for i1325, elem1324 := range fields1323 {
			if (i1325 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1324))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1330 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
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
			p.pretty_type(elem1328)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1335 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1335 != nil {
		p.write(*flat1335)
		return nil
	} else {
		_dollar_dollar := msg
		fields1331 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1332 := fields1331
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1333 := unwrapped_fields1332[0].(*pb.RelationId)
		p.pretty_relation_id(field1333)
		p.newline()
		field1334 := unwrapped_fields1332[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1334)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1341 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1341 != nil {
		p.write(*flat1341)
		return nil
	} else {
		_dollar_dollar := msg
		_t1650 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1336 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1650}
		unwrapped_fields1337 := fields1336
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1338 := unwrapped_fields1337[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1338)
		p.newline()
		field1339 := unwrapped_fields1337[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1339)
		p.newline()
		field1340 := unwrapped_fields1337[2].([][]interface{})
		p.pretty_config_dict(field1340)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1345 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1345 != nil {
		p.write(*flat1345)
		return nil
	} else {
		fields1342 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1342) == 0) {
			p.newline()
			for i1344, elem1343 := range fields1342 {
				if (i1344 > 0) {
					p.newline()
				}
				p.pretty_type(elem1343)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1349 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1349 != nil {
		p.write(*flat1349)
		return nil
	} else {
		fields1346 := msg
		p.write("(")
		p.write("value_types")
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

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1356 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1356 != nil {
		p.write(*flat1356)
		return nil
	} else {
		_dollar_dollar := msg
		fields1350 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1351 := fields1350
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1352 := unwrapped_fields1351[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1352)
		p.newline()
		field1353 := unwrapped_fields1351[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1353)
		p.newline()
		field1354 := unwrapped_fields1351[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1354)
		p.newline()
		field1355 := unwrapped_fields1351[3].(string)
		p.pretty_csv_asof(field1355)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1363 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1363 != nil {
		p.write(*flat1363)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1651 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1651 = _dollar_dollar.GetPaths()
		}
		var _t1652 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1652 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1357 := []interface{}{_t1651, _t1652}
		unwrapped_fields1358 := fields1357
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1359 := unwrapped_fields1358[0].([]string)
		if field1359 != nil {
			p.newline()
			opt_val1360 := field1359
			p.pretty_csv_locator_paths(opt_val1360)
		}
		field1361 := unwrapped_fields1358[1].(*string)
		if field1361 != nil {
			p.newline()
			opt_val1362 := *field1361
			p.pretty_csv_locator_inline_data(opt_val1362)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1367 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1367 != nil {
		p.write(*flat1367)
		return nil
	} else {
		fields1364 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1364) == 0) {
			p.newline()
			for i1366, elem1365 := range fields1364 {
				if (i1366 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1365))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1369 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1369 != nil {
		p.write(*flat1369)
		return nil
	} else {
		fields1368 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1368))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1372 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1372 != nil {
		p.write(*flat1372)
		return nil
	} else {
		_dollar_dollar := msg
		_t1653 := p.deconstruct_csv_config(_dollar_dollar)
		fields1370 := _t1653
		unwrapped_fields1371 := fields1370
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1371)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1376 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1376 != nil {
		p.write(*flat1376)
		return nil
	} else {
		fields1373 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1373) == 0) {
			p.newline()
			for i1375, elem1374 := range fields1373 {
				if (i1375 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1374)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1385 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1385 != nil {
		p.write(*flat1385)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1654 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1654 = _dollar_dollar.GetTargetId()
		}
		fields1377 := []interface{}{_dollar_dollar.GetColumnPath(), _t1654, _dollar_dollar.GetTypes()}
		unwrapped_fields1378 := fields1377
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1379 := unwrapped_fields1378[0].([]string)
		p.pretty_gnf_column_path(field1379)
		field1380 := unwrapped_fields1378[1].(*pb.RelationId)
		if field1380 != nil {
			p.newline()
			opt_val1381 := field1380
			p.pretty_relation_id(opt_val1381)
		}
		p.newline()
		p.write("[")
		field1382 := unwrapped_fields1378[2].([]*pb.Type)
		for i1384, elem1383 := range field1382 {
			if (i1384 > 0) {
				p.newline()
			}
			p.pretty_type(elem1383)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1392 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1392 != nil {
		p.write(*flat1392)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1655 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1655 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1390 := _t1655
		if deconstruct_result1390 != nil {
			unwrapped1391 := *deconstruct_result1390
			p.write(p.formatStringValue(unwrapped1391))
		} else {
			_dollar_dollar := msg
			var _t1656 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1656 = _dollar_dollar
			}
			deconstruct_result1386 := _t1656
			if deconstruct_result1386 != nil {
				unwrapped1387 := deconstruct_result1386
				p.write("[")
				p.indent()
				for i1389, elem1388 := range unwrapped1387 {
					if (i1389 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1388))
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
	flat1394 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1394 != nil {
		p.write(*flat1394)
		return nil
	} else {
		fields1393 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1393))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_data(msg *pb.IcebergData) interface{} {
	flat1402 := p.tryFlat(msg, func() { p.pretty_iceberg_data(msg) })
	if flat1402 != nil {
		p.write(*flat1402)
		return nil
	} else {
		_dollar_dollar := msg
		_t1657 := p.deconstruct_iceberg_data_to_snapshot_optional(_dollar_dollar)
		fields1395 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1657}
		unwrapped_fields1396 := fields1395
		p.write("(")
		p.write("iceberg_data")
		p.indentSexp()
		p.newline()
		field1397 := unwrapped_fields1396[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1397)
		p.newline()
		field1398 := unwrapped_fields1396[1].(*pb.IcebergConfig)
		p.pretty_iceberg_config(field1398)
		p.newline()
		field1399 := unwrapped_fields1396[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1399)
		field1400 := unwrapped_fields1396[3].(*string)
		if field1400 != nil {
			p.newline()
			opt_val1401 := *field1400
			p.pretty_iceberg_to_snapshot(opt_val1401)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_locator(msg *pb.IcebergLocator) interface{} {
	flat1410 := p.tryFlat(msg, func() { p.pretty_iceberg_locator(msg) })
	if flat1410 != nil {
		p.write(*flat1410)
		return nil
	} else {
		_dollar_dollar := msg
		fields1403 := []interface{}{_dollar_dollar.GetTableName(), _dollar_dollar.GetNamespace(), _dollar_dollar.GetWarehouse()}
		unwrapped_fields1404 := fields1403
		p.write("(")
		p.write("iceberg_locator")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("table_name")
		p.newline()
		field1405 := unwrapped_fields1404[0].(string)
		p.write(p.formatStringValue(field1405))
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("namespace")
		field1406 := unwrapped_fields1404[1].([]string)
		if !(len(field1406) == 0) {
			p.newline()
			for i1408, elem1407 := range field1406 {
				if (i1408 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1407))
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("warehouse")
		p.newline()
		field1409 := unwrapped_fields1404[2].(string)
		p.write(p.formatStringValue(field1409))
		p.dedent()
		p.write(")")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_config(msg *pb.IcebergConfig) interface{} {
	flat1422 := p.tryFlat(msg, func() { p.pretty_iceberg_config(msg) })
	if flat1422 != nil {
		p.write(*flat1422)
		return nil
	} else {
		_dollar_dollar := msg
		_t1658 := p.deconstruct_iceberg_config_scope_optional(_dollar_dollar)
		fields1411 := []interface{}{_dollar_dollar.GetCatalogUri(), _t1658, dictToPairs(_dollar_dollar.GetProperties()), dictToPairs(_dollar_dollar.GetAuthProperties())}
		unwrapped_fields1412 := fields1411
		p.write("(")
		p.write("iceberg_config")
		p.indentSexp()
		p.newline()
		p.write("(")
		p.newline()
		p.write("catalog_uri")
		p.newline()
		field1413 := unwrapped_fields1412[0].(string)
		p.write(p.formatStringValue(field1413))
		p.dedent()
		p.write(")")
		field1414 := unwrapped_fields1412[1].(*string)
		if field1414 != nil {
			p.newline()
			opt_val1415 := *field1414
			p.pretty_iceberg_config_scope(opt_val1415)
		}
		p.newline()
		p.write("(")
		p.newline()
		p.write("properties")
		field1416 := unwrapped_fields1412[2].([][]interface{})
		if !(len(field1416) == 0) {
			p.newline()
			for i1418, elem1417 := range field1416 {
				if (i1418 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1417)
			}
		}
		p.dedent()
		p.write(")")
		p.newline()
		p.write("(")
		p.newline()
		p.write("auth_properties")
		field1419 := unwrapped_fields1412[3].([][]interface{})
		if !(len(field1419) == 0) {
			p.newline()
			for i1421, elem1420 := range field1419 {
				if (i1421 > 0) {
					p.newline()
				}
				p.pretty_iceberg_property_entry(elem1420)
			}
		}
		p.dedent()
		p.write(")")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_config_scope(msg string) interface{} {
	flat1424 := p.tryFlat(msg, func() { p.pretty_iceberg_config_scope(msg) })
	if flat1424 != nil {
		p.write(*flat1424)
		return nil
	} else {
		fields1423 := msg
		p.write("(")
		p.write("scope")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1423))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_property_entry(msg []interface{}) interface{} {
	flat1429 := p.tryFlat(msg, func() { p.pretty_iceberg_property_entry(msg) })
	if flat1429 != nil {
		p.write(*flat1429)
		return nil
	} else {
		_dollar_dollar := msg
		fields1425 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(string)}
		unwrapped_fields1426 := fields1425
		p.write("(")
		p.write("prop")
		p.indentSexp()
		p.newline()
		field1427 := unwrapped_fields1426[0].(string)
		p.write(p.formatStringValue(field1427))
		p.newline()
		field1428 := unwrapped_fields1426[1].(string)
		p.write(p.formatStringValue(field1428))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_to_snapshot(msg string) interface{} {
	flat1431 := p.tryFlat(msg, func() { p.pretty_iceberg_to_snapshot(msg) })
	if flat1431 != nil {
		p.write(*flat1431)
		return nil
	} else {
		fields1430 := msg
		p.write("(")
		p.write("to_snapshot")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1430))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1434 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1434 != nil {
		p.write(*flat1434)
		return nil
	} else {
		_dollar_dollar := msg
		fields1432 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1433 := fields1432
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1433)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1439 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1439 != nil {
		p.write(*flat1439)
		return nil
	} else {
		_dollar_dollar := msg
		fields1435 := _dollar_dollar.GetRelations()
		unwrapped_fields1436 := fields1435
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1436) == 0) {
			p.newline()
			for i1438, elem1437 := range unwrapped_fields1436 {
				if (i1438 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1437)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1444 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1444 != nil {
		p.write(*flat1444)
		return nil
	} else {
		_dollar_dollar := msg
		fields1440 := _dollar_dollar.GetMappings()
		unwrapped_fields1441 := fields1440
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1441) == 0) {
			p.newline()
			for i1443, elem1442 := range unwrapped_fields1441 {
				if (i1443 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1442)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1449 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1449 != nil {
		p.write(*flat1449)
		return nil
	} else {
		_dollar_dollar := msg
		fields1445 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1446 := fields1445
		field1447 := unwrapped_fields1446[0].([]string)
		p.pretty_edb_path(field1447)
		p.write(" ")
		field1448 := unwrapped_fields1446[1].(*pb.RelationId)
		p.pretty_relation_id(field1448)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1453 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1453 != nil {
		p.write(*flat1453)
		return nil
	} else {
		fields1450 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1450) == 0) {
			p.newline()
			for i1452, elem1451 := range fields1450 {
				if (i1452 > 0) {
					p.newline()
				}
				p.pretty_read(elem1451)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1464 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1464 != nil {
		p.write(*flat1464)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1659 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1659 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1462 := _t1659
		if deconstruct_result1462 != nil {
			unwrapped1463 := deconstruct_result1462
			p.pretty_demand(unwrapped1463)
		} else {
			_dollar_dollar := msg
			var _t1660 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1660 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1460 := _t1660
			if deconstruct_result1460 != nil {
				unwrapped1461 := deconstruct_result1460
				p.pretty_output(unwrapped1461)
			} else {
				_dollar_dollar := msg
				var _t1661 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1661 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1458 := _t1661
				if deconstruct_result1458 != nil {
					unwrapped1459 := deconstruct_result1458
					p.pretty_what_if(unwrapped1459)
				} else {
					_dollar_dollar := msg
					var _t1662 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1662 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1456 := _t1662
					if deconstruct_result1456 != nil {
						unwrapped1457 := deconstruct_result1456
						p.pretty_abort(unwrapped1457)
					} else {
						_dollar_dollar := msg
						var _t1663 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1663 = _dollar_dollar.GetExport()
						}
						deconstruct_result1454 := _t1663
						if deconstruct_result1454 != nil {
							unwrapped1455 := deconstruct_result1454
							p.pretty_export(unwrapped1455)
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
	flat1467 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1467 != nil {
		p.write(*flat1467)
		return nil
	} else {
		_dollar_dollar := msg
		fields1465 := _dollar_dollar.GetRelationId()
		unwrapped_fields1466 := fields1465
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1466)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1472 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1472 != nil {
		p.write(*flat1472)
		return nil
	} else {
		_dollar_dollar := msg
		fields1468 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1469 := fields1468
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1470 := unwrapped_fields1469[0].(string)
		p.pretty_name(field1470)
		p.newline()
		field1471 := unwrapped_fields1469[1].(*pb.RelationId)
		p.pretty_relation_id(field1471)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1477 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1477 != nil {
		p.write(*flat1477)
		return nil
	} else {
		_dollar_dollar := msg
		fields1473 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1474 := fields1473
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1475 := unwrapped_fields1474[0].(string)
		p.pretty_name(field1475)
		p.newline()
		field1476 := unwrapped_fields1474[1].(*pb.Epoch)
		p.pretty_epoch(field1476)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1483 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1483 != nil {
		p.write(*flat1483)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1664 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1664 = ptr(_dollar_dollar.GetName())
		}
		fields1478 := []interface{}{_t1664, _dollar_dollar.GetRelationId()}
		unwrapped_fields1479 := fields1478
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1480 := unwrapped_fields1479[0].(*string)
		if field1480 != nil {
			p.newline()
			opt_val1481 := *field1480
			p.pretty_name(opt_val1481)
		}
		p.newline()
		field1482 := unwrapped_fields1479[1].(*pb.RelationId)
		p.pretty_relation_id(field1482)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1488 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1488 != nil {
		p.write(*flat1488)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1665 *pb.ExportCSVConfig
		if hasProtoField(_dollar_dollar, "csv_config") {
			_t1665 = _dollar_dollar.GetCsvConfig()
		}
		deconstruct_result1486 := _t1665
		if deconstruct_result1486 != nil {
			unwrapped1487 := deconstruct_result1486
			p.write("(")
			p.write("export")
			p.indentSexp()
			p.newline()
			p.pretty_export_csv_config(unwrapped1487)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1666 *pb.ExportIcebergConfig
			if hasProtoField(_dollar_dollar, "iceberg_config") {
				_t1666 = _dollar_dollar.GetIcebergConfig()
			}
			deconstruct_result1484 := _t1666
			if deconstruct_result1484 != nil {
				unwrapped1485 := deconstruct_result1484
				p.write("(")
				p.write("export_iceberg")
				p.indentSexp()
				p.newline()
				p.pretty_export_iceberg_config(unwrapped1485)
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
	flat1499 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1499 != nil {
		p.write(*flat1499)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1667 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1667 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1494 := _t1667
		if deconstruct_result1494 != nil {
			unwrapped1495 := deconstruct_result1494
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1496 := unwrapped1495[0].(string)
			p.pretty_export_csv_path(field1496)
			p.newline()
			field1497 := unwrapped1495[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1497)
			p.newline()
			field1498 := unwrapped1495[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1498)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1668 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1669 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1668 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1669}
			}
			deconstruct_result1489 := _t1668
			if deconstruct_result1489 != nil {
				unwrapped1490 := deconstruct_result1489
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1491 := unwrapped1490[0].(string)
				p.pretty_export_csv_path(field1491)
				p.newline()
				field1492 := unwrapped1490[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1492)
				p.newline()
				field1493 := unwrapped1490[2].([][]interface{})
				p.pretty_config_dict(field1493)
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
	flat1501 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1501 != nil {
		p.write(*flat1501)
		return nil
	} else {
		fields1500 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1500))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1508 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1508 != nil {
		p.write(*flat1508)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1670 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1670 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1504 := _t1670
		if deconstruct_result1504 != nil {
			unwrapped1505 := deconstruct_result1504
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1505) == 0) {
				p.newline()
				for i1507, elem1506 := range unwrapped1505 {
					if (i1507 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1506)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1671 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1671 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1502 := _t1671
			if deconstruct_result1502 != nil {
				unwrapped1503 := deconstruct_result1502
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1503)
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
	flat1513 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1513 != nil {
		p.write(*flat1513)
		return nil
	} else {
		_dollar_dollar := msg
		fields1509 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1510 := fields1509
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1511 := unwrapped_fields1510[0].(string)
		p.write(p.formatStringValue(field1511))
		p.newline()
		field1512 := unwrapped_fields1510[1].(*pb.RelationId)
		p.pretty_relation_id(field1512)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1517 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1517 != nil {
		p.write(*flat1517)
		return nil
	} else {
		fields1514 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1514) == 0) {
			p.newline()
			for i1516, elem1515 := range fields1514 {
				if (i1516 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1515)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_iceberg_config(msg *pb.ExportIcebergConfig) interface{} {
	flat1527 := p.tryFlat(msg, func() { p.pretty_export_iceberg_config(msg) })
	if flat1527 != nil {
		p.write(*flat1527)
		return nil
	} else {
		_dollar_dollar := msg
		_t1672 := p.deconstruct_export_iceberg_config_optional(_dollar_dollar)
		fields1518 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _t1672}
		unwrapped_fields1519 := fields1518
		p.write("(")
		p.write("export_iceberg_config")
		p.indentSexp()
		p.newline()
		field1520 := unwrapped_fields1519[0].(*pb.IcebergLocator)
		p.pretty_iceberg_locator(field1520)
		p.newline()
		field1521 := unwrapped_fields1519[1].(*pb.IcebergConfig)
		p.pretty_iceberg_config(field1521)
		p.newline()
		p.write("(")
		p.newline()
		p.write("columns")
		field1522 := unwrapped_fields1519[2].([]*pb.IcebergExportColumn)
		if !(len(field1522) == 0) {
			p.newline()
			for i1524, elem1523 := range field1522 {
				if (i1524 > 0) {
					p.newline()
				}
				p.pretty_iceberg_export_column(elem1523)
			}
		}
		p.dedent()
		p.write(")")
		field1525 := unwrapped_fields1519[3].([][]interface{})
		if field1525 != nil {
			p.newline()
			opt_val1526 := field1525
			p.pretty_config_dict(opt_val1526)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_iceberg_export_column(msg *pb.IcebergExportColumn) interface{} {
	flat1533 := p.tryFlat(msg, func() { p.pretty_iceberg_export_column(msg) })
	if flat1533 != nil {
		p.write(*flat1533)
		return nil
	} else {
		_dollar_dollar := msg
		fields1528 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetType(), _dollar_dollar.GetNullable()}
		unwrapped_fields1529 := fields1528
		p.write("(")
		p.write("iceberg_column")
		p.indentSexp()
		p.newline()
		field1530 := unwrapped_fields1529[0].(string)
		p.write(p.formatStringValue(field1530))
		p.newline()
		field1531 := unwrapped_fields1529[1].(*pb.Type)
		p.pretty_type(field1531)
		p.newline()
		field1532 := unwrapped_fields1529[2].(bool)
		p.pretty_boolean_value(field1532)
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
		_t1717 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1717)
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
	case *pb.IcebergConfig:
		p.pretty_iceberg_config(m)
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
	case *pb.IcebergExportColumn:
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
