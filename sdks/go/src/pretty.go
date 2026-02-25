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
	"reflect"
	"sort"
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

func formatBool(b bool) string {
	if b {
		return "true"
	}
	return "false"
}

// --- Helper functions ---

func (p *PrettyPrinter) _make_value_int32(v int32) *pb.Value {
	_t1698 := &pb.Value{}
	_t1698.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t1698
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1699 := &pb.Value{}
	_t1699.Value = &pb.Value_IntValue{IntValue: v}
	return _t1699
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1700 := &pb.Value{}
	_t1700.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1700
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1701 := &pb.Value{}
	_t1701.Value = &pb.Value_StringValue{StringValue: v}
	return _t1701
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1702 := &pb.Value{}
	_t1702.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1702
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1703 := &pb.Value{}
	_t1703.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1703
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1704 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1704})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1705 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1705})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1706 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1706})
			}
		}
	}
	_t1707 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1707})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1708 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1708})
	_t1709 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1709})
	if msg.GetNewLine() != "" {
		_t1710 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1710})
	}
	_t1711 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1711})
	_t1712 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1712})
	_t1713 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1713})
	if msg.GetComment() != "" {
		_t1714 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1714})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1715 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1715})
	}
	_t1716 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1716})
	_t1717 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1717})
	_t1718 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1718})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1719 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1719})
	_t1720 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1720})
	_t1721 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1721})
	_t1722 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1722})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1723 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1723})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1724 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1724})
		}
	}
	_t1725 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1725})
	_t1726 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1726})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1727 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1727})
	}
	if msg.Compression != nil {
		_t1728 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1728})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1729 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1729})
	}
	if msg.SyntaxMissingString != nil {
		_t1730 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1730})
	}
	if msg.SyntaxDelim != nil {
		_t1731 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1731})
	}
	if msg.SyntaxQuotechar != nil {
		_t1732 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1732})
	}
	if msg.SyntaxEscapechar != nil {
		_t1733 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1733})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_column_tail(col *pb.CSVColumn) []interface{} {
	var _t1734 interface{}
	if (hasProtoField(col, "target_id") || !(len(col.GetTypes()) == 0)) {
		return []interface{}{col.GetTargetId(), col.GetTypes()}
	}
	_ = _t1734
	return nil
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1735 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1735
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
	flat654 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat654 != nil {
		p.write(*flat654)
		return nil
	} else {
		_t1290 := func(_dollar_dollar *pb.Transaction) []interface{} {
			var _t1291 *pb.Configure
			if hasProtoField(_dollar_dollar, "configure") {
				_t1291 = _dollar_dollar.GetConfigure()
			}
			var _t1292 *pb.Sync
			if hasProtoField(_dollar_dollar, "sync") {
				_t1292 = _dollar_dollar.GetSync()
			}
			return []interface{}{_t1291, _t1292, _dollar_dollar.GetEpochs()}
		}
		_t1293 := _t1290(msg)
		fields645 := _t1293
		unwrapped_fields646 := fields645
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field647 := unwrapped_fields646[0].(*pb.Configure)
		if field647 != nil {
			p.newline()
			opt_val648 := field647
			p.pretty_configure(opt_val648)
		}
		field649 := unwrapped_fields646[1].(*pb.Sync)
		if field649 != nil {
			p.newline()
			opt_val650 := field649
			p.pretty_sync(opt_val650)
		}
		field651 := unwrapped_fields646[2].([]*pb.Epoch)
		if !(len(field651) == 0) {
			p.newline()
			for i653, elem652 := range field651 {
				if (i653 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem652)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat657 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat657 != nil {
		p.write(*flat657)
		return nil
	} else {
		_t1294 := func(_dollar_dollar *pb.Configure) [][]interface{} {
			_t1295 := p.deconstruct_configure(_dollar_dollar)
			return _t1295
		}
		_t1296 := _t1294(msg)
		fields655 := _t1296
		unwrapped_fields656 := fields655
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields656)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat661 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat661 != nil {
		p.write(*flat661)
		return nil
	} else {
		fields658 := msg
		p.write("{")
		p.indent()
		if !(len(fields658) == 0) {
			p.newline()
			for i660, elem659 := range fields658 {
				if (i660 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem659)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat666 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat666 != nil {
		p.write(*flat666)
		return nil
	} else {
		_t1297 := func(_dollar_dollar []interface{}) []interface{} {
			return []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		}
		_t1298 := _t1297(msg)
		fields662 := _t1298
		unwrapped_fields663 := fields662
		p.write(":")
		field664 := unwrapped_fields663[0].(string)
		p.write(field664)
		p.write(" ")
		field665 := unwrapped_fields663[1].(*pb.Value)
		p.pretty_value(field665)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat686 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat686 != nil {
		p.write(*flat686)
		return nil
	} else {
		_t1299 := func(_dollar_dollar *pb.Value) *pb.DateValue {
			var _t1300 *pb.DateValue
			if hasProtoField(_dollar_dollar, "date_value") {
				_t1300 = _dollar_dollar.GetDateValue()
			}
			return _t1300
		}
		_t1301 := _t1299(msg)
		deconstruct_result684 := _t1301
		if deconstruct_result684 != nil {
			unwrapped685 := deconstruct_result684
			p.pretty_date(unwrapped685)
		} else {
			_t1302 := func(_dollar_dollar *pb.Value) *pb.DateTimeValue {
				var _t1303 *pb.DateTimeValue
				if hasProtoField(_dollar_dollar, "datetime_value") {
					_t1303 = _dollar_dollar.GetDatetimeValue()
				}
				return _t1303
			}
			_t1304 := _t1302(msg)
			deconstruct_result682 := _t1304
			if deconstruct_result682 != nil {
				unwrapped683 := deconstruct_result682
				p.pretty_datetime(unwrapped683)
			} else {
				_t1305 := func(_dollar_dollar *pb.Value) *string {
					var _t1306 *string
					if hasProtoField(_dollar_dollar, "string_value") {
						_t1306 = ptr(_dollar_dollar.GetStringValue())
					}
					return _t1306
				}
				_t1307 := _t1305(msg)
				deconstruct_result680 := _t1307
				if deconstruct_result680 != nil {
					unwrapped681 := *deconstruct_result680
					p.write(p.formatStringValue(unwrapped681))
				} else {
					_t1308 := func(_dollar_dollar *pb.Value) *int64 {
						var _t1309 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1309 = ptr(_dollar_dollar.GetIntValue())
						}
						return _t1309
					}
					_t1310 := _t1308(msg)
					deconstruct_result678 := _t1310
					if deconstruct_result678 != nil {
						unwrapped679 := *deconstruct_result678
						p.write(fmt.Sprintf("%d", unwrapped679))
					} else {
						_t1311 := func(_dollar_dollar *pb.Value) *float64 {
							var _t1312 *float64
							if hasProtoField(_dollar_dollar, "float_value") {
								_t1312 = ptr(_dollar_dollar.GetFloatValue())
							}
							return _t1312
						}
						_t1313 := _t1311(msg)
						deconstruct_result676 := _t1313
						if deconstruct_result676 != nil {
							unwrapped677 := *deconstruct_result676
							p.write(formatFloat64(unwrapped677))
						} else {
							_t1314 := func(_dollar_dollar *pb.Value) *pb.UInt128Value {
								var _t1315 *pb.UInt128Value
								if hasProtoField(_dollar_dollar, "uint128_value") {
									_t1315 = _dollar_dollar.GetUint128Value()
								}
								return _t1315
							}
							_t1316 := _t1314(msg)
							deconstruct_result674 := _t1316
							if deconstruct_result674 != nil {
								unwrapped675 := deconstruct_result674
								p.write(p.formatUint128(unwrapped675))
							} else {
								_t1317 := func(_dollar_dollar *pb.Value) *pb.Int128Value {
									var _t1318 *pb.Int128Value
									if hasProtoField(_dollar_dollar, "int128_value") {
										_t1318 = _dollar_dollar.GetInt128Value()
									}
									return _t1318
								}
								_t1319 := _t1317(msg)
								deconstruct_result672 := _t1319
								if deconstruct_result672 != nil {
									unwrapped673 := deconstruct_result672
									p.write(p.formatInt128(unwrapped673))
								} else {
									_t1320 := func(_dollar_dollar *pb.Value) *pb.DecimalValue {
										var _t1321 *pb.DecimalValue
										if hasProtoField(_dollar_dollar, "decimal_value") {
											_t1321 = _dollar_dollar.GetDecimalValue()
										}
										return _t1321
									}
									_t1322 := _t1320(msg)
									deconstruct_result670 := _t1322
									if deconstruct_result670 != nil {
										unwrapped671 := deconstruct_result670
										p.write(p.formatDecimal(unwrapped671))
									} else {
										_t1323 := func(_dollar_dollar *pb.Value) *bool {
											var _t1324 *bool
											if hasProtoField(_dollar_dollar, "boolean_value") {
												_t1324 = ptr(_dollar_dollar.GetBooleanValue())
											}
											return _t1324
										}
										_t1325 := _t1323(msg)
										deconstruct_result668 := _t1325
										if deconstruct_result668 != nil {
											unwrapped669 := *deconstruct_result668
											p.pretty_boolean_value(unwrapped669)
										} else {
											fields667 := msg
											_ = fields667
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
	return nil
}

func (p *PrettyPrinter) pretty_date(msg *pb.DateValue) interface{} {
	flat692 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat692 != nil {
		p.write(*flat692)
		return nil
	} else {
		_t1326 := func(_dollar_dollar *pb.DateValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		}
		_t1327 := _t1326(msg)
		fields687 := _t1327
		unwrapped_fields688 := fields687
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field689 := unwrapped_fields688[0].(int64)
		p.write(fmt.Sprintf("%d", field689))
		p.newline()
		field690 := unwrapped_fields688[1].(int64)
		p.write(fmt.Sprintf("%d", field690))
		p.newline()
		field691 := unwrapped_fields688[2].(int64)
		p.write(fmt.Sprintf("%d", field691))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat703 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat703 != nil {
		p.write(*flat703)
		return nil
	} else {
		_t1328 := func(_dollar_dollar *pb.DateTimeValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		}
		_t1329 := _t1328(msg)
		fields693 := _t1329
		unwrapped_fields694 := fields693
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field695 := unwrapped_fields694[0].(int64)
		p.write(fmt.Sprintf("%d", field695))
		p.newline()
		field696 := unwrapped_fields694[1].(int64)
		p.write(fmt.Sprintf("%d", field696))
		p.newline()
		field697 := unwrapped_fields694[2].(int64)
		p.write(fmt.Sprintf("%d", field697))
		p.newline()
		field698 := unwrapped_fields694[3].(int64)
		p.write(fmt.Sprintf("%d", field698))
		p.newline()
		field699 := unwrapped_fields694[4].(int64)
		p.write(fmt.Sprintf("%d", field699))
		p.newline()
		field700 := unwrapped_fields694[5].(int64)
		p.write(fmt.Sprintf("%d", field700))
		field701 := unwrapped_fields694[6].(*int64)
		if field701 != nil {
			p.newline()
			opt_val702 := *field701
			p.write(fmt.Sprintf("%d", opt_val702))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_t1330 := func(_dollar_dollar bool) []interface{} {
		var _t1331 []interface{}
		if _dollar_dollar {
			_t1331 = []interface{}{}
		}
		return _t1331
	}
	_t1332 := _t1330(msg)
	deconstruct_result706 := _t1332
	if deconstruct_result706 != nil {
		unwrapped707 := deconstruct_result706
		_ = unwrapped707
		p.write("true")
	} else {
		_t1333 := func(_dollar_dollar bool) []interface{} {
			var _t1334 []interface{}
			if !(_dollar_dollar) {
				_t1334 = []interface{}{}
			}
			return _t1334
		}
		_t1335 := _t1333(msg)
		deconstruct_result704 := _t1335
		if deconstruct_result704 != nil {
			unwrapped705 := deconstruct_result704
			_ = unwrapped705
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat712 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat712 != nil {
		p.write(*flat712)
		return nil
	} else {
		_t1336 := func(_dollar_dollar *pb.Sync) []*pb.FragmentId {
			return _dollar_dollar.GetFragments()
		}
		_t1337 := _t1336(msg)
		fields708 := _t1337
		unwrapped_fields709 := fields708
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields709) == 0) {
			p.newline()
			for i711, elem710 := range unwrapped_fields709 {
				if (i711 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem710)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat715 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat715 != nil {
		p.write(*flat715)
		return nil
	} else {
		_t1338 := func(_dollar_dollar *pb.FragmentId) string {
			return p.fragmentIdToString(_dollar_dollar)
		}
		_t1339 := _t1338(msg)
		fields713 := _t1339
		unwrapped_fields714 := fields713
		p.write(":")
		p.write(unwrapped_fields714)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat722 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat722 != nil {
		p.write(*flat722)
		return nil
	} else {
		_t1340 := func(_dollar_dollar *pb.Epoch) []interface{} {
			var _t1341 []*pb.Write
			if !(len(_dollar_dollar.GetWrites()) == 0) {
				_t1341 = _dollar_dollar.GetWrites()
			}
			var _t1342 []*pb.Read
			if !(len(_dollar_dollar.GetReads()) == 0) {
				_t1342 = _dollar_dollar.GetReads()
			}
			return []interface{}{_t1341, _t1342}
		}
		_t1343 := _t1340(msg)
		fields716 := _t1343
		unwrapped_fields717 := fields716
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field718 := unwrapped_fields717[0].([]*pb.Write)
		if field718 != nil {
			p.newline()
			opt_val719 := field718
			p.pretty_epoch_writes(opt_val719)
		}
		field720 := unwrapped_fields717[1].([]*pb.Read)
		if field720 != nil {
			p.newline()
			opt_val721 := field720
			p.pretty_epoch_reads(opt_val721)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat726 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat726 != nil {
		p.write(*flat726)
		return nil
	} else {
		fields723 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields723) == 0) {
			p.newline()
			for i725, elem724 := range fields723 {
				if (i725 > 0) {
					p.newline()
				}
				p.pretty_write(elem724)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat735 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat735 != nil {
		p.write(*flat735)
		return nil
	} else {
		_t1344 := func(_dollar_dollar *pb.Write) *pb.Define {
			var _t1345 *pb.Define
			if hasProtoField(_dollar_dollar, "define") {
				_t1345 = _dollar_dollar.GetDefine()
			}
			return _t1345
		}
		_t1346 := _t1344(msg)
		deconstruct_result733 := _t1346
		if deconstruct_result733 != nil {
			unwrapped734 := deconstruct_result733
			p.pretty_define(unwrapped734)
		} else {
			_t1347 := func(_dollar_dollar *pb.Write) *pb.Undefine {
				var _t1348 *pb.Undefine
				if hasProtoField(_dollar_dollar, "undefine") {
					_t1348 = _dollar_dollar.GetUndefine()
				}
				return _t1348
			}
			_t1349 := _t1347(msg)
			deconstruct_result731 := _t1349
			if deconstruct_result731 != nil {
				unwrapped732 := deconstruct_result731
				p.pretty_undefine(unwrapped732)
			} else {
				_t1350 := func(_dollar_dollar *pb.Write) *pb.Context {
					var _t1351 *pb.Context
					if hasProtoField(_dollar_dollar, "context") {
						_t1351 = _dollar_dollar.GetContext()
					}
					return _t1351
				}
				_t1352 := _t1350(msg)
				deconstruct_result729 := _t1352
				if deconstruct_result729 != nil {
					unwrapped730 := deconstruct_result729
					p.pretty_context(unwrapped730)
				} else {
					_t1353 := func(_dollar_dollar *pb.Write) *pb.Snapshot {
						var _t1354 *pb.Snapshot
						if hasProtoField(_dollar_dollar, "snapshot") {
							_t1354 = _dollar_dollar.GetSnapshot()
						}
						return _t1354
					}
					_t1355 := _t1353(msg)
					deconstruct_result727 := _t1355
					if deconstruct_result727 != nil {
						unwrapped728 := deconstruct_result727
						p.pretty_snapshot(unwrapped728)
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
	flat738 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat738 != nil {
		p.write(*flat738)
		return nil
	} else {
		_t1356 := func(_dollar_dollar *pb.Define) *pb.Fragment {
			return _dollar_dollar.GetFragment()
		}
		_t1357 := _t1356(msg)
		fields736 := _t1357
		unwrapped_fields737 := fields736
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields737)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat745 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat745 != nil {
		p.write(*flat745)
		return nil
	} else {
		_t1358 := func(_dollar_dollar *pb.Fragment) []interface{} {
			p.startPrettyFragment(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		}
		_t1359 := _t1358(msg)
		fields739 := _t1359
		unwrapped_fields740 := fields739
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field741 := unwrapped_fields740[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field741)
		field742 := unwrapped_fields740[1].([]*pb.Declaration)
		if !(len(field742) == 0) {
			p.newline()
			for i744, elem743 := range field742 {
				if (i744 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem743)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat747 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat747 != nil {
		p.write(*flat747)
		return nil
	} else {
		fields746 := msg
		p.pretty_fragment_id(fields746)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat756 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat756 != nil {
		p.write(*flat756)
		return nil
	} else {
		_t1360 := func(_dollar_dollar *pb.Declaration) *pb.Def {
			var _t1361 *pb.Def
			if hasProtoField(_dollar_dollar, "def") {
				_t1361 = _dollar_dollar.GetDef()
			}
			return _t1361
		}
		_t1362 := _t1360(msg)
		deconstruct_result754 := _t1362
		if deconstruct_result754 != nil {
			unwrapped755 := deconstruct_result754
			p.pretty_def(unwrapped755)
		} else {
			_t1363 := func(_dollar_dollar *pb.Declaration) *pb.Algorithm {
				var _t1364 *pb.Algorithm
				if hasProtoField(_dollar_dollar, "algorithm") {
					_t1364 = _dollar_dollar.GetAlgorithm()
				}
				return _t1364
			}
			_t1365 := _t1363(msg)
			deconstruct_result752 := _t1365
			if deconstruct_result752 != nil {
				unwrapped753 := deconstruct_result752
				p.pretty_algorithm(unwrapped753)
			} else {
				_t1366 := func(_dollar_dollar *pb.Declaration) *pb.Constraint {
					var _t1367 *pb.Constraint
					if hasProtoField(_dollar_dollar, "constraint") {
						_t1367 = _dollar_dollar.GetConstraint()
					}
					return _t1367
				}
				_t1368 := _t1366(msg)
				deconstruct_result750 := _t1368
				if deconstruct_result750 != nil {
					unwrapped751 := deconstruct_result750
					p.pretty_constraint(unwrapped751)
				} else {
					_t1369 := func(_dollar_dollar *pb.Declaration) *pb.Data {
						var _t1370 *pb.Data
						if hasProtoField(_dollar_dollar, "data") {
							_t1370 = _dollar_dollar.GetData()
						}
						return _t1370
					}
					_t1371 := _t1369(msg)
					deconstruct_result748 := _t1371
					if deconstruct_result748 != nil {
						unwrapped749 := deconstruct_result748
						p.pretty_data(unwrapped749)
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
	flat763 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat763 != nil {
		p.write(*flat763)
		return nil
	} else {
		_t1372 := func(_dollar_dollar *pb.Def) []interface{} {
			var _t1373 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1373 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1373}
		}
		_t1374 := _t1372(msg)
		fields757 := _t1374
		unwrapped_fields758 := fields757
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field759 := unwrapped_fields758[0].(*pb.RelationId)
		p.pretty_relation_id(field759)
		p.newline()
		field760 := unwrapped_fields758[1].(*pb.Abstraction)
		p.pretty_abstraction(field760)
		field761 := unwrapped_fields758[2].([]*pb.Attribute)
		if field761 != nil {
			p.newline()
			opt_val762 := field761
			p.pretty_attrs(opt_val762)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat768 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat768 != nil {
		p.write(*flat768)
		return nil
	} else {
		_t1375 := func(_dollar_dollar *pb.RelationId) *string {
			var _t1376 *string
			if p.relationIdToString(_dollar_dollar) != nil {
				_t1377 := p.deconstruct_relation_id_string(_dollar_dollar)
				_t1376 = ptr(_t1377)
			}
			return _t1376
		}
		_t1378 := _t1375(msg)
		deconstruct_result766 := _t1378
		if deconstruct_result766 != nil {
			unwrapped767 := *deconstruct_result766
			p.write(":")
			p.write(unwrapped767)
		} else {
			_t1379 := func(_dollar_dollar *pb.RelationId) *pb.UInt128Value {
				_t1380 := p.deconstruct_relation_id_uint128(_dollar_dollar)
				return _t1380
			}
			_t1381 := _t1379(msg)
			deconstruct_result764 := _t1381
			if deconstruct_result764 != nil {
				unwrapped765 := deconstruct_result764
				p.write(p.formatUint128(unwrapped765))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat773 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat773 != nil {
		p.write(*flat773)
		return nil
	} else {
		_t1382 := func(_dollar_dollar *pb.Abstraction) []interface{} {
			_t1383 := p.deconstruct_bindings(_dollar_dollar)
			return []interface{}{_t1383, _dollar_dollar.GetValue()}
		}
		_t1384 := _t1382(msg)
		fields769 := _t1384
		unwrapped_fields770 := fields769
		p.write("(")
		p.indent()
		field771 := unwrapped_fields770[0].([]interface{})
		p.pretty_bindings(field771)
		p.newline()
		field772 := unwrapped_fields770[1].(*pb.Formula)
		p.pretty_formula(field772)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat781 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat781 != nil {
		p.write(*flat781)
		return nil
	} else {
		_t1385 := func(_dollar_dollar []interface{}) []interface{} {
			var _t1386 []*pb.Binding
			if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
				_t1386 = _dollar_dollar[1].([]*pb.Binding)
			}
			return []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1386}
		}
		_t1387 := _t1385(msg)
		fields774 := _t1387
		unwrapped_fields775 := fields774
		p.write("[")
		p.indent()
		field776 := unwrapped_fields775[0].([]*pb.Binding)
		for i778, elem777 := range field776 {
			if (i778 > 0) {
				p.newline()
			}
			p.pretty_binding(elem777)
		}
		field779 := unwrapped_fields775[1].([]*pb.Binding)
		if field779 != nil {
			p.newline()
			opt_val780 := field779
			p.pretty_value_bindings(opt_val780)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat786 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat786 != nil {
		p.write(*flat786)
		return nil
	} else {
		_t1388 := func(_dollar_dollar *pb.Binding) []interface{} {
			return []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		}
		_t1389 := _t1388(msg)
		fields782 := _t1389
		unwrapped_fields783 := fields782
		field784 := unwrapped_fields783[0].(string)
		p.write(field784)
		p.write("::")
		field785 := unwrapped_fields783[1].(*pb.Type)
		p.pretty_type(field785)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat809 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat809 != nil {
		p.write(*flat809)
		return nil
	} else {
		_t1390 := func(_dollar_dollar *pb.Type) *pb.UnspecifiedType {
			var _t1391 *pb.UnspecifiedType
			if hasProtoField(_dollar_dollar, "unspecified_type") {
				_t1391 = _dollar_dollar.GetUnspecifiedType()
			}
			return _t1391
		}
		_t1392 := _t1390(msg)
		deconstruct_result807 := _t1392
		if deconstruct_result807 != nil {
			unwrapped808 := deconstruct_result807
			p.pretty_unspecified_type(unwrapped808)
		} else {
			_t1393 := func(_dollar_dollar *pb.Type) *pb.StringType {
				var _t1394 *pb.StringType
				if hasProtoField(_dollar_dollar, "string_type") {
					_t1394 = _dollar_dollar.GetStringType()
				}
				return _t1394
			}
			_t1395 := _t1393(msg)
			deconstruct_result805 := _t1395
			if deconstruct_result805 != nil {
				unwrapped806 := deconstruct_result805
				p.pretty_string_type(unwrapped806)
			} else {
				_t1396 := func(_dollar_dollar *pb.Type) *pb.IntType {
					var _t1397 *pb.IntType
					if hasProtoField(_dollar_dollar, "int_type") {
						_t1397 = _dollar_dollar.GetIntType()
					}
					return _t1397
				}
				_t1398 := _t1396(msg)
				deconstruct_result803 := _t1398
				if deconstruct_result803 != nil {
					unwrapped804 := deconstruct_result803
					p.pretty_int_type(unwrapped804)
				} else {
					_t1399 := func(_dollar_dollar *pb.Type) *pb.FloatType {
						var _t1400 *pb.FloatType
						if hasProtoField(_dollar_dollar, "float_type") {
							_t1400 = _dollar_dollar.GetFloatType()
						}
						return _t1400
					}
					_t1401 := _t1399(msg)
					deconstruct_result801 := _t1401
					if deconstruct_result801 != nil {
						unwrapped802 := deconstruct_result801
						p.pretty_float_type(unwrapped802)
					} else {
						_t1402 := func(_dollar_dollar *pb.Type) *pb.UInt128Type {
							var _t1403 *pb.UInt128Type
							if hasProtoField(_dollar_dollar, "uint128_type") {
								_t1403 = _dollar_dollar.GetUint128Type()
							}
							return _t1403
						}
						_t1404 := _t1402(msg)
						deconstruct_result799 := _t1404
						if deconstruct_result799 != nil {
							unwrapped800 := deconstruct_result799
							p.pretty_uint128_type(unwrapped800)
						} else {
							_t1405 := func(_dollar_dollar *pb.Type) *pb.Int128Type {
								var _t1406 *pb.Int128Type
								if hasProtoField(_dollar_dollar, "int128_type") {
									_t1406 = _dollar_dollar.GetInt128Type()
								}
								return _t1406
							}
							_t1407 := _t1405(msg)
							deconstruct_result797 := _t1407
							if deconstruct_result797 != nil {
								unwrapped798 := deconstruct_result797
								p.pretty_int128_type(unwrapped798)
							} else {
								_t1408 := func(_dollar_dollar *pb.Type) *pb.DateType {
									var _t1409 *pb.DateType
									if hasProtoField(_dollar_dollar, "date_type") {
										_t1409 = _dollar_dollar.GetDateType()
									}
									return _t1409
								}
								_t1410 := _t1408(msg)
								deconstruct_result795 := _t1410
								if deconstruct_result795 != nil {
									unwrapped796 := deconstruct_result795
									p.pretty_date_type(unwrapped796)
								} else {
									_t1411 := func(_dollar_dollar *pb.Type) *pb.DateTimeType {
										var _t1412 *pb.DateTimeType
										if hasProtoField(_dollar_dollar, "datetime_type") {
											_t1412 = _dollar_dollar.GetDatetimeType()
										}
										return _t1412
									}
									_t1413 := _t1411(msg)
									deconstruct_result793 := _t1413
									if deconstruct_result793 != nil {
										unwrapped794 := deconstruct_result793
										p.pretty_datetime_type(unwrapped794)
									} else {
										_t1414 := func(_dollar_dollar *pb.Type) *pb.MissingType {
											var _t1415 *pb.MissingType
											if hasProtoField(_dollar_dollar, "missing_type") {
												_t1415 = _dollar_dollar.GetMissingType()
											}
											return _t1415
										}
										_t1416 := _t1414(msg)
										deconstruct_result791 := _t1416
										if deconstruct_result791 != nil {
											unwrapped792 := deconstruct_result791
											p.pretty_missing_type(unwrapped792)
										} else {
											_t1417 := func(_dollar_dollar *pb.Type) *pb.DecimalType {
												var _t1418 *pb.DecimalType
												if hasProtoField(_dollar_dollar, "decimal_type") {
													_t1418 = _dollar_dollar.GetDecimalType()
												}
												return _t1418
											}
											_t1419 := _t1417(msg)
											deconstruct_result789 := _t1419
											if deconstruct_result789 != nil {
												unwrapped790 := deconstruct_result789
												p.pretty_decimal_type(unwrapped790)
											} else {
												_t1420 := func(_dollar_dollar *pb.Type) *pb.BooleanType {
													var _t1421 *pb.BooleanType
													if hasProtoField(_dollar_dollar, "boolean_type") {
														_t1421 = _dollar_dollar.GetBooleanType()
													}
													return _t1421
												}
												_t1422 := _t1420(msg)
												deconstruct_result787 := _t1422
												if deconstruct_result787 != nil {
													unwrapped788 := deconstruct_result787
													p.pretty_boolean_type(unwrapped788)
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
	return nil
}

func (p *PrettyPrinter) pretty_unspecified_type(msg *pb.UnspecifiedType) interface{} {
	fields810 := msg
	_ = fields810
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields811 := msg
	_ = fields811
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields812 := msg
	_ = fields812
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields813 := msg
	_ = fields813
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields814 := msg
	_ = fields814
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields815 := msg
	_ = fields815
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields816 := msg
	_ = fields816
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields817 := msg
	_ = fields817
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields818 := msg
	_ = fields818
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat823 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat823 != nil {
		p.write(*flat823)
		return nil
	} else {
		_t1423 := func(_dollar_dollar *pb.DecimalType) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		}
		_t1424 := _t1423(msg)
		fields819 := _t1424
		unwrapped_fields820 := fields819
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field821 := unwrapped_fields820[0].(int64)
		p.write(fmt.Sprintf("%d", field821))
		p.newline()
		field822 := unwrapped_fields820[1].(int64)
		p.write(fmt.Sprintf("%d", field822))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields824 := msg
	_ = fields824
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat828 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat828 != nil {
		p.write(*flat828)
		return nil
	} else {
		fields825 := msg
		p.write("|")
		if !(len(fields825) == 0) {
			p.write(" ")
			for i827, elem826 := range fields825 {
				if (i827 > 0) {
					p.newline()
				}
				p.pretty_binding(elem826)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat855 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat855 != nil {
		p.write(*flat855)
		return nil
	} else {
		_t1425 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
			var _t1426 *pb.Conjunction
			if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
				_t1426 = _dollar_dollar.GetConjunction()
			}
			return _t1426
		}
		_t1427 := _t1425(msg)
		deconstruct_result853 := _t1427
		if deconstruct_result853 != nil {
			unwrapped854 := deconstruct_result853
			p.pretty_true(unwrapped854)
		} else {
			_t1428 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
				var _t1429 *pb.Disjunction
				if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
					_t1429 = _dollar_dollar.GetDisjunction()
				}
				return _t1429
			}
			_t1430 := _t1428(msg)
			deconstruct_result851 := _t1430
			if deconstruct_result851 != nil {
				unwrapped852 := deconstruct_result851
				p.pretty_false(unwrapped852)
			} else {
				_t1431 := func(_dollar_dollar *pb.Formula) *pb.Exists {
					var _t1432 *pb.Exists
					if hasProtoField(_dollar_dollar, "exists") {
						_t1432 = _dollar_dollar.GetExists()
					}
					return _t1432
				}
				_t1433 := _t1431(msg)
				deconstruct_result849 := _t1433
				if deconstruct_result849 != nil {
					unwrapped850 := deconstruct_result849
					p.pretty_exists(unwrapped850)
				} else {
					_t1434 := func(_dollar_dollar *pb.Formula) *pb.Reduce {
						var _t1435 *pb.Reduce
						if hasProtoField(_dollar_dollar, "reduce") {
							_t1435 = _dollar_dollar.GetReduce()
						}
						return _t1435
					}
					_t1436 := _t1434(msg)
					deconstruct_result847 := _t1436
					if deconstruct_result847 != nil {
						unwrapped848 := deconstruct_result847
						p.pretty_reduce(unwrapped848)
					} else {
						_t1437 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
							var _t1438 *pb.Conjunction
							if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
								_t1438 = _dollar_dollar.GetConjunction()
							}
							return _t1438
						}
						_t1439 := _t1437(msg)
						deconstruct_result845 := _t1439
						if deconstruct_result845 != nil {
							unwrapped846 := deconstruct_result845
							p.pretty_conjunction(unwrapped846)
						} else {
							_t1440 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
								var _t1441 *pb.Disjunction
								if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
									_t1441 = _dollar_dollar.GetDisjunction()
								}
								return _t1441
							}
							_t1442 := _t1440(msg)
							deconstruct_result843 := _t1442
							if deconstruct_result843 != nil {
								unwrapped844 := deconstruct_result843
								p.pretty_disjunction(unwrapped844)
							} else {
								_t1443 := func(_dollar_dollar *pb.Formula) *pb.Not {
									var _t1444 *pb.Not
									if hasProtoField(_dollar_dollar, "not") {
										_t1444 = _dollar_dollar.GetNot()
									}
									return _t1444
								}
								_t1445 := _t1443(msg)
								deconstruct_result841 := _t1445
								if deconstruct_result841 != nil {
									unwrapped842 := deconstruct_result841
									p.pretty_not(unwrapped842)
								} else {
									_t1446 := func(_dollar_dollar *pb.Formula) *pb.FFI {
										var _t1447 *pb.FFI
										if hasProtoField(_dollar_dollar, "ffi") {
											_t1447 = _dollar_dollar.GetFfi()
										}
										return _t1447
									}
									_t1448 := _t1446(msg)
									deconstruct_result839 := _t1448
									if deconstruct_result839 != nil {
										unwrapped840 := deconstruct_result839
										p.pretty_ffi(unwrapped840)
									} else {
										_t1449 := func(_dollar_dollar *pb.Formula) *pb.Atom {
											var _t1450 *pb.Atom
											if hasProtoField(_dollar_dollar, "atom") {
												_t1450 = _dollar_dollar.GetAtom()
											}
											return _t1450
										}
										_t1451 := _t1449(msg)
										deconstruct_result837 := _t1451
										if deconstruct_result837 != nil {
											unwrapped838 := deconstruct_result837
											p.pretty_atom(unwrapped838)
										} else {
											_t1452 := func(_dollar_dollar *pb.Formula) *pb.Pragma {
												var _t1453 *pb.Pragma
												if hasProtoField(_dollar_dollar, "pragma") {
													_t1453 = _dollar_dollar.GetPragma()
												}
												return _t1453
											}
											_t1454 := _t1452(msg)
											deconstruct_result835 := _t1454
											if deconstruct_result835 != nil {
												unwrapped836 := deconstruct_result835
												p.pretty_pragma(unwrapped836)
											} else {
												_t1455 := func(_dollar_dollar *pb.Formula) *pb.Primitive {
													var _t1456 *pb.Primitive
													if hasProtoField(_dollar_dollar, "primitive") {
														_t1456 = _dollar_dollar.GetPrimitive()
													}
													return _t1456
												}
												_t1457 := _t1455(msg)
												deconstruct_result833 := _t1457
												if deconstruct_result833 != nil {
													unwrapped834 := deconstruct_result833
													p.pretty_primitive(unwrapped834)
												} else {
													_t1458 := func(_dollar_dollar *pb.Formula) *pb.RelAtom {
														var _t1459 *pb.RelAtom
														if hasProtoField(_dollar_dollar, "rel_atom") {
															_t1459 = _dollar_dollar.GetRelAtom()
														}
														return _t1459
													}
													_t1460 := _t1458(msg)
													deconstruct_result831 := _t1460
													if deconstruct_result831 != nil {
														unwrapped832 := deconstruct_result831
														p.pretty_rel_atom(unwrapped832)
													} else {
														_t1461 := func(_dollar_dollar *pb.Formula) *pb.Cast {
															var _t1462 *pb.Cast
															if hasProtoField(_dollar_dollar, "cast") {
																_t1462 = _dollar_dollar.GetCast()
															}
															return _t1462
														}
														_t1463 := _t1461(msg)
														deconstruct_result829 := _t1463
														if deconstruct_result829 != nil {
															unwrapped830 := deconstruct_result829
															p.pretty_cast(unwrapped830)
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
	fields856 := msg
	_ = fields856
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields857 := msg
	_ = fields857
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat862 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat862 != nil {
		p.write(*flat862)
		return nil
	} else {
		_t1464 := func(_dollar_dollar *pb.Exists) []interface{} {
			_t1465 := p.deconstruct_bindings(_dollar_dollar.GetBody())
			return []interface{}{_t1465, _dollar_dollar.GetBody().GetValue()}
		}
		_t1466 := _t1464(msg)
		fields858 := _t1466
		unwrapped_fields859 := fields858
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field860 := unwrapped_fields859[0].([]interface{})
		p.pretty_bindings(field860)
		p.newline()
		field861 := unwrapped_fields859[1].(*pb.Formula)
		p.pretty_formula(field861)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat868 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat868 != nil {
		p.write(*flat868)
		return nil
	} else {
		_t1467 := func(_dollar_dollar *pb.Reduce) []interface{} {
			return []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		}
		_t1468 := _t1467(msg)
		fields863 := _t1468
		unwrapped_fields864 := fields863
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field865 := unwrapped_fields864[0].(*pb.Abstraction)
		p.pretty_abstraction(field865)
		p.newline()
		field866 := unwrapped_fields864[1].(*pb.Abstraction)
		p.pretty_abstraction(field866)
		p.newline()
		field867 := unwrapped_fields864[2].([]*pb.Term)
		p.pretty_terms(field867)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat872 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat872 != nil {
		p.write(*flat872)
		return nil
	} else {
		fields869 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields869) == 0) {
			p.newline()
			for i871, elem870 := range fields869 {
				if (i871 > 0) {
					p.newline()
				}
				p.pretty_term(elem870)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat877 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat877 != nil {
		p.write(*flat877)
		return nil
	} else {
		_t1469 := func(_dollar_dollar *pb.Term) *pb.Var {
			var _t1470 *pb.Var
			if hasProtoField(_dollar_dollar, "var") {
				_t1470 = _dollar_dollar.GetVar()
			}
			return _t1470
		}
		_t1471 := _t1469(msg)
		deconstruct_result875 := _t1471
		if deconstruct_result875 != nil {
			unwrapped876 := deconstruct_result875
			p.pretty_var(unwrapped876)
		} else {
			_t1472 := func(_dollar_dollar *pb.Term) *pb.Value {
				var _t1473 *pb.Value
				if hasProtoField(_dollar_dollar, "constant") {
					_t1473 = _dollar_dollar.GetConstant()
				}
				return _t1473
			}
			_t1474 := _t1472(msg)
			deconstruct_result873 := _t1474
			if deconstruct_result873 != nil {
				unwrapped874 := deconstruct_result873
				p.pretty_constant(unwrapped874)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat880 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat880 != nil {
		p.write(*flat880)
		return nil
	} else {
		_t1475 := func(_dollar_dollar *pb.Var) string {
			return _dollar_dollar.GetName()
		}
		_t1476 := _t1475(msg)
		fields878 := _t1476
		unwrapped_fields879 := fields878
		p.write(unwrapped_fields879)
	}
	return nil
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) interface{} {
	flat882 := p.tryFlat(msg, func() { p.pretty_constant(msg) })
	if flat882 != nil {
		p.write(*flat882)
		return nil
	} else {
		fields881 := msg
		p.pretty_value(fields881)
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat887 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat887 != nil {
		p.write(*flat887)
		return nil
	} else {
		_t1477 := func(_dollar_dollar *pb.Conjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1478 := _t1477(msg)
		fields883 := _t1478
		unwrapped_fields884 := fields883
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields884) == 0) {
			p.newline()
			for i886, elem885 := range unwrapped_fields884 {
				if (i886 > 0) {
					p.newline()
				}
				p.pretty_formula(elem885)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat892 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat892 != nil {
		p.write(*flat892)
		return nil
	} else {
		_t1479 := func(_dollar_dollar *pb.Disjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1480 := _t1479(msg)
		fields888 := _t1480
		unwrapped_fields889 := fields888
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields889) == 0) {
			p.newline()
			for i891, elem890 := range unwrapped_fields889 {
				if (i891 > 0) {
					p.newline()
				}
				p.pretty_formula(elem890)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat895 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat895 != nil {
		p.write(*flat895)
		return nil
	} else {
		_t1481 := func(_dollar_dollar *pb.Not) *pb.Formula {
			return _dollar_dollar.GetArg()
		}
		_t1482 := _t1481(msg)
		fields893 := _t1482
		unwrapped_fields894 := fields893
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields894)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat901 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat901 != nil {
		p.write(*flat901)
		return nil
	} else {
		_t1483 := func(_dollar_dollar *pb.FFI) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		}
		_t1484 := _t1483(msg)
		fields896 := _t1484
		unwrapped_fields897 := fields896
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field898 := unwrapped_fields897[0].(string)
		p.pretty_name(field898)
		p.newline()
		field899 := unwrapped_fields897[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field899)
		p.newline()
		field900 := unwrapped_fields897[2].([]*pb.Term)
		p.pretty_terms(field900)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat903 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat903 != nil {
		p.write(*flat903)
		return nil
	} else {
		fields902 := msg
		p.write(":")
		p.write(fields902)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat907 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat907 != nil {
		p.write(*flat907)
		return nil
	} else {
		fields904 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields904) == 0) {
			p.newline()
			for i906, elem905 := range fields904 {
				if (i906 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem905)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat914 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat914 != nil {
		p.write(*flat914)
		return nil
	} else {
		_t1485 := func(_dollar_dollar *pb.Atom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1486 := _t1485(msg)
		fields908 := _t1486
		unwrapped_fields909 := fields908
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field910 := unwrapped_fields909[0].(*pb.RelationId)
		p.pretty_relation_id(field910)
		field911 := unwrapped_fields909[1].([]*pb.Term)
		if !(len(field911) == 0) {
			p.newline()
			for i913, elem912 := range field911 {
				if (i913 > 0) {
					p.newline()
				}
				p.pretty_term(elem912)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat921 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat921 != nil {
		p.write(*flat921)
		return nil
	} else {
		_t1487 := func(_dollar_dollar *pb.Pragma) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1488 := _t1487(msg)
		fields915 := _t1488
		unwrapped_fields916 := fields915
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field917 := unwrapped_fields916[0].(string)
		p.pretty_name(field917)
		field918 := unwrapped_fields916[1].([]*pb.Term)
		if !(len(field918) == 0) {
			p.newline()
			for i920, elem919 := range field918 {
				if (i920 > 0) {
					p.newline()
				}
				p.pretty_term(elem919)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat937 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat937 != nil {
		p.write(*flat937)
		return nil
	} else {
		_t1489 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1490 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1490 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1490
		}
		_t1491 := _t1489(msg)
		guard_result936 := _t1491
		if guard_result936 != nil {
			p.pretty_eq(msg)
		} else {
			_t1492 := func(_dollar_dollar *pb.Primitive) []interface{} {
				var _t1493 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
					_t1493 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				return _t1493
			}
			_t1494 := _t1492(msg)
			guard_result935 := _t1494
			if guard_result935 != nil {
				p.pretty_lt(msg)
			} else {
				_t1495 := func(_dollar_dollar *pb.Primitive) []interface{} {
					var _t1496 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
						_t1496 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					return _t1496
				}
				_t1497 := _t1495(msg)
				guard_result934 := _t1497
				if guard_result934 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_t1498 := func(_dollar_dollar *pb.Primitive) []interface{} {
						var _t1499 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
							_t1499 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						return _t1499
					}
					_t1500 := _t1498(msg)
					guard_result933 := _t1500
					if guard_result933 != nil {
						p.pretty_gt(msg)
					} else {
						_t1501 := func(_dollar_dollar *pb.Primitive) []interface{} {
							var _t1502 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
								_t1502 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
							}
							return _t1502
						}
						_t1503 := _t1501(msg)
						guard_result932 := _t1503
						if guard_result932 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_t1504 := func(_dollar_dollar *pb.Primitive) []interface{} {
								var _t1505 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
									_t1505 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								return _t1505
							}
							_t1506 := _t1504(msg)
							guard_result931 := _t1506
							if guard_result931 != nil {
								p.pretty_add(msg)
							} else {
								_t1507 := func(_dollar_dollar *pb.Primitive) []interface{} {
									var _t1508 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
										_t1508 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									return _t1508
								}
								_t1509 := _t1507(msg)
								guard_result930 := _t1509
								if guard_result930 != nil {
									p.pretty_minus(msg)
								} else {
									_t1510 := func(_dollar_dollar *pb.Primitive) []interface{} {
										var _t1511 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
											_t1511 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										return _t1511
									}
									_t1512 := _t1510(msg)
									guard_result929 := _t1512
									if guard_result929 != nil {
										p.pretty_multiply(msg)
									} else {
										_t1513 := func(_dollar_dollar *pb.Primitive) []interface{} {
											var _t1514 []interface{}
											if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
												_t1514 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
											}
											return _t1514
										}
										_t1515 := _t1513(msg)
										guard_result928 := _t1515
										if guard_result928 != nil {
											p.pretty_divide(msg)
										} else {
											_t1516 := func(_dollar_dollar *pb.Primitive) []interface{} {
												return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											}
											_t1517 := _t1516(msg)
											fields922 := _t1517
											unwrapped_fields923 := fields922
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field924 := unwrapped_fields923[0].(string)
											p.pretty_name(field924)
											field925 := unwrapped_fields923[1].([]*pb.RelTerm)
											if !(len(field925) == 0) {
												p.newline()
												for i927, elem926 := range field925 {
													if (i927 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem926)
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
	flat942 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat942 != nil {
		p.write(*flat942)
		return nil
	} else {
		_t1518 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1519 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1519 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1519
		}
		_t1520 := _t1518(msg)
		fields938 := _t1520
		unwrapped_fields939 := fields938
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field940 := unwrapped_fields939[0].(*pb.Term)
		p.pretty_term(field940)
		p.newline()
		field941 := unwrapped_fields939[1].(*pb.Term)
		p.pretty_term(field941)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat947 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat947 != nil {
		p.write(*flat947)
		return nil
	} else {
		_t1521 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1522 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1522 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1522
		}
		_t1523 := _t1521(msg)
		fields943 := _t1523
		unwrapped_fields944 := fields943
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field945 := unwrapped_fields944[0].(*pb.Term)
		p.pretty_term(field945)
		p.newline()
		field946 := unwrapped_fields944[1].(*pb.Term)
		p.pretty_term(field946)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat952 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat952 != nil {
		p.write(*flat952)
		return nil
	} else {
		_t1524 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1525 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
				_t1525 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1525
		}
		_t1526 := _t1524(msg)
		fields948 := _t1526
		unwrapped_fields949 := fields948
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field950 := unwrapped_fields949[0].(*pb.Term)
		p.pretty_term(field950)
		p.newline()
		field951 := unwrapped_fields949[1].(*pb.Term)
		p.pretty_term(field951)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat957 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat957 != nil {
		p.write(*flat957)
		return nil
	} else {
		_t1527 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1528 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
				_t1528 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1528
		}
		_t1529 := _t1527(msg)
		fields953 := _t1529
		unwrapped_fields954 := fields953
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field955 := unwrapped_fields954[0].(*pb.Term)
		p.pretty_term(field955)
		p.newline()
		field956 := unwrapped_fields954[1].(*pb.Term)
		p.pretty_term(field956)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat962 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat962 != nil {
		p.write(*flat962)
		return nil
	} else {
		_t1530 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1531 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
				_t1531 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1531
		}
		_t1532 := _t1530(msg)
		fields958 := _t1532
		unwrapped_fields959 := fields958
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field960 := unwrapped_fields959[0].(*pb.Term)
		p.pretty_term(field960)
		p.newline()
		field961 := unwrapped_fields959[1].(*pb.Term)
		p.pretty_term(field961)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat968 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat968 != nil {
		p.write(*flat968)
		return nil
	} else {
		_t1533 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1534 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
				_t1534 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1534
		}
		_t1535 := _t1533(msg)
		fields963 := _t1535
		unwrapped_fields964 := fields963
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field965 := unwrapped_fields964[0].(*pb.Term)
		p.pretty_term(field965)
		p.newline()
		field966 := unwrapped_fields964[1].(*pb.Term)
		p.pretty_term(field966)
		p.newline()
		field967 := unwrapped_fields964[2].(*pb.Term)
		p.pretty_term(field967)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat974 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat974 != nil {
		p.write(*flat974)
		return nil
	} else {
		_t1536 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1537 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
				_t1537 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1537
		}
		_t1538 := _t1536(msg)
		fields969 := _t1538
		unwrapped_fields970 := fields969
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field971 := unwrapped_fields970[0].(*pb.Term)
		p.pretty_term(field971)
		p.newline()
		field972 := unwrapped_fields970[1].(*pb.Term)
		p.pretty_term(field972)
		p.newline()
		field973 := unwrapped_fields970[2].(*pb.Term)
		p.pretty_term(field973)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat980 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat980 != nil {
		p.write(*flat980)
		return nil
	} else {
		_t1539 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1540 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
				_t1540 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1540
		}
		_t1541 := _t1539(msg)
		fields975 := _t1541
		unwrapped_fields976 := fields975
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field977 := unwrapped_fields976[0].(*pb.Term)
		p.pretty_term(field977)
		p.newline()
		field978 := unwrapped_fields976[1].(*pb.Term)
		p.pretty_term(field978)
		p.newline()
		field979 := unwrapped_fields976[2].(*pb.Term)
		p.pretty_term(field979)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat986 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat986 != nil {
		p.write(*flat986)
		return nil
	} else {
		_t1542 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1543 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
				_t1543 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1543
		}
		_t1544 := _t1542(msg)
		fields981 := _t1544
		unwrapped_fields982 := fields981
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field983 := unwrapped_fields982[0].(*pb.Term)
		p.pretty_term(field983)
		p.newline()
		field984 := unwrapped_fields982[1].(*pb.Term)
		p.pretty_term(field984)
		p.newline()
		field985 := unwrapped_fields982[2].(*pb.Term)
		p.pretty_term(field985)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat991 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat991 != nil {
		p.write(*flat991)
		return nil
	} else {
		_t1545 := func(_dollar_dollar *pb.RelTerm) *pb.Value {
			var _t1546 *pb.Value
			if hasProtoField(_dollar_dollar, "specialized_value") {
				_t1546 = _dollar_dollar.GetSpecializedValue()
			}
			return _t1546
		}
		_t1547 := _t1545(msg)
		deconstruct_result989 := _t1547
		if deconstruct_result989 != nil {
			unwrapped990 := deconstruct_result989
			p.pretty_specialized_value(unwrapped990)
		} else {
			_t1548 := func(_dollar_dollar *pb.RelTerm) *pb.Term {
				var _t1549 *pb.Term
				if hasProtoField(_dollar_dollar, "term") {
					_t1549 = _dollar_dollar.GetTerm()
				}
				return _t1549
			}
			_t1550 := _t1548(msg)
			deconstruct_result987 := _t1550
			if deconstruct_result987 != nil {
				unwrapped988 := deconstruct_result987
				p.pretty_term(unwrapped988)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat993 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat993 != nil {
		p.write(*flat993)
		return nil
	} else {
		fields992 := msg
		p.write("#")
		p.pretty_value(fields992)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1000 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1000 != nil {
		p.write(*flat1000)
		return nil
	} else {
		_t1551 := func(_dollar_dollar *pb.RelAtom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1552 := _t1551(msg)
		fields994 := _t1552
		unwrapped_fields995 := fields994
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field996 := unwrapped_fields995[0].(string)
		p.pretty_name(field996)
		field997 := unwrapped_fields995[1].([]*pb.RelTerm)
		if !(len(field997) == 0) {
			p.newline()
			for i999, elem998 := range field997 {
				if (i999 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem998)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1005 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1005 != nil {
		p.write(*flat1005)
		return nil
	} else {
		_t1553 := func(_dollar_dollar *pb.Cast) []interface{} {
			return []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		}
		_t1554 := _t1553(msg)
		fields1001 := _t1554
		unwrapped_fields1002 := fields1001
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1003 := unwrapped_fields1002[0].(*pb.Term)
		p.pretty_term(field1003)
		p.newline()
		field1004 := unwrapped_fields1002[1].(*pb.Term)
		p.pretty_term(field1004)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1009 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1009 != nil {
		p.write(*flat1009)
		return nil
	} else {
		fields1006 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1006) == 0) {
			p.newline()
			for i1008, elem1007 := range fields1006 {
				if (i1008 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1007)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1016 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1016 != nil {
		p.write(*flat1016)
		return nil
	} else {
		_t1555 := func(_dollar_dollar *pb.Attribute) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		}
		_t1556 := _t1555(msg)
		fields1010 := _t1556
		unwrapped_fields1011 := fields1010
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1012 := unwrapped_fields1011[0].(string)
		p.pretty_name(field1012)
		field1013 := unwrapped_fields1011[1].([]*pb.Value)
		if !(len(field1013) == 0) {
			p.newline()
			for i1015, elem1014 := range field1013 {
				if (i1015 > 0) {
					p.newline()
				}
				p.pretty_value(elem1014)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1023 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1023 != nil {
		p.write(*flat1023)
		return nil
	} else {
		_t1557 := func(_dollar_dollar *pb.Algorithm) []interface{} {
			return []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		}
		_t1558 := _t1557(msg)
		fields1017 := _t1558
		unwrapped_fields1018 := fields1017
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1019 := unwrapped_fields1018[0].([]*pb.RelationId)
		if !(len(field1019) == 0) {
			p.newline()
			for i1021, elem1020 := range field1019 {
				if (i1021 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1020)
			}
		}
		p.newline()
		field1022 := unwrapped_fields1018[1].(*pb.Script)
		p.pretty_script(field1022)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1028 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1028 != nil {
		p.write(*flat1028)
		return nil
	} else {
		_t1559 := func(_dollar_dollar *pb.Script) []*pb.Construct {
			return _dollar_dollar.GetConstructs()
		}
		_t1560 := _t1559(msg)
		fields1024 := _t1560
		unwrapped_fields1025 := fields1024
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1025) == 0) {
			p.newline()
			for i1027, elem1026 := range unwrapped_fields1025 {
				if (i1027 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1026)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1033 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1033 != nil {
		p.write(*flat1033)
		return nil
	} else {
		_t1561 := func(_dollar_dollar *pb.Construct) *pb.Loop {
			var _t1562 *pb.Loop
			if hasProtoField(_dollar_dollar, "loop") {
				_t1562 = _dollar_dollar.GetLoop()
			}
			return _t1562
		}
		_t1563 := _t1561(msg)
		deconstruct_result1031 := _t1563
		if deconstruct_result1031 != nil {
			unwrapped1032 := deconstruct_result1031
			p.pretty_loop(unwrapped1032)
		} else {
			_t1564 := func(_dollar_dollar *pb.Construct) *pb.Instruction {
				var _t1565 *pb.Instruction
				if hasProtoField(_dollar_dollar, "instruction") {
					_t1565 = _dollar_dollar.GetInstruction()
				}
				return _t1565
			}
			_t1566 := _t1564(msg)
			deconstruct_result1029 := _t1566
			if deconstruct_result1029 != nil {
				unwrapped1030 := deconstruct_result1029
				p.pretty_instruction(unwrapped1030)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1038 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1038 != nil {
		p.write(*flat1038)
		return nil
	} else {
		_t1567 := func(_dollar_dollar *pb.Loop) []interface{} {
			return []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		}
		_t1568 := _t1567(msg)
		fields1034 := _t1568
		unwrapped_fields1035 := fields1034
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1036 := unwrapped_fields1035[0].([]*pb.Instruction)
		p.pretty_init(field1036)
		p.newline()
		field1037 := unwrapped_fields1035[1].(*pb.Script)
		p.pretty_script(field1037)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1042 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1042 != nil {
		p.write(*flat1042)
		return nil
	} else {
		fields1039 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1039) == 0) {
			p.newline()
			for i1041, elem1040 := range fields1039 {
				if (i1041 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1040)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1053 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1053 != nil {
		p.write(*flat1053)
		return nil
	} else {
		_t1569 := func(_dollar_dollar *pb.Instruction) *pb.Assign {
			var _t1570 *pb.Assign
			if hasProtoField(_dollar_dollar, "assign") {
				_t1570 = _dollar_dollar.GetAssign()
			}
			return _t1570
		}
		_t1571 := _t1569(msg)
		deconstruct_result1051 := _t1571
		if deconstruct_result1051 != nil {
			unwrapped1052 := deconstruct_result1051
			p.pretty_assign(unwrapped1052)
		} else {
			_t1572 := func(_dollar_dollar *pb.Instruction) *pb.Upsert {
				var _t1573 *pb.Upsert
				if hasProtoField(_dollar_dollar, "upsert") {
					_t1573 = _dollar_dollar.GetUpsert()
				}
				return _t1573
			}
			_t1574 := _t1572(msg)
			deconstruct_result1049 := _t1574
			if deconstruct_result1049 != nil {
				unwrapped1050 := deconstruct_result1049
				p.pretty_upsert(unwrapped1050)
			} else {
				_t1575 := func(_dollar_dollar *pb.Instruction) *pb.Break {
					var _t1576 *pb.Break
					if hasProtoField(_dollar_dollar, "break") {
						_t1576 = _dollar_dollar.GetBreak()
					}
					return _t1576
				}
				_t1577 := _t1575(msg)
				deconstruct_result1047 := _t1577
				if deconstruct_result1047 != nil {
					unwrapped1048 := deconstruct_result1047
					p.pretty_break(unwrapped1048)
				} else {
					_t1578 := func(_dollar_dollar *pb.Instruction) *pb.MonoidDef {
						var _t1579 *pb.MonoidDef
						if hasProtoField(_dollar_dollar, "monoid_def") {
							_t1579 = _dollar_dollar.GetMonoidDef()
						}
						return _t1579
					}
					_t1580 := _t1578(msg)
					deconstruct_result1045 := _t1580
					if deconstruct_result1045 != nil {
						unwrapped1046 := deconstruct_result1045
						p.pretty_monoid_def(unwrapped1046)
					} else {
						_t1581 := func(_dollar_dollar *pb.Instruction) *pb.MonusDef {
							var _t1582 *pb.MonusDef
							if hasProtoField(_dollar_dollar, "monus_def") {
								_t1582 = _dollar_dollar.GetMonusDef()
							}
							return _t1582
						}
						_t1583 := _t1581(msg)
						deconstruct_result1043 := _t1583
						if deconstruct_result1043 != nil {
							unwrapped1044 := deconstruct_result1043
							p.pretty_monus_def(unwrapped1044)
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
	flat1060 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1060 != nil {
		p.write(*flat1060)
		return nil
	} else {
		_t1584 := func(_dollar_dollar *pb.Assign) []interface{} {
			var _t1585 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1585 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1585}
		}
		_t1586 := _t1584(msg)
		fields1054 := _t1586
		unwrapped_fields1055 := fields1054
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1056 := unwrapped_fields1055[0].(*pb.RelationId)
		p.pretty_relation_id(field1056)
		p.newline()
		field1057 := unwrapped_fields1055[1].(*pb.Abstraction)
		p.pretty_abstraction(field1057)
		field1058 := unwrapped_fields1055[2].([]*pb.Attribute)
		if field1058 != nil {
			p.newline()
			opt_val1059 := field1058
			p.pretty_attrs(opt_val1059)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1067 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1067 != nil {
		p.write(*flat1067)
		return nil
	} else {
		_t1587 := func(_dollar_dollar *pb.Upsert) []interface{} {
			var _t1588 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1588 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1588}
		}
		_t1589 := _t1587(msg)
		fields1061 := _t1589
		unwrapped_fields1062 := fields1061
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1063 := unwrapped_fields1062[0].(*pb.RelationId)
		p.pretty_relation_id(field1063)
		p.newline()
		field1064 := unwrapped_fields1062[1].([]interface{})
		p.pretty_abstraction_with_arity(field1064)
		field1065 := unwrapped_fields1062[2].([]*pb.Attribute)
		if field1065 != nil {
			p.newline()
			opt_val1066 := field1065
			p.pretty_attrs(opt_val1066)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1072 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1072 != nil {
		p.write(*flat1072)
		return nil
	} else {
		_t1590 := func(_dollar_dollar []interface{}) []interface{} {
			_t1591 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
			return []interface{}{_t1591, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		}
		_t1592 := _t1590(msg)
		fields1068 := _t1592
		unwrapped_fields1069 := fields1068
		p.write("(")
		p.indent()
		field1070 := unwrapped_fields1069[0].([]interface{})
		p.pretty_bindings(field1070)
		p.newline()
		field1071 := unwrapped_fields1069[1].(*pb.Formula)
		p.pretty_formula(field1071)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1079 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1079 != nil {
		p.write(*flat1079)
		return nil
	} else {
		_t1593 := func(_dollar_dollar *pb.Break) []interface{} {
			var _t1594 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1594 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1594}
		}
		_t1595 := _t1593(msg)
		fields1073 := _t1595
		unwrapped_fields1074 := fields1073
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1075 := unwrapped_fields1074[0].(*pb.RelationId)
		p.pretty_relation_id(field1075)
		p.newline()
		field1076 := unwrapped_fields1074[1].(*pb.Abstraction)
		p.pretty_abstraction(field1076)
		field1077 := unwrapped_fields1074[2].([]*pb.Attribute)
		if field1077 != nil {
			p.newline()
			opt_val1078 := field1077
			p.pretty_attrs(opt_val1078)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1087 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1087 != nil {
		p.write(*flat1087)
		return nil
	} else {
		_t1596 := func(_dollar_dollar *pb.MonoidDef) []interface{} {
			var _t1597 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1597 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1597}
		}
		_t1598 := _t1596(msg)
		fields1080 := _t1598
		unwrapped_fields1081 := fields1080
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1082 := unwrapped_fields1081[0].(*pb.Monoid)
		p.pretty_monoid(field1082)
		p.newline()
		field1083 := unwrapped_fields1081[1].(*pb.RelationId)
		p.pretty_relation_id(field1083)
		p.newline()
		field1084 := unwrapped_fields1081[2].([]interface{})
		p.pretty_abstraction_with_arity(field1084)
		field1085 := unwrapped_fields1081[3].([]*pb.Attribute)
		if field1085 != nil {
			p.newline()
			opt_val1086 := field1085
			p.pretty_attrs(opt_val1086)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1096 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1096 != nil {
		p.write(*flat1096)
		return nil
	} else {
		_t1599 := func(_dollar_dollar *pb.Monoid) *pb.OrMonoid {
			var _t1600 *pb.OrMonoid
			if hasProtoField(_dollar_dollar, "or_monoid") {
				_t1600 = _dollar_dollar.GetOrMonoid()
			}
			return _t1600
		}
		_t1601 := _t1599(msg)
		deconstruct_result1094 := _t1601
		if deconstruct_result1094 != nil {
			unwrapped1095 := deconstruct_result1094
			p.pretty_or_monoid(unwrapped1095)
		} else {
			_t1602 := func(_dollar_dollar *pb.Monoid) *pb.MinMonoid {
				var _t1603 *pb.MinMonoid
				if hasProtoField(_dollar_dollar, "min_monoid") {
					_t1603 = _dollar_dollar.GetMinMonoid()
				}
				return _t1603
			}
			_t1604 := _t1602(msg)
			deconstruct_result1092 := _t1604
			if deconstruct_result1092 != nil {
				unwrapped1093 := deconstruct_result1092
				p.pretty_min_monoid(unwrapped1093)
			} else {
				_t1605 := func(_dollar_dollar *pb.Monoid) *pb.MaxMonoid {
					var _t1606 *pb.MaxMonoid
					if hasProtoField(_dollar_dollar, "max_monoid") {
						_t1606 = _dollar_dollar.GetMaxMonoid()
					}
					return _t1606
				}
				_t1607 := _t1605(msg)
				deconstruct_result1090 := _t1607
				if deconstruct_result1090 != nil {
					unwrapped1091 := deconstruct_result1090
					p.pretty_max_monoid(unwrapped1091)
				} else {
					_t1608 := func(_dollar_dollar *pb.Monoid) *pb.SumMonoid {
						var _t1609 *pb.SumMonoid
						if hasProtoField(_dollar_dollar, "sum_monoid") {
							_t1609 = _dollar_dollar.GetSumMonoid()
						}
						return _t1609
					}
					_t1610 := _t1608(msg)
					deconstruct_result1088 := _t1610
					if deconstruct_result1088 != nil {
						unwrapped1089 := deconstruct_result1088
						p.pretty_sum_monoid(unwrapped1089)
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
	fields1097 := msg
	_ = fields1097
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1100 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1100 != nil {
		p.write(*flat1100)
		return nil
	} else {
		_t1611 := func(_dollar_dollar *pb.MinMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1612 := _t1611(msg)
		fields1098 := _t1612
		unwrapped_fields1099 := fields1098
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1099)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1103 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1103 != nil {
		p.write(*flat1103)
		return nil
	} else {
		_t1613 := func(_dollar_dollar *pb.MaxMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1614 := _t1613(msg)
		fields1101 := _t1614
		unwrapped_fields1102 := fields1101
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1102)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1106 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1106 != nil {
		p.write(*flat1106)
		return nil
	} else {
		_t1615 := func(_dollar_dollar *pb.SumMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1616 := _t1615(msg)
		fields1104 := _t1616
		unwrapped_fields1105 := fields1104
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1105)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1114 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1114 != nil {
		p.write(*flat1114)
		return nil
	} else {
		_t1617 := func(_dollar_dollar *pb.MonusDef) []interface{} {
			var _t1618 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1618 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1618}
		}
		_t1619 := _t1617(msg)
		fields1107 := _t1619
		unwrapped_fields1108 := fields1107
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1109 := unwrapped_fields1108[0].(*pb.Monoid)
		p.pretty_monoid(field1109)
		p.newline()
		field1110 := unwrapped_fields1108[1].(*pb.RelationId)
		p.pretty_relation_id(field1110)
		p.newline()
		field1111 := unwrapped_fields1108[2].([]interface{})
		p.pretty_abstraction_with_arity(field1111)
		field1112 := unwrapped_fields1108[3].([]*pb.Attribute)
		if field1112 != nil {
			p.newline()
			opt_val1113 := field1112
			p.pretty_attrs(opt_val1113)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1121 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1121 != nil {
		p.write(*flat1121)
		return nil
	} else {
		_t1620 := func(_dollar_dollar *pb.Constraint) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		}
		_t1621 := _t1620(msg)
		fields1115 := _t1621
		unwrapped_fields1116 := fields1115
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1117 := unwrapped_fields1116[0].(*pb.RelationId)
		p.pretty_relation_id(field1117)
		p.newline()
		field1118 := unwrapped_fields1116[1].(*pb.Abstraction)
		p.pretty_abstraction(field1118)
		p.newline()
		field1119 := unwrapped_fields1116[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1119)
		p.newline()
		field1120 := unwrapped_fields1116[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1120)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1125 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1125 != nil {
		p.write(*flat1125)
		return nil
	} else {
		fields1122 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1122) == 0) {
			p.newline()
			for i1124, elem1123 := range fields1122 {
				if (i1124 > 0) {
					p.newline()
				}
				p.pretty_var(elem1123)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1129 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1129 != nil {
		p.write(*flat1129)
		return nil
	} else {
		fields1126 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1126) == 0) {
			p.newline()
			for i1128, elem1127 := range fields1126 {
				if (i1128 > 0) {
					p.newline()
				}
				p.pretty_var(elem1127)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1136 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1136 != nil {
		p.write(*flat1136)
		return nil
	} else {
		_t1622 := func(_dollar_dollar *pb.Data) *pb.RelEDB {
			var _t1623 *pb.RelEDB
			if hasProtoField(_dollar_dollar, "rel_edb") {
				_t1623 = _dollar_dollar.GetRelEdb()
			}
			return _t1623
		}
		_t1624 := _t1622(msg)
		deconstruct_result1134 := _t1624
		if deconstruct_result1134 != nil {
			unwrapped1135 := deconstruct_result1134
			p.pretty_rel_edb(unwrapped1135)
		} else {
			_t1625 := func(_dollar_dollar *pb.Data) *pb.BeTreeRelation {
				var _t1626 *pb.BeTreeRelation
				if hasProtoField(_dollar_dollar, "betree_relation") {
					_t1626 = _dollar_dollar.GetBetreeRelation()
				}
				return _t1626
			}
			_t1627 := _t1625(msg)
			deconstruct_result1132 := _t1627
			if deconstruct_result1132 != nil {
				unwrapped1133 := deconstruct_result1132
				p.pretty_betree_relation(unwrapped1133)
			} else {
				_t1628 := func(_dollar_dollar *pb.Data) *pb.CSVData {
					var _t1629 *pb.CSVData
					if hasProtoField(_dollar_dollar, "csv_data") {
						_t1629 = _dollar_dollar.GetCsvData()
					}
					return _t1629
				}
				_t1630 := _t1628(msg)
				deconstruct_result1130 := _t1630
				if deconstruct_result1130 != nil {
					unwrapped1131 := deconstruct_result1130
					p.pretty_csv_data(unwrapped1131)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_edb(msg *pb.RelEDB) interface{} {
	flat1142 := p.tryFlat(msg, func() { p.pretty_rel_edb(msg) })
	if flat1142 != nil {
		p.write(*flat1142)
		return nil
	} else {
		_t1631 := func(_dollar_dollar *pb.RelEDB) []interface{} {
			return []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		}
		_t1632 := _t1631(msg)
		fields1137 := _t1632
		unwrapped_fields1138 := fields1137
		p.write("(")
		p.write("rel_edb")
		p.indentSexp()
		p.newline()
		field1139 := unwrapped_fields1138[0].(*pb.RelationId)
		p.pretty_relation_id(field1139)
		p.newline()
		field1140 := unwrapped_fields1138[1].([]string)
		p.pretty_rel_edb_path(field1140)
		p.newline()
		field1141 := unwrapped_fields1138[2].([]*pb.Type)
		p.pretty_rel_edb_types(field1141)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_edb_path(msg []string) interface{} {
	flat1146 := p.tryFlat(msg, func() { p.pretty_rel_edb_path(msg) })
	if flat1146 != nil {
		p.write(*flat1146)
		return nil
	} else {
		fields1143 := msg
		p.write("[")
		p.indent()
		for i1145, elem1144 := range fields1143 {
			if (i1145 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1144))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_edb_types(msg []*pb.Type) interface{} {
	flat1150 := p.tryFlat(msg, func() { p.pretty_rel_edb_types(msg) })
	if flat1150 != nil {
		p.write(*flat1150)
		return nil
	} else {
		fields1147 := msg
		p.write("[")
		p.indent()
		for i1149, elem1148 := range fields1147 {
			if (i1149 > 0) {
				p.newline()
			}
			p.pretty_type(elem1148)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1155 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1155 != nil {
		p.write(*flat1155)
		return nil
	} else {
		_t1633 := func(_dollar_dollar *pb.BeTreeRelation) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		}
		_t1634 := _t1633(msg)
		fields1151 := _t1634
		unwrapped_fields1152 := fields1151
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1153 := unwrapped_fields1152[0].(*pb.RelationId)
		p.pretty_relation_id(field1153)
		p.newline()
		field1154 := unwrapped_fields1152[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1154)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1161 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1161 != nil {
		p.write(*flat1161)
		return nil
	} else {
		_t1635 := func(_dollar_dollar *pb.BeTreeInfo) []interface{} {
			_t1636 := p.deconstruct_betree_info_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1636}
		}
		_t1637 := _t1635(msg)
		fields1156 := _t1637
		unwrapped_fields1157 := fields1156
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1158 := unwrapped_fields1157[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1158)
		p.newline()
		field1159 := unwrapped_fields1157[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1159)
		p.newline()
		field1160 := unwrapped_fields1157[2].([][]interface{})
		p.pretty_config_dict(field1160)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1165 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1165 != nil {
		p.write(*flat1165)
		return nil
	} else {
		fields1162 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1162) == 0) {
			p.newline()
			for i1164, elem1163 := range fields1162 {
				if (i1164 > 0) {
					p.newline()
				}
				p.pretty_type(elem1163)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1169 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1169 != nil {
		p.write(*flat1169)
		return nil
	} else {
		fields1166 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1166) == 0) {
			p.newline()
			for i1168, elem1167 := range fields1166 {
				if (i1168 > 0) {
					p.newline()
				}
				p.pretty_type(elem1167)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1176 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1176 != nil {
		p.write(*flat1176)
		return nil
	} else {
		_t1638 := func(_dollar_dollar *pb.CSVData) []interface{} {
			return []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		}
		_t1639 := _t1638(msg)
		fields1170 := _t1639
		unwrapped_fields1171 := fields1170
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1172 := unwrapped_fields1171[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1172)
		p.newline()
		field1173 := unwrapped_fields1171[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1173)
		p.newline()
		field1174 := unwrapped_fields1171[2].([]*pb.CSVColumn)
		p.pretty_csv_columns(field1174)
		p.newline()
		field1175 := unwrapped_fields1171[3].(string)
		p.pretty_csv_asof(field1175)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1183 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1183 != nil {
		p.write(*flat1183)
		return nil
	} else {
		_t1640 := func(_dollar_dollar *pb.CSVLocator) []interface{} {
			var _t1641 []string
			if !(len(_dollar_dollar.GetPaths()) == 0) {
				_t1641 = _dollar_dollar.GetPaths()
			}
			var _t1642 *string
			if string(_dollar_dollar.GetInlineData()) != "" {
				_t1642 = ptr(string(_dollar_dollar.GetInlineData()))
			}
			return []interface{}{_t1641, _t1642}
		}
		_t1643 := _t1640(msg)
		fields1177 := _t1643
		unwrapped_fields1178 := fields1177
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1179 := unwrapped_fields1178[0].([]string)
		if field1179 != nil {
			p.newline()
			opt_val1180 := field1179
			p.pretty_csv_locator_paths(opt_val1180)
		}
		field1181 := unwrapped_fields1178[1].(*string)
		if field1181 != nil {
			p.newline()
			opt_val1182 := *field1181
			p.pretty_csv_locator_inline_data(opt_val1182)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1187 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1187 != nil {
		p.write(*flat1187)
		return nil
	} else {
		fields1184 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1184) == 0) {
			p.newline()
			for i1186, elem1185 := range fields1184 {
				if (i1186 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1185))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1189 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1189 != nil {
		p.write(*flat1189)
		return nil
	} else {
		fields1188 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1188))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1192 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1192 != nil {
		p.write(*flat1192)
		return nil
	} else {
		_t1644 := func(_dollar_dollar *pb.CSVConfig) [][]interface{} {
			_t1645 := p.deconstruct_csv_config(_dollar_dollar)
			return _t1645
		}
		_t1646 := _t1644(msg)
		fields1190 := _t1646
		unwrapped_fields1191 := fields1190
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1191)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_columns(msg []*pb.CSVColumn) interface{} {
	flat1196 := p.tryFlat(msg, func() { p.pretty_csv_columns(msg) })
	if flat1196 != nil {
		p.write(*flat1196)
		return nil
	} else {
		fields1193 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1193) == 0) {
			p.newline()
			for i1195, elem1194 := range fields1193 {
				if (i1195 > 0) {
					p.newline()
				}
				p.pretty_csv_column(elem1194)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_column(msg *pb.CSVColumn) interface{} {
	flat1202 := p.tryFlat(msg, func() { p.pretty_csv_column(msg) })
	if flat1202 != nil {
		p.write(*flat1202)
		return nil
	} else {
		_t1647 := func(_dollar_dollar *pb.CSVColumn) []interface{} {
			_t1648 := p.deconstruct_csv_column_tail(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetColumnPath(), _t1648}
		}
		_t1649 := _t1647(msg)
		fields1197 := _t1649
		unwrapped_fields1198 := fields1197
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1199 := unwrapped_fields1198[0].([]string)
		p.pretty_csv_column_path(field1199)
		field1200 := unwrapped_fields1198[1].([]interface{})
		if field1200 != nil {
			p.newline()
			opt_val1201 := field1200
			p.pretty_csv_column_tail(opt_val1201)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_column_path(msg []string) interface{} {
	flat1209 := p.tryFlat(msg, func() { p.pretty_csv_column_path(msg) })
	if flat1209 != nil {
		p.write(*flat1209)
		return nil
	} else {
		_t1650 := func(_dollar_dollar []string) *string {
			var _t1651 *string
			if int64(len(_dollar_dollar)) == 1 {
				_t1651 = ptr(_dollar_dollar[0])
			}
			return _t1651
		}
		_t1652 := _t1650(msg)
		deconstruct_result1207 := _t1652
		if deconstruct_result1207 != nil {
			unwrapped1208 := *deconstruct_result1207
			p.write(p.formatStringValue(unwrapped1208))
		} else {
			_t1653 := func(_dollar_dollar []string) []string {
				var _t1654 []string
				if int64(len(_dollar_dollar)) != 1 {
					_t1654 = _dollar_dollar
				}
				return _t1654
			}
			_t1655 := _t1653(msg)
			deconstruct_result1203 := _t1655
			if deconstruct_result1203 != nil {
				unwrapped1204 := deconstruct_result1203
				p.write("[")
				p.indent()
				for i1206, elem1205 := range unwrapped1204 {
					if (i1206 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1205))
				}
				p.dedent()
				p.write("]")
			} else {
				panic(ParseError{msg: "No matching rule for csv_column_path"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_column_tail(msg []interface{}) interface{} {
	flat1220 := p.tryFlat(msg, func() { p.pretty_csv_column_tail(msg) })
	if flat1220 != nil {
		p.write(*flat1220)
		return nil
	} else {
		_t1656 := func(_dollar_dollar []interface{}) []interface{} {
			var _t1657 []interface{}
			if _dollar_dollar[0].(*pb.RelationId) != nil {
				_t1657 = []interface{}{_dollar_dollar[0].(*pb.RelationId), _dollar_dollar[1].([]*pb.Type)}
			}
			return _t1657
		}
		_t1658 := _t1656(msg)
		deconstruct_result1214 := _t1658
		if deconstruct_result1214 != nil {
			unwrapped1215 := deconstruct_result1214
			field1216 := unwrapped1215[0].(*pb.RelationId)
			p.pretty_relation_id(field1216)
			p.write(" ")
			p.write("[")
			field1217 := unwrapped1215[1].([]*pb.Type)
			for i1219, elem1218 := range field1217 {
				if (i1219 > 0) {
					p.newline()
				}
				p.pretty_type(elem1218)
			}
			p.write("]")
		} else {
			_t1659 := func(_dollar_dollar []interface{}) []*pb.Type {
				return _dollar_dollar[1].([]*pb.Type)
			}
			_t1660 := _t1659(msg)
			fields1210 := _t1660
			unwrapped_fields1211 := fields1210
			p.write("[")
			p.indent()
			for i1213, elem1212 := range unwrapped_fields1211 {
				if (i1213 > 0) {
					p.newline()
				}
				p.pretty_type(elem1212)
			}
			p.dedent()
			p.write("]")
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1222 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1222 != nil {
		p.write(*flat1222)
		return nil
	} else {
		fields1221 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1221))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1225 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1225 != nil {
		p.write(*flat1225)
		return nil
	} else {
		_t1661 := func(_dollar_dollar *pb.Undefine) *pb.FragmentId {
			return _dollar_dollar.GetFragmentId()
		}
		_t1662 := _t1661(msg)
		fields1223 := _t1662
		unwrapped_fields1224 := fields1223
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1224)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1230 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1230 != nil {
		p.write(*flat1230)
		return nil
	} else {
		_t1663 := func(_dollar_dollar *pb.Context) []*pb.RelationId {
			return _dollar_dollar.GetRelations()
		}
		_t1664 := _t1663(msg)
		fields1226 := _t1664
		unwrapped_fields1227 := fields1226
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1227) == 0) {
			p.newline()
			for i1229, elem1228 := range unwrapped_fields1227 {
				if (i1229 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1228)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1235 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1235 != nil {
		p.write(*flat1235)
		return nil
	} else {
		_t1665 := func(_dollar_dollar *pb.Snapshot) []interface{} {
			return []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		}
		_t1666 := _t1665(msg)
		fields1231 := _t1666
		unwrapped_fields1232 := fields1231
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1233 := unwrapped_fields1232[0].([]string)
		p.pretty_rel_edb_path(field1233)
		p.newline()
		field1234 := unwrapped_fields1232[1].(*pb.RelationId)
		p.pretty_relation_id(field1234)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1239 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1239 != nil {
		p.write(*flat1239)
		return nil
	} else {
		fields1236 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1236) == 0) {
			p.newline()
			for i1238, elem1237 := range fields1236 {
				if (i1238 > 0) {
					p.newline()
				}
				p.pretty_read(elem1237)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1250 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1250 != nil {
		p.write(*flat1250)
		return nil
	} else {
		_t1667 := func(_dollar_dollar *pb.Read) *pb.Demand {
			var _t1668 *pb.Demand
			if hasProtoField(_dollar_dollar, "demand") {
				_t1668 = _dollar_dollar.GetDemand()
			}
			return _t1668
		}
		_t1669 := _t1667(msg)
		deconstruct_result1248 := _t1669
		if deconstruct_result1248 != nil {
			unwrapped1249 := deconstruct_result1248
			p.pretty_demand(unwrapped1249)
		} else {
			_t1670 := func(_dollar_dollar *pb.Read) *pb.Output {
				var _t1671 *pb.Output
				if hasProtoField(_dollar_dollar, "output") {
					_t1671 = _dollar_dollar.GetOutput()
				}
				return _t1671
			}
			_t1672 := _t1670(msg)
			deconstruct_result1246 := _t1672
			if deconstruct_result1246 != nil {
				unwrapped1247 := deconstruct_result1246
				p.pretty_output(unwrapped1247)
			} else {
				_t1673 := func(_dollar_dollar *pb.Read) *pb.WhatIf {
					var _t1674 *pb.WhatIf
					if hasProtoField(_dollar_dollar, "what_if") {
						_t1674 = _dollar_dollar.GetWhatIf()
					}
					return _t1674
				}
				_t1675 := _t1673(msg)
				deconstruct_result1244 := _t1675
				if deconstruct_result1244 != nil {
					unwrapped1245 := deconstruct_result1244
					p.pretty_what_if(unwrapped1245)
				} else {
					_t1676 := func(_dollar_dollar *pb.Read) *pb.Abort {
						var _t1677 *pb.Abort
						if hasProtoField(_dollar_dollar, "abort") {
							_t1677 = _dollar_dollar.GetAbort()
						}
						return _t1677
					}
					_t1678 := _t1676(msg)
					deconstruct_result1242 := _t1678
					if deconstruct_result1242 != nil {
						unwrapped1243 := deconstruct_result1242
						p.pretty_abort(unwrapped1243)
					} else {
						_t1679 := func(_dollar_dollar *pb.Read) *pb.Export {
							var _t1680 *pb.Export
							if hasProtoField(_dollar_dollar, "export") {
								_t1680 = _dollar_dollar.GetExport()
							}
							return _t1680
						}
						_t1681 := _t1679(msg)
						deconstruct_result1240 := _t1681
						if deconstruct_result1240 != nil {
							unwrapped1241 := deconstruct_result1240
							p.pretty_export(unwrapped1241)
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
	flat1253 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		_t1682 := func(_dollar_dollar *pb.Demand) *pb.RelationId {
			return _dollar_dollar.GetRelationId()
		}
		_t1683 := _t1682(msg)
		fields1251 := _t1683
		unwrapped_fields1252 := fields1251
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1252)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1258 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1258 != nil {
		p.write(*flat1258)
		return nil
	} else {
		_t1684 := func(_dollar_dollar *pb.Output) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		}
		_t1685 := _t1684(msg)
		fields1254 := _t1685
		unwrapped_fields1255 := fields1254
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1256 := unwrapped_fields1255[0].(string)
		p.pretty_name(field1256)
		p.newline()
		field1257 := unwrapped_fields1255[1].(*pb.RelationId)
		p.pretty_relation_id(field1257)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1263 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1263 != nil {
		p.write(*flat1263)
		return nil
	} else {
		_t1686 := func(_dollar_dollar *pb.WhatIf) []interface{} {
			return []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		}
		_t1687 := _t1686(msg)
		fields1259 := _t1687
		unwrapped_fields1260 := fields1259
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1261 := unwrapped_fields1260[0].(string)
		p.pretty_name(field1261)
		p.newline()
		field1262 := unwrapped_fields1260[1].(*pb.Epoch)
		p.pretty_epoch(field1262)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1269 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1269 != nil {
		p.write(*flat1269)
		return nil
	} else {
		_t1688 := func(_dollar_dollar *pb.Abort) []interface{} {
			var _t1689 *string
			if _dollar_dollar.GetName() != "abort" {
				_t1689 = ptr(_dollar_dollar.GetName())
			}
			return []interface{}{_t1689, _dollar_dollar.GetRelationId()}
		}
		_t1690 := _t1688(msg)
		fields1264 := _t1690
		unwrapped_fields1265 := fields1264
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1266 := unwrapped_fields1265[0].(*string)
		if field1266 != nil {
			p.newline()
			opt_val1267 := *field1266
			p.pretty_name(opt_val1267)
		}
		p.newline()
		field1268 := unwrapped_fields1265[1].(*pb.RelationId)
		p.pretty_relation_id(field1268)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1272 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1272 != nil {
		p.write(*flat1272)
		return nil
	} else {
		_t1691 := func(_dollar_dollar *pb.Export) *pb.ExportCSVConfig {
			return _dollar_dollar.GetCsvConfig()
		}
		_t1692 := _t1691(msg)
		fields1270 := _t1692
		unwrapped_fields1271 := fields1270
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1271)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1278 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1278 != nil {
		p.write(*flat1278)
		return nil
	} else {
		_t1693 := func(_dollar_dollar *pb.ExportCSVConfig) []interface{} {
			_t1694 := p.deconstruct_export_csv_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1694}
		}
		_t1695 := _t1693(msg)
		fields1273 := _t1695
		unwrapped_fields1274 := fields1273
		p.write("(")
		p.write("export_csv_config")
		p.indentSexp()
		p.newline()
		field1275 := unwrapped_fields1274[0].(string)
		p.pretty_export_csv_path(field1275)
		p.newline()
		field1276 := unwrapped_fields1274[1].([]*pb.ExportCSVColumn)
		p.pretty_export_csv_columns(field1276)
		p.newline()
		field1277 := unwrapped_fields1274[2].([][]interface{})
		p.pretty_config_dict(field1277)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1280 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1280 != nil {
		p.write(*flat1280)
		return nil
	} else {
		fields1279 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1279))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns(msg []*pb.ExportCSVColumn) interface{} {
	flat1284 := p.tryFlat(msg, func() { p.pretty_export_csv_columns(msg) })
	if flat1284 != nil {
		p.write(*flat1284)
		return nil
	} else {
		fields1281 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1281) == 0) {
			p.newline()
			for i1283, elem1282 := range fields1281 {
				if (i1283 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1282)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_column(msg *pb.ExportCSVColumn) interface{} {
	flat1289 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1289 != nil {
		p.write(*flat1289)
		return nil
	} else {
		_t1696 := func(_dollar_dollar *pb.ExportCSVColumn) []interface{} {
			return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		}
		_t1697 := _t1696(msg)
		fields1285 := _t1697
		unwrapped_fields1286 := fields1285
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1287 := unwrapped_fields1286[0].(string)
		p.write(p.formatStringValue(field1287))
		p.newline()
		field1288 := unwrapped_fields1286[1].(*pb.RelationId)
		p.pretty_relation_id(field1288)
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
		_t1736 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1736)
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
		p.pretty_date(m)
	case *pb.DateTimeValue:
		p.pretty_datetime(m)
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
	case *pb.RelEDB:
		p.pretty_rel_edb(m)
	case []string:
		p.pretty_rel_edb_path(m)
	case []*pb.Type:
		p.pretty_rel_edb_types(m)
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
	case []*pb.CSVColumn:
		p.pretty_csv_columns(m)
	case *pb.CSVColumn:
		p.pretty_csv_column(m)
	case *pb.Undefine:
		p.pretty_undefine(m)
	case *pb.Context:
		p.pretty_context(m)
	case *pb.Snapshot:
		p.pretty_snapshot(m)
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
	case []*pb.ExportCSVColumn:
		p.pretty_export_csv_columns(m)
	case *pb.ExportCSVColumn:
		p.pretty_export_csv_column(m)
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
