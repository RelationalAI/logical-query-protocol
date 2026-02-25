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
	_t1689 := &pb.Value{}
	_t1689.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t1689
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1690 := &pb.Value{}
	_t1690.Value = &pb.Value_IntValue{IntValue: v}
	return _t1690
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1691 := &pb.Value{}
	_t1691.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1691
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1692 := &pb.Value{}
	_t1692.Value = &pb.Value_StringValue{StringValue: v}
	return _t1692
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1693 := &pb.Value{}
	_t1693.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1693
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1694 := &pb.Value{}
	_t1694.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1694
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1695 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1695})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1696 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1696})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1697 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1697})
			}
		}
	}
	_t1698 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1698})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1699 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1699})
	_t1700 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1700})
	if msg.GetNewLine() != "" {
		_t1701 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1701})
	}
	_t1702 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1702})
	_t1703 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1703})
	_t1704 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1704})
	if msg.GetComment() != "" {
		_t1705 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1705})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1706 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1706})
	}
	_t1707 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1707})
	_t1708 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1708})
	_t1709 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1709})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1710 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1710})
	_t1711 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1711})
	_t1712 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1712})
	_t1713 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1713})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1714 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1714})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1715 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1715})
		}
	}
	_t1716 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1716})
	_t1717 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1717})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1718 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1718})
	}
	if msg.Compression != nil {
		_t1719 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1719})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1720 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1720})
	}
	if msg.SyntaxMissingString != nil {
		_t1721 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1721})
	}
	if msg.SyntaxDelim != nil {
		_t1722 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1722})
	}
	if msg.SyntaxQuotechar != nil {
		_t1723 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1723})
	}
	if msg.SyntaxEscapechar != nil {
		_t1724 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1724})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1725 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1725
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
	flat651 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat651 != nil {
		p.write(*flat651)
		return nil
	} else {
		_t1284 := func(_dollar_dollar *pb.Transaction) []interface{} {
			var _t1285 *pb.Configure
			if hasProtoField(_dollar_dollar, "configure") {
				_t1285 = _dollar_dollar.GetConfigure()
			}
			var _t1286 *pb.Sync
			if hasProtoField(_dollar_dollar, "sync") {
				_t1286 = _dollar_dollar.GetSync()
			}
			return []interface{}{_t1285, _t1286, _dollar_dollar.GetEpochs()}
		}
		_t1287 := _t1284(msg)
		fields642 := _t1287
		unwrapped_fields643 := fields642
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field644 := unwrapped_fields643[0].(*pb.Configure)
		if field644 != nil {
			p.newline()
			opt_val645 := field644
			p.pretty_configure(opt_val645)
		}
		field646 := unwrapped_fields643[1].(*pb.Sync)
		if field646 != nil {
			p.newline()
			opt_val647 := field646
			p.pretty_sync(opt_val647)
		}
		field648 := unwrapped_fields643[2].([]*pb.Epoch)
		if !(len(field648) == 0) {
			p.newline()
			for i650, elem649 := range field648 {
				if (i650 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem649)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat654 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat654 != nil {
		p.write(*flat654)
		return nil
	} else {
		_t1288 := func(_dollar_dollar *pb.Configure) [][]interface{} {
			_t1289 := p.deconstruct_configure(_dollar_dollar)
			return _t1289
		}
		_t1290 := _t1288(msg)
		fields652 := _t1290
		unwrapped_fields653 := fields652
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields653)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat658 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat658 != nil {
		p.write(*flat658)
		return nil
	} else {
		fields655 := msg
		p.write("{")
		p.indent()
		if !(len(fields655) == 0) {
			p.newline()
			for i657, elem656 := range fields655 {
				if (i657 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem656)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat663 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat663 != nil {
		p.write(*flat663)
		return nil
	} else {
		_t1291 := func(_dollar_dollar []interface{}) []interface{} {
			return []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		}
		_t1292 := _t1291(msg)
		fields659 := _t1292
		unwrapped_fields660 := fields659
		p.write(":")
		field661 := unwrapped_fields660[0].(string)
		p.write(field661)
		p.write(" ")
		field662 := unwrapped_fields660[1].(*pb.Value)
		p.pretty_value(field662)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat683 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat683 != nil {
		p.write(*flat683)
		return nil
	} else {
		_t1293 := func(_dollar_dollar *pb.Value) *pb.DateValue {
			var _t1294 *pb.DateValue
			if hasProtoField(_dollar_dollar, "date_value") {
				_t1294 = _dollar_dollar.GetDateValue()
			}
			return _t1294
		}
		_t1295 := _t1293(msg)
		deconstruct_result681 := _t1295
		if deconstruct_result681 != nil {
			unwrapped682 := deconstruct_result681
			p.pretty_date(unwrapped682)
		} else {
			_t1296 := func(_dollar_dollar *pb.Value) *pb.DateTimeValue {
				var _t1297 *pb.DateTimeValue
				if hasProtoField(_dollar_dollar, "datetime_value") {
					_t1297 = _dollar_dollar.GetDatetimeValue()
				}
				return _t1297
			}
			_t1298 := _t1296(msg)
			deconstruct_result679 := _t1298
			if deconstruct_result679 != nil {
				unwrapped680 := deconstruct_result679
				p.pretty_datetime(unwrapped680)
			} else {
				_t1299 := func(_dollar_dollar *pb.Value) *string {
					var _t1300 *string
					if hasProtoField(_dollar_dollar, "string_value") {
						_t1300 = ptr(_dollar_dollar.GetStringValue())
					}
					return _t1300
				}
				_t1301 := _t1299(msg)
				deconstruct_result677 := _t1301
				if deconstruct_result677 != nil {
					unwrapped678 := *deconstruct_result677
					p.write(p.formatStringValue(unwrapped678))
				} else {
					_t1302 := func(_dollar_dollar *pb.Value) *int64 {
						var _t1303 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1303 = ptr(_dollar_dollar.GetIntValue())
						}
						return _t1303
					}
					_t1304 := _t1302(msg)
					deconstruct_result675 := _t1304
					if deconstruct_result675 != nil {
						unwrapped676 := *deconstruct_result675
						p.write(fmt.Sprintf("%d", unwrapped676))
					} else {
						_t1305 := func(_dollar_dollar *pb.Value) *float64 {
							var _t1306 *float64
							if hasProtoField(_dollar_dollar, "float_value") {
								_t1306 = ptr(_dollar_dollar.GetFloatValue())
							}
							return _t1306
						}
						_t1307 := _t1305(msg)
						deconstruct_result673 := _t1307
						if deconstruct_result673 != nil {
							unwrapped674 := *deconstruct_result673
							p.write(formatFloat64(unwrapped674))
						} else {
							_t1308 := func(_dollar_dollar *pb.Value) *pb.UInt128Value {
								var _t1309 *pb.UInt128Value
								if hasProtoField(_dollar_dollar, "uint128_value") {
									_t1309 = _dollar_dollar.GetUint128Value()
								}
								return _t1309
							}
							_t1310 := _t1308(msg)
							deconstruct_result671 := _t1310
							if deconstruct_result671 != nil {
								unwrapped672 := deconstruct_result671
								p.write(p.formatUint128(unwrapped672))
							} else {
								_t1311 := func(_dollar_dollar *pb.Value) *pb.Int128Value {
									var _t1312 *pb.Int128Value
									if hasProtoField(_dollar_dollar, "int128_value") {
										_t1312 = _dollar_dollar.GetInt128Value()
									}
									return _t1312
								}
								_t1313 := _t1311(msg)
								deconstruct_result669 := _t1313
								if deconstruct_result669 != nil {
									unwrapped670 := deconstruct_result669
									p.write(p.formatInt128(unwrapped670))
								} else {
									_t1314 := func(_dollar_dollar *pb.Value) *pb.DecimalValue {
										var _t1315 *pb.DecimalValue
										if hasProtoField(_dollar_dollar, "decimal_value") {
											_t1315 = _dollar_dollar.GetDecimalValue()
										}
										return _t1315
									}
									_t1316 := _t1314(msg)
									deconstruct_result667 := _t1316
									if deconstruct_result667 != nil {
										unwrapped668 := deconstruct_result667
										p.write(p.formatDecimal(unwrapped668))
									} else {
										_t1317 := func(_dollar_dollar *pb.Value) *bool {
											var _t1318 *bool
											if hasProtoField(_dollar_dollar, "boolean_value") {
												_t1318 = ptr(_dollar_dollar.GetBooleanValue())
											}
											return _t1318
										}
										_t1319 := _t1317(msg)
										deconstruct_result665 := _t1319
										if deconstruct_result665 != nil {
											unwrapped666 := *deconstruct_result665
											p.pretty_boolean_value(unwrapped666)
										} else {
											fields664 := msg
											_ = fields664
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
	flat689 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat689 != nil {
		p.write(*flat689)
		return nil
	} else {
		_t1320 := func(_dollar_dollar *pb.DateValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		}
		_t1321 := _t1320(msg)
		fields684 := _t1321
		unwrapped_fields685 := fields684
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field686 := unwrapped_fields685[0].(int64)
		p.write(fmt.Sprintf("%d", field686))
		p.newline()
		field687 := unwrapped_fields685[1].(int64)
		p.write(fmt.Sprintf("%d", field687))
		p.newline()
		field688 := unwrapped_fields685[2].(int64)
		p.write(fmt.Sprintf("%d", field688))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat700 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat700 != nil {
		p.write(*flat700)
		return nil
	} else {
		_t1322 := func(_dollar_dollar *pb.DateTimeValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		}
		_t1323 := _t1322(msg)
		fields690 := _t1323
		unwrapped_fields691 := fields690
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field692 := unwrapped_fields691[0].(int64)
		p.write(fmt.Sprintf("%d", field692))
		p.newline()
		field693 := unwrapped_fields691[1].(int64)
		p.write(fmt.Sprintf("%d", field693))
		p.newline()
		field694 := unwrapped_fields691[2].(int64)
		p.write(fmt.Sprintf("%d", field694))
		p.newline()
		field695 := unwrapped_fields691[3].(int64)
		p.write(fmt.Sprintf("%d", field695))
		p.newline()
		field696 := unwrapped_fields691[4].(int64)
		p.write(fmt.Sprintf("%d", field696))
		p.newline()
		field697 := unwrapped_fields691[5].(int64)
		p.write(fmt.Sprintf("%d", field697))
		field698 := unwrapped_fields691[6].(*int64)
		if field698 != nil {
			p.newline()
			opt_val699 := *field698
			p.write(fmt.Sprintf("%d", opt_val699))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_t1324 := func(_dollar_dollar bool) []interface{} {
		var _t1325 []interface{}
		if _dollar_dollar {
			_t1325 = []interface{}{}
		}
		return _t1325
	}
	_t1326 := _t1324(msg)
	deconstruct_result703 := _t1326
	if deconstruct_result703 != nil {
		unwrapped704 := deconstruct_result703
		_ = unwrapped704
		p.write("true")
	} else {
		_t1327 := func(_dollar_dollar bool) []interface{} {
			var _t1328 []interface{}
			if !(_dollar_dollar) {
				_t1328 = []interface{}{}
			}
			return _t1328
		}
		_t1329 := _t1327(msg)
		deconstruct_result701 := _t1329
		if deconstruct_result701 != nil {
			unwrapped702 := deconstruct_result701
			_ = unwrapped702
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat709 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat709 != nil {
		p.write(*flat709)
		return nil
	} else {
		_t1330 := func(_dollar_dollar *pb.Sync) []*pb.FragmentId {
			return _dollar_dollar.GetFragments()
		}
		_t1331 := _t1330(msg)
		fields705 := _t1331
		unwrapped_fields706 := fields705
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields706) == 0) {
			p.newline()
			for i708, elem707 := range unwrapped_fields706 {
				if (i708 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem707)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat712 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat712 != nil {
		p.write(*flat712)
		return nil
	} else {
		_t1332 := func(_dollar_dollar *pb.FragmentId) string {
			return p.fragmentIdToString(_dollar_dollar)
		}
		_t1333 := _t1332(msg)
		fields710 := _t1333
		unwrapped_fields711 := fields710
		p.write(":")
		p.write(unwrapped_fields711)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat719 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat719 != nil {
		p.write(*flat719)
		return nil
	} else {
		_t1334 := func(_dollar_dollar *pb.Epoch) []interface{} {
			var _t1335 []*pb.Write
			if !(len(_dollar_dollar.GetWrites()) == 0) {
				_t1335 = _dollar_dollar.GetWrites()
			}
			var _t1336 []*pb.Read
			if !(len(_dollar_dollar.GetReads()) == 0) {
				_t1336 = _dollar_dollar.GetReads()
			}
			return []interface{}{_t1335, _t1336}
		}
		_t1337 := _t1334(msg)
		fields713 := _t1337
		unwrapped_fields714 := fields713
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field715 := unwrapped_fields714[0].([]*pb.Write)
		if field715 != nil {
			p.newline()
			opt_val716 := field715
			p.pretty_epoch_writes(opt_val716)
		}
		field717 := unwrapped_fields714[1].([]*pb.Read)
		if field717 != nil {
			p.newline()
			opt_val718 := field717
			p.pretty_epoch_reads(opt_val718)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat723 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat723 != nil {
		p.write(*flat723)
		return nil
	} else {
		fields720 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields720) == 0) {
			p.newline()
			for i722, elem721 := range fields720 {
				if (i722 > 0) {
					p.newline()
				}
				p.pretty_write(elem721)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat732 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat732 != nil {
		p.write(*flat732)
		return nil
	} else {
		_t1338 := func(_dollar_dollar *pb.Write) *pb.Define {
			var _t1339 *pb.Define
			if hasProtoField(_dollar_dollar, "define") {
				_t1339 = _dollar_dollar.GetDefine()
			}
			return _t1339
		}
		_t1340 := _t1338(msg)
		deconstruct_result730 := _t1340
		if deconstruct_result730 != nil {
			unwrapped731 := deconstruct_result730
			p.pretty_define(unwrapped731)
		} else {
			_t1341 := func(_dollar_dollar *pb.Write) *pb.Undefine {
				var _t1342 *pb.Undefine
				if hasProtoField(_dollar_dollar, "undefine") {
					_t1342 = _dollar_dollar.GetUndefine()
				}
				return _t1342
			}
			_t1343 := _t1341(msg)
			deconstruct_result728 := _t1343
			if deconstruct_result728 != nil {
				unwrapped729 := deconstruct_result728
				p.pretty_undefine(unwrapped729)
			} else {
				_t1344 := func(_dollar_dollar *pb.Write) *pb.Context {
					var _t1345 *pb.Context
					if hasProtoField(_dollar_dollar, "context") {
						_t1345 = _dollar_dollar.GetContext()
					}
					return _t1345
				}
				_t1346 := _t1344(msg)
				deconstruct_result726 := _t1346
				if deconstruct_result726 != nil {
					unwrapped727 := deconstruct_result726
					p.pretty_context(unwrapped727)
				} else {
					_t1347 := func(_dollar_dollar *pb.Write) *pb.Snapshot {
						var _t1348 *pb.Snapshot
						if hasProtoField(_dollar_dollar, "snapshot") {
							_t1348 = _dollar_dollar.GetSnapshot()
						}
						return _t1348
					}
					_t1349 := _t1347(msg)
					deconstruct_result724 := _t1349
					if deconstruct_result724 != nil {
						unwrapped725 := deconstruct_result724
						p.pretty_snapshot(unwrapped725)
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
	flat735 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat735 != nil {
		p.write(*flat735)
		return nil
	} else {
		_t1350 := func(_dollar_dollar *pb.Define) *pb.Fragment {
			return _dollar_dollar.GetFragment()
		}
		_t1351 := _t1350(msg)
		fields733 := _t1351
		unwrapped_fields734 := fields733
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields734)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat742 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat742 != nil {
		p.write(*flat742)
		return nil
	} else {
		_t1352 := func(_dollar_dollar *pb.Fragment) []interface{} {
			p.startPrettyFragment(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		}
		_t1353 := _t1352(msg)
		fields736 := _t1353
		unwrapped_fields737 := fields736
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field738 := unwrapped_fields737[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field738)
		field739 := unwrapped_fields737[1].([]*pb.Declaration)
		if !(len(field739) == 0) {
			p.newline()
			for i741, elem740 := range field739 {
				if (i741 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem740)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat744 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat744 != nil {
		p.write(*flat744)
		return nil
	} else {
		fields743 := msg
		p.pretty_fragment_id(fields743)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat753 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat753 != nil {
		p.write(*flat753)
		return nil
	} else {
		_t1354 := func(_dollar_dollar *pb.Declaration) *pb.Def {
			var _t1355 *pb.Def
			if hasProtoField(_dollar_dollar, "def") {
				_t1355 = _dollar_dollar.GetDef()
			}
			return _t1355
		}
		_t1356 := _t1354(msg)
		deconstruct_result751 := _t1356
		if deconstruct_result751 != nil {
			unwrapped752 := deconstruct_result751
			p.pretty_def(unwrapped752)
		} else {
			_t1357 := func(_dollar_dollar *pb.Declaration) *pb.Algorithm {
				var _t1358 *pb.Algorithm
				if hasProtoField(_dollar_dollar, "algorithm") {
					_t1358 = _dollar_dollar.GetAlgorithm()
				}
				return _t1358
			}
			_t1359 := _t1357(msg)
			deconstruct_result749 := _t1359
			if deconstruct_result749 != nil {
				unwrapped750 := deconstruct_result749
				p.pretty_algorithm(unwrapped750)
			} else {
				_t1360 := func(_dollar_dollar *pb.Declaration) *pb.Constraint {
					var _t1361 *pb.Constraint
					if hasProtoField(_dollar_dollar, "constraint") {
						_t1361 = _dollar_dollar.GetConstraint()
					}
					return _t1361
				}
				_t1362 := _t1360(msg)
				deconstruct_result747 := _t1362
				if deconstruct_result747 != nil {
					unwrapped748 := deconstruct_result747
					p.pretty_constraint(unwrapped748)
				} else {
					_t1363 := func(_dollar_dollar *pb.Declaration) *pb.Data {
						var _t1364 *pb.Data
						if hasProtoField(_dollar_dollar, "data") {
							_t1364 = _dollar_dollar.GetData()
						}
						return _t1364
					}
					_t1365 := _t1363(msg)
					deconstruct_result745 := _t1365
					if deconstruct_result745 != nil {
						unwrapped746 := deconstruct_result745
						p.pretty_data(unwrapped746)
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
	flat760 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat760 != nil {
		p.write(*flat760)
		return nil
	} else {
		_t1366 := func(_dollar_dollar *pb.Def) []interface{} {
			var _t1367 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1367 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1367}
		}
		_t1368 := _t1366(msg)
		fields754 := _t1368
		unwrapped_fields755 := fields754
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field756 := unwrapped_fields755[0].(*pb.RelationId)
		p.pretty_relation_id(field756)
		p.newline()
		field757 := unwrapped_fields755[1].(*pb.Abstraction)
		p.pretty_abstraction(field757)
		field758 := unwrapped_fields755[2].([]*pb.Attribute)
		if field758 != nil {
			p.newline()
			opt_val759 := field758
			p.pretty_attrs(opt_val759)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat765 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat765 != nil {
		p.write(*flat765)
		return nil
	} else {
		_t1369 := func(_dollar_dollar *pb.RelationId) *string {
			var _t1370 *string
			if p.relationIdToString(_dollar_dollar) != nil {
				_t1371 := p.deconstruct_relation_id_string(_dollar_dollar)
				_t1370 = ptr(_t1371)
			}
			return _t1370
		}
		_t1372 := _t1369(msg)
		deconstruct_result763 := _t1372
		if deconstruct_result763 != nil {
			unwrapped764 := *deconstruct_result763
			p.write(":")
			p.write(unwrapped764)
		} else {
			_t1373 := func(_dollar_dollar *pb.RelationId) *pb.UInt128Value {
				_t1374 := p.deconstruct_relation_id_uint128(_dollar_dollar)
				return _t1374
			}
			_t1375 := _t1373(msg)
			deconstruct_result761 := _t1375
			if deconstruct_result761 != nil {
				unwrapped762 := deconstruct_result761
				p.write(p.formatUint128(unwrapped762))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat770 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat770 != nil {
		p.write(*flat770)
		return nil
	} else {
		_t1376 := func(_dollar_dollar *pb.Abstraction) []interface{} {
			_t1377 := p.deconstruct_bindings(_dollar_dollar)
			return []interface{}{_t1377, _dollar_dollar.GetValue()}
		}
		_t1378 := _t1376(msg)
		fields766 := _t1378
		unwrapped_fields767 := fields766
		p.write("(")
		p.indent()
		field768 := unwrapped_fields767[0].([]interface{})
		p.pretty_bindings(field768)
		p.newline()
		field769 := unwrapped_fields767[1].(*pb.Formula)
		p.pretty_formula(field769)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat778 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat778 != nil {
		p.write(*flat778)
		return nil
	} else {
		_t1379 := func(_dollar_dollar []interface{}) []interface{} {
			var _t1380 []*pb.Binding
			if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
				_t1380 = _dollar_dollar[1].([]*pb.Binding)
			}
			return []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1380}
		}
		_t1381 := _t1379(msg)
		fields771 := _t1381
		unwrapped_fields772 := fields771
		p.write("[")
		p.indent()
		field773 := unwrapped_fields772[0].([]*pb.Binding)
		for i775, elem774 := range field773 {
			if (i775 > 0) {
				p.newline()
			}
			p.pretty_binding(elem774)
		}
		field776 := unwrapped_fields772[1].([]*pb.Binding)
		if field776 != nil {
			p.newline()
			opt_val777 := field776
			p.pretty_value_bindings(opt_val777)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat783 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat783 != nil {
		p.write(*flat783)
		return nil
	} else {
		_t1382 := func(_dollar_dollar *pb.Binding) []interface{} {
			return []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		}
		_t1383 := _t1382(msg)
		fields779 := _t1383
		unwrapped_fields780 := fields779
		field781 := unwrapped_fields780[0].(string)
		p.write(field781)
		p.write("::")
		field782 := unwrapped_fields780[1].(*pb.Type)
		p.pretty_type(field782)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat806 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat806 != nil {
		p.write(*flat806)
		return nil
	} else {
		_t1384 := func(_dollar_dollar *pb.Type) *pb.UnspecifiedType {
			var _t1385 *pb.UnspecifiedType
			if hasProtoField(_dollar_dollar, "unspecified_type") {
				_t1385 = _dollar_dollar.GetUnspecifiedType()
			}
			return _t1385
		}
		_t1386 := _t1384(msg)
		deconstruct_result804 := _t1386
		if deconstruct_result804 != nil {
			unwrapped805 := deconstruct_result804
			p.pretty_unspecified_type(unwrapped805)
		} else {
			_t1387 := func(_dollar_dollar *pb.Type) *pb.StringType {
				var _t1388 *pb.StringType
				if hasProtoField(_dollar_dollar, "string_type") {
					_t1388 = _dollar_dollar.GetStringType()
				}
				return _t1388
			}
			_t1389 := _t1387(msg)
			deconstruct_result802 := _t1389
			if deconstruct_result802 != nil {
				unwrapped803 := deconstruct_result802
				p.pretty_string_type(unwrapped803)
			} else {
				_t1390 := func(_dollar_dollar *pb.Type) *pb.IntType {
					var _t1391 *pb.IntType
					if hasProtoField(_dollar_dollar, "int_type") {
						_t1391 = _dollar_dollar.GetIntType()
					}
					return _t1391
				}
				_t1392 := _t1390(msg)
				deconstruct_result800 := _t1392
				if deconstruct_result800 != nil {
					unwrapped801 := deconstruct_result800
					p.pretty_int_type(unwrapped801)
				} else {
					_t1393 := func(_dollar_dollar *pb.Type) *pb.FloatType {
						var _t1394 *pb.FloatType
						if hasProtoField(_dollar_dollar, "float_type") {
							_t1394 = _dollar_dollar.GetFloatType()
						}
						return _t1394
					}
					_t1395 := _t1393(msg)
					deconstruct_result798 := _t1395
					if deconstruct_result798 != nil {
						unwrapped799 := deconstruct_result798
						p.pretty_float_type(unwrapped799)
					} else {
						_t1396 := func(_dollar_dollar *pb.Type) *pb.UInt128Type {
							var _t1397 *pb.UInt128Type
							if hasProtoField(_dollar_dollar, "uint128_type") {
								_t1397 = _dollar_dollar.GetUint128Type()
							}
							return _t1397
						}
						_t1398 := _t1396(msg)
						deconstruct_result796 := _t1398
						if deconstruct_result796 != nil {
							unwrapped797 := deconstruct_result796
							p.pretty_uint128_type(unwrapped797)
						} else {
							_t1399 := func(_dollar_dollar *pb.Type) *pb.Int128Type {
								var _t1400 *pb.Int128Type
								if hasProtoField(_dollar_dollar, "int128_type") {
									_t1400 = _dollar_dollar.GetInt128Type()
								}
								return _t1400
							}
							_t1401 := _t1399(msg)
							deconstruct_result794 := _t1401
							if deconstruct_result794 != nil {
								unwrapped795 := deconstruct_result794
								p.pretty_int128_type(unwrapped795)
							} else {
								_t1402 := func(_dollar_dollar *pb.Type) *pb.DateType {
									var _t1403 *pb.DateType
									if hasProtoField(_dollar_dollar, "date_type") {
										_t1403 = _dollar_dollar.GetDateType()
									}
									return _t1403
								}
								_t1404 := _t1402(msg)
								deconstruct_result792 := _t1404
								if deconstruct_result792 != nil {
									unwrapped793 := deconstruct_result792
									p.pretty_date_type(unwrapped793)
								} else {
									_t1405 := func(_dollar_dollar *pb.Type) *pb.DateTimeType {
										var _t1406 *pb.DateTimeType
										if hasProtoField(_dollar_dollar, "datetime_type") {
											_t1406 = _dollar_dollar.GetDatetimeType()
										}
										return _t1406
									}
									_t1407 := _t1405(msg)
									deconstruct_result790 := _t1407
									if deconstruct_result790 != nil {
										unwrapped791 := deconstruct_result790
										p.pretty_datetime_type(unwrapped791)
									} else {
										_t1408 := func(_dollar_dollar *pb.Type) *pb.MissingType {
											var _t1409 *pb.MissingType
											if hasProtoField(_dollar_dollar, "missing_type") {
												_t1409 = _dollar_dollar.GetMissingType()
											}
											return _t1409
										}
										_t1410 := _t1408(msg)
										deconstruct_result788 := _t1410
										if deconstruct_result788 != nil {
											unwrapped789 := deconstruct_result788
											p.pretty_missing_type(unwrapped789)
										} else {
											_t1411 := func(_dollar_dollar *pb.Type) *pb.DecimalType {
												var _t1412 *pb.DecimalType
												if hasProtoField(_dollar_dollar, "decimal_type") {
													_t1412 = _dollar_dollar.GetDecimalType()
												}
												return _t1412
											}
											_t1413 := _t1411(msg)
											deconstruct_result786 := _t1413
											if deconstruct_result786 != nil {
												unwrapped787 := deconstruct_result786
												p.pretty_decimal_type(unwrapped787)
											} else {
												_t1414 := func(_dollar_dollar *pb.Type) *pb.BooleanType {
													var _t1415 *pb.BooleanType
													if hasProtoField(_dollar_dollar, "boolean_type") {
														_t1415 = _dollar_dollar.GetBooleanType()
													}
													return _t1415
												}
												_t1416 := _t1414(msg)
												deconstruct_result784 := _t1416
												if deconstruct_result784 != nil {
													unwrapped785 := deconstruct_result784
													p.pretty_boolean_type(unwrapped785)
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
	fields807 := msg
	_ = fields807
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields808 := msg
	_ = fields808
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields809 := msg
	_ = fields809
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields810 := msg
	_ = fields810
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields811 := msg
	_ = fields811
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields812 := msg
	_ = fields812
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields813 := msg
	_ = fields813
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields814 := msg
	_ = fields814
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields815 := msg
	_ = fields815
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat820 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat820 != nil {
		p.write(*flat820)
		return nil
	} else {
		_t1417 := func(_dollar_dollar *pb.DecimalType) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		}
		_t1418 := _t1417(msg)
		fields816 := _t1418
		unwrapped_fields817 := fields816
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field818 := unwrapped_fields817[0].(int64)
		p.write(fmt.Sprintf("%d", field818))
		p.newline()
		field819 := unwrapped_fields817[1].(int64)
		p.write(fmt.Sprintf("%d", field819))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields821 := msg
	_ = fields821
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat825 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat825 != nil {
		p.write(*flat825)
		return nil
	} else {
		fields822 := msg
		p.write("|")
		if !(len(fields822) == 0) {
			p.write(" ")
			for i824, elem823 := range fields822 {
				if (i824 > 0) {
					p.newline()
				}
				p.pretty_binding(elem823)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat852 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat852 != nil {
		p.write(*flat852)
		return nil
	} else {
		_t1419 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
			var _t1420 *pb.Conjunction
			if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
				_t1420 = _dollar_dollar.GetConjunction()
			}
			return _t1420
		}
		_t1421 := _t1419(msg)
		deconstruct_result850 := _t1421
		if deconstruct_result850 != nil {
			unwrapped851 := deconstruct_result850
			p.pretty_true(unwrapped851)
		} else {
			_t1422 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
				var _t1423 *pb.Disjunction
				if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
					_t1423 = _dollar_dollar.GetDisjunction()
				}
				return _t1423
			}
			_t1424 := _t1422(msg)
			deconstruct_result848 := _t1424
			if deconstruct_result848 != nil {
				unwrapped849 := deconstruct_result848
				p.pretty_false(unwrapped849)
			} else {
				_t1425 := func(_dollar_dollar *pb.Formula) *pb.Exists {
					var _t1426 *pb.Exists
					if hasProtoField(_dollar_dollar, "exists") {
						_t1426 = _dollar_dollar.GetExists()
					}
					return _t1426
				}
				_t1427 := _t1425(msg)
				deconstruct_result846 := _t1427
				if deconstruct_result846 != nil {
					unwrapped847 := deconstruct_result846
					p.pretty_exists(unwrapped847)
				} else {
					_t1428 := func(_dollar_dollar *pb.Formula) *pb.Reduce {
						var _t1429 *pb.Reduce
						if hasProtoField(_dollar_dollar, "reduce") {
							_t1429 = _dollar_dollar.GetReduce()
						}
						return _t1429
					}
					_t1430 := _t1428(msg)
					deconstruct_result844 := _t1430
					if deconstruct_result844 != nil {
						unwrapped845 := deconstruct_result844
						p.pretty_reduce(unwrapped845)
					} else {
						_t1431 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
							var _t1432 *pb.Conjunction
							if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
								_t1432 = _dollar_dollar.GetConjunction()
							}
							return _t1432
						}
						_t1433 := _t1431(msg)
						deconstruct_result842 := _t1433
						if deconstruct_result842 != nil {
							unwrapped843 := deconstruct_result842
							p.pretty_conjunction(unwrapped843)
						} else {
							_t1434 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
								var _t1435 *pb.Disjunction
								if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
									_t1435 = _dollar_dollar.GetDisjunction()
								}
								return _t1435
							}
							_t1436 := _t1434(msg)
							deconstruct_result840 := _t1436
							if deconstruct_result840 != nil {
								unwrapped841 := deconstruct_result840
								p.pretty_disjunction(unwrapped841)
							} else {
								_t1437 := func(_dollar_dollar *pb.Formula) *pb.Not {
									var _t1438 *pb.Not
									if hasProtoField(_dollar_dollar, "not") {
										_t1438 = _dollar_dollar.GetNot()
									}
									return _t1438
								}
								_t1439 := _t1437(msg)
								deconstruct_result838 := _t1439
								if deconstruct_result838 != nil {
									unwrapped839 := deconstruct_result838
									p.pretty_not(unwrapped839)
								} else {
									_t1440 := func(_dollar_dollar *pb.Formula) *pb.FFI {
										var _t1441 *pb.FFI
										if hasProtoField(_dollar_dollar, "ffi") {
											_t1441 = _dollar_dollar.GetFfi()
										}
										return _t1441
									}
									_t1442 := _t1440(msg)
									deconstruct_result836 := _t1442
									if deconstruct_result836 != nil {
										unwrapped837 := deconstruct_result836
										p.pretty_ffi(unwrapped837)
									} else {
										_t1443 := func(_dollar_dollar *pb.Formula) *pb.Atom {
											var _t1444 *pb.Atom
											if hasProtoField(_dollar_dollar, "atom") {
												_t1444 = _dollar_dollar.GetAtom()
											}
											return _t1444
										}
										_t1445 := _t1443(msg)
										deconstruct_result834 := _t1445
										if deconstruct_result834 != nil {
											unwrapped835 := deconstruct_result834
											p.pretty_atom(unwrapped835)
										} else {
											_t1446 := func(_dollar_dollar *pb.Formula) *pb.Pragma {
												var _t1447 *pb.Pragma
												if hasProtoField(_dollar_dollar, "pragma") {
													_t1447 = _dollar_dollar.GetPragma()
												}
												return _t1447
											}
											_t1448 := _t1446(msg)
											deconstruct_result832 := _t1448
											if deconstruct_result832 != nil {
												unwrapped833 := deconstruct_result832
												p.pretty_pragma(unwrapped833)
											} else {
												_t1449 := func(_dollar_dollar *pb.Formula) *pb.Primitive {
													var _t1450 *pb.Primitive
													if hasProtoField(_dollar_dollar, "primitive") {
														_t1450 = _dollar_dollar.GetPrimitive()
													}
													return _t1450
												}
												_t1451 := _t1449(msg)
												deconstruct_result830 := _t1451
												if deconstruct_result830 != nil {
													unwrapped831 := deconstruct_result830
													p.pretty_primitive(unwrapped831)
												} else {
													_t1452 := func(_dollar_dollar *pb.Formula) *pb.RelAtom {
														var _t1453 *pb.RelAtom
														if hasProtoField(_dollar_dollar, "rel_atom") {
															_t1453 = _dollar_dollar.GetRelAtom()
														}
														return _t1453
													}
													_t1454 := _t1452(msg)
													deconstruct_result828 := _t1454
													if deconstruct_result828 != nil {
														unwrapped829 := deconstruct_result828
														p.pretty_rel_atom(unwrapped829)
													} else {
														_t1455 := func(_dollar_dollar *pb.Formula) *pb.Cast {
															var _t1456 *pb.Cast
															if hasProtoField(_dollar_dollar, "cast") {
																_t1456 = _dollar_dollar.GetCast()
															}
															return _t1456
														}
														_t1457 := _t1455(msg)
														deconstruct_result826 := _t1457
														if deconstruct_result826 != nil {
															unwrapped827 := deconstruct_result826
															p.pretty_cast(unwrapped827)
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
	fields853 := msg
	_ = fields853
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields854 := msg
	_ = fields854
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat859 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat859 != nil {
		p.write(*flat859)
		return nil
	} else {
		_t1458 := func(_dollar_dollar *pb.Exists) []interface{} {
			_t1459 := p.deconstruct_bindings(_dollar_dollar.GetBody())
			return []interface{}{_t1459, _dollar_dollar.GetBody().GetValue()}
		}
		_t1460 := _t1458(msg)
		fields855 := _t1460
		unwrapped_fields856 := fields855
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field857 := unwrapped_fields856[0].([]interface{})
		p.pretty_bindings(field857)
		p.newline()
		field858 := unwrapped_fields856[1].(*pb.Formula)
		p.pretty_formula(field858)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat865 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat865 != nil {
		p.write(*flat865)
		return nil
	} else {
		_t1461 := func(_dollar_dollar *pb.Reduce) []interface{} {
			return []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		}
		_t1462 := _t1461(msg)
		fields860 := _t1462
		unwrapped_fields861 := fields860
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field862 := unwrapped_fields861[0].(*pb.Abstraction)
		p.pretty_abstraction(field862)
		p.newline()
		field863 := unwrapped_fields861[1].(*pb.Abstraction)
		p.pretty_abstraction(field863)
		p.newline()
		field864 := unwrapped_fields861[2].([]*pb.Term)
		p.pretty_terms(field864)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat869 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat869 != nil {
		p.write(*flat869)
		return nil
	} else {
		fields866 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields866) == 0) {
			p.newline()
			for i868, elem867 := range fields866 {
				if (i868 > 0) {
					p.newline()
				}
				p.pretty_term(elem867)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat874 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat874 != nil {
		p.write(*flat874)
		return nil
	} else {
		_t1463 := func(_dollar_dollar *pb.Term) *pb.Var {
			var _t1464 *pb.Var
			if hasProtoField(_dollar_dollar, "var") {
				_t1464 = _dollar_dollar.GetVar()
			}
			return _t1464
		}
		_t1465 := _t1463(msg)
		deconstruct_result872 := _t1465
		if deconstruct_result872 != nil {
			unwrapped873 := deconstruct_result872
			p.pretty_var(unwrapped873)
		} else {
			_t1466 := func(_dollar_dollar *pb.Term) *pb.Value {
				var _t1467 *pb.Value
				if hasProtoField(_dollar_dollar, "constant") {
					_t1467 = _dollar_dollar.GetConstant()
				}
				return _t1467
			}
			_t1468 := _t1466(msg)
			deconstruct_result870 := _t1468
			if deconstruct_result870 != nil {
				unwrapped871 := deconstruct_result870
				p.pretty_constant(unwrapped871)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat877 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat877 != nil {
		p.write(*flat877)
		return nil
	} else {
		_t1469 := func(_dollar_dollar *pb.Var) string {
			return _dollar_dollar.GetName()
		}
		_t1470 := _t1469(msg)
		fields875 := _t1470
		unwrapped_fields876 := fields875
		p.write(unwrapped_fields876)
	}
	return nil
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) interface{} {
	flat879 := p.tryFlat(msg, func() { p.pretty_constant(msg) })
	if flat879 != nil {
		p.write(*flat879)
		return nil
	} else {
		fields878 := msg
		p.pretty_value(fields878)
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat884 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat884 != nil {
		p.write(*flat884)
		return nil
	} else {
		_t1471 := func(_dollar_dollar *pb.Conjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1472 := _t1471(msg)
		fields880 := _t1472
		unwrapped_fields881 := fields880
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields881) == 0) {
			p.newline()
			for i883, elem882 := range unwrapped_fields881 {
				if (i883 > 0) {
					p.newline()
				}
				p.pretty_formula(elem882)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat889 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat889 != nil {
		p.write(*flat889)
		return nil
	} else {
		_t1473 := func(_dollar_dollar *pb.Disjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1474 := _t1473(msg)
		fields885 := _t1474
		unwrapped_fields886 := fields885
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields886) == 0) {
			p.newline()
			for i888, elem887 := range unwrapped_fields886 {
				if (i888 > 0) {
					p.newline()
				}
				p.pretty_formula(elem887)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat892 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat892 != nil {
		p.write(*flat892)
		return nil
	} else {
		_t1475 := func(_dollar_dollar *pb.Not) *pb.Formula {
			return _dollar_dollar.GetArg()
		}
		_t1476 := _t1475(msg)
		fields890 := _t1476
		unwrapped_fields891 := fields890
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields891)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat898 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat898 != nil {
		p.write(*flat898)
		return nil
	} else {
		_t1477 := func(_dollar_dollar *pb.FFI) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		}
		_t1478 := _t1477(msg)
		fields893 := _t1478
		unwrapped_fields894 := fields893
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field895 := unwrapped_fields894[0].(string)
		p.pretty_name(field895)
		p.newline()
		field896 := unwrapped_fields894[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field896)
		p.newline()
		field897 := unwrapped_fields894[2].([]*pb.Term)
		p.pretty_terms(field897)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat900 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat900 != nil {
		p.write(*flat900)
		return nil
	} else {
		fields899 := msg
		p.write(":")
		p.write(fields899)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat904 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat904 != nil {
		p.write(*flat904)
		return nil
	} else {
		fields901 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields901) == 0) {
			p.newline()
			for i903, elem902 := range fields901 {
				if (i903 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem902)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat911 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat911 != nil {
		p.write(*flat911)
		return nil
	} else {
		_t1479 := func(_dollar_dollar *pb.Atom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1480 := _t1479(msg)
		fields905 := _t1480
		unwrapped_fields906 := fields905
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field907 := unwrapped_fields906[0].(*pb.RelationId)
		p.pretty_relation_id(field907)
		field908 := unwrapped_fields906[1].([]*pb.Term)
		if !(len(field908) == 0) {
			p.newline()
			for i910, elem909 := range field908 {
				if (i910 > 0) {
					p.newline()
				}
				p.pretty_term(elem909)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat918 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat918 != nil {
		p.write(*flat918)
		return nil
	} else {
		_t1481 := func(_dollar_dollar *pb.Pragma) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1482 := _t1481(msg)
		fields912 := _t1482
		unwrapped_fields913 := fields912
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field914 := unwrapped_fields913[0].(string)
		p.pretty_name(field914)
		field915 := unwrapped_fields913[1].([]*pb.Term)
		if !(len(field915) == 0) {
			p.newline()
			for i917, elem916 := range field915 {
				if (i917 > 0) {
					p.newline()
				}
				p.pretty_term(elem916)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat934 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat934 != nil {
		p.write(*flat934)
		return nil
	} else {
		_t1483 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1484 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1484 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1484
		}
		_t1485 := _t1483(msg)
		guard_result933 := _t1485
		if guard_result933 != nil {
			p.pretty_eq(msg)
		} else {
			_t1486 := func(_dollar_dollar *pb.Primitive) []interface{} {
				var _t1487 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
					_t1487 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				return _t1487
			}
			_t1488 := _t1486(msg)
			guard_result932 := _t1488
			if guard_result932 != nil {
				p.pretty_lt(msg)
			} else {
				_t1489 := func(_dollar_dollar *pb.Primitive) []interface{} {
					var _t1490 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
						_t1490 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					return _t1490
				}
				_t1491 := _t1489(msg)
				guard_result931 := _t1491
				if guard_result931 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_t1492 := func(_dollar_dollar *pb.Primitive) []interface{} {
						var _t1493 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
							_t1493 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						return _t1493
					}
					_t1494 := _t1492(msg)
					guard_result930 := _t1494
					if guard_result930 != nil {
						p.pretty_gt(msg)
					} else {
						_t1495 := func(_dollar_dollar *pb.Primitive) []interface{} {
							var _t1496 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
								_t1496 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
							}
							return _t1496
						}
						_t1497 := _t1495(msg)
						guard_result929 := _t1497
						if guard_result929 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_t1498 := func(_dollar_dollar *pb.Primitive) []interface{} {
								var _t1499 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
									_t1499 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								return _t1499
							}
							_t1500 := _t1498(msg)
							guard_result928 := _t1500
							if guard_result928 != nil {
								p.pretty_add(msg)
							} else {
								_t1501 := func(_dollar_dollar *pb.Primitive) []interface{} {
									var _t1502 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
										_t1502 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									return _t1502
								}
								_t1503 := _t1501(msg)
								guard_result927 := _t1503
								if guard_result927 != nil {
									p.pretty_minus(msg)
								} else {
									_t1504 := func(_dollar_dollar *pb.Primitive) []interface{} {
										var _t1505 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
											_t1505 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										return _t1505
									}
									_t1506 := _t1504(msg)
									guard_result926 := _t1506
									if guard_result926 != nil {
										p.pretty_multiply(msg)
									} else {
										_t1507 := func(_dollar_dollar *pb.Primitive) []interface{} {
											var _t1508 []interface{}
											if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
												_t1508 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
											}
											return _t1508
										}
										_t1509 := _t1507(msg)
										guard_result925 := _t1509
										if guard_result925 != nil {
											p.pretty_divide(msg)
										} else {
											_t1510 := func(_dollar_dollar *pb.Primitive) []interface{} {
												return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											}
											_t1511 := _t1510(msg)
											fields919 := _t1511
											unwrapped_fields920 := fields919
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field921 := unwrapped_fields920[0].(string)
											p.pretty_name(field921)
											field922 := unwrapped_fields920[1].([]*pb.RelTerm)
											if !(len(field922) == 0) {
												p.newline()
												for i924, elem923 := range field922 {
													if (i924 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem923)
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
	flat939 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat939 != nil {
		p.write(*flat939)
		return nil
	} else {
		_t1512 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1513 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1513 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1513
		}
		_t1514 := _t1512(msg)
		fields935 := _t1514
		unwrapped_fields936 := fields935
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field937 := unwrapped_fields936[0].(*pb.Term)
		p.pretty_term(field937)
		p.newline()
		field938 := unwrapped_fields936[1].(*pb.Term)
		p.pretty_term(field938)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat944 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat944 != nil {
		p.write(*flat944)
		return nil
	} else {
		_t1515 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1516 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1516 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1516
		}
		_t1517 := _t1515(msg)
		fields940 := _t1517
		unwrapped_fields941 := fields940
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field942 := unwrapped_fields941[0].(*pb.Term)
		p.pretty_term(field942)
		p.newline()
		field943 := unwrapped_fields941[1].(*pb.Term)
		p.pretty_term(field943)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat949 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat949 != nil {
		p.write(*flat949)
		return nil
	} else {
		_t1518 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1519 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
				_t1519 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1519
		}
		_t1520 := _t1518(msg)
		fields945 := _t1520
		unwrapped_fields946 := fields945
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field947 := unwrapped_fields946[0].(*pb.Term)
		p.pretty_term(field947)
		p.newline()
		field948 := unwrapped_fields946[1].(*pb.Term)
		p.pretty_term(field948)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat954 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat954 != nil {
		p.write(*flat954)
		return nil
	} else {
		_t1521 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1522 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
				_t1522 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1522
		}
		_t1523 := _t1521(msg)
		fields950 := _t1523
		unwrapped_fields951 := fields950
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field952 := unwrapped_fields951[0].(*pb.Term)
		p.pretty_term(field952)
		p.newline()
		field953 := unwrapped_fields951[1].(*pb.Term)
		p.pretty_term(field953)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat959 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat959 != nil {
		p.write(*flat959)
		return nil
	} else {
		_t1524 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1525 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
				_t1525 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1525
		}
		_t1526 := _t1524(msg)
		fields955 := _t1526
		unwrapped_fields956 := fields955
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field957 := unwrapped_fields956[0].(*pb.Term)
		p.pretty_term(field957)
		p.newline()
		field958 := unwrapped_fields956[1].(*pb.Term)
		p.pretty_term(field958)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat965 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat965 != nil {
		p.write(*flat965)
		return nil
	} else {
		_t1527 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1528 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
				_t1528 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1528
		}
		_t1529 := _t1527(msg)
		fields960 := _t1529
		unwrapped_fields961 := fields960
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field962 := unwrapped_fields961[0].(*pb.Term)
		p.pretty_term(field962)
		p.newline()
		field963 := unwrapped_fields961[1].(*pb.Term)
		p.pretty_term(field963)
		p.newline()
		field964 := unwrapped_fields961[2].(*pb.Term)
		p.pretty_term(field964)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat971 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat971 != nil {
		p.write(*flat971)
		return nil
	} else {
		_t1530 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1531 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
				_t1531 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1531
		}
		_t1532 := _t1530(msg)
		fields966 := _t1532
		unwrapped_fields967 := fields966
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field968 := unwrapped_fields967[0].(*pb.Term)
		p.pretty_term(field968)
		p.newline()
		field969 := unwrapped_fields967[1].(*pb.Term)
		p.pretty_term(field969)
		p.newline()
		field970 := unwrapped_fields967[2].(*pb.Term)
		p.pretty_term(field970)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat977 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat977 != nil {
		p.write(*flat977)
		return nil
	} else {
		_t1533 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1534 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
				_t1534 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1534
		}
		_t1535 := _t1533(msg)
		fields972 := _t1535
		unwrapped_fields973 := fields972
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field974 := unwrapped_fields973[0].(*pb.Term)
		p.pretty_term(field974)
		p.newline()
		field975 := unwrapped_fields973[1].(*pb.Term)
		p.pretty_term(field975)
		p.newline()
		field976 := unwrapped_fields973[2].(*pb.Term)
		p.pretty_term(field976)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat983 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat983 != nil {
		p.write(*flat983)
		return nil
	} else {
		_t1536 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1537 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
				_t1537 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1537
		}
		_t1538 := _t1536(msg)
		fields978 := _t1538
		unwrapped_fields979 := fields978
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field980 := unwrapped_fields979[0].(*pb.Term)
		p.pretty_term(field980)
		p.newline()
		field981 := unwrapped_fields979[1].(*pb.Term)
		p.pretty_term(field981)
		p.newline()
		field982 := unwrapped_fields979[2].(*pb.Term)
		p.pretty_term(field982)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat988 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat988 != nil {
		p.write(*flat988)
		return nil
	} else {
		_t1539 := func(_dollar_dollar *pb.RelTerm) *pb.Value {
			var _t1540 *pb.Value
			if hasProtoField(_dollar_dollar, "specialized_value") {
				_t1540 = _dollar_dollar.GetSpecializedValue()
			}
			return _t1540
		}
		_t1541 := _t1539(msg)
		deconstruct_result986 := _t1541
		if deconstruct_result986 != nil {
			unwrapped987 := deconstruct_result986
			p.pretty_specialized_value(unwrapped987)
		} else {
			_t1542 := func(_dollar_dollar *pb.RelTerm) *pb.Term {
				var _t1543 *pb.Term
				if hasProtoField(_dollar_dollar, "term") {
					_t1543 = _dollar_dollar.GetTerm()
				}
				return _t1543
			}
			_t1544 := _t1542(msg)
			deconstruct_result984 := _t1544
			if deconstruct_result984 != nil {
				unwrapped985 := deconstruct_result984
				p.pretty_term(unwrapped985)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat990 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat990 != nil {
		p.write(*flat990)
		return nil
	} else {
		fields989 := msg
		p.write("#")
		p.pretty_value(fields989)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat997 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat997 != nil {
		p.write(*flat997)
		return nil
	} else {
		_t1545 := func(_dollar_dollar *pb.RelAtom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1546 := _t1545(msg)
		fields991 := _t1546
		unwrapped_fields992 := fields991
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field993 := unwrapped_fields992[0].(string)
		p.pretty_name(field993)
		field994 := unwrapped_fields992[1].([]*pb.RelTerm)
		if !(len(field994) == 0) {
			p.newline()
			for i996, elem995 := range field994 {
				if (i996 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem995)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1002 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1002 != nil {
		p.write(*flat1002)
		return nil
	} else {
		_t1547 := func(_dollar_dollar *pb.Cast) []interface{} {
			return []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		}
		_t1548 := _t1547(msg)
		fields998 := _t1548
		unwrapped_fields999 := fields998
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1000 := unwrapped_fields999[0].(*pb.Term)
		p.pretty_term(field1000)
		p.newline()
		field1001 := unwrapped_fields999[1].(*pb.Term)
		p.pretty_term(field1001)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1006 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1006 != nil {
		p.write(*flat1006)
		return nil
	} else {
		fields1003 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1003) == 0) {
			p.newline()
			for i1005, elem1004 := range fields1003 {
				if (i1005 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1004)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1013 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1013 != nil {
		p.write(*flat1013)
		return nil
	} else {
		_t1549 := func(_dollar_dollar *pb.Attribute) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		}
		_t1550 := _t1549(msg)
		fields1007 := _t1550
		unwrapped_fields1008 := fields1007
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1009 := unwrapped_fields1008[0].(string)
		p.pretty_name(field1009)
		field1010 := unwrapped_fields1008[1].([]*pb.Value)
		if !(len(field1010) == 0) {
			p.newline()
			for i1012, elem1011 := range field1010 {
				if (i1012 > 0) {
					p.newline()
				}
				p.pretty_value(elem1011)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1020 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1020 != nil {
		p.write(*flat1020)
		return nil
	} else {
		_t1551 := func(_dollar_dollar *pb.Algorithm) []interface{} {
			return []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		}
		_t1552 := _t1551(msg)
		fields1014 := _t1552
		unwrapped_fields1015 := fields1014
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1016 := unwrapped_fields1015[0].([]*pb.RelationId)
		if !(len(field1016) == 0) {
			p.newline()
			for i1018, elem1017 := range field1016 {
				if (i1018 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1017)
			}
		}
		p.newline()
		field1019 := unwrapped_fields1015[1].(*pb.Script)
		p.pretty_script(field1019)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1025 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1025 != nil {
		p.write(*flat1025)
		return nil
	} else {
		_t1553 := func(_dollar_dollar *pb.Script) []*pb.Construct {
			return _dollar_dollar.GetConstructs()
		}
		_t1554 := _t1553(msg)
		fields1021 := _t1554
		unwrapped_fields1022 := fields1021
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1022) == 0) {
			p.newline()
			for i1024, elem1023 := range unwrapped_fields1022 {
				if (i1024 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1023)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1030 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1030 != nil {
		p.write(*flat1030)
		return nil
	} else {
		_t1555 := func(_dollar_dollar *pb.Construct) *pb.Loop {
			var _t1556 *pb.Loop
			if hasProtoField(_dollar_dollar, "loop") {
				_t1556 = _dollar_dollar.GetLoop()
			}
			return _t1556
		}
		_t1557 := _t1555(msg)
		deconstruct_result1028 := _t1557
		if deconstruct_result1028 != nil {
			unwrapped1029 := deconstruct_result1028
			p.pretty_loop(unwrapped1029)
		} else {
			_t1558 := func(_dollar_dollar *pb.Construct) *pb.Instruction {
				var _t1559 *pb.Instruction
				if hasProtoField(_dollar_dollar, "instruction") {
					_t1559 = _dollar_dollar.GetInstruction()
				}
				return _t1559
			}
			_t1560 := _t1558(msg)
			deconstruct_result1026 := _t1560
			if deconstruct_result1026 != nil {
				unwrapped1027 := deconstruct_result1026
				p.pretty_instruction(unwrapped1027)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1035 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1035 != nil {
		p.write(*flat1035)
		return nil
	} else {
		_t1561 := func(_dollar_dollar *pb.Loop) []interface{} {
			return []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		}
		_t1562 := _t1561(msg)
		fields1031 := _t1562
		unwrapped_fields1032 := fields1031
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1033 := unwrapped_fields1032[0].([]*pb.Instruction)
		p.pretty_init(field1033)
		p.newline()
		field1034 := unwrapped_fields1032[1].(*pb.Script)
		p.pretty_script(field1034)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1039 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1039 != nil {
		p.write(*flat1039)
		return nil
	} else {
		fields1036 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1036) == 0) {
			p.newline()
			for i1038, elem1037 := range fields1036 {
				if (i1038 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1037)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1050 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1050 != nil {
		p.write(*flat1050)
		return nil
	} else {
		_t1563 := func(_dollar_dollar *pb.Instruction) *pb.Assign {
			var _t1564 *pb.Assign
			if hasProtoField(_dollar_dollar, "assign") {
				_t1564 = _dollar_dollar.GetAssign()
			}
			return _t1564
		}
		_t1565 := _t1563(msg)
		deconstruct_result1048 := _t1565
		if deconstruct_result1048 != nil {
			unwrapped1049 := deconstruct_result1048
			p.pretty_assign(unwrapped1049)
		} else {
			_t1566 := func(_dollar_dollar *pb.Instruction) *pb.Upsert {
				var _t1567 *pb.Upsert
				if hasProtoField(_dollar_dollar, "upsert") {
					_t1567 = _dollar_dollar.GetUpsert()
				}
				return _t1567
			}
			_t1568 := _t1566(msg)
			deconstruct_result1046 := _t1568
			if deconstruct_result1046 != nil {
				unwrapped1047 := deconstruct_result1046
				p.pretty_upsert(unwrapped1047)
			} else {
				_t1569 := func(_dollar_dollar *pb.Instruction) *pb.Break {
					var _t1570 *pb.Break
					if hasProtoField(_dollar_dollar, "break") {
						_t1570 = _dollar_dollar.GetBreak()
					}
					return _t1570
				}
				_t1571 := _t1569(msg)
				deconstruct_result1044 := _t1571
				if deconstruct_result1044 != nil {
					unwrapped1045 := deconstruct_result1044
					p.pretty_break(unwrapped1045)
				} else {
					_t1572 := func(_dollar_dollar *pb.Instruction) *pb.MonoidDef {
						var _t1573 *pb.MonoidDef
						if hasProtoField(_dollar_dollar, "monoid_def") {
							_t1573 = _dollar_dollar.GetMonoidDef()
						}
						return _t1573
					}
					_t1574 := _t1572(msg)
					deconstruct_result1042 := _t1574
					if deconstruct_result1042 != nil {
						unwrapped1043 := deconstruct_result1042
						p.pretty_monoid_def(unwrapped1043)
					} else {
						_t1575 := func(_dollar_dollar *pb.Instruction) *pb.MonusDef {
							var _t1576 *pb.MonusDef
							if hasProtoField(_dollar_dollar, "monus_def") {
								_t1576 = _dollar_dollar.GetMonusDef()
							}
							return _t1576
						}
						_t1577 := _t1575(msg)
						deconstruct_result1040 := _t1577
						if deconstruct_result1040 != nil {
							unwrapped1041 := deconstruct_result1040
							p.pretty_monus_def(unwrapped1041)
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
	flat1057 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1057 != nil {
		p.write(*flat1057)
		return nil
	} else {
		_t1578 := func(_dollar_dollar *pb.Assign) []interface{} {
			var _t1579 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1579 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1579}
		}
		_t1580 := _t1578(msg)
		fields1051 := _t1580
		unwrapped_fields1052 := fields1051
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1053 := unwrapped_fields1052[0].(*pb.RelationId)
		p.pretty_relation_id(field1053)
		p.newline()
		field1054 := unwrapped_fields1052[1].(*pb.Abstraction)
		p.pretty_abstraction(field1054)
		field1055 := unwrapped_fields1052[2].([]*pb.Attribute)
		if field1055 != nil {
			p.newline()
			opt_val1056 := field1055
			p.pretty_attrs(opt_val1056)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1064 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1064 != nil {
		p.write(*flat1064)
		return nil
	} else {
		_t1581 := func(_dollar_dollar *pb.Upsert) []interface{} {
			var _t1582 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1582 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1582}
		}
		_t1583 := _t1581(msg)
		fields1058 := _t1583
		unwrapped_fields1059 := fields1058
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1060 := unwrapped_fields1059[0].(*pb.RelationId)
		p.pretty_relation_id(field1060)
		p.newline()
		field1061 := unwrapped_fields1059[1].([]interface{})
		p.pretty_abstraction_with_arity(field1061)
		field1062 := unwrapped_fields1059[2].([]*pb.Attribute)
		if field1062 != nil {
			p.newline()
			opt_val1063 := field1062
			p.pretty_attrs(opt_val1063)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1069 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1069 != nil {
		p.write(*flat1069)
		return nil
	} else {
		_t1584 := func(_dollar_dollar []interface{}) []interface{} {
			_t1585 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
			return []interface{}{_t1585, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		}
		_t1586 := _t1584(msg)
		fields1065 := _t1586
		unwrapped_fields1066 := fields1065
		p.write("(")
		p.indent()
		field1067 := unwrapped_fields1066[0].([]interface{})
		p.pretty_bindings(field1067)
		p.newline()
		field1068 := unwrapped_fields1066[1].(*pb.Formula)
		p.pretty_formula(field1068)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1076 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1076 != nil {
		p.write(*flat1076)
		return nil
	} else {
		_t1587 := func(_dollar_dollar *pb.Break) []interface{} {
			var _t1588 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1588 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1588}
		}
		_t1589 := _t1587(msg)
		fields1070 := _t1589
		unwrapped_fields1071 := fields1070
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1072 := unwrapped_fields1071[0].(*pb.RelationId)
		p.pretty_relation_id(field1072)
		p.newline()
		field1073 := unwrapped_fields1071[1].(*pb.Abstraction)
		p.pretty_abstraction(field1073)
		field1074 := unwrapped_fields1071[2].([]*pb.Attribute)
		if field1074 != nil {
			p.newline()
			opt_val1075 := field1074
			p.pretty_attrs(opt_val1075)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1084 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1084 != nil {
		p.write(*flat1084)
		return nil
	} else {
		_t1590 := func(_dollar_dollar *pb.MonoidDef) []interface{} {
			var _t1591 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1591 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1591}
		}
		_t1592 := _t1590(msg)
		fields1077 := _t1592
		unwrapped_fields1078 := fields1077
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1079 := unwrapped_fields1078[0].(*pb.Monoid)
		p.pretty_monoid(field1079)
		p.newline()
		field1080 := unwrapped_fields1078[1].(*pb.RelationId)
		p.pretty_relation_id(field1080)
		p.newline()
		field1081 := unwrapped_fields1078[2].([]interface{})
		p.pretty_abstraction_with_arity(field1081)
		field1082 := unwrapped_fields1078[3].([]*pb.Attribute)
		if field1082 != nil {
			p.newline()
			opt_val1083 := field1082
			p.pretty_attrs(opt_val1083)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1093 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1093 != nil {
		p.write(*flat1093)
		return nil
	} else {
		_t1593 := func(_dollar_dollar *pb.Monoid) *pb.OrMonoid {
			var _t1594 *pb.OrMonoid
			if hasProtoField(_dollar_dollar, "or_monoid") {
				_t1594 = _dollar_dollar.GetOrMonoid()
			}
			return _t1594
		}
		_t1595 := _t1593(msg)
		deconstruct_result1091 := _t1595
		if deconstruct_result1091 != nil {
			unwrapped1092 := deconstruct_result1091
			p.pretty_or_monoid(unwrapped1092)
		} else {
			_t1596 := func(_dollar_dollar *pb.Monoid) *pb.MinMonoid {
				var _t1597 *pb.MinMonoid
				if hasProtoField(_dollar_dollar, "min_monoid") {
					_t1597 = _dollar_dollar.GetMinMonoid()
				}
				return _t1597
			}
			_t1598 := _t1596(msg)
			deconstruct_result1089 := _t1598
			if deconstruct_result1089 != nil {
				unwrapped1090 := deconstruct_result1089
				p.pretty_min_monoid(unwrapped1090)
			} else {
				_t1599 := func(_dollar_dollar *pb.Monoid) *pb.MaxMonoid {
					var _t1600 *pb.MaxMonoid
					if hasProtoField(_dollar_dollar, "max_monoid") {
						_t1600 = _dollar_dollar.GetMaxMonoid()
					}
					return _t1600
				}
				_t1601 := _t1599(msg)
				deconstruct_result1087 := _t1601
				if deconstruct_result1087 != nil {
					unwrapped1088 := deconstruct_result1087
					p.pretty_max_monoid(unwrapped1088)
				} else {
					_t1602 := func(_dollar_dollar *pb.Monoid) *pb.SumMonoid {
						var _t1603 *pb.SumMonoid
						if hasProtoField(_dollar_dollar, "sum_monoid") {
							_t1603 = _dollar_dollar.GetSumMonoid()
						}
						return _t1603
					}
					_t1604 := _t1602(msg)
					deconstruct_result1085 := _t1604
					if deconstruct_result1085 != nil {
						unwrapped1086 := deconstruct_result1085
						p.pretty_sum_monoid(unwrapped1086)
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
	fields1094 := msg
	_ = fields1094
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1097 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1097 != nil {
		p.write(*flat1097)
		return nil
	} else {
		_t1605 := func(_dollar_dollar *pb.MinMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1606 := _t1605(msg)
		fields1095 := _t1606
		unwrapped_fields1096 := fields1095
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1096)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1100 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1100 != nil {
		p.write(*flat1100)
		return nil
	} else {
		_t1607 := func(_dollar_dollar *pb.MaxMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1608 := _t1607(msg)
		fields1098 := _t1608
		unwrapped_fields1099 := fields1098
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1099)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1103 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1103 != nil {
		p.write(*flat1103)
		return nil
	} else {
		_t1609 := func(_dollar_dollar *pb.SumMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1610 := _t1609(msg)
		fields1101 := _t1610
		unwrapped_fields1102 := fields1101
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1102)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1111 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1111 != nil {
		p.write(*flat1111)
		return nil
	} else {
		_t1611 := func(_dollar_dollar *pb.MonusDef) []interface{} {
			var _t1612 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1612 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1612}
		}
		_t1613 := _t1611(msg)
		fields1104 := _t1613
		unwrapped_fields1105 := fields1104
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1106 := unwrapped_fields1105[0].(*pb.Monoid)
		p.pretty_monoid(field1106)
		p.newline()
		field1107 := unwrapped_fields1105[1].(*pb.RelationId)
		p.pretty_relation_id(field1107)
		p.newline()
		field1108 := unwrapped_fields1105[2].([]interface{})
		p.pretty_abstraction_with_arity(field1108)
		field1109 := unwrapped_fields1105[3].([]*pb.Attribute)
		if field1109 != nil {
			p.newline()
			opt_val1110 := field1109
			p.pretty_attrs(opt_val1110)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1118 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1118 != nil {
		p.write(*flat1118)
		return nil
	} else {
		_t1614 := func(_dollar_dollar *pb.Constraint) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		}
		_t1615 := _t1614(msg)
		fields1112 := _t1615
		unwrapped_fields1113 := fields1112
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1114 := unwrapped_fields1113[0].(*pb.RelationId)
		p.pretty_relation_id(field1114)
		p.newline()
		field1115 := unwrapped_fields1113[1].(*pb.Abstraction)
		p.pretty_abstraction(field1115)
		p.newline()
		field1116 := unwrapped_fields1113[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1116)
		p.newline()
		field1117 := unwrapped_fields1113[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1117)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1122 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1122 != nil {
		p.write(*flat1122)
		return nil
	} else {
		fields1119 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1119) == 0) {
			p.newline()
			for i1121, elem1120 := range fields1119 {
				if (i1121 > 0) {
					p.newline()
				}
				p.pretty_var(elem1120)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1126 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1126 != nil {
		p.write(*flat1126)
		return nil
	} else {
		fields1123 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1123) == 0) {
			p.newline()
			for i1125, elem1124 := range fields1123 {
				if (i1125 > 0) {
					p.newline()
				}
				p.pretty_var(elem1124)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1133 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1133 != nil {
		p.write(*flat1133)
		return nil
	} else {
		_t1616 := func(_dollar_dollar *pb.Data) *pb.EDB {
			var _t1617 *pb.EDB
			if hasProtoField(_dollar_dollar, "edb") {
				_t1617 = _dollar_dollar.GetEdb()
			}
			return _t1617
		}
		_t1618 := _t1616(msg)
		deconstruct_result1131 := _t1618
		if deconstruct_result1131 != nil {
			unwrapped1132 := deconstruct_result1131
			p.pretty_edb(unwrapped1132)
		} else {
			_t1619 := func(_dollar_dollar *pb.Data) *pb.BeTreeRelation {
				var _t1620 *pb.BeTreeRelation
				if hasProtoField(_dollar_dollar, "betree_relation") {
					_t1620 = _dollar_dollar.GetBetreeRelation()
				}
				return _t1620
			}
			_t1621 := _t1619(msg)
			deconstruct_result1129 := _t1621
			if deconstruct_result1129 != nil {
				unwrapped1130 := deconstruct_result1129
				p.pretty_betree_relation(unwrapped1130)
			} else {
				_t1622 := func(_dollar_dollar *pb.Data) *pb.CSVData {
					var _t1623 *pb.CSVData
					if hasProtoField(_dollar_dollar, "csv_data") {
						_t1623 = _dollar_dollar.GetCsvData()
					}
					return _t1623
				}
				_t1624 := _t1622(msg)
				deconstruct_result1127 := _t1624
				if deconstruct_result1127 != nil {
					unwrapped1128 := deconstruct_result1127
					p.pretty_csv_data(unwrapped1128)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb(msg *pb.EDB) interface{} {
	flat1139 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1139 != nil {
		p.write(*flat1139)
		return nil
	} else {
		_t1625 := func(_dollar_dollar *pb.EDB) []interface{} {
			return []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		}
		_t1626 := _t1625(msg)
		fields1134 := _t1626
		unwrapped_fields1135 := fields1134
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1136 := unwrapped_fields1135[0].(*pb.RelationId)
		p.pretty_relation_id(field1136)
		p.newline()
		field1137 := unwrapped_fields1135[1].([]string)
		p.pretty_edb_path(field1137)
		p.newline()
		field1138 := unwrapped_fields1135[2].([]*pb.Type)
		p.pretty_edb_types(field1138)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1143 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1143 != nil {
		p.write(*flat1143)
		return nil
	} else {
		fields1140 := msg
		p.write("[")
		p.indent()
		for i1142, elem1141 := range fields1140 {
			if (i1142 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1141))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1147 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1147 != nil {
		p.write(*flat1147)
		return nil
	} else {
		fields1144 := msg
		p.write("[")
		p.indent()
		for i1146, elem1145 := range fields1144 {
			if (i1146 > 0) {
				p.newline()
			}
			p.pretty_type(elem1145)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1152 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1152 != nil {
		p.write(*flat1152)
		return nil
	} else {
		_t1627 := func(_dollar_dollar *pb.BeTreeRelation) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		}
		_t1628 := _t1627(msg)
		fields1148 := _t1628
		unwrapped_fields1149 := fields1148
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1150 := unwrapped_fields1149[0].(*pb.RelationId)
		p.pretty_relation_id(field1150)
		p.newline()
		field1151 := unwrapped_fields1149[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1151)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1158 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1158 != nil {
		p.write(*flat1158)
		return nil
	} else {
		_t1629 := func(_dollar_dollar *pb.BeTreeInfo) []interface{} {
			_t1630 := p.deconstruct_betree_info_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1630}
		}
		_t1631 := _t1629(msg)
		fields1153 := _t1631
		unwrapped_fields1154 := fields1153
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1155 := unwrapped_fields1154[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1155)
		p.newline()
		field1156 := unwrapped_fields1154[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1156)
		p.newline()
		field1157 := unwrapped_fields1154[2].([][]interface{})
		p.pretty_config_dict(field1157)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1162 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1162 != nil {
		p.write(*flat1162)
		return nil
	} else {
		fields1159 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1159) == 0) {
			p.newline()
			for i1161, elem1160 := range fields1159 {
				if (i1161 > 0) {
					p.newline()
				}
				p.pretty_type(elem1160)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1166 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1166 != nil {
		p.write(*flat1166)
		return nil
	} else {
		fields1163 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1163) == 0) {
			p.newline()
			for i1165, elem1164 := range fields1163 {
				if (i1165 > 0) {
					p.newline()
				}
				p.pretty_type(elem1164)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1173 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1173 != nil {
		p.write(*flat1173)
		return nil
	} else {
		_t1632 := func(_dollar_dollar *pb.CSVData) []interface{} {
			return []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		}
		_t1633 := _t1632(msg)
		fields1167 := _t1633
		unwrapped_fields1168 := fields1167
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1169 := unwrapped_fields1168[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1169)
		p.newline()
		field1170 := unwrapped_fields1168[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1170)
		p.newline()
		field1171 := unwrapped_fields1168[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1171)
		p.newline()
		field1172 := unwrapped_fields1168[3].(string)
		p.pretty_csv_asof(field1172)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1180 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1180 != nil {
		p.write(*flat1180)
		return nil
	} else {
		_t1634 := func(_dollar_dollar *pb.CSVLocator) []interface{} {
			var _t1635 []string
			if !(len(_dollar_dollar.GetPaths()) == 0) {
				_t1635 = _dollar_dollar.GetPaths()
			}
			var _t1636 *string
			if string(_dollar_dollar.GetInlineData()) != "" {
				_t1636 = ptr(string(_dollar_dollar.GetInlineData()))
			}
			return []interface{}{_t1635, _t1636}
		}
		_t1637 := _t1634(msg)
		fields1174 := _t1637
		unwrapped_fields1175 := fields1174
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1176 := unwrapped_fields1175[0].([]string)
		if field1176 != nil {
			p.newline()
			opt_val1177 := field1176
			p.pretty_csv_locator_paths(opt_val1177)
		}
		field1178 := unwrapped_fields1175[1].(*string)
		if field1178 != nil {
			p.newline()
			opt_val1179 := *field1178
			p.pretty_csv_locator_inline_data(opt_val1179)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1184 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1184 != nil {
		p.write(*flat1184)
		return nil
	} else {
		fields1181 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1181) == 0) {
			p.newline()
			for i1183, elem1182 := range fields1181 {
				if (i1183 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1182))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1186 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1186 != nil {
		p.write(*flat1186)
		return nil
	} else {
		fields1185 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1185))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1189 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1189 != nil {
		p.write(*flat1189)
		return nil
	} else {
		_t1638 := func(_dollar_dollar *pb.CSVConfig) [][]interface{} {
			_t1639 := p.deconstruct_csv_config(_dollar_dollar)
			return _t1639
		}
		_t1640 := _t1638(msg)
		fields1187 := _t1640
		unwrapped_fields1188 := fields1187
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1188)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1193 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1193 != nil {
		p.write(*flat1193)
		return nil
	} else {
		fields1190 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1190) == 0) {
			p.newline()
			for i1192, elem1191 := range fields1190 {
				if (i1192 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1191)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1202 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1202 != nil {
		p.write(*flat1202)
		return nil
	} else {
		_t1641 := func(_dollar_dollar *pb.GNFColumn) []interface{} {
			var _t1642 *pb.RelationId
			if hasProtoField(_dollar_dollar, "target_id") {
				_t1642 = _dollar_dollar.GetTargetId()
			}
			return []interface{}{_dollar_dollar.GetColumnPath(), _t1642, _dollar_dollar.GetTypes()}
		}
		_t1643 := _t1641(msg)
		fields1194 := _t1643
		unwrapped_fields1195 := fields1194
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1196 := unwrapped_fields1195[0].([]string)
		p.pretty_gnf_column_path(field1196)
		field1197 := unwrapped_fields1195[1].(*pb.RelationId)
		if field1197 != nil {
			p.newline()
			opt_val1198 := field1197
			p.pretty_relation_id(opt_val1198)
		}
		p.newline()
		p.write("[")
		field1199 := unwrapped_fields1195[2].([]*pb.Type)
		for i1201, elem1200 := range field1199 {
			if (i1201 > 0) {
				p.newline()
			}
			p.pretty_type(elem1200)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1209 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1209 != nil {
		p.write(*flat1209)
		return nil
	} else {
		_t1644 := func(_dollar_dollar []string) *string {
			var _t1645 *string
			if int64(len(_dollar_dollar)) == 1 {
				_t1645 = ptr(_dollar_dollar[0])
			}
			return _t1645
		}
		_t1646 := _t1644(msg)
		deconstruct_result1207 := _t1646
		if deconstruct_result1207 != nil {
			unwrapped1208 := *deconstruct_result1207
			p.write(p.formatStringValue(unwrapped1208))
		} else {
			_t1647 := func(_dollar_dollar []string) []string {
				var _t1648 []string
				if int64(len(_dollar_dollar)) != 1 {
					_t1648 = _dollar_dollar
				}
				return _t1648
			}
			_t1649 := _t1647(msg)
			deconstruct_result1203 := _t1649
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
				panic(ParseError{msg: "No matching rule for gnf_column_path"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1211 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1211 != nil {
		p.write(*flat1211)
		return nil
	} else {
		fields1210 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1210))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1214 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1214 != nil {
		p.write(*flat1214)
		return nil
	} else {
		_t1650 := func(_dollar_dollar *pb.Undefine) *pb.FragmentId {
			return _dollar_dollar.GetFragmentId()
		}
		_t1651 := _t1650(msg)
		fields1212 := _t1651
		unwrapped_fields1213 := fields1212
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1213)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1219 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1219 != nil {
		p.write(*flat1219)
		return nil
	} else {
		_t1652 := func(_dollar_dollar *pb.Context) []*pb.RelationId {
			return _dollar_dollar.GetRelations()
		}
		_t1653 := _t1652(msg)
		fields1215 := _t1653
		unwrapped_fields1216 := fields1215
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1216) == 0) {
			p.newline()
			for i1218, elem1217 := range unwrapped_fields1216 {
				if (i1218 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1217)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1224 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1224 != nil {
		p.write(*flat1224)
		return nil
	} else {
		_t1654 := func(_dollar_dollar *pb.Snapshot) []*pb.SnapshotMapping {
			return _dollar_dollar.GetMappings()
		}
		_t1655 := _t1654(msg)
		fields1220 := _t1655
		unwrapped_fields1221 := fields1220
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1221) == 0) {
			p.newline()
			for i1223, elem1222 := range unwrapped_fields1221 {
				if (i1223 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1222)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1229 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1229 != nil {
		p.write(*flat1229)
		return nil
	} else {
		_t1656 := func(_dollar_dollar *pb.SnapshotMapping) []interface{} {
			return []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		}
		_t1657 := _t1656(msg)
		fields1225 := _t1657
		unwrapped_fields1226 := fields1225
		field1227 := unwrapped_fields1226[0].([]string)
		p.pretty_edb_path(field1227)
		p.write(" ")
		field1228 := unwrapped_fields1226[1].(*pb.RelationId)
		p.pretty_relation_id(field1228)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1233 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1233 != nil {
		p.write(*flat1233)
		return nil
	} else {
		fields1230 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1230) == 0) {
			p.newline()
			for i1232, elem1231 := range fields1230 {
				if (i1232 > 0) {
					p.newline()
				}
				p.pretty_read(elem1231)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1244 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1244 != nil {
		p.write(*flat1244)
		return nil
	} else {
		_t1658 := func(_dollar_dollar *pb.Read) *pb.Demand {
			var _t1659 *pb.Demand
			if hasProtoField(_dollar_dollar, "demand") {
				_t1659 = _dollar_dollar.GetDemand()
			}
			return _t1659
		}
		_t1660 := _t1658(msg)
		deconstruct_result1242 := _t1660
		if deconstruct_result1242 != nil {
			unwrapped1243 := deconstruct_result1242
			p.pretty_demand(unwrapped1243)
		} else {
			_t1661 := func(_dollar_dollar *pb.Read) *pb.Output {
				var _t1662 *pb.Output
				if hasProtoField(_dollar_dollar, "output") {
					_t1662 = _dollar_dollar.GetOutput()
				}
				return _t1662
			}
			_t1663 := _t1661(msg)
			deconstruct_result1240 := _t1663
			if deconstruct_result1240 != nil {
				unwrapped1241 := deconstruct_result1240
				p.pretty_output(unwrapped1241)
			} else {
				_t1664 := func(_dollar_dollar *pb.Read) *pb.WhatIf {
					var _t1665 *pb.WhatIf
					if hasProtoField(_dollar_dollar, "what_if") {
						_t1665 = _dollar_dollar.GetWhatIf()
					}
					return _t1665
				}
				_t1666 := _t1664(msg)
				deconstruct_result1238 := _t1666
				if deconstruct_result1238 != nil {
					unwrapped1239 := deconstruct_result1238
					p.pretty_what_if(unwrapped1239)
				} else {
					_t1667 := func(_dollar_dollar *pb.Read) *pb.Abort {
						var _t1668 *pb.Abort
						if hasProtoField(_dollar_dollar, "abort") {
							_t1668 = _dollar_dollar.GetAbort()
						}
						return _t1668
					}
					_t1669 := _t1667(msg)
					deconstruct_result1236 := _t1669
					if deconstruct_result1236 != nil {
						unwrapped1237 := deconstruct_result1236
						p.pretty_abort(unwrapped1237)
					} else {
						_t1670 := func(_dollar_dollar *pb.Read) *pb.Export {
							var _t1671 *pb.Export
							if hasProtoField(_dollar_dollar, "export") {
								_t1671 = _dollar_dollar.GetExport()
							}
							return _t1671
						}
						_t1672 := _t1670(msg)
						deconstruct_result1234 := _t1672
						if deconstruct_result1234 != nil {
							unwrapped1235 := deconstruct_result1234
							p.pretty_export(unwrapped1235)
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
	flat1247 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1247 != nil {
		p.write(*flat1247)
		return nil
	} else {
		_t1673 := func(_dollar_dollar *pb.Demand) *pb.RelationId {
			return _dollar_dollar.GetRelationId()
		}
		_t1674 := _t1673(msg)
		fields1245 := _t1674
		unwrapped_fields1246 := fields1245
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1246)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1252 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1252 != nil {
		p.write(*flat1252)
		return nil
	} else {
		_t1675 := func(_dollar_dollar *pb.Output) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		}
		_t1676 := _t1675(msg)
		fields1248 := _t1676
		unwrapped_fields1249 := fields1248
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1250 := unwrapped_fields1249[0].(string)
		p.pretty_name(field1250)
		p.newline()
		field1251 := unwrapped_fields1249[1].(*pb.RelationId)
		p.pretty_relation_id(field1251)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1257 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1257 != nil {
		p.write(*flat1257)
		return nil
	} else {
		_t1677 := func(_dollar_dollar *pb.WhatIf) []interface{} {
			return []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		}
		_t1678 := _t1677(msg)
		fields1253 := _t1678
		unwrapped_fields1254 := fields1253
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1255 := unwrapped_fields1254[0].(string)
		p.pretty_name(field1255)
		p.newline()
		field1256 := unwrapped_fields1254[1].(*pb.Epoch)
		p.pretty_epoch(field1256)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1263 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1263 != nil {
		p.write(*flat1263)
		return nil
	} else {
		_t1679 := func(_dollar_dollar *pb.Abort) []interface{} {
			var _t1680 *string
			if _dollar_dollar.GetName() != "abort" {
				_t1680 = ptr(_dollar_dollar.GetName())
			}
			return []interface{}{_t1680, _dollar_dollar.GetRelationId()}
		}
		_t1681 := _t1679(msg)
		fields1258 := _t1681
		unwrapped_fields1259 := fields1258
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1260 := unwrapped_fields1259[0].(*string)
		if field1260 != nil {
			p.newline()
			opt_val1261 := *field1260
			p.pretty_name(opt_val1261)
		}
		p.newline()
		field1262 := unwrapped_fields1259[1].(*pb.RelationId)
		p.pretty_relation_id(field1262)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1266 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1266 != nil {
		p.write(*flat1266)
		return nil
	} else {
		_t1682 := func(_dollar_dollar *pb.Export) *pb.ExportCSVConfig {
			return _dollar_dollar.GetCsvConfig()
		}
		_t1683 := _t1682(msg)
		fields1264 := _t1683
		unwrapped_fields1265 := fields1264
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1265)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1272 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1272 != nil {
		p.write(*flat1272)
		return nil
	} else {
		_t1684 := func(_dollar_dollar *pb.ExportCSVConfig) []interface{} {
			_t1685 := p.deconstruct_export_csv_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1685}
		}
		_t1686 := _t1684(msg)
		fields1267 := _t1686
		unwrapped_fields1268 := fields1267
		p.write("(")
		p.write("export_csv_config")
		p.indentSexp()
		p.newline()
		field1269 := unwrapped_fields1268[0].(string)
		p.pretty_export_csv_path(field1269)
		p.newline()
		field1270 := unwrapped_fields1268[1].([]*pb.ExportCSVColumn)
		p.pretty_export_csv_columns(field1270)
		p.newline()
		field1271 := unwrapped_fields1268[2].([][]interface{})
		p.pretty_config_dict(field1271)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1274 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1274 != nil {
		p.write(*flat1274)
		return nil
	} else {
		fields1273 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1273))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns(msg []*pb.ExportCSVColumn) interface{} {
	flat1278 := p.tryFlat(msg, func() { p.pretty_export_csv_columns(msg) })
	if flat1278 != nil {
		p.write(*flat1278)
		return nil
	} else {
		fields1275 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1275) == 0) {
			p.newline()
			for i1277, elem1276 := range fields1275 {
				if (i1277 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1276)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_column(msg *pb.ExportCSVColumn) interface{} {
	flat1283 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1283 != nil {
		p.write(*flat1283)
		return nil
	} else {
		_t1687 := func(_dollar_dollar *pb.ExportCSVColumn) []interface{} {
			return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		}
		_t1688 := _t1687(msg)
		fields1279 := _t1688
		unwrapped_fields1280 := fields1279
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1281 := unwrapped_fields1280[0].(string)
		p.write(p.formatStringValue(field1281))
		p.newline()
		field1282 := unwrapped_fields1280[1].(*pb.RelationId)
		p.pretty_relation_id(field1282)
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
		_t1726 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1726)
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
