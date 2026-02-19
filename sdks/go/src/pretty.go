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

	pb "logical-query-protocol/src/lqp/v1"
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
	_t1653 := &pb.Value{}
	_t1653.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t1653
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1654 := &pb.Value{}
	_t1654.Value = &pb.Value_IntValue{IntValue: v}
	return _t1654
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1655 := &pb.Value{}
	_t1655.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1655
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1656 := &pb.Value{}
	_t1656.Value = &pb.Value_StringValue{StringValue: v}
	return _t1656
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1657 := &pb.Value{}
	_t1657.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1657
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1658 := &pb.Value{}
	_t1658.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1658
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1659 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1659})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1660 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1660})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1661 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1661})
			}
		}
	}
	_t1662 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1662})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1663 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1663})
	_t1664 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1664})
	if msg.GetNewLine() != "" {
		_t1665 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1665})
	}
	_t1666 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1666})
	_t1667 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1667})
	_t1668 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1668})
	if msg.GetComment() != "" {
		_t1669 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1669})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1670 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1670})
	}
	_t1671 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1671})
	_t1672 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1672})
	_t1673 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1673})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1674 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1674})
	_t1675 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1675})
	_t1676 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1676})
	_t1677 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1677})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1678 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1678})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1679 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1679})
		}
	}
	_t1680 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1680})
	_t1681 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1681})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1682 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1682})
	}
	if msg.Compression != nil {
		_t1683 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1683})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1684 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1684})
	}
	if msg.SyntaxMissingString != nil {
		_t1685 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1685})
	}
	if msg.SyntaxDelim != nil {
		_t1686 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1686})
	}
	if msg.SyntaxQuotechar != nil {
		_t1687 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1687})
	}
	if msg.SyntaxEscapechar != nil {
		_t1688 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1688})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) *string {
	name := p.relationIdToString(msg)
	var _t1689 interface{}
	if name != nil {
		return ptr(*name)
	}
	_ = _t1689
	return nil
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1690 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1690
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
	flat638 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat638 != nil {
		p.write(*flat638)
		return nil
	} else {
		_t1258 := func(_dollar_dollar *pb.Transaction) []interface{} {
			var _t1259 *pb.Configure
			if hasProtoField(_dollar_dollar, "configure") {
				_t1259 = _dollar_dollar.GetConfigure()
			}
			var _t1260 *pb.Sync
			if hasProtoField(_dollar_dollar, "sync") {
				_t1260 = _dollar_dollar.GetSync()
			}
			return []interface{}{_t1259, _t1260, _dollar_dollar.GetEpochs()}
		}
		_t1261 := _t1258(msg)
		fields629 := _t1261
		unwrapped_fields630 := fields629
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field631 := unwrapped_fields630[0].(*pb.Configure)
		if field631 != nil {
			p.newline()
			opt_val632 := field631
			p.pretty_configure(opt_val632)
		}
		field633 := unwrapped_fields630[1].(*pb.Sync)
		if field633 != nil {
			p.newline()
			opt_val634 := field633
			p.pretty_sync(opt_val634)
		}
		field635 := unwrapped_fields630[2].([]*pb.Epoch)
		if !(len(field635) == 0) {
			p.newline()
			for i637, elem636 := range field635 {
				if (i637 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem636)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat641 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat641 != nil {
		p.write(*flat641)
		return nil
	} else {
		_t1262 := func(_dollar_dollar *pb.Configure) [][]interface{} {
			_t1263 := p.deconstruct_configure(_dollar_dollar)
			return _t1263
		}
		_t1264 := _t1262(msg)
		fields639 := _t1264
		unwrapped_fields640 := fields639
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields640)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat645 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat645 != nil {
		p.write(*flat645)
		return nil
	} else {
		fields642 := msg
		p.write("{")
		p.indent()
		if !(len(fields642) == 0) {
			p.newline()
			for i644, elem643 := range fields642 {
				if (i644 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem643)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat650 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat650 != nil {
		p.write(*flat650)
		return nil
	} else {
		_t1265 := func(_dollar_dollar []interface{}) []interface{} {
			return []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		}
		_t1266 := _t1265(msg)
		fields646 := _t1266
		unwrapped_fields647 := fields646
		p.write(":")
		field648 := unwrapped_fields647[0].(string)
		p.write(field648)
		p.write(" ")
		field649 := unwrapped_fields647[1].(*pb.Value)
		p.pretty_value(field649)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat670 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat670 != nil {
		p.write(*flat670)
		return nil
	} else {
		_t1267 := func(_dollar_dollar *pb.Value) *pb.DateValue {
			var _t1268 *pb.DateValue
			if hasProtoField(_dollar_dollar, "date_value") {
				_t1268 = _dollar_dollar.GetDateValue()
			}
			return _t1268
		}
		_t1269 := _t1267(msg)
		deconstruct_result668 := _t1269
		if deconstruct_result668 != nil {
			unwrapped669 := deconstruct_result668
			p.pretty_date(unwrapped669)
		} else {
			_t1270 := func(_dollar_dollar *pb.Value) *pb.DateTimeValue {
				var _t1271 *pb.DateTimeValue
				if hasProtoField(_dollar_dollar, "datetime_value") {
					_t1271 = _dollar_dollar.GetDatetimeValue()
				}
				return _t1271
			}
			_t1272 := _t1270(msg)
			deconstruct_result666 := _t1272
			if deconstruct_result666 != nil {
				unwrapped667 := deconstruct_result666
				p.pretty_datetime(unwrapped667)
			} else {
				_t1273 := func(_dollar_dollar *pb.Value) *string {
					var _t1274 *string
					if hasProtoField(_dollar_dollar, "string_value") {
						_t1274 = ptr(_dollar_dollar.GetStringValue())
					}
					return _t1274
				}
				_t1275 := _t1273(msg)
				deconstruct_result664 := _t1275
				if deconstruct_result664 != nil {
					unwrapped665 := *deconstruct_result664
					p.write(p.formatStringValue(unwrapped665))
				} else {
					_t1276 := func(_dollar_dollar *pb.Value) *int64 {
						var _t1277 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1277 = ptr(_dollar_dollar.GetIntValue())
						}
						return _t1277
					}
					_t1278 := _t1276(msg)
					deconstruct_result662 := _t1278
					if deconstruct_result662 != nil {
						unwrapped663 := *deconstruct_result662
						p.write(fmt.Sprintf("%d", unwrapped663))
					} else {
						_t1279 := func(_dollar_dollar *pb.Value) *float64 {
							var _t1280 *float64
							if hasProtoField(_dollar_dollar, "float_value") {
								_t1280 = ptr(_dollar_dollar.GetFloatValue())
							}
							return _t1280
						}
						_t1281 := _t1279(msg)
						deconstruct_result660 := _t1281
						if deconstruct_result660 != nil {
							unwrapped661 := *deconstruct_result660
							p.write(formatFloat64(unwrapped661))
						} else {
							_t1282 := func(_dollar_dollar *pb.Value) *pb.UInt128Value {
								var _t1283 *pb.UInt128Value
								if hasProtoField(_dollar_dollar, "uint128_value") {
									_t1283 = _dollar_dollar.GetUint128Value()
								}
								return _t1283
							}
							_t1284 := _t1282(msg)
							deconstruct_result658 := _t1284
							if deconstruct_result658 != nil {
								unwrapped659 := deconstruct_result658
								p.write(p.formatUint128(unwrapped659))
							} else {
								_t1285 := func(_dollar_dollar *pb.Value) *pb.Int128Value {
									var _t1286 *pb.Int128Value
									if hasProtoField(_dollar_dollar, "int128_value") {
										_t1286 = _dollar_dollar.GetInt128Value()
									}
									return _t1286
								}
								_t1287 := _t1285(msg)
								deconstruct_result656 := _t1287
								if deconstruct_result656 != nil {
									unwrapped657 := deconstruct_result656
									p.write(p.formatInt128(unwrapped657))
								} else {
									_t1288 := func(_dollar_dollar *pb.Value) *pb.DecimalValue {
										var _t1289 *pb.DecimalValue
										if hasProtoField(_dollar_dollar, "decimal_value") {
											_t1289 = _dollar_dollar.GetDecimalValue()
										}
										return _t1289
									}
									_t1290 := _t1288(msg)
									deconstruct_result654 := _t1290
									if deconstruct_result654 != nil {
										unwrapped655 := deconstruct_result654
										p.write(p.formatDecimal(unwrapped655))
									} else {
										_t1291 := func(_dollar_dollar *pb.Value) *bool {
											var _t1292 *bool
											if hasProtoField(_dollar_dollar, "boolean_value") {
												_t1292 = ptr(_dollar_dollar.GetBooleanValue())
											}
											return _t1292
										}
										_t1293 := _t1291(msg)
										deconstruct_result652 := _t1293
										if deconstruct_result652 != nil {
											unwrapped653 := *deconstruct_result652
											p.pretty_boolean_value(unwrapped653)
										} else {
											fields651 := msg
											_ = fields651
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
	flat676 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat676 != nil {
		p.write(*flat676)
		return nil
	} else {
		_t1294 := func(_dollar_dollar *pb.DateValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		}
		_t1295 := _t1294(msg)
		fields671 := _t1295
		unwrapped_fields672 := fields671
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field673 := unwrapped_fields672[0].(int64)
		p.write(fmt.Sprintf("%d", field673))
		p.newline()
		field674 := unwrapped_fields672[1].(int64)
		p.write(fmt.Sprintf("%d", field674))
		p.newline()
		field675 := unwrapped_fields672[2].(int64)
		p.write(fmt.Sprintf("%d", field675))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat687 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat687 != nil {
		p.write(*flat687)
		return nil
	} else {
		_t1296 := func(_dollar_dollar *pb.DateTimeValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		}
		_t1297 := _t1296(msg)
		fields677 := _t1297
		unwrapped_fields678 := fields677
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field679 := unwrapped_fields678[0].(int64)
		p.write(fmt.Sprintf("%d", field679))
		p.newline()
		field680 := unwrapped_fields678[1].(int64)
		p.write(fmt.Sprintf("%d", field680))
		p.newline()
		field681 := unwrapped_fields678[2].(int64)
		p.write(fmt.Sprintf("%d", field681))
		p.newline()
		field682 := unwrapped_fields678[3].(int64)
		p.write(fmt.Sprintf("%d", field682))
		p.newline()
		field683 := unwrapped_fields678[4].(int64)
		p.write(fmt.Sprintf("%d", field683))
		p.newline()
		field684 := unwrapped_fields678[5].(int64)
		p.write(fmt.Sprintf("%d", field684))
		field685 := unwrapped_fields678[6].(*int64)
		if field685 != nil {
			p.newline()
			opt_val686 := *field685
			p.write(fmt.Sprintf("%d", opt_val686))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_t1298 := func(_dollar_dollar bool) []interface{} {
		var _t1299 []interface{}
		if _dollar_dollar {
			_t1299 = []interface{}{}
		}
		return _t1299
	}
	_t1300 := _t1298(msg)
	deconstruct_result690 := _t1300
	if deconstruct_result690 != nil {
		unwrapped691 := deconstruct_result690
		_ = unwrapped691
		p.write("true")
	} else {
		_t1301 := func(_dollar_dollar bool) []interface{} {
			var _t1302 []interface{}
			if !(_dollar_dollar) {
				_t1302 = []interface{}{}
			}
			return _t1302
		}
		_t1303 := _t1301(msg)
		deconstruct_result688 := _t1303
		if deconstruct_result688 != nil {
			unwrapped689 := deconstruct_result688
			_ = unwrapped689
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat696 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat696 != nil {
		p.write(*flat696)
		return nil
	} else {
		_t1304 := func(_dollar_dollar *pb.Sync) []*pb.FragmentId {
			return _dollar_dollar.GetFragments()
		}
		_t1305 := _t1304(msg)
		fields692 := _t1305
		unwrapped_fields693 := fields692
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields693) == 0) {
			p.newline()
			for i695, elem694 := range unwrapped_fields693 {
				if (i695 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem694)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat699 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat699 != nil {
		p.write(*flat699)
		return nil
	} else {
		_t1306 := func(_dollar_dollar *pb.FragmentId) string {
			return p.fragmentIdToString(_dollar_dollar)
		}
		_t1307 := _t1306(msg)
		fields697 := _t1307
		unwrapped_fields698 := fields697
		p.write(":")
		p.write(unwrapped_fields698)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat706 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat706 != nil {
		p.write(*flat706)
		return nil
	} else {
		_t1308 := func(_dollar_dollar *pb.Epoch) []interface{} {
			var _t1309 []*pb.Write
			if !(len(_dollar_dollar.GetWrites()) == 0) {
				_t1309 = _dollar_dollar.GetWrites()
			}
			var _t1310 []*pb.Read
			if !(len(_dollar_dollar.GetReads()) == 0) {
				_t1310 = _dollar_dollar.GetReads()
			}
			return []interface{}{_t1309, _t1310}
		}
		_t1311 := _t1308(msg)
		fields700 := _t1311
		unwrapped_fields701 := fields700
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field702 := unwrapped_fields701[0].([]*pb.Write)
		if field702 != nil {
			p.newline()
			opt_val703 := field702
			p.pretty_epoch_writes(opt_val703)
		}
		field704 := unwrapped_fields701[1].([]*pb.Read)
		if field704 != nil {
			p.newline()
			opt_val705 := field704
			p.pretty_epoch_reads(opt_val705)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat710 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat710 != nil {
		p.write(*flat710)
		return nil
	} else {
		fields707 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields707) == 0) {
			p.newline()
			for i709, elem708 := range fields707 {
				if (i709 > 0) {
					p.newline()
				}
				p.pretty_write(elem708)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat719 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat719 != nil {
		p.write(*flat719)
		return nil
	} else {
		_t1312 := func(_dollar_dollar *pb.Write) *pb.Define {
			var _t1313 *pb.Define
			if hasProtoField(_dollar_dollar, "define") {
				_t1313 = _dollar_dollar.GetDefine()
			}
			return _t1313
		}
		_t1314 := _t1312(msg)
		deconstruct_result717 := _t1314
		if deconstruct_result717 != nil {
			unwrapped718 := deconstruct_result717
			p.pretty_define(unwrapped718)
		} else {
			_t1315 := func(_dollar_dollar *pb.Write) *pb.Undefine {
				var _t1316 *pb.Undefine
				if hasProtoField(_dollar_dollar, "undefine") {
					_t1316 = _dollar_dollar.GetUndefine()
				}
				return _t1316
			}
			_t1317 := _t1315(msg)
			deconstruct_result715 := _t1317
			if deconstruct_result715 != nil {
				unwrapped716 := deconstruct_result715
				p.pretty_undefine(unwrapped716)
			} else {
				_t1318 := func(_dollar_dollar *pb.Write) *pb.Context {
					var _t1319 *pb.Context
					if hasProtoField(_dollar_dollar, "context") {
						_t1319 = _dollar_dollar.GetContext()
					}
					return _t1319
				}
				_t1320 := _t1318(msg)
				deconstruct_result713 := _t1320
				if deconstruct_result713 != nil {
					unwrapped714 := deconstruct_result713
					p.pretty_context(unwrapped714)
				} else {
					_t1321 := func(_dollar_dollar *pb.Write) *pb.Snapshot {
						var _t1322 *pb.Snapshot
						if hasProtoField(_dollar_dollar, "snapshot") {
							_t1322 = _dollar_dollar.GetSnapshot()
						}
						return _t1322
					}
					_t1323 := _t1321(msg)
					deconstruct_result711 := _t1323
					if deconstruct_result711 != nil {
						unwrapped712 := deconstruct_result711
						p.pretty_snapshot(unwrapped712)
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
	flat722 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat722 != nil {
		p.write(*flat722)
		return nil
	} else {
		_t1324 := func(_dollar_dollar *pb.Define) *pb.Fragment {
			return _dollar_dollar.GetFragment()
		}
		_t1325 := _t1324(msg)
		fields720 := _t1325
		unwrapped_fields721 := fields720
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields721)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat729 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat729 != nil {
		p.write(*flat729)
		return nil
	} else {
		_t1326 := func(_dollar_dollar *pb.Fragment) []interface{} {
			p.startPrettyFragment(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		}
		_t1327 := _t1326(msg)
		fields723 := _t1327
		unwrapped_fields724 := fields723
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field725 := unwrapped_fields724[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field725)
		field726 := unwrapped_fields724[1].([]*pb.Declaration)
		if !(len(field726) == 0) {
			p.newline()
			for i728, elem727 := range field726 {
				if (i728 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem727)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat731 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat731 != nil {
		p.write(*flat731)
		return nil
	} else {
		fields730 := msg
		p.pretty_fragment_id(fields730)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat740 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat740 != nil {
		p.write(*flat740)
		return nil
	} else {
		_t1328 := func(_dollar_dollar *pb.Declaration) *pb.Def {
			var _t1329 *pb.Def
			if hasProtoField(_dollar_dollar, "def") {
				_t1329 = _dollar_dollar.GetDef()
			}
			return _t1329
		}
		_t1330 := _t1328(msg)
		deconstruct_result738 := _t1330
		if deconstruct_result738 != nil {
			unwrapped739 := deconstruct_result738
			p.pretty_def(unwrapped739)
		} else {
			_t1331 := func(_dollar_dollar *pb.Declaration) *pb.Algorithm {
				var _t1332 *pb.Algorithm
				if hasProtoField(_dollar_dollar, "algorithm") {
					_t1332 = _dollar_dollar.GetAlgorithm()
				}
				return _t1332
			}
			_t1333 := _t1331(msg)
			deconstruct_result736 := _t1333
			if deconstruct_result736 != nil {
				unwrapped737 := deconstruct_result736
				p.pretty_algorithm(unwrapped737)
			} else {
				_t1334 := func(_dollar_dollar *pb.Declaration) *pb.Constraint {
					var _t1335 *pb.Constraint
					if hasProtoField(_dollar_dollar, "constraint") {
						_t1335 = _dollar_dollar.GetConstraint()
					}
					return _t1335
				}
				_t1336 := _t1334(msg)
				deconstruct_result734 := _t1336
				if deconstruct_result734 != nil {
					unwrapped735 := deconstruct_result734
					p.pretty_constraint(unwrapped735)
				} else {
					_t1337 := func(_dollar_dollar *pb.Declaration) *pb.Data {
						var _t1338 *pb.Data
						if hasProtoField(_dollar_dollar, "data") {
							_t1338 = _dollar_dollar.GetData()
						}
						return _t1338
					}
					_t1339 := _t1337(msg)
					deconstruct_result732 := _t1339
					if deconstruct_result732 != nil {
						unwrapped733 := deconstruct_result732
						p.pretty_data(unwrapped733)
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
	flat747 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat747 != nil {
		p.write(*flat747)
		return nil
	} else {
		_t1340 := func(_dollar_dollar *pb.Def) []interface{} {
			var _t1341 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1341 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1341}
		}
		_t1342 := _t1340(msg)
		fields741 := _t1342
		unwrapped_fields742 := fields741
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field743 := unwrapped_fields742[0].(*pb.RelationId)
		p.pretty_relation_id(field743)
		p.newline()
		field744 := unwrapped_fields742[1].(*pb.Abstraction)
		p.pretty_abstraction(field744)
		field745 := unwrapped_fields742[2].([]*pb.Attribute)
		if field745 != nil {
			p.newline()
			opt_val746 := field745
			p.pretty_attrs(opt_val746)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat752 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat752 != nil {
		p.write(*flat752)
		return nil
	} else {
		_t1343 := func(_dollar_dollar *pb.RelationId) *string {
			_t1344 := p.deconstruct_relation_id_string(_dollar_dollar)
			return _t1344
		}
		_t1345 := _t1343(msg)
		deconstruct_result750 := _t1345
		if deconstruct_result750 != nil {
			unwrapped751 := *deconstruct_result750
			p.write(":")
			p.write(unwrapped751)
		} else {
			_t1346 := func(_dollar_dollar *pb.RelationId) *pb.UInt128Value {
				_t1347 := p.deconstruct_relation_id_uint128(_dollar_dollar)
				return _t1347
			}
			_t1348 := _t1346(msg)
			deconstruct_result748 := _t1348
			if deconstruct_result748 != nil {
				unwrapped749 := deconstruct_result748
				p.write(p.formatUint128(unwrapped749))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat757 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat757 != nil {
		p.write(*flat757)
		return nil
	} else {
		_t1349 := func(_dollar_dollar *pb.Abstraction) []interface{} {
			_t1350 := p.deconstruct_bindings(_dollar_dollar)
			return []interface{}{_t1350, _dollar_dollar.GetValue()}
		}
		_t1351 := _t1349(msg)
		fields753 := _t1351
		unwrapped_fields754 := fields753
		p.write("(")
		p.indent()
		field755 := unwrapped_fields754[0].([]interface{})
		p.pretty_bindings(field755)
		p.newline()
		field756 := unwrapped_fields754[1].(*pb.Formula)
		p.pretty_formula(field756)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat765 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat765 != nil {
		p.write(*flat765)
		return nil
	} else {
		_t1352 := func(_dollar_dollar []interface{}) []interface{} {
			var _t1353 []*pb.Binding
			if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
				_t1353 = _dollar_dollar[1].([]*pb.Binding)
			}
			return []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1353}
		}
		_t1354 := _t1352(msg)
		fields758 := _t1354
		unwrapped_fields759 := fields758
		p.write("[")
		p.indent()
		field760 := unwrapped_fields759[0].([]*pb.Binding)
		for i762, elem761 := range field760 {
			if (i762 > 0) {
				p.newline()
			}
			p.pretty_binding(elem761)
		}
		field763 := unwrapped_fields759[1].([]*pb.Binding)
		if field763 != nil {
			p.newline()
			opt_val764 := field763
			p.pretty_value_bindings(opt_val764)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat770 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat770 != nil {
		p.write(*flat770)
		return nil
	} else {
		_t1355 := func(_dollar_dollar *pb.Binding) []interface{} {
			return []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		}
		_t1356 := _t1355(msg)
		fields766 := _t1356
		unwrapped_fields767 := fields766
		field768 := unwrapped_fields767[0].(string)
		p.write(field768)
		p.write("::")
		field769 := unwrapped_fields767[1].(*pb.Type)
		p.pretty_type(field769)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat793 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat793 != nil {
		p.write(*flat793)
		return nil
	} else {
		_t1357 := func(_dollar_dollar *pb.Type) *pb.UnspecifiedType {
			var _t1358 *pb.UnspecifiedType
			if hasProtoField(_dollar_dollar, "unspecified_type") {
				_t1358 = _dollar_dollar.GetUnspecifiedType()
			}
			return _t1358
		}
		_t1359 := _t1357(msg)
		deconstruct_result791 := _t1359
		if deconstruct_result791 != nil {
			unwrapped792 := deconstruct_result791
			p.pretty_unspecified_type(unwrapped792)
		} else {
			_t1360 := func(_dollar_dollar *pb.Type) *pb.StringType {
				var _t1361 *pb.StringType
				if hasProtoField(_dollar_dollar, "string_type") {
					_t1361 = _dollar_dollar.GetStringType()
				}
				return _t1361
			}
			_t1362 := _t1360(msg)
			deconstruct_result789 := _t1362
			if deconstruct_result789 != nil {
				unwrapped790 := deconstruct_result789
				p.pretty_string_type(unwrapped790)
			} else {
				_t1363 := func(_dollar_dollar *pb.Type) *pb.IntType {
					var _t1364 *pb.IntType
					if hasProtoField(_dollar_dollar, "int_type") {
						_t1364 = _dollar_dollar.GetIntType()
					}
					return _t1364
				}
				_t1365 := _t1363(msg)
				deconstruct_result787 := _t1365
				if deconstruct_result787 != nil {
					unwrapped788 := deconstruct_result787
					p.pretty_int_type(unwrapped788)
				} else {
					_t1366 := func(_dollar_dollar *pb.Type) *pb.FloatType {
						var _t1367 *pb.FloatType
						if hasProtoField(_dollar_dollar, "float_type") {
							_t1367 = _dollar_dollar.GetFloatType()
						}
						return _t1367
					}
					_t1368 := _t1366(msg)
					deconstruct_result785 := _t1368
					if deconstruct_result785 != nil {
						unwrapped786 := deconstruct_result785
						p.pretty_float_type(unwrapped786)
					} else {
						_t1369 := func(_dollar_dollar *pb.Type) *pb.UInt128Type {
							var _t1370 *pb.UInt128Type
							if hasProtoField(_dollar_dollar, "uint128_type") {
								_t1370 = _dollar_dollar.GetUint128Type()
							}
							return _t1370
						}
						_t1371 := _t1369(msg)
						deconstruct_result783 := _t1371
						if deconstruct_result783 != nil {
							unwrapped784 := deconstruct_result783
							p.pretty_uint128_type(unwrapped784)
						} else {
							_t1372 := func(_dollar_dollar *pb.Type) *pb.Int128Type {
								var _t1373 *pb.Int128Type
								if hasProtoField(_dollar_dollar, "int128_type") {
									_t1373 = _dollar_dollar.GetInt128Type()
								}
								return _t1373
							}
							_t1374 := _t1372(msg)
							deconstruct_result781 := _t1374
							if deconstruct_result781 != nil {
								unwrapped782 := deconstruct_result781
								p.pretty_int128_type(unwrapped782)
							} else {
								_t1375 := func(_dollar_dollar *pb.Type) *pb.DateType {
									var _t1376 *pb.DateType
									if hasProtoField(_dollar_dollar, "date_type") {
										_t1376 = _dollar_dollar.GetDateType()
									}
									return _t1376
								}
								_t1377 := _t1375(msg)
								deconstruct_result779 := _t1377
								if deconstruct_result779 != nil {
									unwrapped780 := deconstruct_result779
									p.pretty_date_type(unwrapped780)
								} else {
									_t1378 := func(_dollar_dollar *pb.Type) *pb.DateTimeType {
										var _t1379 *pb.DateTimeType
										if hasProtoField(_dollar_dollar, "datetime_type") {
											_t1379 = _dollar_dollar.GetDatetimeType()
										}
										return _t1379
									}
									_t1380 := _t1378(msg)
									deconstruct_result777 := _t1380
									if deconstruct_result777 != nil {
										unwrapped778 := deconstruct_result777
										p.pretty_datetime_type(unwrapped778)
									} else {
										_t1381 := func(_dollar_dollar *pb.Type) *pb.MissingType {
											var _t1382 *pb.MissingType
											if hasProtoField(_dollar_dollar, "missing_type") {
												_t1382 = _dollar_dollar.GetMissingType()
											}
											return _t1382
										}
										_t1383 := _t1381(msg)
										deconstruct_result775 := _t1383
										if deconstruct_result775 != nil {
											unwrapped776 := deconstruct_result775
											p.pretty_missing_type(unwrapped776)
										} else {
											_t1384 := func(_dollar_dollar *pb.Type) *pb.DecimalType {
												var _t1385 *pb.DecimalType
												if hasProtoField(_dollar_dollar, "decimal_type") {
													_t1385 = _dollar_dollar.GetDecimalType()
												}
												return _t1385
											}
											_t1386 := _t1384(msg)
											deconstruct_result773 := _t1386
											if deconstruct_result773 != nil {
												unwrapped774 := deconstruct_result773
												p.pretty_decimal_type(unwrapped774)
											} else {
												_t1387 := func(_dollar_dollar *pb.Type) *pb.BooleanType {
													var _t1388 *pb.BooleanType
													if hasProtoField(_dollar_dollar, "boolean_type") {
														_t1388 = _dollar_dollar.GetBooleanType()
													}
													return _t1388
												}
												_t1389 := _t1387(msg)
												deconstruct_result771 := _t1389
												if deconstruct_result771 != nil {
													unwrapped772 := deconstruct_result771
													p.pretty_boolean_type(unwrapped772)
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
	fields794 := msg
	_ = fields794
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields795 := msg
	_ = fields795
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields796 := msg
	_ = fields796
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields797 := msg
	_ = fields797
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields798 := msg
	_ = fields798
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields799 := msg
	_ = fields799
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields800 := msg
	_ = fields800
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields801 := msg
	_ = fields801
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields802 := msg
	_ = fields802
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat807 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat807 != nil {
		p.write(*flat807)
		return nil
	} else {
		_t1390 := func(_dollar_dollar *pb.DecimalType) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		}
		_t1391 := _t1390(msg)
		fields803 := _t1391
		unwrapped_fields804 := fields803
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field805 := unwrapped_fields804[0].(int64)
		p.write(fmt.Sprintf("%d", field805))
		p.newline()
		field806 := unwrapped_fields804[1].(int64)
		p.write(fmt.Sprintf("%d", field806))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields808 := msg
	_ = fields808
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat812 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat812 != nil {
		p.write(*flat812)
		return nil
	} else {
		fields809 := msg
		p.write("|")
		if !(len(fields809) == 0) {
			p.write(" ")
			for i811, elem810 := range fields809 {
				if (i811 > 0) {
					p.newline()
				}
				p.pretty_binding(elem810)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat839 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat839 != nil {
		p.write(*flat839)
		return nil
	} else {
		_t1392 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
			var _t1393 *pb.Conjunction
			if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
				_t1393 = _dollar_dollar.GetConjunction()
			}
			return _t1393
		}
		_t1394 := _t1392(msg)
		deconstruct_result837 := _t1394
		if deconstruct_result837 != nil {
			unwrapped838 := deconstruct_result837
			p.pretty_true(unwrapped838)
		} else {
			_t1395 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
				var _t1396 *pb.Disjunction
				if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
					_t1396 = _dollar_dollar.GetDisjunction()
				}
				return _t1396
			}
			_t1397 := _t1395(msg)
			deconstruct_result835 := _t1397
			if deconstruct_result835 != nil {
				unwrapped836 := deconstruct_result835
				p.pretty_false(unwrapped836)
			} else {
				_t1398 := func(_dollar_dollar *pb.Formula) *pb.Exists {
					var _t1399 *pb.Exists
					if hasProtoField(_dollar_dollar, "exists") {
						_t1399 = _dollar_dollar.GetExists()
					}
					return _t1399
				}
				_t1400 := _t1398(msg)
				deconstruct_result833 := _t1400
				if deconstruct_result833 != nil {
					unwrapped834 := deconstruct_result833
					p.pretty_exists(unwrapped834)
				} else {
					_t1401 := func(_dollar_dollar *pb.Formula) *pb.Reduce {
						var _t1402 *pb.Reduce
						if hasProtoField(_dollar_dollar, "reduce") {
							_t1402 = _dollar_dollar.GetReduce()
						}
						return _t1402
					}
					_t1403 := _t1401(msg)
					deconstruct_result831 := _t1403
					if deconstruct_result831 != nil {
						unwrapped832 := deconstruct_result831
						p.pretty_reduce(unwrapped832)
					} else {
						_t1404 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
							var _t1405 *pb.Conjunction
							if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
								_t1405 = _dollar_dollar.GetConjunction()
							}
							return _t1405
						}
						_t1406 := _t1404(msg)
						deconstruct_result829 := _t1406
						if deconstruct_result829 != nil {
							unwrapped830 := deconstruct_result829
							p.pretty_conjunction(unwrapped830)
						} else {
							_t1407 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
								var _t1408 *pb.Disjunction
								if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
									_t1408 = _dollar_dollar.GetDisjunction()
								}
								return _t1408
							}
							_t1409 := _t1407(msg)
							deconstruct_result827 := _t1409
							if deconstruct_result827 != nil {
								unwrapped828 := deconstruct_result827
								p.pretty_disjunction(unwrapped828)
							} else {
								_t1410 := func(_dollar_dollar *pb.Formula) *pb.Not {
									var _t1411 *pb.Not
									if hasProtoField(_dollar_dollar, "not") {
										_t1411 = _dollar_dollar.GetNot()
									}
									return _t1411
								}
								_t1412 := _t1410(msg)
								deconstruct_result825 := _t1412
								if deconstruct_result825 != nil {
									unwrapped826 := deconstruct_result825
									p.pretty_not(unwrapped826)
								} else {
									_t1413 := func(_dollar_dollar *pb.Formula) *pb.FFI {
										var _t1414 *pb.FFI
										if hasProtoField(_dollar_dollar, "ffi") {
											_t1414 = _dollar_dollar.GetFfi()
										}
										return _t1414
									}
									_t1415 := _t1413(msg)
									deconstruct_result823 := _t1415
									if deconstruct_result823 != nil {
										unwrapped824 := deconstruct_result823
										p.pretty_ffi(unwrapped824)
									} else {
										_t1416 := func(_dollar_dollar *pb.Formula) *pb.Atom {
											var _t1417 *pb.Atom
											if hasProtoField(_dollar_dollar, "atom") {
												_t1417 = _dollar_dollar.GetAtom()
											}
											return _t1417
										}
										_t1418 := _t1416(msg)
										deconstruct_result821 := _t1418
										if deconstruct_result821 != nil {
											unwrapped822 := deconstruct_result821
											p.pretty_atom(unwrapped822)
										} else {
											_t1419 := func(_dollar_dollar *pb.Formula) *pb.Pragma {
												var _t1420 *pb.Pragma
												if hasProtoField(_dollar_dollar, "pragma") {
													_t1420 = _dollar_dollar.GetPragma()
												}
												return _t1420
											}
											_t1421 := _t1419(msg)
											deconstruct_result819 := _t1421
											if deconstruct_result819 != nil {
												unwrapped820 := deconstruct_result819
												p.pretty_pragma(unwrapped820)
											} else {
												_t1422 := func(_dollar_dollar *pb.Formula) *pb.Primitive {
													var _t1423 *pb.Primitive
													if hasProtoField(_dollar_dollar, "primitive") {
														_t1423 = _dollar_dollar.GetPrimitive()
													}
													return _t1423
												}
												_t1424 := _t1422(msg)
												deconstruct_result817 := _t1424
												if deconstruct_result817 != nil {
													unwrapped818 := deconstruct_result817
													p.pretty_primitive(unwrapped818)
												} else {
													_t1425 := func(_dollar_dollar *pb.Formula) *pb.RelAtom {
														var _t1426 *pb.RelAtom
														if hasProtoField(_dollar_dollar, "rel_atom") {
															_t1426 = _dollar_dollar.GetRelAtom()
														}
														return _t1426
													}
													_t1427 := _t1425(msg)
													deconstruct_result815 := _t1427
													if deconstruct_result815 != nil {
														unwrapped816 := deconstruct_result815
														p.pretty_rel_atom(unwrapped816)
													} else {
														_t1428 := func(_dollar_dollar *pb.Formula) *pb.Cast {
															var _t1429 *pb.Cast
															if hasProtoField(_dollar_dollar, "cast") {
																_t1429 = _dollar_dollar.GetCast()
															}
															return _t1429
														}
														_t1430 := _t1428(msg)
														deconstruct_result813 := _t1430
														if deconstruct_result813 != nil {
															unwrapped814 := deconstruct_result813
															p.pretty_cast(unwrapped814)
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
	fields840 := msg
	_ = fields840
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields841 := msg
	_ = fields841
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat846 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat846 != nil {
		p.write(*flat846)
		return nil
	} else {
		_t1431 := func(_dollar_dollar *pb.Exists) []interface{} {
			_t1432 := p.deconstruct_bindings(_dollar_dollar.GetBody())
			return []interface{}{_t1432, _dollar_dollar.GetBody().GetValue()}
		}
		_t1433 := _t1431(msg)
		fields842 := _t1433
		unwrapped_fields843 := fields842
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field844 := unwrapped_fields843[0].([]interface{})
		p.pretty_bindings(field844)
		p.newline()
		field845 := unwrapped_fields843[1].(*pb.Formula)
		p.pretty_formula(field845)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat852 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat852 != nil {
		p.write(*flat852)
		return nil
	} else {
		_t1434 := func(_dollar_dollar *pb.Reduce) []interface{} {
			return []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		}
		_t1435 := _t1434(msg)
		fields847 := _t1435
		unwrapped_fields848 := fields847
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field849 := unwrapped_fields848[0].(*pb.Abstraction)
		p.pretty_abstraction(field849)
		p.newline()
		field850 := unwrapped_fields848[1].(*pb.Abstraction)
		p.pretty_abstraction(field850)
		p.newline()
		field851 := unwrapped_fields848[2].([]*pb.Term)
		p.pretty_terms(field851)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat856 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat856 != nil {
		p.write(*flat856)
		return nil
	} else {
		fields853 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields853) == 0) {
			p.newline()
			for i855, elem854 := range fields853 {
				if (i855 > 0) {
					p.newline()
				}
				p.pretty_term(elem854)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat861 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat861 != nil {
		p.write(*flat861)
		return nil
	} else {
		_t1436 := func(_dollar_dollar *pb.Term) *pb.Var {
			var _t1437 *pb.Var
			if hasProtoField(_dollar_dollar, "var") {
				_t1437 = _dollar_dollar.GetVar()
			}
			return _t1437
		}
		_t1438 := _t1436(msg)
		deconstruct_result859 := _t1438
		if deconstruct_result859 != nil {
			unwrapped860 := deconstruct_result859
			p.pretty_var(unwrapped860)
		} else {
			_t1439 := func(_dollar_dollar *pb.Term) *pb.Value {
				var _t1440 *pb.Value
				if hasProtoField(_dollar_dollar, "constant") {
					_t1440 = _dollar_dollar.GetConstant()
				}
				return _t1440
			}
			_t1441 := _t1439(msg)
			deconstruct_result857 := _t1441
			if deconstruct_result857 != nil {
				unwrapped858 := deconstruct_result857
				p.pretty_constant(unwrapped858)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat864 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat864 != nil {
		p.write(*flat864)
		return nil
	} else {
		_t1442 := func(_dollar_dollar *pb.Var) string {
			return _dollar_dollar.GetName()
		}
		_t1443 := _t1442(msg)
		fields862 := _t1443
		unwrapped_fields863 := fields862
		p.write(unwrapped_fields863)
	}
	return nil
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) interface{} {
	flat866 := p.tryFlat(msg, func() { p.pretty_constant(msg) })
	if flat866 != nil {
		p.write(*flat866)
		return nil
	} else {
		fields865 := msg
		p.pretty_value(fields865)
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat871 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat871 != nil {
		p.write(*flat871)
		return nil
	} else {
		_t1444 := func(_dollar_dollar *pb.Conjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1445 := _t1444(msg)
		fields867 := _t1445
		unwrapped_fields868 := fields867
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields868) == 0) {
			p.newline()
			for i870, elem869 := range unwrapped_fields868 {
				if (i870 > 0) {
					p.newline()
				}
				p.pretty_formula(elem869)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat876 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat876 != nil {
		p.write(*flat876)
		return nil
	} else {
		_t1446 := func(_dollar_dollar *pb.Disjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1447 := _t1446(msg)
		fields872 := _t1447
		unwrapped_fields873 := fields872
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields873) == 0) {
			p.newline()
			for i875, elem874 := range unwrapped_fields873 {
				if (i875 > 0) {
					p.newline()
				}
				p.pretty_formula(elem874)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat879 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat879 != nil {
		p.write(*flat879)
		return nil
	} else {
		_t1448 := func(_dollar_dollar *pb.Not) *pb.Formula {
			return _dollar_dollar.GetArg()
		}
		_t1449 := _t1448(msg)
		fields877 := _t1449
		unwrapped_fields878 := fields877
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields878)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat885 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat885 != nil {
		p.write(*flat885)
		return nil
	} else {
		_t1450 := func(_dollar_dollar *pb.FFI) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		}
		_t1451 := _t1450(msg)
		fields880 := _t1451
		unwrapped_fields881 := fields880
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field882 := unwrapped_fields881[0].(string)
		p.pretty_name(field882)
		p.newline()
		field883 := unwrapped_fields881[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field883)
		p.newline()
		field884 := unwrapped_fields881[2].([]*pb.Term)
		p.pretty_terms(field884)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat887 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat887 != nil {
		p.write(*flat887)
		return nil
	} else {
		fields886 := msg
		p.write(":")
		p.write(fields886)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat891 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat891 != nil {
		p.write(*flat891)
		return nil
	} else {
		fields888 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields888) == 0) {
			p.newline()
			for i890, elem889 := range fields888 {
				if (i890 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem889)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat898 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat898 != nil {
		p.write(*flat898)
		return nil
	} else {
		_t1452 := func(_dollar_dollar *pb.Atom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1453 := _t1452(msg)
		fields892 := _t1453
		unwrapped_fields893 := fields892
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field894 := unwrapped_fields893[0].(*pb.RelationId)
		p.pretty_relation_id(field894)
		field895 := unwrapped_fields893[1].([]*pb.Term)
		if !(len(field895) == 0) {
			p.newline()
			for i897, elem896 := range field895 {
				if (i897 > 0) {
					p.newline()
				}
				p.pretty_term(elem896)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat905 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat905 != nil {
		p.write(*flat905)
		return nil
	} else {
		_t1454 := func(_dollar_dollar *pb.Pragma) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1455 := _t1454(msg)
		fields899 := _t1455
		unwrapped_fields900 := fields899
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field901 := unwrapped_fields900[0].(string)
		p.pretty_name(field901)
		field902 := unwrapped_fields900[1].([]*pb.Term)
		if !(len(field902) == 0) {
			p.newline()
			for i904, elem903 := range field902 {
				if (i904 > 0) {
					p.newline()
				}
				p.pretty_term(elem903)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat921 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat921 != nil {
		p.write(*flat921)
		return nil
	} else {
		_t1456 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1457 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1457 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1457
		}
		_t1458 := _t1456(msg)
		guard_result920 := _t1458
		if guard_result920 != nil {
			p.pretty_eq(msg)
		} else {
			_t1459 := func(_dollar_dollar *pb.Primitive) []interface{} {
				var _t1460 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
					_t1460 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				return _t1460
			}
			_t1461 := _t1459(msg)
			guard_result919 := _t1461
			if guard_result919 != nil {
				p.pretty_lt(msg)
			} else {
				_t1462 := func(_dollar_dollar *pb.Primitive) []interface{} {
					var _t1463 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
						_t1463 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					return _t1463
				}
				_t1464 := _t1462(msg)
				guard_result918 := _t1464
				if guard_result918 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_t1465 := func(_dollar_dollar *pb.Primitive) []interface{} {
						var _t1466 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
							_t1466 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						return _t1466
					}
					_t1467 := _t1465(msg)
					guard_result917 := _t1467
					if guard_result917 != nil {
						p.pretty_gt(msg)
					} else {
						_t1468 := func(_dollar_dollar *pb.Primitive) []interface{} {
							var _t1469 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
								_t1469 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
							}
							return _t1469
						}
						_t1470 := _t1468(msg)
						guard_result916 := _t1470
						if guard_result916 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_t1471 := func(_dollar_dollar *pb.Primitive) []interface{} {
								var _t1472 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
									_t1472 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								return _t1472
							}
							_t1473 := _t1471(msg)
							guard_result915 := _t1473
							if guard_result915 != nil {
								p.pretty_add(msg)
							} else {
								_t1474 := func(_dollar_dollar *pb.Primitive) []interface{} {
									var _t1475 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
										_t1475 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									return _t1475
								}
								_t1476 := _t1474(msg)
								guard_result914 := _t1476
								if guard_result914 != nil {
									p.pretty_minus(msg)
								} else {
									_t1477 := func(_dollar_dollar *pb.Primitive) []interface{} {
										var _t1478 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
											_t1478 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										return _t1478
									}
									_t1479 := _t1477(msg)
									guard_result913 := _t1479
									if guard_result913 != nil {
										p.pretty_multiply(msg)
									} else {
										_t1480 := func(_dollar_dollar *pb.Primitive) []interface{} {
											var _t1481 []interface{}
											if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
												_t1481 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
											}
											return _t1481
										}
										_t1482 := _t1480(msg)
										guard_result912 := _t1482
										if guard_result912 != nil {
											p.pretty_divide(msg)
										} else {
											_t1483 := func(_dollar_dollar *pb.Primitive) []interface{} {
												return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											}
											_t1484 := _t1483(msg)
											fields906 := _t1484
											unwrapped_fields907 := fields906
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field908 := unwrapped_fields907[0].(string)
											p.pretty_name(field908)
											field909 := unwrapped_fields907[1].([]*pb.RelTerm)
											if !(len(field909) == 0) {
												p.newline()
												for i911, elem910 := range field909 {
													if (i911 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem910)
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
	flat926 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat926 != nil {
		p.write(*flat926)
		return nil
	} else {
		_t1485 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1486 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1486 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1486
		}
		_t1487 := _t1485(msg)
		fields922 := _t1487
		unwrapped_fields923 := fields922
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field924 := unwrapped_fields923[0].(*pb.Term)
		p.pretty_term(field924)
		p.newline()
		field925 := unwrapped_fields923[1].(*pb.Term)
		p.pretty_term(field925)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat931 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat931 != nil {
		p.write(*flat931)
		return nil
	} else {
		_t1488 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1489 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1489 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1489
		}
		_t1490 := _t1488(msg)
		fields927 := _t1490
		unwrapped_fields928 := fields927
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field929 := unwrapped_fields928[0].(*pb.Term)
		p.pretty_term(field929)
		p.newline()
		field930 := unwrapped_fields928[1].(*pb.Term)
		p.pretty_term(field930)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat936 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat936 != nil {
		p.write(*flat936)
		return nil
	} else {
		_t1491 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1492 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
				_t1492 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1492
		}
		_t1493 := _t1491(msg)
		fields932 := _t1493
		unwrapped_fields933 := fields932
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field934 := unwrapped_fields933[0].(*pb.Term)
		p.pretty_term(field934)
		p.newline()
		field935 := unwrapped_fields933[1].(*pb.Term)
		p.pretty_term(field935)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat941 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat941 != nil {
		p.write(*flat941)
		return nil
	} else {
		_t1494 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1495 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
				_t1495 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1495
		}
		_t1496 := _t1494(msg)
		fields937 := _t1496
		unwrapped_fields938 := fields937
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field939 := unwrapped_fields938[0].(*pb.Term)
		p.pretty_term(field939)
		p.newline()
		field940 := unwrapped_fields938[1].(*pb.Term)
		p.pretty_term(field940)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat946 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat946 != nil {
		p.write(*flat946)
		return nil
	} else {
		_t1497 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1498 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
				_t1498 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1498
		}
		_t1499 := _t1497(msg)
		fields942 := _t1499
		unwrapped_fields943 := fields942
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field944 := unwrapped_fields943[0].(*pb.Term)
		p.pretty_term(field944)
		p.newline()
		field945 := unwrapped_fields943[1].(*pb.Term)
		p.pretty_term(field945)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat952 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat952 != nil {
		p.write(*flat952)
		return nil
	} else {
		_t1500 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1501 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
				_t1501 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1501
		}
		_t1502 := _t1500(msg)
		fields947 := _t1502
		unwrapped_fields948 := fields947
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field949 := unwrapped_fields948[0].(*pb.Term)
		p.pretty_term(field949)
		p.newline()
		field950 := unwrapped_fields948[1].(*pb.Term)
		p.pretty_term(field950)
		p.newline()
		field951 := unwrapped_fields948[2].(*pb.Term)
		p.pretty_term(field951)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat958 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat958 != nil {
		p.write(*flat958)
		return nil
	} else {
		_t1503 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1504 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
				_t1504 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1504
		}
		_t1505 := _t1503(msg)
		fields953 := _t1505
		unwrapped_fields954 := fields953
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field955 := unwrapped_fields954[0].(*pb.Term)
		p.pretty_term(field955)
		p.newline()
		field956 := unwrapped_fields954[1].(*pb.Term)
		p.pretty_term(field956)
		p.newline()
		field957 := unwrapped_fields954[2].(*pb.Term)
		p.pretty_term(field957)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat964 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat964 != nil {
		p.write(*flat964)
		return nil
	} else {
		_t1506 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1507 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
				_t1507 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1507
		}
		_t1508 := _t1506(msg)
		fields959 := _t1508
		unwrapped_fields960 := fields959
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field961 := unwrapped_fields960[0].(*pb.Term)
		p.pretty_term(field961)
		p.newline()
		field962 := unwrapped_fields960[1].(*pb.Term)
		p.pretty_term(field962)
		p.newline()
		field963 := unwrapped_fields960[2].(*pb.Term)
		p.pretty_term(field963)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat970 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat970 != nil {
		p.write(*flat970)
		return nil
	} else {
		_t1509 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1510 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
				_t1510 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1510
		}
		_t1511 := _t1509(msg)
		fields965 := _t1511
		unwrapped_fields966 := fields965
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field967 := unwrapped_fields966[0].(*pb.Term)
		p.pretty_term(field967)
		p.newline()
		field968 := unwrapped_fields966[1].(*pb.Term)
		p.pretty_term(field968)
		p.newline()
		field969 := unwrapped_fields966[2].(*pb.Term)
		p.pretty_term(field969)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat975 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat975 != nil {
		p.write(*flat975)
		return nil
	} else {
		_t1512 := func(_dollar_dollar *pb.RelTerm) *pb.Value {
			var _t1513 *pb.Value
			if hasProtoField(_dollar_dollar, "specialized_value") {
				_t1513 = _dollar_dollar.GetSpecializedValue()
			}
			return _t1513
		}
		_t1514 := _t1512(msg)
		deconstruct_result973 := _t1514
		if deconstruct_result973 != nil {
			unwrapped974 := deconstruct_result973
			p.pretty_specialized_value(unwrapped974)
		} else {
			_t1515 := func(_dollar_dollar *pb.RelTerm) *pb.Term {
				var _t1516 *pb.Term
				if hasProtoField(_dollar_dollar, "term") {
					_t1516 = _dollar_dollar.GetTerm()
				}
				return _t1516
			}
			_t1517 := _t1515(msg)
			deconstruct_result971 := _t1517
			if deconstruct_result971 != nil {
				unwrapped972 := deconstruct_result971
				p.pretty_term(unwrapped972)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat977 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat977 != nil {
		p.write(*flat977)
		return nil
	} else {
		fields976 := msg
		p.write("#")
		p.pretty_value(fields976)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat984 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat984 != nil {
		p.write(*flat984)
		return nil
	} else {
		_t1518 := func(_dollar_dollar *pb.RelAtom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1519 := _t1518(msg)
		fields978 := _t1519
		unwrapped_fields979 := fields978
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field980 := unwrapped_fields979[0].(string)
		p.pretty_name(field980)
		field981 := unwrapped_fields979[1].([]*pb.RelTerm)
		if !(len(field981) == 0) {
			p.newline()
			for i983, elem982 := range field981 {
				if (i983 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem982)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat989 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat989 != nil {
		p.write(*flat989)
		return nil
	} else {
		_t1520 := func(_dollar_dollar *pb.Cast) []interface{} {
			return []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		}
		_t1521 := _t1520(msg)
		fields985 := _t1521
		unwrapped_fields986 := fields985
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field987 := unwrapped_fields986[0].(*pb.Term)
		p.pretty_term(field987)
		p.newline()
		field988 := unwrapped_fields986[1].(*pb.Term)
		p.pretty_term(field988)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat993 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat993 != nil {
		p.write(*flat993)
		return nil
	} else {
		fields990 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields990) == 0) {
			p.newline()
			for i992, elem991 := range fields990 {
				if (i992 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem991)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1000 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1000 != nil {
		p.write(*flat1000)
		return nil
	} else {
		_t1522 := func(_dollar_dollar *pb.Attribute) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		}
		_t1523 := _t1522(msg)
		fields994 := _t1523
		unwrapped_fields995 := fields994
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field996 := unwrapped_fields995[0].(string)
		p.pretty_name(field996)
		field997 := unwrapped_fields995[1].([]*pb.Value)
		if !(len(field997) == 0) {
			p.newline()
			for i999, elem998 := range field997 {
				if (i999 > 0) {
					p.newline()
				}
				p.pretty_value(elem998)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1007 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1007 != nil {
		p.write(*flat1007)
		return nil
	} else {
		_t1524 := func(_dollar_dollar *pb.Algorithm) []interface{} {
			return []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		}
		_t1525 := _t1524(msg)
		fields1001 := _t1525
		unwrapped_fields1002 := fields1001
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1003 := unwrapped_fields1002[0].([]*pb.RelationId)
		if !(len(field1003) == 0) {
			p.newline()
			for i1005, elem1004 := range field1003 {
				if (i1005 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1004)
			}
		}
		p.newline()
		field1006 := unwrapped_fields1002[1].(*pb.Script)
		p.pretty_script(field1006)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1012 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1012 != nil {
		p.write(*flat1012)
		return nil
	} else {
		_t1526 := func(_dollar_dollar *pb.Script) []*pb.Construct {
			return _dollar_dollar.GetConstructs()
		}
		_t1527 := _t1526(msg)
		fields1008 := _t1527
		unwrapped_fields1009 := fields1008
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1009) == 0) {
			p.newline()
			for i1011, elem1010 := range unwrapped_fields1009 {
				if (i1011 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1010)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1017 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1017 != nil {
		p.write(*flat1017)
		return nil
	} else {
		_t1528 := func(_dollar_dollar *pb.Construct) *pb.Loop {
			var _t1529 *pb.Loop
			if hasProtoField(_dollar_dollar, "loop") {
				_t1529 = _dollar_dollar.GetLoop()
			}
			return _t1529
		}
		_t1530 := _t1528(msg)
		deconstruct_result1015 := _t1530
		if deconstruct_result1015 != nil {
			unwrapped1016 := deconstruct_result1015
			p.pretty_loop(unwrapped1016)
		} else {
			_t1531 := func(_dollar_dollar *pb.Construct) *pb.Instruction {
				var _t1532 *pb.Instruction
				if hasProtoField(_dollar_dollar, "instruction") {
					_t1532 = _dollar_dollar.GetInstruction()
				}
				return _t1532
			}
			_t1533 := _t1531(msg)
			deconstruct_result1013 := _t1533
			if deconstruct_result1013 != nil {
				unwrapped1014 := deconstruct_result1013
				p.pretty_instruction(unwrapped1014)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1022 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1022 != nil {
		p.write(*flat1022)
		return nil
	} else {
		_t1534 := func(_dollar_dollar *pb.Loop) []interface{} {
			return []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		}
		_t1535 := _t1534(msg)
		fields1018 := _t1535
		unwrapped_fields1019 := fields1018
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1020 := unwrapped_fields1019[0].([]*pb.Instruction)
		p.pretty_init(field1020)
		p.newline()
		field1021 := unwrapped_fields1019[1].(*pb.Script)
		p.pretty_script(field1021)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1026 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1026 != nil {
		p.write(*flat1026)
		return nil
	} else {
		fields1023 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1023) == 0) {
			p.newline()
			for i1025, elem1024 := range fields1023 {
				if (i1025 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1024)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1037 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1037 != nil {
		p.write(*flat1037)
		return nil
	} else {
		_t1536 := func(_dollar_dollar *pb.Instruction) *pb.Assign {
			var _t1537 *pb.Assign
			if hasProtoField(_dollar_dollar, "assign") {
				_t1537 = _dollar_dollar.GetAssign()
			}
			return _t1537
		}
		_t1538 := _t1536(msg)
		deconstruct_result1035 := _t1538
		if deconstruct_result1035 != nil {
			unwrapped1036 := deconstruct_result1035
			p.pretty_assign(unwrapped1036)
		} else {
			_t1539 := func(_dollar_dollar *pb.Instruction) *pb.Upsert {
				var _t1540 *pb.Upsert
				if hasProtoField(_dollar_dollar, "upsert") {
					_t1540 = _dollar_dollar.GetUpsert()
				}
				return _t1540
			}
			_t1541 := _t1539(msg)
			deconstruct_result1033 := _t1541
			if deconstruct_result1033 != nil {
				unwrapped1034 := deconstruct_result1033
				p.pretty_upsert(unwrapped1034)
			} else {
				_t1542 := func(_dollar_dollar *pb.Instruction) *pb.Break {
					var _t1543 *pb.Break
					if hasProtoField(_dollar_dollar, "break") {
						_t1543 = _dollar_dollar.GetBreak()
					}
					return _t1543
				}
				_t1544 := _t1542(msg)
				deconstruct_result1031 := _t1544
				if deconstruct_result1031 != nil {
					unwrapped1032 := deconstruct_result1031
					p.pretty_break(unwrapped1032)
				} else {
					_t1545 := func(_dollar_dollar *pb.Instruction) *pb.MonoidDef {
						var _t1546 *pb.MonoidDef
						if hasProtoField(_dollar_dollar, "monoid_def") {
							_t1546 = _dollar_dollar.GetMonoidDef()
						}
						return _t1546
					}
					_t1547 := _t1545(msg)
					deconstruct_result1029 := _t1547
					if deconstruct_result1029 != nil {
						unwrapped1030 := deconstruct_result1029
						p.pretty_monoid_def(unwrapped1030)
					} else {
						_t1548 := func(_dollar_dollar *pb.Instruction) *pb.MonusDef {
							var _t1549 *pb.MonusDef
							if hasProtoField(_dollar_dollar, "monus_def") {
								_t1549 = _dollar_dollar.GetMonusDef()
							}
							return _t1549
						}
						_t1550 := _t1548(msg)
						deconstruct_result1027 := _t1550
						if deconstruct_result1027 != nil {
							unwrapped1028 := deconstruct_result1027
							p.pretty_monus_def(unwrapped1028)
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
	flat1044 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1044 != nil {
		p.write(*flat1044)
		return nil
	} else {
		_t1551 := func(_dollar_dollar *pb.Assign) []interface{} {
			var _t1552 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1552 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1552}
		}
		_t1553 := _t1551(msg)
		fields1038 := _t1553
		unwrapped_fields1039 := fields1038
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1040 := unwrapped_fields1039[0].(*pb.RelationId)
		p.pretty_relation_id(field1040)
		p.newline()
		field1041 := unwrapped_fields1039[1].(*pb.Abstraction)
		p.pretty_abstraction(field1041)
		field1042 := unwrapped_fields1039[2].([]*pb.Attribute)
		if field1042 != nil {
			p.newline()
			opt_val1043 := field1042
			p.pretty_attrs(opt_val1043)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1051 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1051 != nil {
		p.write(*flat1051)
		return nil
	} else {
		_t1554 := func(_dollar_dollar *pb.Upsert) []interface{} {
			var _t1555 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1555 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1555}
		}
		_t1556 := _t1554(msg)
		fields1045 := _t1556
		unwrapped_fields1046 := fields1045
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1047 := unwrapped_fields1046[0].(*pb.RelationId)
		p.pretty_relation_id(field1047)
		p.newline()
		field1048 := unwrapped_fields1046[1].([]interface{})
		p.pretty_abstraction_with_arity(field1048)
		field1049 := unwrapped_fields1046[2].([]*pb.Attribute)
		if field1049 != nil {
			p.newline()
			opt_val1050 := field1049
			p.pretty_attrs(opt_val1050)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1056 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1056 != nil {
		p.write(*flat1056)
		return nil
	} else {
		_t1557 := func(_dollar_dollar []interface{}) []interface{} {
			_t1558 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
			return []interface{}{_t1558, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		}
		_t1559 := _t1557(msg)
		fields1052 := _t1559
		unwrapped_fields1053 := fields1052
		p.write("(")
		p.indent()
		field1054 := unwrapped_fields1053[0].([]interface{})
		p.pretty_bindings(field1054)
		p.newline()
		field1055 := unwrapped_fields1053[1].(*pb.Formula)
		p.pretty_formula(field1055)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1063 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1063 != nil {
		p.write(*flat1063)
		return nil
	} else {
		_t1560 := func(_dollar_dollar *pb.Break) []interface{} {
			var _t1561 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1561 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1561}
		}
		_t1562 := _t1560(msg)
		fields1057 := _t1562
		unwrapped_fields1058 := fields1057
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1059 := unwrapped_fields1058[0].(*pb.RelationId)
		p.pretty_relation_id(field1059)
		p.newline()
		field1060 := unwrapped_fields1058[1].(*pb.Abstraction)
		p.pretty_abstraction(field1060)
		field1061 := unwrapped_fields1058[2].([]*pb.Attribute)
		if field1061 != nil {
			p.newline()
			opt_val1062 := field1061
			p.pretty_attrs(opt_val1062)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1071 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1071 != nil {
		p.write(*flat1071)
		return nil
	} else {
		_t1563 := func(_dollar_dollar *pb.MonoidDef) []interface{} {
			var _t1564 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1564 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1564}
		}
		_t1565 := _t1563(msg)
		fields1064 := _t1565
		unwrapped_fields1065 := fields1064
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1066 := unwrapped_fields1065[0].(*pb.Monoid)
		p.pretty_monoid(field1066)
		p.newline()
		field1067 := unwrapped_fields1065[1].(*pb.RelationId)
		p.pretty_relation_id(field1067)
		p.newline()
		field1068 := unwrapped_fields1065[2].([]interface{})
		p.pretty_abstraction_with_arity(field1068)
		field1069 := unwrapped_fields1065[3].([]*pb.Attribute)
		if field1069 != nil {
			p.newline()
			opt_val1070 := field1069
			p.pretty_attrs(opt_val1070)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1080 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1080 != nil {
		p.write(*flat1080)
		return nil
	} else {
		_t1566 := func(_dollar_dollar *pb.Monoid) *pb.OrMonoid {
			var _t1567 *pb.OrMonoid
			if hasProtoField(_dollar_dollar, "or_monoid") {
				_t1567 = _dollar_dollar.GetOrMonoid()
			}
			return _t1567
		}
		_t1568 := _t1566(msg)
		deconstruct_result1078 := _t1568
		if deconstruct_result1078 != nil {
			unwrapped1079 := deconstruct_result1078
			p.pretty_or_monoid(unwrapped1079)
		} else {
			_t1569 := func(_dollar_dollar *pb.Monoid) *pb.MinMonoid {
				var _t1570 *pb.MinMonoid
				if hasProtoField(_dollar_dollar, "min_monoid") {
					_t1570 = _dollar_dollar.GetMinMonoid()
				}
				return _t1570
			}
			_t1571 := _t1569(msg)
			deconstruct_result1076 := _t1571
			if deconstruct_result1076 != nil {
				unwrapped1077 := deconstruct_result1076
				p.pretty_min_monoid(unwrapped1077)
			} else {
				_t1572 := func(_dollar_dollar *pb.Monoid) *pb.MaxMonoid {
					var _t1573 *pb.MaxMonoid
					if hasProtoField(_dollar_dollar, "max_monoid") {
						_t1573 = _dollar_dollar.GetMaxMonoid()
					}
					return _t1573
				}
				_t1574 := _t1572(msg)
				deconstruct_result1074 := _t1574
				if deconstruct_result1074 != nil {
					unwrapped1075 := deconstruct_result1074
					p.pretty_max_monoid(unwrapped1075)
				} else {
					_t1575 := func(_dollar_dollar *pb.Monoid) *pb.SumMonoid {
						var _t1576 *pb.SumMonoid
						if hasProtoField(_dollar_dollar, "sum_monoid") {
							_t1576 = _dollar_dollar.GetSumMonoid()
						}
						return _t1576
					}
					_t1577 := _t1575(msg)
					deconstruct_result1072 := _t1577
					if deconstruct_result1072 != nil {
						unwrapped1073 := deconstruct_result1072
						p.pretty_sum_monoid(unwrapped1073)
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
	fields1081 := msg
	_ = fields1081
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1084 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1084 != nil {
		p.write(*flat1084)
		return nil
	} else {
		_t1578 := func(_dollar_dollar *pb.MinMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1579 := _t1578(msg)
		fields1082 := _t1579
		unwrapped_fields1083 := fields1082
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1083)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1087 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1087 != nil {
		p.write(*flat1087)
		return nil
	} else {
		_t1580 := func(_dollar_dollar *pb.MaxMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1581 := _t1580(msg)
		fields1085 := _t1581
		unwrapped_fields1086 := fields1085
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1086)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1090 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1090 != nil {
		p.write(*flat1090)
		return nil
	} else {
		_t1582 := func(_dollar_dollar *pb.SumMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1583 := _t1582(msg)
		fields1088 := _t1583
		unwrapped_fields1089 := fields1088
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1089)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1098 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1098 != nil {
		p.write(*flat1098)
		return nil
	} else {
		_t1584 := func(_dollar_dollar *pb.MonusDef) []interface{} {
			var _t1585 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1585 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1585}
		}
		_t1586 := _t1584(msg)
		fields1091 := _t1586
		unwrapped_fields1092 := fields1091
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1093 := unwrapped_fields1092[0].(*pb.Monoid)
		p.pretty_monoid(field1093)
		p.newline()
		field1094 := unwrapped_fields1092[1].(*pb.RelationId)
		p.pretty_relation_id(field1094)
		p.newline()
		field1095 := unwrapped_fields1092[2].([]interface{})
		p.pretty_abstraction_with_arity(field1095)
		field1096 := unwrapped_fields1092[3].([]*pb.Attribute)
		if field1096 != nil {
			p.newline()
			opt_val1097 := field1096
			p.pretty_attrs(opt_val1097)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1105 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1105 != nil {
		p.write(*flat1105)
		return nil
	} else {
		_t1587 := func(_dollar_dollar *pb.Constraint) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		}
		_t1588 := _t1587(msg)
		fields1099 := _t1588
		unwrapped_fields1100 := fields1099
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1101 := unwrapped_fields1100[0].(*pb.RelationId)
		p.pretty_relation_id(field1101)
		p.newline()
		field1102 := unwrapped_fields1100[1].(*pb.Abstraction)
		p.pretty_abstraction(field1102)
		p.newline()
		field1103 := unwrapped_fields1100[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1103)
		p.newline()
		field1104 := unwrapped_fields1100[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1104)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1109 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1109 != nil {
		p.write(*flat1109)
		return nil
	} else {
		fields1106 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1106) == 0) {
			p.newline()
			for i1108, elem1107 := range fields1106 {
				if (i1108 > 0) {
					p.newline()
				}
				p.pretty_var(elem1107)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1113 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1113 != nil {
		p.write(*flat1113)
		return nil
	} else {
		fields1110 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1110) == 0) {
			p.newline()
			for i1112, elem1111 := range fields1110 {
				if (i1112 > 0) {
					p.newline()
				}
				p.pretty_var(elem1111)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1120 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1120 != nil {
		p.write(*flat1120)
		return nil
	} else {
		_t1589 := func(_dollar_dollar *pb.Data) *pb.RelEDB {
			var _t1590 *pb.RelEDB
			if hasProtoField(_dollar_dollar, "rel_edb") {
				_t1590 = _dollar_dollar.GetRelEdb()
			}
			return _t1590
		}
		_t1591 := _t1589(msg)
		deconstruct_result1118 := _t1591
		if deconstruct_result1118 != nil {
			unwrapped1119 := deconstruct_result1118
			p.pretty_rel_edb(unwrapped1119)
		} else {
			_t1592 := func(_dollar_dollar *pb.Data) *pb.BeTreeRelation {
				var _t1593 *pb.BeTreeRelation
				if hasProtoField(_dollar_dollar, "betree_relation") {
					_t1593 = _dollar_dollar.GetBetreeRelation()
				}
				return _t1593
			}
			_t1594 := _t1592(msg)
			deconstruct_result1116 := _t1594
			if deconstruct_result1116 != nil {
				unwrapped1117 := deconstruct_result1116
				p.pretty_betree_relation(unwrapped1117)
			} else {
				_t1595 := func(_dollar_dollar *pb.Data) *pb.CSVData {
					var _t1596 *pb.CSVData
					if hasProtoField(_dollar_dollar, "csv_data") {
						_t1596 = _dollar_dollar.GetCsvData()
					}
					return _t1596
				}
				_t1597 := _t1595(msg)
				deconstruct_result1114 := _t1597
				if deconstruct_result1114 != nil {
					unwrapped1115 := deconstruct_result1114
					p.pretty_csv_data(unwrapped1115)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_edb(msg *pb.RelEDB) interface{} {
	flat1126 := p.tryFlat(msg, func() { p.pretty_rel_edb(msg) })
	if flat1126 != nil {
		p.write(*flat1126)
		return nil
	} else {
		_t1598 := func(_dollar_dollar *pb.RelEDB) []interface{} {
			return []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		}
		_t1599 := _t1598(msg)
		fields1121 := _t1599
		unwrapped_fields1122 := fields1121
		p.write("(")
		p.write("rel_edb")
		p.indentSexp()
		p.newline()
		field1123 := unwrapped_fields1122[0].(*pb.RelationId)
		p.pretty_relation_id(field1123)
		p.newline()
		field1124 := unwrapped_fields1122[1].([]string)
		p.pretty_rel_edb_path(field1124)
		p.newline()
		field1125 := unwrapped_fields1122[2].([]*pb.Type)
		p.pretty_rel_edb_types(field1125)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_edb_path(msg []string) interface{} {
	flat1130 := p.tryFlat(msg, func() { p.pretty_rel_edb_path(msg) })
	if flat1130 != nil {
		p.write(*flat1130)
		return nil
	} else {
		fields1127 := msg
		p.write("[")
		p.indent()
		for i1129, elem1128 := range fields1127 {
			if (i1129 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1128))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_edb_types(msg []*pb.Type) interface{} {
	flat1134 := p.tryFlat(msg, func() { p.pretty_rel_edb_types(msg) })
	if flat1134 != nil {
		p.write(*flat1134)
		return nil
	} else {
		fields1131 := msg
		p.write("[")
		p.indent()
		for i1133, elem1132 := range fields1131 {
			if (i1133 > 0) {
				p.newline()
			}
			p.pretty_type(elem1132)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1139 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1139 != nil {
		p.write(*flat1139)
		return nil
	} else {
		_t1600 := func(_dollar_dollar *pb.BeTreeRelation) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		}
		_t1601 := _t1600(msg)
		fields1135 := _t1601
		unwrapped_fields1136 := fields1135
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1137 := unwrapped_fields1136[0].(*pb.RelationId)
		p.pretty_relation_id(field1137)
		p.newline()
		field1138 := unwrapped_fields1136[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1138)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1145 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1145 != nil {
		p.write(*flat1145)
		return nil
	} else {
		_t1602 := func(_dollar_dollar *pb.BeTreeInfo) []interface{} {
			_t1603 := p.deconstruct_betree_info_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1603}
		}
		_t1604 := _t1602(msg)
		fields1140 := _t1604
		unwrapped_fields1141 := fields1140
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1142 := unwrapped_fields1141[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1142)
		p.newline()
		field1143 := unwrapped_fields1141[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1143)
		p.newline()
		field1144 := unwrapped_fields1141[2].([][]interface{})
		p.pretty_config_dict(field1144)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1149 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1149 != nil {
		p.write(*flat1149)
		return nil
	} else {
		fields1146 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1146) == 0) {
			p.newline()
			for i1148, elem1147 := range fields1146 {
				if (i1148 > 0) {
					p.newline()
				}
				p.pretty_type(elem1147)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1153 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1153 != nil {
		p.write(*flat1153)
		return nil
	} else {
		fields1150 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1150) == 0) {
			p.newline()
			for i1152, elem1151 := range fields1150 {
				if (i1152 > 0) {
					p.newline()
				}
				p.pretty_type(elem1151)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1160 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1160 != nil {
		p.write(*flat1160)
		return nil
	} else {
		_t1605 := func(_dollar_dollar *pb.CSVData) []interface{} {
			return []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		}
		_t1606 := _t1605(msg)
		fields1154 := _t1606
		unwrapped_fields1155 := fields1154
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1156 := unwrapped_fields1155[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1156)
		p.newline()
		field1157 := unwrapped_fields1155[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1157)
		p.newline()
		field1158 := unwrapped_fields1155[2].([]*pb.CSVColumn)
		p.pretty_csv_columns(field1158)
		p.newline()
		field1159 := unwrapped_fields1155[3].(string)
		p.pretty_csv_asof(field1159)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1167 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1167 != nil {
		p.write(*flat1167)
		return nil
	} else {
		_t1607 := func(_dollar_dollar *pb.CSVLocator) []interface{} {
			var _t1608 []string
			if !(len(_dollar_dollar.GetPaths()) == 0) {
				_t1608 = _dollar_dollar.GetPaths()
			}
			var _t1609 *string
			if string(_dollar_dollar.GetInlineData()) != "" {
				_t1609 = ptr(string(_dollar_dollar.GetInlineData()))
			}
			return []interface{}{_t1608, _t1609}
		}
		_t1610 := _t1607(msg)
		fields1161 := _t1610
		unwrapped_fields1162 := fields1161
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1163 := unwrapped_fields1162[0].([]string)
		if field1163 != nil {
			p.newline()
			opt_val1164 := field1163
			p.pretty_csv_locator_paths(opt_val1164)
		}
		field1165 := unwrapped_fields1162[1].(*string)
		if field1165 != nil {
			p.newline()
			opt_val1166 := *field1165
			p.pretty_csv_locator_inline_data(opt_val1166)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1171 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1171 != nil {
		p.write(*flat1171)
		return nil
	} else {
		fields1168 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1168) == 0) {
			p.newline()
			for i1170, elem1169 := range fields1168 {
				if (i1170 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1169))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1173 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1173 != nil {
		p.write(*flat1173)
		return nil
	} else {
		fields1172 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1172))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1176 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1176 != nil {
		p.write(*flat1176)
		return nil
	} else {
		_t1611 := func(_dollar_dollar *pb.CSVConfig) [][]interface{} {
			_t1612 := p.deconstruct_csv_config(_dollar_dollar)
			return _t1612
		}
		_t1613 := _t1611(msg)
		fields1174 := _t1613
		unwrapped_fields1175 := fields1174
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1175)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_columns(msg []*pb.CSVColumn) interface{} {
	flat1180 := p.tryFlat(msg, func() { p.pretty_csv_columns(msg) })
	if flat1180 != nil {
		p.write(*flat1180)
		return nil
	} else {
		fields1177 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1177) == 0) {
			p.newline()
			for i1179, elem1178 := range fields1177 {
				if (i1179 > 0) {
					p.newline()
				}
				p.pretty_csv_column(elem1178)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_column(msg *pb.CSVColumn) interface{} {
	flat1188 := p.tryFlat(msg, func() { p.pretty_csv_column(msg) })
	if flat1188 != nil {
		p.write(*flat1188)
		return nil
	} else {
		_t1614 := func(_dollar_dollar *pb.CSVColumn) []interface{} {
			return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetTargetId(), _dollar_dollar.GetTypes()}
		}
		_t1615 := _t1614(msg)
		fields1181 := _t1615
		unwrapped_fields1182 := fields1181
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1183 := unwrapped_fields1182[0].(string)
		p.write(p.formatStringValue(field1183))
		p.newline()
		field1184 := unwrapped_fields1182[1].(*pb.RelationId)
		p.pretty_relation_id(field1184)
		p.newline()
		p.write("[")
		field1185 := unwrapped_fields1182[2].([]*pb.Type)
		for i1187, elem1186 := range field1185 {
			if (i1187 > 0) {
				p.newline()
			}
			p.pretty_type(elem1186)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1190 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1190 != nil {
		p.write(*flat1190)
		return nil
	} else {
		fields1189 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1189))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1193 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1193 != nil {
		p.write(*flat1193)
		return nil
	} else {
		_t1616 := func(_dollar_dollar *pb.Undefine) *pb.FragmentId {
			return _dollar_dollar.GetFragmentId()
		}
		_t1617 := _t1616(msg)
		fields1191 := _t1617
		unwrapped_fields1192 := fields1191
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1192)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1198 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1198 != nil {
		p.write(*flat1198)
		return nil
	} else {
		_t1618 := func(_dollar_dollar *pb.Context) []*pb.RelationId {
			return _dollar_dollar.GetRelations()
		}
		_t1619 := _t1618(msg)
		fields1194 := _t1619
		unwrapped_fields1195 := fields1194
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1195) == 0) {
			p.newline()
			for i1197, elem1196 := range unwrapped_fields1195 {
				if (i1197 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1196)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1203 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1203 != nil {
		p.write(*flat1203)
		return nil
	} else {
		_t1620 := func(_dollar_dollar *pb.Snapshot) []interface{} {
			return []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		}
		_t1621 := _t1620(msg)
		fields1199 := _t1621
		unwrapped_fields1200 := fields1199
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1201 := unwrapped_fields1200[0].([]string)
		p.pretty_rel_edb_path(field1201)
		p.newline()
		field1202 := unwrapped_fields1200[1].(*pb.RelationId)
		p.pretty_relation_id(field1202)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1207 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1207 != nil {
		p.write(*flat1207)
		return nil
	} else {
		fields1204 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1204) == 0) {
			p.newline()
			for i1206, elem1205 := range fields1204 {
				if (i1206 > 0) {
					p.newline()
				}
				p.pretty_read(elem1205)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1218 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1218 != nil {
		p.write(*flat1218)
		return nil
	} else {
		_t1622 := func(_dollar_dollar *pb.Read) *pb.Demand {
			var _t1623 *pb.Demand
			if hasProtoField(_dollar_dollar, "demand") {
				_t1623 = _dollar_dollar.GetDemand()
			}
			return _t1623
		}
		_t1624 := _t1622(msg)
		deconstruct_result1216 := _t1624
		if deconstruct_result1216 != nil {
			unwrapped1217 := deconstruct_result1216
			p.pretty_demand(unwrapped1217)
		} else {
			_t1625 := func(_dollar_dollar *pb.Read) *pb.Output {
				var _t1626 *pb.Output
				if hasProtoField(_dollar_dollar, "output") {
					_t1626 = _dollar_dollar.GetOutput()
				}
				return _t1626
			}
			_t1627 := _t1625(msg)
			deconstruct_result1214 := _t1627
			if deconstruct_result1214 != nil {
				unwrapped1215 := deconstruct_result1214
				p.pretty_output(unwrapped1215)
			} else {
				_t1628 := func(_dollar_dollar *pb.Read) *pb.WhatIf {
					var _t1629 *pb.WhatIf
					if hasProtoField(_dollar_dollar, "what_if") {
						_t1629 = _dollar_dollar.GetWhatIf()
					}
					return _t1629
				}
				_t1630 := _t1628(msg)
				deconstruct_result1212 := _t1630
				if deconstruct_result1212 != nil {
					unwrapped1213 := deconstruct_result1212
					p.pretty_what_if(unwrapped1213)
				} else {
					_t1631 := func(_dollar_dollar *pb.Read) *pb.Abort {
						var _t1632 *pb.Abort
						if hasProtoField(_dollar_dollar, "abort") {
							_t1632 = _dollar_dollar.GetAbort()
						}
						return _t1632
					}
					_t1633 := _t1631(msg)
					deconstruct_result1210 := _t1633
					if deconstruct_result1210 != nil {
						unwrapped1211 := deconstruct_result1210
						p.pretty_abort(unwrapped1211)
					} else {
						_t1634 := func(_dollar_dollar *pb.Read) *pb.Export {
							var _t1635 *pb.Export
							if hasProtoField(_dollar_dollar, "export") {
								_t1635 = _dollar_dollar.GetExport()
							}
							return _t1635
						}
						_t1636 := _t1634(msg)
						deconstruct_result1208 := _t1636
						if deconstruct_result1208 != nil {
							unwrapped1209 := deconstruct_result1208
							p.pretty_export(unwrapped1209)
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
	flat1221 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1221 != nil {
		p.write(*flat1221)
		return nil
	} else {
		_t1637 := func(_dollar_dollar *pb.Demand) *pb.RelationId {
			return _dollar_dollar.GetRelationId()
		}
		_t1638 := _t1637(msg)
		fields1219 := _t1638
		unwrapped_fields1220 := fields1219
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1220)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1226 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1226 != nil {
		p.write(*flat1226)
		return nil
	} else {
		_t1639 := func(_dollar_dollar *pb.Output) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		}
		_t1640 := _t1639(msg)
		fields1222 := _t1640
		unwrapped_fields1223 := fields1222
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1224 := unwrapped_fields1223[0].(string)
		p.pretty_name(field1224)
		p.newline()
		field1225 := unwrapped_fields1223[1].(*pb.RelationId)
		p.pretty_relation_id(field1225)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1231 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1231 != nil {
		p.write(*flat1231)
		return nil
	} else {
		_t1641 := func(_dollar_dollar *pb.WhatIf) []interface{} {
			return []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		}
		_t1642 := _t1641(msg)
		fields1227 := _t1642
		unwrapped_fields1228 := fields1227
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1229 := unwrapped_fields1228[0].(string)
		p.pretty_name(field1229)
		p.newline()
		field1230 := unwrapped_fields1228[1].(*pb.Epoch)
		p.pretty_epoch(field1230)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1237 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1237 != nil {
		p.write(*flat1237)
		return nil
	} else {
		_t1643 := func(_dollar_dollar *pb.Abort) []interface{} {
			var _t1644 *string
			if _dollar_dollar.GetName() != "abort" {
				_t1644 = ptr(_dollar_dollar.GetName())
			}
			return []interface{}{_t1644, _dollar_dollar.GetRelationId()}
		}
		_t1645 := _t1643(msg)
		fields1232 := _t1645
		unwrapped_fields1233 := fields1232
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1234 := unwrapped_fields1233[0].(*string)
		if field1234 != nil {
			p.newline()
			opt_val1235 := *field1234
			p.pretty_name(opt_val1235)
		}
		p.newline()
		field1236 := unwrapped_fields1233[1].(*pb.RelationId)
		p.pretty_relation_id(field1236)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1240 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1240 != nil {
		p.write(*flat1240)
		return nil
	} else {
		_t1646 := func(_dollar_dollar *pb.Export) *pb.ExportCSVConfig {
			return _dollar_dollar.GetCsvConfig()
		}
		_t1647 := _t1646(msg)
		fields1238 := _t1647
		unwrapped_fields1239 := fields1238
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1239)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1246 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1246 != nil {
		p.write(*flat1246)
		return nil
	} else {
		_t1648 := func(_dollar_dollar *pb.ExportCSVConfig) []interface{} {
			_t1649 := p.deconstruct_export_csv_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1649}
		}
		_t1650 := _t1648(msg)
		fields1241 := _t1650
		unwrapped_fields1242 := fields1241
		p.write("(")
		p.write("export_csv_config")
		p.indentSexp()
		p.newline()
		field1243 := unwrapped_fields1242[0].(string)
		p.pretty_export_csv_path(field1243)
		p.newline()
		field1244 := unwrapped_fields1242[1].([]*pb.ExportCSVColumn)
		p.pretty_export_csv_columns(field1244)
		p.newline()
		field1245 := unwrapped_fields1242[2].([][]interface{})
		p.pretty_config_dict(field1245)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1248 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1248 != nil {
		p.write(*flat1248)
		return nil
	} else {
		fields1247 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1247))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns(msg []*pb.ExportCSVColumn) interface{} {
	flat1252 := p.tryFlat(msg, func() { p.pretty_export_csv_columns(msg) })
	if flat1252 != nil {
		p.write(*flat1252)
		return nil
	} else {
		fields1249 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1249) == 0) {
			p.newline()
			for i1251, elem1250 := range fields1249 {
				if (i1251 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1250)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_column(msg *pb.ExportCSVColumn) interface{} {
	flat1257 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1257 != nil {
		p.write(*flat1257)
		return nil
	} else {
		_t1651 := func(_dollar_dollar *pb.ExportCSVColumn) []interface{} {
			return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		}
		_t1652 := _t1651(msg)
		fields1253 := _t1652
		unwrapped_fields1254 := fields1253
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1255 := unwrapped_fields1254[0].(string)
		p.write(p.formatStringValue(field1255))
		p.newline()
		field1256 := unwrapped_fields1254[1].(*pb.RelationId)
		p.pretty_relation_id(field1256)
		p.dedent()
		p.write(")")
	}
	return nil
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
