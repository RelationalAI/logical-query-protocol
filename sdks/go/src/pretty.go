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
	_t1677 := &pb.Value{}
	_t1677.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t1677
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1678 := &pb.Value{}
	_t1678.Value = &pb.Value_IntValue{IntValue: v}
	return _t1678
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1679 := &pb.Value{}
	_t1679.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1679
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1680 := &pb.Value{}
	_t1680.Value = &pb.Value_StringValue{StringValue: v}
	return _t1680
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1681 := &pb.Value{}
	_t1681.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1681
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1682 := &pb.Value{}
	_t1682.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1682
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1683 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1683})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1684 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1684})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1685 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1685})
			}
		}
	}
	_t1686 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1686})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1687 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1687})
	_t1688 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1688})
	if msg.GetNewLine() != "" {
		_t1689 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1689})
	}
	_t1690 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1690})
	_t1691 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1691})
	_t1692 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1692})
	if msg.GetComment() != "" {
		_t1693 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1693})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1694 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1694})
	}
	_t1695 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1695})
	_t1696 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1696})
	_t1697 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1697})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1698 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1698})
	_t1699 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1699})
	_t1700 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1700})
	_t1701 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1701})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1702 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1702})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1703 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1703})
		}
	}
	_t1704 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1704})
	_t1705 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1705})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1706 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1706})
	}
	if msg.Compression != nil {
		_t1707 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1707})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1708 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1708})
	}
	if msg.SyntaxMissingString != nil {
		_t1709 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1709})
	}
	if msg.SyntaxDelim != nil {
		_t1710 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1710})
	}
	if msg.SyntaxQuotechar != nil {
		_t1711 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1711})
	}
	if msg.SyntaxEscapechar != nil {
		_t1712 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1712})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1713 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1713
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
	flat646 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat646 != nil {
		p.write(*flat646)
		return nil
	} else {
		_t1274 := func(_dollar_dollar *pb.Transaction) []interface{} {
			var _t1275 *pb.Configure
			if hasProtoField(_dollar_dollar, "configure") {
				_t1275 = _dollar_dollar.GetConfigure()
			}
			var _t1276 *pb.Sync
			if hasProtoField(_dollar_dollar, "sync") {
				_t1276 = _dollar_dollar.GetSync()
			}
			return []interface{}{_t1275, _t1276, _dollar_dollar.GetEpochs()}
		}
		_t1277 := _t1274(msg)
		fields637 := _t1277
		unwrapped_fields638 := fields637
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field639 := unwrapped_fields638[0].(*pb.Configure)
		if field639 != nil {
			p.newline()
			opt_val640 := field639
			p.pretty_configure(opt_val640)
		}
		field641 := unwrapped_fields638[1].(*pb.Sync)
		if field641 != nil {
			p.newline()
			opt_val642 := field641
			p.pretty_sync(opt_val642)
		}
		field643 := unwrapped_fields638[2].([]*pb.Epoch)
		if !(len(field643) == 0) {
			p.newline()
			for i645, elem644 := range field643 {
				if (i645 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem644)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat649 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat649 != nil {
		p.write(*flat649)
		return nil
	} else {
		_t1278 := func(_dollar_dollar *pb.Configure) [][]interface{} {
			_t1279 := p.deconstruct_configure(_dollar_dollar)
			return _t1279
		}
		_t1280 := _t1278(msg)
		fields647 := _t1280
		unwrapped_fields648 := fields647
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields648)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat653 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat653 != nil {
		p.write(*flat653)
		return nil
	} else {
		fields650 := msg
		p.write("{")
		p.indent()
		if !(len(fields650) == 0) {
			p.newline()
			for i652, elem651 := range fields650 {
				if (i652 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem651)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat658 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat658 != nil {
		p.write(*flat658)
		return nil
	} else {
		_t1281 := func(_dollar_dollar []interface{}) []interface{} {
			return []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		}
		_t1282 := _t1281(msg)
		fields654 := _t1282
		unwrapped_fields655 := fields654
		p.write(":")
		field656 := unwrapped_fields655[0].(string)
		p.write(field656)
		p.write(" ")
		field657 := unwrapped_fields655[1].(*pb.Value)
		p.pretty_value(field657)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat678 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat678 != nil {
		p.write(*flat678)
		return nil
	} else {
		_t1283 := func(_dollar_dollar *pb.Value) *pb.DateValue {
			var _t1284 *pb.DateValue
			if hasProtoField(_dollar_dollar, "date_value") {
				_t1284 = _dollar_dollar.GetDateValue()
			}
			return _t1284
		}
		_t1285 := _t1283(msg)
		deconstruct_result676 := _t1285
		if deconstruct_result676 != nil {
			unwrapped677 := deconstruct_result676
			p.pretty_date(unwrapped677)
		} else {
			_t1286 := func(_dollar_dollar *pb.Value) *pb.DateTimeValue {
				var _t1287 *pb.DateTimeValue
				if hasProtoField(_dollar_dollar, "datetime_value") {
					_t1287 = _dollar_dollar.GetDatetimeValue()
				}
				return _t1287
			}
			_t1288 := _t1286(msg)
			deconstruct_result674 := _t1288
			if deconstruct_result674 != nil {
				unwrapped675 := deconstruct_result674
				p.pretty_datetime(unwrapped675)
			} else {
				_t1289 := func(_dollar_dollar *pb.Value) *string {
					var _t1290 *string
					if hasProtoField(_dollar_dollar, "string_value") {
						_t1290 = ptr(_dollar_dollar.GetStringValue())
					}
					return _t1290
				}
				_t1291 := _t1289(msg)
				deconstruct_result672 := _t1291
				if deconstruct_result672 != nil {
					unwrapped673 := *deconstruct_result672
					p.write(p.formatStringValue(unwrapped673))
				} else {
					_t1292 := func(_dollar_dollar *pb.Value) *int64 {
						var _t1293 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1293 = ptr(_dollar_dollar.GetIntValue())
						}
						return _t1293
					}
					_t1294 := _t1292(msg)
					deconstruct_result670 := _t1294
					if deconstruct_result670 != nil {
						unwrapped671 := *deconstruct_result670
						p.write(fmt.Sprintf("%d", unwrapped671))
					} else {
						_t1295 := func(_dollar_dollar *pb.Value) *float64 {
							var _t1296 *float64
							if hasProtoField(_dollar_dollar, "float_value") {
								_t1296 = ptr(_dollar_dollar.GetFloatValue())
							}
							return _t1296
						}
						_t1297 := _t1295(msg)
						deconstruct_result668 := _t1297
						if deconstruct_result668 != nil {
							unwrapped669 := *deconstruct_result668
							p.write(formatFloat64(unwrapped669))
						} else {
							_t1298 := func(_dollar_dollar *pb.Value) *pb.UInt128Value {
								var _t1299 *pb.UInt128Value
								if hasProtoField(_dollar_dollar, "uint128_value") {
									_t1299 = _dollar_dollar.GetUint128Value()
								}
								return _t1299
							}
							_t1300 := _t1298(msg)
							deconstruct_result666 := _t1300
							if deconstruct_result666 != nil {
								unwrapped667 := deconstruct_result666
								p.write(p.formatUint128(unwrapped667))
							} else {
								_t1301 := func(_dollar_dollar *pb.Value) *pb.Int128Value {
									var _t1302 *pb.Int128Value
									if hasProtoField(_dollar_dollar, "int128_value") {
										_t1302 = _dollar_dollar.GetInt128Value()
									}
									return _t1302
								}
								_t1303 := _t1301(msg)
								deconstruct_result664 := _t1303
								if deconstruct_result664 != nil {
									unwrapped665 := deconstruct_result664
									p.write(p.formatInt128(unwrapped665))
								} else {
									_t1304 := func(_dollar_dollar *pb.Value) *pb.DecimalValue {
										var _t1305 *pb.DecimalValue
										if hasProtoField(_dollar_dollar, "decimal_value") {
											_t1305 = _dollar_dollar.GetDecimalValue()
										}
										return _t1305
									}
									_t1306 := _t1304(msg)
									deconstruct_result662 := _t1306
									if deconstruct_result662 != nil {
										unwrapped663 := deconstruct_result662
										p.write(p.formatDecimal(unwrapped663))
									} else {
										_t1307 := func(_dollar_dollar *pb.Value) *bool {
											var _t1308 *bool
											if hasProtoField(_dollar_dollar, "boolean_value") {
												_t1308 = ptr(_dollar_dollar.GetBooleanValue())
											}
											return _t1308
										}
										_t1309 := _t1307(msg)
										deconstruct_result660 := _t1309
										if deconstruct_result660 != nil {
											unwrapped661 := *deconstruct_result660
											p.pretty_boolean_value(unwrapped661)
										} else {
											fields659 := msg
											_ = fields659
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
	flat684 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat684 != nil {
		p.write(*flat684)
		return nil
	} else {
		_t1310 := func(_dollar_dollar *pb.DateValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		}
		_t1311 := _t1310(msg)
		fields679 := _t1311
		unwrapped_fields680 := fields679
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field681 := unwrapped_fields680[0].(int64)
		p.write(fmt.Sprintf("%d", field681))
		p.newline()
		field682 := unwrapped_fields680[1].(int64)
		p.write(fmt.Sprintf("%d", field682))
		p.newline()
		field683 := unwrapped_fields680[2].(int64)
		p.write(fmt.Sprintf("%d", field683))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat695 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat695 != nil {
		p.write(*flat695)
		return nil
	} else {
		_t1312 := func(_dollar_dollar *pb.DateTimeValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		}
		_t1313 := _t1312(msg)
		fields685 := _t1313
		unwrapped_fields686 := fields685
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field687 := unwrapped_fields686[0].(int64)
		p.write(fmt.Sprintf("%d", field687))
		p.newline()
		field688 := unwrapped_fields686[1].(int64)
		p.write(fmt.Sprintf("%d", field688))
		p.newline()
		field689 := unwrapped_fields686[2].(int64)
		p.write(fmt.Sprintf("%d", field689))
		p.newline()
		field690 := unwrapped_fields686[3].(int64)
		p.write(fmt.Sprintf("%d", field690))
		p.newline()
		field691 := unwrapped_fields686[4].(int64)
		p.write(fmt.Sprintf("%d", field691))
		p.newline()
		field692 := unwrapped_fields686[5].(int64)
		p.write(fmt.Sprintf("%d", field692))
		field693 := unwrapped_fields686[6].(*int64)
		if field693 != nil {
			p.newline()
			opt_val694 := *field693
			p.write(fmt.Sprintf("%d", opt_val694))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_t1314 := func(_dollar_dollar bool) []interface{} {
		var _t1315 []interface{}
		if _dollar_dollar {
			_t1315 = []interface{}{}
		}
		return _t1315
	}
	_t1316 := _t1314(msg)
	deconstruct_result698 := _t1316
	if deconstruct_result698 != nil {
		unwrapped699 := deconstruct_result698
		_ = unwrapped699
		p.write("true")
	} else {
		_t1317 := func(_dollar_dollar bool) []interface{} {
			var _t1318 []interface{}
			if !(_dollar_dollar) {
				_t1318 = []interface{}{}
			}
			return _t1318
		}
		_t1319 := _t1317(msg)
		deconstruct_result696 := _t1319
		if deconstruct_result696 != nil {
			unwrapped697 := deconstruct_result696
			_ = unwrapped697
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat704 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat704 != nil {
		p.write(*flat704)
		return nil
	} else {
		_t1320 := func(_dollar_dollar *pb.Sync) []*pb.FragmentId {
			return _dollar_dollar.GetFragments()
		}
		_t1321 := _t1320(msg)
		fields700 := _t1321
		unwrapped_fields701 := fields700
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields701) == 0) {
			p.newline()
			for i703, elem702 := range unwrapped_fields701 {
				if (i703 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem702)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat707 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat707 != nil {
		p.write(*flat707)
		return nil
	} else {
		_t1322 := func(_dollar_dollar *pb.FragmentId) string {
			return p.fragmentIdToString(_dollar_dollar)
		}
		_t1323 := _t1322(msg)
		fields705 := _t1323
		unwrapped_fields706 := fields705
		p.write(":")
		p.write(unwrapped_fields706)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat714 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat714 != nil {
		p.write(*flat714)
		return nil
	} else {
		_t1324 := func(_dollar_dollar *pb.Epoch) []interface{} {
			var _t1325 []*pb.Write
			if !(len(_dollar_dollar.GetWrites()) == 0) {
				_t1325 = _dollar_dollar.GetWrites()
			}
			var _t1326 []*pb.Read
			if !(len(_dollar_dollar.GetReads()) == 0) {
				_t1326 = _dollar_dollar.GetReads()
			}
			return []interface{}{_t1325, _t1326}
		}
		_t1327 := _t1324(msg)
		fields708 := _t1327
		unwrapped_fields709 := fields708
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field710 := unwrapped_fields709[0].([]*pb.Write)
		if field710 != nil {
			p.newline()
			opt_val711 := field710
			p.pretty_epoch_writes(opt_val711)
		}
		field712 := unwrapped_fields709[1].([]*pb.Read)
		if field712 != nil {
			p.newline()
			opt_val713 := field712
			p.pretty_epoch_reads(opt_val713)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat718 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat718 != nil {
		p.write(*flat718)
		return nil
	} else {
		fields715 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields715) == 0) {
			p.newline()
			for i717, elem716 := range fields715 {
				if (i717 > 0) {
					p.newline()
				}
				p.pretty_write(elem716)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat727 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat727 != nil {
		p.write(*flat727)
		return nil
	} else {
		_t1328 := func(_dollar_dollar *pb.Write) *pb.Define {
			var _t1329 *pb.Define
			if hasProtoField(_dollar_dollar, "define") {
				_t1329 = _dollar_dollar.GetDefine()
			}
			return _t1329
		}
		_t1330 := _t1328(msg)
		deconstruct_result725 := _t1330
		if deconstruct_result725 != nil {
			unwrapped726 := deconstruct_result725
			p.pretty_define(unwrapped726)
		} else {
			_t1331 := func(_dollar_dollar *pb.Write) *pb.Undefine {
				var _t1332 *pb.Undefine
				if hasProtoField(_dollar_dollar, "undefine") {
					_t1332 = _dollar_dollar.GetUndefine()
				}
				return _t1332
			}
			_t1333 := _t1331(msg)
			deconstruct_result723 := _t1333
			if deconstruct_result723 != nil {
				unwrapped724 := deconstruct_result723
				p.pretty_undefine(unwrapped724)
			} else {
				_t1334 := func(_dollar_dollar *pb.Write) *pb.Context {
					var _t1335 *pb.Context
					if hasProtoField(_dollar_dollar, "context") {
						_t1335 = _dollar_dollar.GetContext()
					}
					return _t1335
				}
				_t1336 := _t1334(msg)
				deconstruct_result721 := _t1336
				if deconstruct_result721 != nil {
					unwrapped722 := deconstruct_result721
					p.pretty_context(unwrapped722)
				} else {
					_t1337 := func(_dollar_dollar *pb.Write) *pb.Snapshot {
						var _t1338 *pb.Snapshot
						if hasProtoField(_dollar_dollar, "snapshot") {
							_t1338 = _dollar_dollar.GetSnapshot()
						}
						return _t1338
					}
					_t1339 := _t1337(msg)
					deconstruct_result719 := _t1339
					if deconstruct_result719 != nil {
						unwrapped720 := deconstruct_result719
						p.pretty_snapshot(unwrapped720)
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
	flat730 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat730 != nil {
		p.write(*flat730)
		return nil
	} else {
		_t1340 := func(_dollar_dollar *pb.Define) *pb.Fragment {
			return _dollar_dollar.GetFragment()
		}
		_t1341 := _t1340(msg)
		fields728 := _t1341
		unwrapped_fields729 := fields728
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields729)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat737 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat737 != nil {
		p.write(*flat737)
		return nil
	} else {
		_t1342 := func(_dollar_dollar *pb.Fragment) []interface{} {
			p.startPrettyFragment(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		}
		_t1343 := _t1342(msg)
		fields731 := _t1343
		unwrapped_fields732 := fields731
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field733 := unwrapped_fields732[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field733)
		field734 := unwrapped_fields732[1].([]*pb.Declaration)
		if !(len(field734) == 0) {
			p.newline()
			for i736, elem735 := range field734 {
				if (i736 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem735)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat739 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat739 != nil {
		p.write(*flat739)
		return nil
	} else {
		fields738 := msg
		p.pretty_fragment_id(fields738)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat748 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat748 != nil {
		p.write(*flat748)
		return nil
	} else {
		_t1344 := func(_dollar_dollar *pb.Declaration) *pb.Def {
			var _t1345 *pb.Def
			if hasProtoField(_dollar_dollar, "def") {
				_t1345 = _dollar_dollar.GetDef()
			}
			return _t1345
		}
		_t1346 := _t1344(msg)
		deconstruct_result746 := _t1346
		if deconstruct_result746 != nil {
			unwrapped747 := deconstruct_result746
			p.pretty_def(unwrapped747)
		} else {
			_t1347 := func(_dollar_dollar *pb.Declaration) *pb.Algorithm {
				var _t1348 *pb.Algorithm
				if hasProtoField(_dollar_dollar, "algorithm") {
					_t1348 = _dollar_dollar.GetAlgorithm()
				}
				return _t1348
			}
			_t1349 := _t1347(msg)
			deconstruct_result744 := _t1349
			if deconstruct_result744 != nil {
				unwrapped745 := deconstruct_result744
				p.pretty_algorithm(unwrapped745)
			} else {
				_t1350 := func(_dollar_dollar *pb.Declaration) *pb.Constraint {
					var _t1351 *pb.Constraint
					if hasProtoField(_dollar_dollar, "constraint") {
						_t1351 = _dollar_dollar.GetConstraint()
					}
					return _t1351
				}
				_t1352 := _t1350(msg)
				deconstruct_result742 := _t1352
				if deconstruct_result742 != nil {
					unwrapped743 := deconstruct_result742
					p.pretty_constraint(unwrapped743)
				} else {
					_t1353 := func(_dollar_dollar *pb.Declaration) *pb.Data {
						var _t1354 *pb.Data
						if hasProtoField(_dollar_dollar, "data") {
							_t1354 = _dollar_dollar.GetData()
						}
						return _t1354
					}
					_t1355 := _t1353(msg)
					deconstruct_result740 := _t1355
					if deconstruct_result740 != nil {
						unwrapped741 := deconstruct_result740
						p.pretty_data(unwrapped741)
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
	flat755 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat755 != nil {
		p.write(*flat755)
		return nil
	} else {
		_t1356 := func(_dollar_dollar *pb.Def) []interface{} {
			var _t1357 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1357 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1357}
		}
		_t1358 := _t1356(msg)
		fields749 := _t1358
		unwrapped_fields750 := fields749
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field751 := unwrapped_fields750[0].(*pb.RelationId)
		p.pretty_relation_id(field751)
		p.newline()
		field752 := unwrapped_fields750[1].(*pb.Abstraction)
		p.pretty_abstraction(field752)
		field753 := unwrapped_fields750[2].([]*pb.Attribute)
		if field753 != nil {
			p.newline()
			opt_val754 := field753
			p.pretty_attrs(opt_val754)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat760 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat760 != nil {
		p.write(*flat760)
		return nil
	} else {
		_t1359 := func(_dollar_dollar *pb.RelationId) *string {
			var _t1360 *string
			if p.relationIdToString(_dollar_dollar) != nil {
				_t1361 := p.deconstruct_relation_id_string(_dollar_dollar)
				_t1360 = ptr(_t1361)
			}
			return _t1360
		}
		_t1362 := _t1359(msg)
		deconstruct_result758 := _t1362
		if deconstruct_result758 != nil {
			unwrapped759 := *deconstruct_result758
			p.write(":")
			p.write(unwrapped759)
		} else {
			_t1363 := func(_dollar_dollar *pb.RelationId) *pb.UInt128Value {
				_t1364 := p.deconstruct_relation_id_uint128(_dollar_dollar)
				return _t1364
			}
			_t1365 := _t1363(msg)
			deconstruct_result756 := _t1365
			if deconstruct_result756 != nil {
				unwrapped757 := deconstruct_result756
				p.write(p.formatUint128(unwrapped757))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat765 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat765 != nil {
		p.write(*flat765)
		return nil
	} else {
		_t1366 := func(_dollar_dollar *pb.Abstraction) []interface{} {
			_t1367 := p.deconstruct_bindings(_dollar_dollar)
			return []interface{}{_t1367, _dollar_dollar.GetValue()}
		}
		_t1368 := _t1366(msg)
		fields761 := _t1368
		unwrapped_fields762 := fields761
		p.write("(")
		p.indent()
		field763 := unwrapped_fields762[0].([]interface{})
		p.pretty_bindings(field763)
		p.newline()
		field764 := unwrapped_fields762[1].(*pb.Formula)
		p.pretty_formula(field764)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat773 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat773 != nil {
		p.write(*flat773)
		return nil
	} else {
		_t1369 := func(_dollar_dollar []interface{}) []interface{} {
			var _t1370 []*pb.Binding
			if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
				_t1370 = _dollar_dollar[1].([]*pb.Binding)
			}
			return []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1370}
		}
		_t1371 := _t1369(msg)
		fields766 := _t1371
		unwrapped_fields767 := fields766
		p.write("[")
		p.indent()
		field768 := unwrapped_fields767[0].([]*pb.Binding)
		for i770, elem769 := range field768 {
			if (i770 > 0) {
				p.newline()
			}
			p.pretty_binding(elem769)
		}
		field771 := unwrapped_fields767[1].([]*pb.Binding)
		if field771 != nil {
			p.newline()
			opt_val772 := field771
			p.pretty_value_bindings(opt_val772)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat778 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat778 != nil {
		p.write(*flat778)
		return nil
	} else {
		_t1372 := func(_dollar_dollar *pb.Binding) []interface{} {
			return []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		}
		_t1373 := _t1372(msg)
		fields774 := _t1373
		unwrapped_fields775 := fields774
		field776 := unwrapped_fields775[0].(string)
		p.write(field776)
		p.write("::")
		field777 := unwrapped_fields775[1].(*pb.Type)
		p.pretty_type(field777)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat801 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat801 != nil {
		p.write(*flat801)
		return nil
	} else {
		_t1374 := func(_dollar_dollar *pb.Type) *pb.UnspecifiedType {
			var _t1375 *pb.UnspecifiedType
			if hasProtoField(_dollar_dollar, "unspecified_type") {
				_t1375 = _dollar_dollar.GetUnspecifiedType()
			}
			return _t1375
		}
		_t1376 := _t1374(msg)
		deconstruct_result799 := _t1376
		if deconstruct_result799 != nil {
			unwrapped800 := deconstruct_result799
			p.pretty_unspecified_type(unwrapped800)
		} else {
			_t1377 := func(_dollar_dollar *pb.Type) *pb.StringType {
				var _t1378 *pb.StringType
				if hasProtoField(_dollar_dollar, "string_type") {
					_t1378 = _dollar_dollar.GetStringType()
				}
				return _t1378
			}
			_t1379 := _t1377(msg)
			deconstruct_result797 := _t1379
			if deconstruct_result797 != nil {
				unwrapped798 := deconstruct_result797
				p.pretty_string_type(unwrapped798)
			} else {
				_t1380 := func(_dollar_dollar *pb.Type) *pb.IntType {
					var _t1381 *pb.IntType
					if hasProtoField(_dollar_dollar, "int_type") {
						_t1381 = _dollar_dollar.GetIntType()
					}
					return _t1381
				}
				_t1382 := _t1380(msg)
				deconstruct_result795 := _t1382
				if deconstruct_result795 != nil {
					unwrapped796 := deconstruct_result795
					p.pretty_int_type(unwrapped796)
				} else {
					_t1383 := func(_dollar_dollar *pb.Type) *pb.FloatType {
						var _t1384 *pb.FloatType
						if hasProtoField(_dollar_dollar, "float_type") {
							_t1384 = _dollar_dollar.GetFloatType()
						}
						return _t1384
					}
					_t1385 := _t1383(msg)
					deconstruct_result793 := _t1385
					if deconstruct_result793 != nil {
						unwrapped794 := deconstruct_result793
						p.pretty_float_type(unwrapped794)
					} else {
						_t1386 := func(_dollar_dollar *pb.Type) *pb.UInt128Type {
							var _t1387 *pb.UInt128Type
							if hasProtoField(_dollar_dollar, "uint128_type") {
								_t1387 = _dollar_dollar.GetUint128Type()
							}
							return _t1387
						}
						_t1388 := _t1386(msg)
						deconstruct_result791 := _t1388
						if deconstruct_result791 != nil {
							unwrapped792 := deconstruct_result791
							p.pretty_uint128_type(unwrapped792)
						} else {
							_t1389 := func(_dollar_dollar *pb.Type) *pb.Int128Type {
								var _t1390 *pb.Int128Type
								if hasProtoField(_dollar_dollar, "int128_type") {
									_t1390 = _dollar_dollar.GetInt128Type()
								}
								return _t1390
							}
							_t1391 := _t1389(msg)
							deconstruct_result789 := _t1391
							if deconstruct_result789 != nil {
								unwrapped790 := deconstruct_result789
								p.pretty_int128_type(unwrapped790)
							} else {
								_t1392 := func(_dollar_dollar *pb.Type) *pb.DateType {
									var _t1393 *pb.DateType
									if hasProtoField(_dollar_dollar, "date_type") {
										_t1393 = _dollar_dollar.GetDateType()
									}
									return _t1393
								}
								_t1394 := _t1392(msg)
								deconstruct_result787 := _t1394
								if deconstruct_result787 != nil {
									unwrapped788 := deconstruct_result787
									p.pretty_date_type(unwrapped788)
								} else {
									_t1395 := func(_dollar_dollar *pb.Type) *pb.DateTimeType {
										var _t1396 *pb.DateTimeType
										if hasProtoField(_dollar_dollar, "datetime_type") {
											_t1396 = _dollar_dollar.GetDatetimeType()
										}
										return _t1396
									}
									_t1397 := _t1395(msg)
									deconstruct_result785 := _t1397
									if deconstruct_result785 != nil {
										unwrapped786 := deconstruct_result785
										p.pretty_datetime_type(unwrapped786)
									} else {
										_t1398 := func(_dollar_dollar *pb.Type) *pb.MissingType {
											var _t1399 *pb.MissingType
											if hasProtoField(_dollar_dollar, "missing_type") {
												_t1399 = _dollar_dollar.GetMissingType()
											}
											return _t1399
										}
										_t1400 := _t1398(msg)
										deconstruct_result783 := _t1400
										if deconstruct_result783 != nil {
											unwrapped784 := deconstruct_result783
											p.pretty_missing_type(unwrapped784)
										} else {
											_t1401 := func(_dollar_dollar *pb.Type) *pb.DecimalType {
												var _t1402 *pb.DecimalType
												if hasProtoField(_dollar_dollar, "decimal_type") {
													_t1402 = _dollar_dollar.GetDecimalType()
												}
												return _t1402
											}
											_t1403 := _t1401(msg)
											deconstruct_result781 := _t1403
											if deconstruct_result781 != nil {
												unwrapped782 := deconstruct_result781
												p.pretty_decimal_type(unwrapped782)
											} else {
												_t1404 := func(_dollar_dollar *pb.Type) *pb.BooleanType {
													var _t1405 *pb.BooleanType
													if hasProtoField(_dollar_dollar, "boolean_type") {
														_t1405 = _dollar_dollar.GetBooleanType()
													}
													return _t1405
												}
												_t1406 := _t1404(msg)
												deconstruct_result779 := _t1406
												if deconstruct_result779 != nil {
													unwrapped780 := deconstruct_result779
													p.pretty_boolean_type(unwrapped780)
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
	fields802 := msg
	_ = fields802
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields803 := msg
	_ = fields803
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields804 := msg
	_ = fields804
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields805 := msg
	_ = fields805
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields806 := msg
	_ = fields806
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields807 := msg
	_ = fields807
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields808 := msg
	_ = fields808
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields809 := msg
	_ = fields809
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields810 := msg
	_ = fields810
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat815 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat815 != nil {
		p.write(*flat815)
		return nil
	} else {
		_t1407 := func(_dollar_dollar *pb.DecimalType) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		}
		_t1408 := _t1407(msg)
		fields811 := _t1408
		unwrapped_fields812 := fields811
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field813 := unwrapped_fields812[0].(int64)
		p.write(fmt.Sprintf("%d", field813))
		p.newline()
		field814 := unwrapped_fields812[1].(int64)
		p.write(fmt.Sprintf("%d", field814))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields816 := msg
	_ = fields816
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat820 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat820 != nil {
		p.write(*flat820)
		return nil
	} else {
		fields817 := msg
		p.write("|")
		if !(len(fields817) == 0) {
			p.write(" ")
			for i819, elem818 := range fields817 {
				if (i819 > 0) {
					p.newline()
				}
				p.pretty_binding(elem818)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat847 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat847 != nil {
		p.write(*flat847)
		return nil
	} else {
		_t1409 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
			var _t1410 *pb.Conjunction
			if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
				_t1410 = _dollar_dollar.GetConjunction()
			}
			return _t1410
		}
		_t1411 := _t1409(msg)
		deconstruct_result845 := _t1411
		if deconstruct_result845 != nil {
			unwrapped846 := deconstruct_result845
			p.pretty_true(unwrapped846)
		} else {
			_t1412 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
				var _t1413 *pb.Disjunction
				if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
					_t1413 = _dollar_dollar.GetDisjunction()
				}
				return _t1413
			}
			_t1414 := _t1412(msg)
			deconstruct_result843 := _t1414
			if deconstruct_result843 != nil {
				unwrapped844 := deconstruct_result843
				p.pretty_false(unwrapped844)
			} else {
				_t1415 := func(_dollar_dollar *pb.Formula) *pb.Exists {
					var _t1416 *pb.Exists
					if hasProtoField(_dollar_dollar, "exists") {
						_t1416 = _dollar_dollar.GetExists()
					}
					return _t1416
				}
				_t1417 := _t1415(msg)
				deconstruct_result841 := _t1417
				if deconstruct_result841 != nil {
					unwrapped842 := deconstruct_result841
					p.pretty_exists(unwrapped842)
				} else {
					_t1418 := func(_dollar_dollar *pb.Formula) *pb.Reduce {
						var _t1419 *pb.Reduce
						if hasProtoField(_dollar_dollar, "reduce") {
							_t1419 = _dollar_dollar.GetReduce()
						}
						return _t1419
					}
					_t1420 := _t1418(msg)
					deconstruct_result839 := _t1420
					if deconstruct_result839 != nil {
						unwrapped840 := deconstruct_result839
						p.pretty_reduce(unwrapped840)
					} else {
						_t1421 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
							var _t1422 *pb.Conjunction
							if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
								_t1422 = _dollar_dollar.GetConjunction()
							}
							return _t1422
						}
						_t1423 := _t1421(msg)
						deconstruct_result837 := _t1423
						if deconstruct_result837 != nil {
							unwrapped838 := deconstruct_result837
							p.pretty_conjunction(unwrapped838)
						} else {
							_t1424 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
								var _t1425 *pb.Disjunction
								if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
									_t1425 = _dollar_dollar.GetDisjunction()
								}
								return _t1425
							}
							_t1426 := _t1424(msg)
							deconstruct_result835 := _t1426
							if deconstruct_result835 != nil {
								unwrapped836 := deconstruct_result835
								p.pretty_disjunction(unwrapped836)
							} else {
								_t1427 := func(_dollar_dollar *pb.Formula) *pb.Not {
									var _t1428 *pb.Not
									if hasProtoField(_dollar_dollar, "not") {
										_t1428 = _dollar_dollar.GetNot()
									}
									return _t1428
								}
								_t1429 := _t1427(msg)
								deconstruct_result833 := _t1429
								if deconstruct_result833 != nil {
									unwrapped834 := deconstruct_result833
									p.pretty_not(unwrapped834)
								} else {
									_t1430 := func(_dollar_dollar *pb.Formula) *pb.FFI {
										var _t1431 *pb.FFI
										if hasProtoField(_dollar_dollar, "ffi") {
											_t1431 = _dollar_dollar.GetFfi()
										}
										return _t1431
									}
									_t1432 := _t1430(msg)
									deconstruct_result831 := _t1432
									if deconstruct_result831 != nil {
										unwrapped832 := deconstruct_result831
										p.pretty_ffi(unwrapped832)
									} else {
										_t1433 := func(_dollar_dollar *pb.Formula) *pb.Atom {
											var _t1434 *pb.Atom
											if hasProtoField(_dollar_dollar, "atom") {
												_t1434 = _dollar_dollar.GetAtom()
											}
											return _t1434
										}
										_t1435 := _t1433(msg)
										deconstruct_result829 := _t1435
										if deconstruct_result829 != nil {
											unwrapped830 := deconstruct_result829
											p.pretty_atom(unwrapped830)
										} else {
											_t1436 := func(_dollar_dollar *pb.Formula) *pb.Pragma {
												var _t1437 *pb.Pragma
												if hasProtoField(_dollar_dollar, "pragma") {
													_t1437 = _dollar_dollar.GetPragma()
												}
												return _t1437
											}
											_t1438 := _t1436(msg)
											deconstruct_result827 := _t1438
											if deconstruct_result827 != nil {
												unwrapped828 := deconstruct_result827
												p.pretty_pragma(unwrapped828)
											} else {
												_t1439 := func(_dollar_dollar *pb.Formula) *pb.Primitive {
													var _t1440 *pb.Primitive
													if hasProtoField(_dollar_dollar, "primitive") {
														_t1440 = _dollar_dollar.GetPrimitive()
													}
													return _t1440
												}
												_t1441 := _t1439(msg)
												deconstruct_result825 := _t1441
												if deconstruct_result825 != nil {
													unwrapped826 := deconstruct_result825
													p.pretty_primitive(unwrapped826)
												} else {
													_t1442 := func(_dollar_dollar *pb.Formula) *pb.RelAtom {
														var _t1443 *pb.RelAtom
														if hasProtoField(_dollar_dollar, "rel_atom") {
															_t1443 = _dollar_dollar.GetRelAtom()
														}
														return _t1443
													}
													_t1444 := _t1442(msg)
													deconstruct_result823 := _t1444
													if deconstruct_result823 != nil {
														unwrapped824 := deconstruct_result823
														p.pretty_rel_atom(unwrapped824)
													} else {
														_t1445 := func(_dollar_dollar *pb.Formula) *pb.Cast {
															var _t1446 *pb.Cast
															if hasProtoField(_dollar_dollar, "cast") {
																_t1446 = _dollar_dollar.GetCast()
															}
															return _t1446
														}
														_t1447 := _t1445(msg)
														deconstruct_result821 := _t1447
														if deconstruct_result821 != nil {
															unwrapped822 := deconstruct_result821
															p.pretty_cast(unwrapped822)
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
	fields848 := msg
	_ = fields848
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields849 := msg
	_ = fields849
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat854 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat854 != nil {
		p.write(*flat854)
		return nil
	} else {
		_t1448 := func(_dollar_dollar *pb.Exists) []interface{} {
			_t1449 := p.deconstruct_bindings(_dollar_dollar.GetBody())
			return []interface{}{_t1449, _dollar_dollar.GetBody().GetValue()}
		}
		_t1450 := _t1448(msg)
		fields850 := _t1450
		unwrapped_fields851 := fields850
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field852 := unwrapped_fields851[0].([]interface{})
		p.pretty_bindings(field852)
		p.newline()
		field853 := unwrapped_fields851[1].(*pb.Formula)
		p.pretty_formula(field853)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat860 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat860 != nil {
		p.write(*flat860)
		return nil
	} else {
		_t1451 := func(_dollar_dollar *pb.Reduce) []interface{} {
			return []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		}
		_t1452 := _t1451(msg)
		fields855 := _t1452
		unwrapped_fields856 := fields855
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field857 := unwrapped_fields856[0].(*pb.Abstraction)
		p.pretty_abstraction(field857)
		p.newline()
		field858 := unwrapped_fields856[1].(*pb.Abstraction)
		p.pretty_abstraction(field858)
		p.newline()
		field859 := unwrapped_fields856[2].([]*pb.Term)
		p.pretty_terms(field859)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat864 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat864 != nil {
		p.write(*flat864)
		return nil
	} else {
		fields861 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields861) == 0) {
			p.newline()
			for i863, elem862 := range fields861 {
				if (i863 > 0) {
					p.newline()
				}
				p.pretty_term(elem862)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat869 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat869 != nil {
		p.write(*flat869)
		return nil
	} else {
		_t1453 := func(_dollar_dollar *pb.Term) *pb.Var {
			var _t1454 *pb.Var
			if hasProtoField(_dollar_dollar, "var") {
				_t1454 = _dollar_dollar.GetVar()
			}
			return _t1454
		}
		_t1455 := _t1453(msg)
		deconstruct_result867 := _t1455
		if deconstruct_result867 != nil {
			unwrapped868 := deconstruct_result867
			p.pretty_var(unwrapped868)
		} else {
			_t1456 := func(_dollar_dollar *pb.Term) *pb.Value {
				var _t1457 *pb.Value
				if hasProtoField(_dollar_dollar, "constant") {
					_t1457 = _dollar_dollar.GetConstant()
				}
				return _t1457
			}
			_t1458 := _t1456(msg)
			deconstruct_result865 := _t1458
			if deconstruct_result865 != nil {
				unwrapped866 := deconstruct_result865
				p.pretty_constant(unwrapped866)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat872 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat872 != nil {
		p.write(*flat872)
		return nil
	} else {
		_t1459 := func(_dollar_dollar *pb.Var) string {
			return _dollar_dollar.GetName()
		}
		_t1460 := _t1459(msg)
		fields870 := _t1460
		unwrapped_fields871 := fields870
		p.write(unwrapped_fields871)
	}
	return nil
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) interface{} {
	flat874 := p.tryFlat(msg, func() { p.pretty_constant(msg) })
	if flat874 != nil {
		p.write(*flat874)
		return nil
	} else {
		fields873 := msg
		p.pretty_value(fields873)
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat879 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat879 != nil {
		p.write(*flat879)
		return nil
	} else {
		_t1461 := func(_dollar_dollar *pb.Conjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1462 := _t1461(msg)
		fields875 := _t1462
		unwrapped_fields876 := fields875
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields876) == 0) {
			p.newline()
			for i878, elem877 := range unwrapped_fields876 {
				if (i878 > 0) {
					p.newline()
				}
				p.pretty_formula(elem877)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat884 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat884 != nil {
		p.write(*flat884)
		return nil
	} else {
		_t1463 := func(_dollar_dollar *pb.Disjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1464 := _t1463(msg)
		fields880 := _t1464
		unwrapped_fields881 := fields880
		p.write("(")
		p.write("or")
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

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat887 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat887 != nil {
		p.write(*flat887)
		return nil
	} else {
		_t1465 := func(_dollar_dollar *pb.Not) *pb.Formula {
			return _dollar_dollar.GetArg()
		}
		_t1466 := _t1465(msg)
		fields885 := _t1466
		unwrapped_fields886 := fields885
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields886)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat893 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat893 != nil {
		p.write(*flat893)
		return nil
	} else {
		_t1467 := func(_dollar_dollar *pb.FFI) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		}
		_t1468 := _t1467(msg)
		fields888 := _t1468
		unwrapped_fields889 := fields888
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field890 := unwrapped_fields889[0].(string)
		p.pretty_name(field890)
		p.newline()
		field891 := unwrapped_fields889[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field891)
		p.newline()
		field892 := unwrapped_fields889[2].([]*pb.Term)
		p.pretty_terms(field892)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat895 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat895 != nil {
		p.write(*flat895)
		return nil
	} else {
		fields894 := msg
		p.write(":")
		p.write(fields894)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat899 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat899 != nil {
		p.write(*flat899)
		return nil
	} else {
		fields896 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields896) == 0) {
			p.newline()
			for i898, elem897 := range fields896 {
				if (i898 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem897)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat906 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat906 != nil {
		p.write(*flat906)
		return nil
	} else {
		_t1469 := func(_dollar_dollar *pb.Atom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1470 := _t1469(msg)
		fields900 := _t1470
		unwrapped_fields901 := fields900
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field902 := unwrapped_fields901[0].(*pb.RelationId)
		p.pretty_relation_id(field902)
		field903 := unwrapped_fields901[1].([]*pb.Term)
		if !(len(field903) == 0) {
			p.newline()
			for i905, elem904 := range field903 {
				if (i905 > 0) {
					p.newline()
				}
				p.pretty_term(elem904)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat913 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat913 != nil {
		p.write(*flat913)
		return nil
	} else {
		_t1471 := func(_dollar_dollar *pb.Pragma) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1472 := _t1471(msg)
		fields907 := _t1472
		unwrapped_fields908 := fields907
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field909 := unwrapped_fields908[0].(string)
		p.pretty_name(field909)
		field910 := unwrapped_fields908[1].([]*pb.Term)
		if !(len(field910) == 0) {
			p.newline()
			for i912, elem911 := range field910 {
				if (i912 > 0) {
					p.newline()
				}
				p.pretty_term(elem911)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat929 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat929 != nil {
		p.write(*flat929)
		return nil
	} else {
		_t1473 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1474 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1474 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1474
		}
		_t1475 := _t1473(msg)
		guard_result928 := _t1475
		if guard_result928 != nil {
			p.pretty_eq(msg)
		} else {
			_t1476 := func(_dollar_dollar *pb.Primitive) []interface{} {
				var _t1477 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
					_t1477 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				return _t1477
			}
			_t1478 := _t1476(msg)
			guard_result927 := _t1478
			if guard_result927 != nil {
				p.pretty_lt(msg)
			} else {
				_t1479 := func(_dollar_dollar *pb.Primitive) []interface{} {
					var _t1480 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
						_t1480 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					return _t1480
				}
				_t1481 := _t1479(msg)
				guard_result926 := _t1481
				if guard_result926 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_t1482 := func(_dollar_dollar *pb.Primitive) []interface{} {
						var _t1483 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
							_t1483 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						return _t1483
					}
					_t1484 := _t1482(msg)
					guard_result925 := _t1484
					if guard_result925 != nil {
						p.pretty_gt(msg)
					} else {
						_t1485 := func(_dollar_dollar *pb.Primitive) []interface{} {
							var _t1486 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
								_t1486 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
							}
							return _t1486
						}
						_t1487 := _t1485(msg)
						guard_result924 := _t1487
						if guard_result924 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_t1488 := func(_dollar_dollar *pb.Primitive) []interface{} {
								var _t1489 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
									_t1489 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								return _t1489
							}
							_t1490 := _t1488(msg)
							guard_result923 := _t1490
							if guard_result923 != nil {
								p.pretty_add(msg)
							} else {
								_t1491 := func(_dollar_dollar *pb.Primitive) []interface{} {
									var _t1492 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
										_t1492 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									return _t1492
								}
								_t1493 := _t1491(msg)
								guard_result922 := _t1493
								if guard_result922 != nil {
									p.pretty_minus(msg)
								} else {
									_t1494 := func(_dollar_dollar *pb.Primitive) []interface{} {
										var _t1495 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
											_t1495 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										return _t1495
									}
									_t1496 := _t1494(msg)
									guard_result921 := _t1496
									if guard_result921 != nil {
										p.pretty_multiply(msg)
									} else {
										_t1497 := func(_dollar_dollar *pb.Primitive) []interface{} {
											var _t1498 []interface{}
											if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
												_t1498 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
											}
											return _t1498
										}
										_t1499 := _t1497(msg)
										guard_result920 := _t1499
										if guard_result920 != nil {
											p.pretty_divide(msg)
										} else {
											_t1500 := func(_dollar_dollar *pb.Primitive) []interface{} {
												return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											}
											_t1501 := _t1500(msg)
											fields914 := _t1501
											unwrapped_fields915 := fields914
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field916 := unwrapped_fields915[0].(string)
											p.pretty_name(field916)
											field917 := unwrapped_fields915[1].([]*pb.RelTerm)
											if !(len(field917) == 0) {
												p.newline()
												for i919, elem918 := range field917 {
													if (i919 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem918)
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
	flat934 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat934 != nil {
		p.write(*flat934)
		return nil
	} else {
		_t1502 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1503 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1503 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1503
		}
		_t1504 := _t1502(msg)
		fields930 := _t1504
		unwrapped_fields931 := fields930
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field932 := unwrapped_fields931[0].(*pb.Term)
		p.pretty_term(field932)
		p.newline()
		field933 := unwrapped_fields931[1].(*pb.Term)
		p.pretty_term(field933)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat939 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat939 != nil {
		p.write(*flat939)
		return nil
	} else {
		_t1505 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1506 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1506 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1506
		}
		_t1507 := _t1505(msg)
		fields935 := _t1507
		unwrapped_fields936 := fields935
		p.write("(")
		p.write("<")
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

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat944 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat944 != nil {
		p.write(*flat944)
		return nil
	} else {
		_t1508 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1509 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
				_t1509 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1509
		}
		_t1510 := _t1508(msg)
		fields940 := _t1510
		unwrapped_fields941 := fields940
		p.write("(")
		p.write("<=")
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

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat949 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat949 != nil {
		p.write(*flat949)
		return nil
	} else {
		_t1511 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1512 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
				_t1512 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1512
		}
		_t1513 := _t1511(msg)
		fields945 := _t1513
		unwrapped_fields946 := fields945
		p.write("(")
		p.write(">")
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

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat954 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat954 != nil {
		p.write(*flat954)
		return nil
	} else {
		_t1514 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1515 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
				_t1515 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1515
		}
		_t1516 := _t1514(msg)
		fields950 := _t1516
		unwrapped_fields951 := fields950
		p.write("(")
		p.write(">=")
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

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat960 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat960 != nil {
		p.write(*flat960)
		return nil
	} else {
		_t1517 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1518 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
				_t1518 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1518
		}
		_t1519 := _t1517(msg)
		fields955 := _t1519
		unwrapped_fields956 := fields955
		p.write("(")
		p.write("+")
		p.indentSexp()
		p.newline()
		field957 := unwrapped_fields956[0].(*pb.Term)
		p.pretty_term(field957)
		p.newline()
		field958 := unwrapped_fields956[1].(*pb.Term)
		p.pretty_term(field958)
		p.newline()
		field959 := unwrapped_fields956[2].(*pb.Term)
		p.pretty_term(field959)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat966 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat966 != nil {
		p.write(*flat966)
		return nil
	} else {
		_t1520 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1521 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
				_t1521 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1521
		}
		_t1522 := _t1520(msg)
		fields961 := _t1522
		unwrapped_fields962 := fields961
		p.write("(")
		p.write("-")
		p.indentSexp()
		p.newline()
		field963 := unwrapped_fields962[0].(*pb.Term)
		p.pretty_term(field963)
		p.newline()
		field964 := unwrapped_fields962[1].(*pb.Term)
		p.pretty_term(field964)
		p.newline()
		field965 := unwrapped_fields962[2].(*pb.Term)
		p.pretty_term(field965)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat972 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat972 != nil {
		p.write(*flat972)
		return nil
	} else {
		_t1523 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1524 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
				_t1524 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1524
		}
		_t1525 := _t1523(msg)
		fields967 := _t1525
		unwrapped_fields968 := fields967
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field969 := unwrapped_fields968[0].(*pb.Term)
		p.pretty_term(field969)
		p.newline()
		field970 := unwrapped_fields968[1].(*pb.Term)
		p.pretty_term(field970)
		p.newline()
		field971 := unwrapped_fields968[2].(*pb.Term)
		p.pretty_term(field971)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat978 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat978 != nil {
		p.write(*flat978)
		return nil
	} else {
		_t1526 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1527 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
				_t1527 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1527
		}
		_t1528 := _t1526(msg)
		fields973 := _t1528
		unwrapped_fields974 := fields973
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field975 := unwrapped_fields974[0].(*pb.Term)
		p.pretty_term(field975)
		p.newline()
		field976 := unwrapped_fields974[1].(*pb.Term)
		p.pretty_term(field976)
		p.newline()
		field977 := unwrapped_fields974[2].(*pb.Term)
		p.pretty_term(field977)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat983 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat983 != nil {
		p.write(*flat983)
		return nil
	} else {
		_t1529 := func(_dollar_dollar *pb.RelTerm) *pb.Value {
			var _t1530 *pb.Value
			if hasProtoField(_dollar_dollar, "specialized_value") {
				_t1530 = _dollar_dollar.GetSpecializedValue()
			}
			return _t1530
		}
		_t1531 := _t1529(msg)
		deconstruct_result981 := _t1531
		if deconstruct_result981 != nil {
			unwrapped982 := deconstruct_result981
			p.pretty_specialized_value(unwrapped982)
		} else {
			_t1532 := func(_dollar_dollar *pb.RelTerm) *pb.Term {
				var _t1533 *pb.Term
				if hasProtoField(_dollar_dollar, "term") {
					_t1533 = _dollar_dollar.GetTerm()
				}
				return _t1533
			}
			_t1534 := _t1532(msg)
			deconstruct_result979 := _t1534
			if deconstruct_result979 != nil {
				unwrapped980 := deconstruct_result979
				p.pretty_term(unwrapped980)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat985 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat985 != nil {
		p.write(*flat985)
		return nil
	} else {
		fields984 := msg
		p.write("#")
		p.pretty_value(fields984)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat992 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat992 != nil {
		p.write(*flat992)
		return nil
	} else {
		_t1535 := func(_dollar_dollar *pb.RelAtom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1536 := _t1535(msg)
		fields986 := _t1536
		unwrapped_fields987 := fields986
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field988 := unwrapped_fields987[0].(string)
		p.pretty_name(field988)
		field989 := unwrapped_fields987[1].([]*pb.RelTerm)
		if !(len(field989) == 0) {
			p.newline()
			for i991, elem990 := range field989 {
				if (i991 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem990)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat997 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat997 != nil {
		p.write(*flat997)
		return nil
	} else {
		_t1537 := func(_dollar_dollar *pb.Cast) []interface{} {
			return []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		}
		_t1538 := _t1537(msg)
		fields993 := _t1538
		unwrapped_fields994 := fields993
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field995 := unwrapped_fields994[0].(*pb.Term)
		p.pretty_term(field995)
		p.newline()
		field996 := unwrapped_fields994[1].(*pb.Term)
		p.pretty_term(field996)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1001 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1001 != nil {
		p.write(*flat1001)
		return nil
	} else {
		fields998 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields998) == 0) {
			p.newline()
			for i1000, elem999 := range fields998 {
				if (i1000 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem999)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1008 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1008 != nil {
		p.write(*flat1008)
		return nil
	} else {
		_t1539 := func(_dollar_dollar *pb.Attribute) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		}
		_t1540 := _t1539(msg)
		fields1002 := _t1540
		unwrapped_fields1003 := fields1002
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1004 := unwrapped_fields1003[0].(string)
		p.pretty_name(field1004)
		field1005 := unwrapped_fields1003[1].([]*pb.Value)
		if !(len(field1005) == 0) {
			p.newline()
			for i1007, elem1006 := range field1005 {
				if (i1007 > 0) {
					p.newline()
				}
				p.pretty_value(elem1006)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1015 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1015 != nil {
		p.write(*flat1015)
		return nil
	} else {
		_t1541 := func(_dollar_dollar *pb.Algorithm) []interface{} {
			return []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		}
		_t1542 := _t1541(msg)
		fields1009 := _t1542
		unwrapped_fields1010 := fields1009
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1011 := unwrapped_fields1010[0].([]*pb.RelationId)
		if !(len(field1011) == 0) {
			p.newline()
			for i1013, elem1012 := range field1011 {
				if (i1013 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1012)
			}
		}
		p.newline()
		field1014 := unwrapped_fields1010[1].(*pb.Script)
		p.pretty_script(field1014)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1020 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1020 != nil {
		p.write(*flat1020)
		return nil
	} else {
		_t1543 := func(_dollar_dollar *pb.Script) []*pb.Construct {
			return _dollar_dollar.GetConstructs()
		}
		_t1544 := _t1543(msg)
		fields1016 := _t1544
		unwrapped_fields1017 := fields1016
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1017) == 0) {
			p.newline()
			for i1019, elem1018 := range unwrapped_fields1017 {
				if (i1019 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1018)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1025 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1025 != nil {
		p.write(*flat1025)
		return nil
	} else {
		_t1545 := func(_dollar_dollar *pb.Construct) *pb.Loop {
			var _t1546 *pb.Loop
			if hasProtoField(_dollar_dollar, "loop") {
				_t1546 = _dollar_dollar.GetLoop()
			}
			return _t1546
		}
		_t1547 := _t1545(msg)
		deconstruct_result1023 := _t1547
		if deconstruct_result1023 != nil {
			unwrapped1024 := deconstruct_result1023
			p.pretty_loop(unwrapped1024)
		} else {
			_t1548 := func(_dollar_dollar *pb.Construct) *pb.Instruction {
				var _t1549 *pb.Instruction
				if hasProtoField(_dollar_dollar, "instruction") {
					_t1549 = _dollar_dollar.GetInstruction()
				}
				return _t1549
			}
			_t1550 := _t1548(msg)
			deconstruct_result1021 := _t1550
			if deconstruct_result1021 != nil {
				unwrapped1022 := deconstruct_result1021
				p.pretty_instruction(unwrapped1022)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1030 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1030 != nil {
		p.write(*flat1030)
		return nil
	} else {
		_t1551 := func(_dollar_dollar *pb.Loop) []interface{} {
			return []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		}
		_t1552 := _t1551(msg)
		fields1026 := _t1552
		unwrapped_fields1027 := fields1026
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1028 := unwrapped_fields1027[0].([]*pb.Instruction)
		p.pretty_init(field1028)
		p.newline()
		field1029 := unwrapped_fields1027[1].(*pb.Script)
		p.pretty_script(field1029)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1034 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1034 != nil {
		p.write(*flat1034)
		return nil
	} else {
		fields1031 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1031) == 0) {
			p.newline()
			for i1033, elem1032 := range fields1031 {
				if (i1033 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1032)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1045 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1045 != nil {
		p.write(*flat1045)
		return nil
	} else {
		_t1553 := func(_dollar_dollar *pb.Instruction) *pb.Assign {
			var _t1554 *pb.Assign
			if hasProtoField(_dollar_dollar, "assign") {
				_t1554 = _dollar_dollar.GetAssign()
			}
			return _t1554
		}
		_t1555 := _t1553(msg)
		deconstruct_result1043 := _t1555
		if deconstruct_result1043 != nil {
			unwrapped1044 := deconstruct_result1043
			p.pretty_assign(unwrapped1044)
		} else {
			_t1556 := func(_dollar_dollar *pb.Instruction) *pb.Upsert {
				var _t1557 *pb.Upsert
				if hasProtoField(_dollar_dollar, "upsert") {
					_t1557 = _dollar_dollar.GetUpsert()
				}
				return _t1557
			}
			_t1558 := _t1556(msg)
			deconstruct_result1041 := _t1558
			if deconstruct_result1041 != nil {
				unwrapped1042 := deconstruct_result1041
				p.pretty_upsert(unwrapped1042)
			} else {
				_t1559 := func(_dollar_dollar *pb.Instruction) *pb.Break {
					var _t1560 *pb.Break
					if hasProtoField(_dollar_dollar, "break") {
						_t1560 = _dollar_dollar.GetBreak()
					}
					return _t1560
				}
				_t1561 := _t1559(msg)
				deconstruct_result1039 := _t1561
				if deconstruct_result1039 != nil {
					unwrapped1040 := deconstruct_result1039
					p.pretty_break(unwrapped1040)
				} else {
					_t1562 := func(_dollar_dollar *pb.Instruction) *pb.MonoidDef {
						var _t1563 *pb.MonoidDef
						if hasProtoField(_dollar_dollar, "monoid_def") {
							_t1563 = _dollar_dollar.GetMonoidDef()
						}
						return _t1563
					}
					_t1564 := _t1562(msg)
					deconstruct_result1037 := _t1564
					if deconstruct_result1037 != nil {
						unwrapped1038 := deconstruct_result1037
						p.pretty_monoid_def(unwrapped1038)
					} else {
						_t1565 := func(_dollar_dollar *pb.Instruction) *pb.MonusDef {
							var _t1566 *pb.MonusDef
							if hasProtoField(_dollar_dollar, "monus_def") {
								_t1566 = _dollar_dollar.GetMonusDef()
							}
							return _t1566
						}
						_t1567 := _t1565(msg)
						deconstruct_result1035 := _t1567
						if deconstruct_result1035 != nil {
							unwrapped1036 := deconstruct_result1035
							p.pretty_monus_def(unwrapped1036)
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
	flat1052 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1052 != nil {
		p.write(*flat1052)
		return nil
	} else {
		_t1568 := func(_dollar_dollar *pb.Assign) []interface{} {
			var _t1569 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1569 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1569}
		}
		_t1570 := _t1568(msg)
		fields1046 := _t1570
		unwrapped_fields1047 := fields1046
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1048 := unwrapped_fields1047[0].(*pb.RelationId)
		p.pretty_relation_id(field1048)
		p.newline()
		field1049 := unwrapped_fields1047[1].(*pb.Abstraction)
		p.pretty_abstraction(field1049)
		field1050 := unwrapped_fields1047[2].([]*pb.Attribute)
		if field1050 != nil {
			p.newline()
			opt_val1051 := field1050
			p.pretty_attrs(opt_val1051)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1059 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1059 != nil {
		p.write(*flat1059)
		return nil
	} else {
		_t1571 := func(_dollar_dollar *pb.Upsert) []interface{} {
			var _t1572 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1572 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1572}
		}
		_t1573 := _t1571(msg)
		fields1053 := _t1573
		unwrapped_fields1054 := fields1053
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1055 := unwrapped_fields1054[0].(*pb.RelationId)
		p.pretty_relation_id(field1055)
		p.newline()
		field1056 := unwrapped_fields1054[1].([]interface{})
		p.pretty_abstraction_with_arity(field1056)
		field1057 := unwrapped_fields1054[2].([]*pb.Attribute)
		if field1057 != nil {
			p.newline()
			opt_val1058 := field1057
			p.pretty_attrs(opt_val1058)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1064 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1064 != nil {
		p.write(*flat1064)
		return nil
	} else {
		_t1574 := func(_dollar_dollar []interface{}) []interface{} {
			_t1575 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
			return []interface{}{_t1575, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		}
		_t1576 := _t1574(msg)
		fields1060 := _t1576
		unwrapped_fields1061 := fields1060
		p.write("(")
		p.indent()
		field1062 := unwrapped_fields1061[0].([]interface{})
		p.pretty_bindings(field1062)
		p.newline()
		field1063 := unwrapped_fields1061[1].(*pb.Formula)
		p.pretty_formula(field1063)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1071 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1071 != nil {
		p.write(*flat1071)
		return nil
	} else {
		_t1577 := func(_dollar_dollar *pb.Break) []interface{} {
			var _t1578 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1578 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1578}
		}
		_t1579 := _t1577(msg)
		fields1065 := _t1579
		unwrapped_fields1066 := fields1065
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1067 := unwrapped_fields1066[0].(*pb.RelationId)
		p.pretty_relation_id(field1067)
		p.newline()
		field1068 := unwrapped_fields1066[1].(*pb.Abstraction)
		p.pretty_abstraction(field1068)
		field1069 := unwrapped_fields1066[2].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1079 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1079 != nil {
		p.write(*flat1079)
		return nil
	} else {
		_t1580 := func(_dollar_dollar *pb.MonoidDef) []interface{} {
			var _t1581 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1581 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1581}
		}
		_t1582 := _t1580(msg)
		fields1072 := _t1582
		unwrapped_fields1073 := fields1072
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1074 := unwrapped_fields1073[0].(*pb.Monoid)
		p.pretty_monoid(field1074)
		p.newline()
		field1075 := unwrapped_fields1073[1].(*pb.RelationId)
		p.pretty_relation_id(field1075)
		p.newline()
		field1076 := unwrapped_fields1073[2].([]interface{})
		p.pretty_abstraction_with_arity(field1076)
		field1077 := unwrapped_fields1073[3].([]*pb.Attribute)
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

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1088 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1088 != nil {
		p.write(*flat1088)
		return nil
	} else {
		_t1583 := func(_dollar_dollar *pb.Monoid) *pb.OrMonoid {
			var _t1584 *pb.OrMonoid
			if hasProtoField(_dollar_dollar, "or_monoid") {
				_t1584 = _dollar_dollar.GetOrMonoid()
			}
			return _t1584
		}
		_t1585 := _t1583(msg)
		deconstruct_result1086 := _t1585
		if deconstruct_result1086 != nil {
			unwrapped1087 := deconstruct_result1086
			p.pretty_or_monoid(unwrapped1087)
		} else {
			_t1586 := func(_dollar_dollar *pb.Monoid) *pb.MinMonoid {
				var _t1587 *pb.MinMonoid
				if hasProtoField(_dollar_dollar, "min_monoid") {
					_t1587 = _dollar_dollar.GetMinMonoid()
				}
				return _t1587
			}
			_t1588 := _t1586(msg)
			deconstruct_result1084 := _t1588
			if deconstruct_result1084 != nil {
				unwrapped1085 := deconstruct_result1084
				p.pretty_min_monoid(unwrapped1085)
			} else {
				_t1589 := func(_dollar_dollar *pb.Monoid) *pb.MaxMonoid {
					var _t1590 *pb.MaxMonoid
					if hasProtoField(_dollar_dollar, "max_monoid") {
						_t1590 = _dollar_dollar.GetMaxMonoid()
					}
					return _t1590
				}
				_t1591 := _t1589(msg)
				deconstruct_result1082 := _t1591
				if deconstruct_result1082 != nil {
					unwrapped1083 := deconstruct_result1082
					p.pretty_max_monoid(unwrapped1083)
				} else {
					_t1592 := func(_dollar_dollar *pb.Monoid) *pb.SumMonoid {
						var _t1593 *pb.SumMonoid
						if hasProtoField(_dollar_dollar, "sum_monoid") {
							_t1593 = _dollar_dollar.GetSumMonoid()
						}
						return _t1593
					}
					_t1594 := _t1592(msg)
					deconstruct_result1080 := _t1594
					if deconstruct_result1080 != nil {
						unwrapped1081 := deconstruct_result1080
						p.pretty_sum_monoid(unwrapped1081)
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
	fields1089 := msg
	_ = fields1089
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1092 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1092 != nil {
		p.write(*flat1092)
		return nil
	} else {
		_t1595 := func(_dollar_dollar *pb.MinMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1596 := _t1595(msg)
		fields1090 := _t1596
		unwrapped_fields1091 := fields1090
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1091)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1095 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1095 != nil {
		p.write(*flat1095)
		return nil
	} else {
		_t1597 := func(_dollar_dollar *pb.MaxMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1598 := _t1597(msg)
		fields1093 := _t1598
		unwrapped_fields1094 := fields1093
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1094)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1098 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1098 != nil {
		p.write(*flat1098)
		return nil
	} else {
		_t1599 := func(_dollar_dollar *pb.SumMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1600 := _t1599(msg)
		fields1096 := _t1600
		unwrapped_fields1097 := fields1096
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1097)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1106 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1106 != nil {
		p.write(*flat1106)
		return nil
	} else {
		_t1601 := func(_dollar_dollar *pb.MonusDef) []interface{} {
			var _t1602 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1602 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1602}
		}
		_t1603 := _t1601(msg)
		fields1099 := _t1603
		unwrapped_fields1100 := fields1099
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1101 := unwrapped_fields1100[0].(*pb.Monoid)
		p.pretty_monoid(field1101)
		p.newline()
		field1102 := unwrapped_fields1100[1].(*pb.RelationId)
		p.pretty_relation_id(field1102)
		p.newline()
		field1103 := unwrapped_fields1100[2].([]interface{})
		p.pretty_abstraction_with_arity(field1103)
		field1104 := unwrapped_fields1100[3].([]*pb.Attribute)
		if field1104 != nil {
			p.newline()
			opt_val1105 := field1104
			p.pretty_attrs(opt_val1105)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1113 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1113 != nil {
		p.write(*flat1113)
		return nil
	} else {
		_t1604 := func(_dollar_dollar *pb.Constraint) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		}
		_t1605 := _t1604(msg)
		fields1107 := _t1605
		unwrapped_fields1108 := fields1107
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1109 := unwrapped_fields1108[0].(*pb.RelationId)
		p.pretty_relation_id(field1109)
		p.newline()
		field1110 := unwrapped_fields1108[1].(*pb.Abstraction)
		p.pretty_abstraction(field1110)
		p.newline()
		field1111 := unwrapped_fields1108[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1111)
		p.newline()
		field1112 := unwrapped_fields1108[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1112)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1117 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1117 != nil {
		p.write(*flat1117)
		return nil
	} else {
		fields1114 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1114) == 0) {
			p.newline()
			for i1116, elem1115 := range fields1114 {
				if (i1116 > 0) {
					p.newline()
				}
				p.pretty_var(elem1115)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1121 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1121 != nil {
		p.write(*flat1121)
		return nil
	} else {
		fields1118 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1118) == 0) {
			p.newline()
			for i1120, elem1119 := range fields1118 {
				if (i1120 > 0) {
					p.newline()
				}
				p.pretty_var(elem1119)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1128 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1128 != nil {
		p.write(*flat1128)
		return nil
	} else {
		_t1606 := func(_dollar_dollar *pb.Data) *pb.EDB {
			var _t1607 *pb.EDB
			if hasProtoField(_dollar_dollar, "edb") {
				_t1607 = _dollar_dollar.GetEdb()
			}
			return _t1607
		}
		_t1608 := _t1606(msg)
		deconstruct_result1126 := _t1608
		if deconstruct_result1126 != nil {
			unwrapped1127 := deconstruct_result1126
			p.pretty_edb(unwrapped1127)
		} else {
			_t1609 := func(_dollar_dollar *pb.Data) *pb.BeTreeRelation {
				var _t1610 *pb.BeTreeRelation
				if hasProtoField(_dollar_dollar, "betree_relation") {
					_t1610 = _dollar_dollar.GetBetreeRelation()
				}
				return _t1610
			}
			_t1611 := _t1609(msg)
			deconstruct_result1124 := _t1611
			if deconstruct_result1124 != nil {
				unwrapped1125 := deconstruct_result1124
				p.pretty_betree_relation(unwrapped1125)
			} else {
				_t1612 := func(_dollar_dollar *pb.Data) *pb.CSVData {
					var _t1613 *pb.CSVData
					if hasProtoField(_dollar_dollar, "csv_data") {
						_t1613 = _dollar_dollar.GetCsvData()
					}
					return _t1613
				}
				_t1614 := _t1612(msg)
				deconstruct_result1122 := _t1614
				if deconstruct_result1122 != nil {
					unwrapped1123 := deconstruct_result1122
					p.pretty_csv_data(unwrapped1123)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb(msg *pb.EDB) interface{} {
	flat1134 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1134 != nil {
		p.write(*flat1134)
		return nil
	} else {
		_t1615 := func(_dollar_dollar *pb.EDB) []interface{} {
			return []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		}
		_t1616 := _t1615(msg)
		fields1129 := _t1616
		unwrapped_fields1130 := fields1129
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1131 := unwrapped_fields1130[0].(*pb.RelationId)
		p.pretty_relation_id(field1131)
		p.newline()
		field1132 := unwrapped_fields1130[1].([]string)
		p.pretty_edb_path(field1132)
		p.newline()
		field1133 := unwrapped_fields1130[2].([]*pb.Type)
		p.pretty_edb_types(field1133)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1138 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1138 != nil {
		p.write(*flat1138)
		return nil
	} else {
		fields1135 := msg
		p.write("[")
		p.indent()
		for i1137, elem1136 := range fields1135 {
			if (i1137 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1136))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1142 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1142 != nil {
		p.write(*flat1142)
		return nil
	} else {
		fields1139 := msg
		p.write("[")
		p.indent()
		for i1141, elem1140 := range fields1139 {
			if (i1141 > 0) {
				p.newline()
			}
			p.pretty_type(elem1140)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1147 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1147 != nil {
		p.write(*flat1147)
		return nil
	} else {
		_t1617 := func(_dollar_dollar *pb.BeTreeRelation) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		}
		_t1618 := _t1617(msg)
		fields1143 := _t1618
		unwrapped_fields1144 := fields1143
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1145 := unwrapped_fields1144[0].(*pb.RelationId)
		p.pretty_relation_id(field1145)
		p.newline()
		field1146 := unwrapped_fields1144[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1146)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1153 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1153 != nil {
		p.write(*flat1153)
		return nil
	} else {
		_t1619 := func(_dollar_dollar *pb.BeTreeInfo) []interface{} {
			_t1620 := p.deconstruct_betree_info_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1620}
		}
		_t1621 := _t1619(msg)
		fields1148 := _t1621
		unwrapped_fields1149 := fields1148
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1150 := unwrapped_fields1149[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1150)
		p.newline()
		field1151 := unwrapped_fields1149[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1151)
		p.newline()
		field1152 := unwrapped_fields1149[2].([][]interface{})
		p.pretty_config_dict(field1152)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1157 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1157 != nil {
		p.write(*flat1157)
		return nil
	} else {
		fields1154 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1154) == 0) {
			p.newline()
			for i1156, elem1155 := range fields1154 {
				if (i1156 > 0) {
					p.newline()
				}
				p.pretty_type(elem1155)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1161 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1161 != nil {
		p.write(*flat1161)
		return nil
	} else {
		fields1158 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1158) == 0) {
			p.newline()
			for i1160, elem1159 := range fields1158 {
				if (i1160 > 0) {
					p.newline()
				}
				p.pretty_type(elem1159)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1168 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1168 != nil {
		p.write(*flat1168)
		return nil
	} else {
		_t1622 := func(_dollar_dollar *pb.CSVData) []interface{} {
			return []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		}
		_t1623 := _t1622(msg)
		fields1162 := _t1623
		unwrapped_fields1163 := fields1162
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1164 := unwrapped_fields1163[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1164)
		p.newline()
		field1165 := unwrapped_fields1163[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1165)
		p.newline()
		field1166 := unwrapped_fields1163[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1166)
		p.newline()
		field1167 := unwrapped_fields1163[3].(string)
		p.pretty_csv_asof(field1167)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1175 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1175 != nil {
		p.write(*flat1175)
		return nil
	} else {
		_t1624 := func(_dollar_dollar *pb.CSVLocator) []interface{} {
			var _t1625 []string
			if !(len(_dollar_dollar.GetPaths()) == 0) {
				_t1625 = _dollar_dollar.GetPaths()
			}
			var _t1626 *string
			if string(_dollar_dollar.GetInlineData()) != "" {
				_t1626 = ptr(string(_dollar_dollar.GetInlineData()))
			}
			return []interface{}{_t1625, _t1626}
		}
		_t1627 := _t1624(msg)
		fields1169 := _t1627
		unwrapped_fields1170 := fields1169
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1171 := unwrapped_fields1170[0].([]string)
		if field1171 != nil {
			p.newline()
			opt_val1172 := field1171
			p.pretty_csv_locator_paths(opt_val1172)
		}
		field1173 := unwrapped_fields1170[1].(*string)
		if field1173 != nil {
			p.newline()
			opt_val1174 := *field1173
			p.pretty_csv_locator_inline_data(opt_val1174)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		fields1176 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1176) == 0) {
			p.newline()
			for i1178, elem1177 := range fields1176 {
				if (i1178 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1177))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1181 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1181 != nil {
		p.write(*flat1181)
		return nil
	} else {
		fields1180 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1180))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1184 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1184 != nil {
		p.write(*flat1184)
		return nil
	} else {
		_t1628 := func(_dollar_dollar *pb.CSVConfig) [][]interface{} {
			_t1629 := p.deconstruct_csv_config(_dollar_dollar)
			return _t1629
		}
		_t1630 := _t1628(msg)
		fields1182 := _t1630
		unwrapped_fields1183 := fields1182
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1183)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1188 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1188 != nil {
		p.write(*flat1188)
		return nil
	} else {
		fields1185 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1185) == 0) {
			p.newline()
			for i1187, elem1186 := range fields1185 {
				if (i1187 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1186)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1197 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1197 != nil {
		p.write(*flat1197)
		return nil
	} else {
		_t1631 := func(_dollar_dollar *pb.GNFColumn) []interface{} {
			var _t1632 *pb.RelationId
			if hasProtoField(_dollar_dollar, "target_id") {
				_t1632 = _dollar_dollar.GetTargetId()
			}
			return []interface{}{_dollar_dollar.GetColumnPath(), _t1632, _dollar_dollar.GetTypes()}
		}
		_t1633 := _t1631(msg)
		fields1189 := _t1633
		unwrapped_fields1190 := fields1189
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1191 := unwrapped_fields1190[0].([]string)
		p.pretty_gnf_column_path(field1191)
		field1192 := unwrapped_fields1190[1].(*pb.RelationId)
		if field1192 != nil {
			p.newline()
			opt_val1193 := field1192
			p.pretty_relation_id(opt_val1193)
		}
		p.newline()
		p.write("[")
		field1194 := unwrapped_fields1190[2].([]*pb.Type)
		for i1196, elem1195 := range field1194 {
			if (i1196 > 0) {
				p.newline()
			}
			p.pretty_type(elem1195)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1204 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1204 != nil {
		p.write(*flat1204)
		return nil
	} else {
		_t1634 := func(_dollar_dollar []string) *string {
			var _t1635 *string
			if int64(len(_dollar_dollar)) == 1 {
				_t1635 = ptr(_dollar_dollar[0])
			}
			return _t1635
		}
		_t1636 := _t1634(msg)
		deconstruct_result1202 := _t1636
		if deconstruct_result1202 != nil {
			unwrapped1203 := *deconstruct_result1202
			p.write(p.formatStringValue(unwrapped1203))
		} else {
			_t1637 := func(_dollar_dollar []string) []string {
				var _t1638 []string
				if int64(len(_dollar_dollar)) != 1 {
					_t1638 = _dollar_dollar
				}
				return _t1638
			}
			_t1639 := _t1637(msg)
			deconstruct_result1198 := _t1639
			if deconstruct_result1198 != nil {
				unwrapped1199 := deconstruct_result1198
				p.write("[")
				p.indent()
				for i1201, elem1200 := range unwrapped1199 {
					if (i1201 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1200))
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
	flat1206 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1206 != nil {
		p.write(*flat1206)
		return nil
	} else {
		fields1205 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1205))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1209 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1209 != nil {
		p.write(*flat1209)
		return nil
	} else {
		_t1640 := func(_dollar_dollar *pb.Undefine) *pb.FragmentId {
			return _dollar_dollar.GetFragmentId()
		}
		_t1641 := _t1640(msg)
		fields1207 := _t1641
		unwrapped_fields1208 := fields1207
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1208)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1214 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1214 != nil {
		p.write(*flat1214)
		return nil
	} else {
		_t1642 := func(_dollar_dollar *pb.Context) []*pb.RelationId {
			return _dollar_dollar.GetRelations()
		}
		_t1643 := _t1642(msg)
		fields1210 := _t1643
		unwrapped_fields1211 := fields1210
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1211) == 0) {
			p.newline()
			for i1213, elem1212 := range unwrapped_fields1211 {
				if (i1213 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1212)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1219 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1219 != nil {
		p.write(*flat1219)
		return nil
	} else {
		_t1644 := func(_dollar_dollar *pb.Snapshot) []interface{} {
			return []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		}
		_t1645 := _t1644(msg)
		fields1215 := _t1645
		unwrapped_fields1216 := fields1215
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1217 := unwrapped_fields1216[0].([]string)
		p.pretty_edb_path(field1217)
		p.newline()
		field1218 := unwrapped_fields1216[1].(*pb.RelationId)
		p.pretty_relation_id(field1218)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1223 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1223 != nil {
		p.write(*flat1223)
		return nil
	} else {
		fields1220 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1220) == 0) {
			p.newline()
			for i1222, elem1221 := range fields1220 {
				if (i1222 > 0) {
					p.newline()
				}
				p.pretty_read(elem1221)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1234 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1234 != nil {
		p.write(*flat1234)
		return nil
	} else {
		_t1646 := func(_dollar_dollar *pb.Read) *pb.Demand {
			var _t1647 *pb.Demand
			if hasProtoField(_dollar_dollar, "demand") {
				_t1647 = _dollar_dollar.GetDemand()
			}
			return _t1647
		}
		_t1648 := _t1646(msg)
		deconstruct_result1232 := _t1648
		if deconstruct_result1232 != nil {
			unwrapped1233 := deconstruct_result1232
			p.pretty_demand(unwrapped1233)
		} else {
			_t1649 := func(_dollar_dollar *pb.Read) *pb.Output {
				var _t1650 *pb.Output
				if hasProtoField(_dollar_dollar, "output") {
					_t1650 = _dollar_dollar.GetOutput()
				}
				return _t1650
			}
			_t1651 := _t1649(msg)
			deconstruct_result1230 := _t1651
			if deconstruct_result1230 != nil {
				unwrapped1231 := deconstruct_result1230
				p.pretty_output(unwrapped1231)
			} else {
				_t1652 := func(_dollar_dollar *pb.Read) *pb.WhatIf {
					var _t1653 *pb.WhatIf
					if hasProtoField(_dollar_dollar, "what_if") {
						_t1653 = _dollar_dollar.GetWhatIf()
					}
					return _t1653
				}
				_t1654 := _t1652(msg)
				deconstruct_result1228 := _t1654
				if deconstruct_result1228 != nil {
					unwrapped1229 := deconstruct_result1228
					p.pretty_what_if(unwrapped1229)
				} else {
					_t1655 := func(_dollar_dollar *pb.Read) *pb.Abort {
						var _t1656 *pb.Abort
						if hasProtoField(_dollar_dollar, "abort") {
							_t1656 = _dollar_dollar.GetAbort()
						}
						return _t1656
					}
					_t1657 := _t1655(msg)
					deconstruct_result1226 := _t1657
					if deconstruct_result1226 != nil {
						unwrapped1227 := deconstruct_result1226
						p.pretty_abort(unwrapped1227)
					} else {
						_t1658 := func(_dollar_dollar *pb.Read) *pb.Export {
							var _t1659 *pb.Export
							if hasProtoField(_dollar_dollar, "export") {
								_t1659 = _dollar_dollar.GetExport()
							}
							return _t1659
						}
						_t1660 := _t1658(msg)
						deconstruct_result1224 := _t1660
						if deconstruct_result1224 != nil {
							unwrapped1225 := deconstruct_result1224
							p.pretty_export(unwrapped1225)
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
	flat1237 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1237 != nil {
		p.write(*flat1237)
		return nil
	} else {
		_t1661 := func(_dollar_dollar *pb.Demand) *pb.RelationId {
			return _dollar_dollar.GetRelationId()
		}
		_t1662 := _t1661(msg)
		fields1235 := _t1662
		unwrapped_fields1236 := fields1235
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1236)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1242 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1242 != nil {
		p.write(*flat1242)
		return nil
	} else {
		_t1663 := func(_dollar_dollar *pb.Output) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		}
		_t1664 := _t1663(msg)
		fields1238 := _t1664
		unwrapped_fields1239 := fields1238
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1240 := unwrapped_fields1239[0].(string)
		p.pretty_name(field1240)
		p.newline()
		field1241 := unwrapped_fields1239[1].(*pb.RelationId)
		p.pretty_relation_id(field1241)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1247 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1247 != nil {
		p.write(*flat1247)
		return nil
	} else {
		_t1665 := func(_dollar_dollar *pb.WhatIf) []interface{} {
			return []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		}
		_t1666 := _t1665(msg)
		fields1243 := _t1666
		unwrapped_fields1244 := fields1243
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1245 := unwrapped_fields1244[0].(string)
		p.pretty_name(field1245)
		p.newline()
		field1246 := unwrapped_fields1244[1].(*pb.Epoch)
		p.pretty_epoch(field1246)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1253 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1253 != nil {
		p.write(*flat1253)
		return nil
	} else {
		_t1667 := func(_dollar_dollar *pb.Abort) []interface{} {
			var _t1668 *string
			if _dollar_dollar.GetName() != "abort" {
				_t1668 = ptr(_dollar_dollar.GetName())
			}
			return []interface{}{_t1668, _dollar_dollar.GetRelationId()}
		}
		_t1669 := _t1667(msg)
		fields1248 := _t1669
		unwrapped_fields1249 := fields1248
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1250 := unwrapped_fields1249[0].(*string)
		if field1250 != nil {
			p.newline()
			opt_val1251 := *field1250
			p.pretty_name(opt_val1251)
		}
		p.newline()
		field1252 := unwrapped_fields1249[1].(*pb.RelationId)
		p.pretty_relation_id(field1252)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1256 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1256 != nil {
		p.write(*flat1256)
		return nil
	} else {
		_t1670 := func(_dollar_dollar *pb.Export) *pb.ExportCSVConfig {
			return _dollar_dollar.GetCsvConfig()
		}
		_t1671 := _t1670(msg)
		fields1254 := _t1671
		unwrapped_fields1255 := fields1254
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1255)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1262 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1262 != nil {
		p.write(*flat1262)
		return nil
	} else {
		_t1672 := func(_dollar_dollar *pb.ExportCSVConfig) []interface{} {
			_t1673 := p.deconstruct_export_csv_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1673}
		}
		_t1674 := _t1672(msg)
		fields1257 := _t1674
		unwrapped_fields1258 := fields1257
		p.write("(")
		p.write("export_csv_config")
		p.indentSexp()
		p.newline()
		field1259 := unwrapped_fields1258[0].(string)
		p.pretty_export_csv_path(field1259)
		p.newline()
		field1260 := unwrapped_fields1258[1].([]*pb.ExportCSVColumn)
		p.pretty_export_csv_columns(field1260)
		p.newline()
		field1261 := unwrapped_fields1258[2].([][]interface{})
		p.pretty_config_dict(field1261)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) interface{} {
	flat1264 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1264 != nil {
		p.write(*flat1264)
		return nil
	} else {
		fields1263 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1263))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns(msg []*pb.ExportCSVColumn) interface{} {
	flat1268 := p.tryFlat(msg, func() { p.pretty_export_csv_columns(msg) })
	if flat1268 != nil {
		p.write(*flat1268)
		return nil
	} else {
		fields1265 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1265) == 0) {
			p.newline()
			for i1267, elem1266 := range fields1265 {
				if (i1267 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1266)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_column(msg *pb.ExportCSVColumn) interface{} {
	flat1273 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1273 != nil {
		p.write(*flat1273)
		return nil
	} else {
		_t1675 := func(_dollar_dollar *pb.ExportCSVColumn) []interface{} {
			return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		}
		_t1676 := _t1675(msg)
		fields1269 := _t1676
		unwrapped_fields1270 := fields1269
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1271 := unwrapped_fields1270[0].(string)
		p.write(p.formatStringValue(field1271))
		p.newline()
		field1272 := unwrapped_fields1270[1].(*pb.RelationId)
		p.pretty_relation_id(field1272)
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
		_t1714 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1714)
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
