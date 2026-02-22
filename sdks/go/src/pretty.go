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
	_t1688 := &pb.Value{}
	_t1688.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t1688
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1689 := &pb.Value{}
	_t1689.Value = &pb.Value_IntValue{IntValue: v}
	return _t1689
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1690 := &pb.Value{}
	_t1690.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1690
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1691 := &pb.Value{}
	_t1691.Value = &pb.Value_StringValue{StringValue: v}
	return _t1691
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1692 := &pb.Value{}
	_t1692.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1692
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1693 := &pb.Value{}
	_t1693.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1693
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1694 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1694})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1695 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1695})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1696 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1696})
			}
		}
	}
	_t1697 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1697})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1698 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1698})
	_t1699 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1699})
	if msg.GetNewLine() != "" {
		_t1700 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1700})
	}
	_t1701 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1701})
	_t1702 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1702})
	_t1703 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1703})
	if msg.GetComment() != "" {
		_t1704 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1704})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1705 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1705})
	}
	_t1706 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1706})
	_t1707 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1707})
	_t1708 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1708})
	if msg.GetPartitionSizeMb() != 0 {
		_t1709 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1709})
	}
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
	flat650 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat650 != nil {
		p.write(*flat650)
		return nil
	} else {
		_t1282 := func(_dollar_dollar *pb.Transaction) []interface{} {
			var _t1283 *pb.Configure
			if hasProtoField(_dollar_dollar, "configure") {
				_t1283 = _dollar_dollar.GetConfigure()
			}
			var _t1284 *pb.Sync
			if hasProtoField(_dollar_dollar, "sync") {
				_t1284 = _dollar_dollar.GetSync()
			}
			return []interface{}{_t1283, _t1284, _dollar_dollar.GetEpochs()}
		}
		_t1285 := _t1282(msg)
		fields641 := _t1285
		unwrapped_fields642 := fields641
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field643 := unwrapped_fields642[0].(*pb.Configure)
		if field643 != nil {
			p.newline()
			opt_val644 := field643
			p.pretty_configure(opt_val644)
		}
		field645 := unwrapped_fields642[1].(*pb.Sync)
		if field645 != nil {
			p.newline()
			opt_val646 := field645
			p.pretty_sync(opt_val646)
		}
		field647 := unwrapped_fields642[2].([]*pb.Epoch)
		if !(len(field647) == 0) {
			p.newline()
			for i649, elem648 := range field647 {
				if (i649 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem648)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat653 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat653 != nil {
		p.write(*flat653)
		return nil
	} else {
		_t1286 := func(_dollar_dollar *pb.Configure) [][]interface{} {
			_t1287 := p.deconstruct_configure(_dollar_dollar)
			return _t1287
		}
		_t1288 := _t1286(msg)
		fields651 := _t1288
		unwrapped_fields652 := fields651
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields652)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat657 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat657 != nil {
		p.write(*flat657)
		return nil
	} else {
		fields654 := msg
		p.write("{")
		p.indent()
		if !(len(fields654) == 0) {
			p.newline()
			for i656, elem655 := range fields654 {
				if (i656 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem655)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat662 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat662 != nil {
		p.write(*flat662)
		return nil
	} else {
		_t1289 := func(_dollar_dollar []interface{}) []interface{} {
			return []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		}
		_t1290 := _t1289(msg)
		fields658 := _t1290
		unwrapped_fields659 := fields658
		p.write(":")
		field660 := unwrapped_fields659[0].(string)
		p.write(field660)
		p.write(" ")
		field661 := unwrapped_fields659[1].(*pb.Value)
		p.pretty_value(field661)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat682 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat682 != nil {
		p.write(*flat682)
		return nil
	} else {
		_t1291 := func(_dollar_dollar *pb.Value) *pb.DateValue {
			var _t1292 *pb.DateValue
			if hasProtoField(_dollar_dollar, "date_value") {
				_t1292 = _dollar_dollar.GetDateValue()
			}
			return _t1292
		}
		_t1293 := _t1291(msg)
		deconstruct_result680 := _t1293
		if deconstruct_result680 != nil {
			unwrapped681 := deconstruct_result680
			p.pretty_date(unwrapped681)
		} else {
			_t1294 := func(_dollar_dollar *pb.Value) *pb.DateTimeValue {
				var _t1295 *pb.DateTimeValue
				if hasProtoField(_dollar_dollar, "datetime_value") {
					_t1295 = _dollar_dollar.GetDatetimeValue()
				}
				return _t1295
			}
			_t1296 := _t1294(msg)
			deconstruct_result678 := _t1296
			if deconstruct_result678 != nil {
				unwrapped679 := deconstruct_result678
				p.pretty_datetime(unwrapped679)
			} else {
				_t1297 := func(_dollar_dollar *pb.Value) *string {
					var _t1298 *string
					if hasProtoField(_dollar_dollar, "string_value") {
						_t1298 = ptr(_dollar_dollar.GetStringValue())
					}
					return _t1298
				}
				_t1299 := _t1297(msg)
				deconstruct_result676 := _t1299
				if deconstruct_result676 != nil {
					unwrapped677 := *deconstruct_result676
					p.write(p.formatStringValue(unwrapped677))
				} else {
					_t1300 := func(_dollar_dollar *pb.Value) *int64 {
						var _t1301 *int64
						if hasProtoField(_dollar_dollar, "int_value") {
							_t1301 = ptr(_dollar_dollar.GetIntValue())
						}
						return _t1301
					}
					_t1302 := _t1300(msg)
					deconstruct_result674 := _t1302
					if deconstruct_result674 != nil {
						unwrapped675 := *deconstruct_result674
						p.write(fmt.Sprintf("%d", unwrapped675))
					} else {
						_t1303 := func(_dollar_dollar *pb.Value) *float64 {
							var _t1304 *float64
							if hasProtoField(_dollar_dollar, "float_value") {
								_t1304 = ptr(_dollar_dollar.GetFloatValue())
							}
							return _t1304
						}
						_t1305 := _t1303(msg)
						deconstruct_result672 := _t1305
						if deconstruct_result672 != nil {
							unwrapped673 := *deconstruct_result672
							p.write(formatFloat64(unwrapped673))
						} else {
							_t1306 := func(_dollar_dollar *pb.Value) *pb.UInt128Value {
								var _t1307 *pb.UInt128Value
								if hasProtoField(_dollar_dollar, "uint128_value") {
									_t1307 = _dollar_dollar.GetUint128Value()
								}
								return _t1307
							}
							_t1308 := _t1306(msg)
							deconstruct_result670 := _t1308
							if deconstruct_result670 != nil {
								unwrapped671 := deconstruct_result670
								p.write(p.formatUint128(unwrapped671))
							} else {
								_t1309 := func(_dollar_dollar *pb.Value) *pb.Int128Value {
									var _t1310 *pb.Int128Value
									if hasProtoField(_dollar_dollar, "int128_value") {
										_t1310 = _dollar_dollar.GetInt128Value()
									}
									return _t1310
								}
								_t1311 := _t1309(msg)
								deconstruct_result668 := _t1311
								if deconstruct_result668 != nil {
									unwrapped669 := deconstruct_result668
									p.write(p.formatInt128(unwrapped669))
								} else {
									_t1312 := func(_dollar_dollar *pb.Value) *pb.DecimalValue {
										var _t1313 *pb.DecimalValue
										if hasProtoField(_dollar_dollar, "decimal_value") {
											_t1313 = _dollar_dollar.GetDecimalValue()
										}
										return _t1313
									}
									_t1314 := _t1312(msg)
									deconstruct_result666 := _t1314
									if deconstruct_result666 != nil {
										unwrapped667 := deconstruct_result666
										p.write(p.formatDecimal(unwrapped667))
									} else {
										_t1315 := func(_dollar_dollar *pb.Value) *bool {
											var _t1316 *bool
											if hasProtoField(_dollar_dollar, "boolean_value") {
												_t1316 = ptr(_dollar_dollar.GetBooleanValue())
											}
											return _t1316
										}
										_t1317 := _t1315(msg)
										deconstruct_result664 := _t1317
										if deconstruct_result664 != nil {
											unwrapped665 := *deconstruct_result664
											p.pretty_boolean_value(unwrapped665)
										} else {
											fields663 := msg
											_ = fields663
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
	flat688 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat688 != nil {
		p.write(*flat688)
		return nil
	} else {
		_t1318 := func(_dollar_dollar *pb.DateValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		}
		_t1319 := _t1318(msg)
		fields683 := _t1319
		unwrapped_fields684 := fields683
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field685 := unwrapped_fields684[0].(int64)
		p.write(fmt.Sprintf("%d", field685))
		p.newline()
		field686 := unwrapped_fields684[1].(int64)
		p.write(fmt.Sprintf("%d", field686))
		p.newline()
		field687 := unwrapped_fields684[2].(int64)
		p.write(fmt.Sprintf("%d", field687))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat699 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat699 != nil {
		p.write(*flat699)
		return nil
	} else {
		_t1320 := func(_dollar_dollar *pb.DateTimeValue) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		}
		_t1321 := _t1320(msg)
		fields689 := _t1321
		unwrapped_fields690 := fields689
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field691 := unwrapped_fields690[0].(int64)
		p.write(fmt.Sprintf("%d", field691))
		p.newline()
		field692 := unwrapped_fields690[1].(int64)
		p.write(fmt.Sprintf("%d", field692))
		p.newline()
		field693 := unwrapped_fields690[2].(int64)
		p.write(fmt.Sprintf("%d", field693))
		p.newline()
		field694 := unwrapped_fields690[3].(int64)
		p.write(fmt.Sprintf("%d", field694))
		p.newline()
		field695 := unwrapped_fields690[4].(int64)
		p.write(fmt.Sprintf("%d", field695))
		p.newline()
		field696 := unwrapped_fields690[5].(int64)
		p.write(fmt.Sprintf("%d", field696))
		field697 := unwrapped_fields690[6].(*int64)
		if field697 != nil {
			p.newline()
			opt_val698 := *field697
			p.write(fmt.Sprintf("%d", opt_val698))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_t1322 := func(_dollar_dollar bool) []interface{} {
		var _t1323 []interface{}
		if _dollar_dollar {
			_t1323 = []interface{}{}
		}
		return _t1323
	}
	_t1324 := _t1322(msg)
	deconstruct_result702 := _t1324
	if deconstruct_result702 != nil {
		unwrapped703 := deconstruct_result702
		_ = unwrapped703
		p.write("true")
	} else {
		_t1325 := func(_dollar_dollar bool) []interface{} {
			var _t1326 []interface{}
			if !(_dollar_dollar) {
				_t1326 = []interface{}{}
			}
			return _t1326
		}
		_t1327 := _t1325(msg)
		deconstruct_result700 := _t1327
		if deconstruct_result700 != nil {
			unwrapped701 := deconstruct_result700
			_ = unwrapped701
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat708 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat708 != nil {
		p.write(*flat708)
		return nil
	} else {
		_t1328 := func(_dollar_dollar *pb.Sync) []*pb.FragmentId {
			return _dollar_dollar.GetFragments()
		}
		_t1329 := _t1328(msg)
		fields704 := _t1329
		unwrapped_fields705 := fields704
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields705) == 0) {
			p.newline()
			for i707, elem706 := range unwrapped_fields705 {
				if (i707 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem706)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat711 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat711 != nil {
		p.write(*flat711)
		return nil
	} else {
		_t1330 := func(_dollar_dollar *pb.FragmentId) string {
			return p.fragmentIdToString(_dollar_dollar)
		}
		_t1331 := _t1330(msg)
		fields709 := _t1331
		unwrapped_fields710 := fields709
		p.write(":")
		p.write(unwrapped_fields710)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat718 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat718 != nil {
		p.write(*flat718)
		return nil
	} else {
		_t1332 := func(_dollar_dollar *pb.Epoch) []interface{} {
			var _t1333 []*pb.Write
			if !(len(_dollar_dollar.GetWrites()) == 0) {
				_t1333 = _dollar_dollar.GetWrites()
			}
			var _t1334 []*pb.Read
			if !(len(_dollar_dollar.GetReads()) == 0) {
				_t1334 = _dollar_dollar.GetReads()
			}
			return []interface{}{_t1333, _t1334}
		}
		_t1335 := _t1332(msg)
		fields712 := _t1335
		unwrapped_fields713 := fields712
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field714 := unwrapped_fields713[0].([]*pb.Write)
		if field714 != nil {
			p.newline()
			opt_val715 := field714
			p.pretty_epoch_writes(opt_val715)
		}
		field716 := unwrapped_fields713[1].([]*pb.Read)
		if field716 != nil {
			p.newline()
			opt_val717 := field716
			p.pretty_epoch_reads(opt_val717)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat722 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat722 != nil {
		p.write(*flat722)
		return nil
	} else {
		fields719 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields719) == 0) {
			p.newline()
			for i721, elem720 := range fields719 {
				if (i721 > 0) {
					p.newline()
				}
				p.pretty_write(elem720)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat731 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat731 != nil {
		p.write(*flat731)
		return nil
	} else {
		_t1336 := func(_dollar_dollar *pb.Write) *pb.Define {
			var _t1337 *pb.Define
			if hasProtoField(_dollar_dollar, "define") {
				_t1337 = _dollar_dollar.GetDefine()
			}
			return _t1337
		}
		_t1338 := _t1336(msg)
		deconstruct_result729 := _t1338
		if deconstruct_result729 != nil {
			unwrapped730 := deconstruct_result729
			p.pretty_define(unwrapped730)
		} else {
			_t1339 := func(_dollar_dollar *pb.Write) *pb.Undefine {
				var _t1340 *pb.Undefine
				if hasProtoField(_dollar_dollar, "undefine") {
					_t1340 = _dollar_dollar.GetUndefine()
				}
				return _t1340
			}
			_t1341 := _t1339(msg)
			deconstruct_result727 := _t1341
			if deconstruct_result727 != nil {
				unwrapped728 := deconstruct_result727
				p.pretty_undefine(unwrapped728)
			} else {
				_t1342 := func(_dollar_dollar *pb.Write) *pb.Context {
					var _t1343 *pb.Context
					if hasProtoField(_dollar_dollar, "context") {
						_t1343 = _dollar_dollar.GetContext()
					}
					return _t1343
				}
				_t1344 := _t1342(msg)
				deconstruct_result725 := _t1344
				if deconstruct_result725 != nil {
					unwrapped726 := deconstruct_result725
					p.pretty_context(unwrapped726)
				} else {
					_t1345 := func(_dollar_dollar *pb.Write) *pb.Snapshot {
						var _t1346 *pb.Snapshot
						if hasProtoField(_dollar_dollar, "snapshot") {
							_t1346 = _dollar_dollar.GetSnapshot()
						}
						return _t1346
					}
					_t1347 := _t1345(msg)
					deconstruct_result723 := _t1347
					if deconstruct_result723 != nil {
						unwrapped724 := deconstruct_result723
						p.pretty_snapshot(unwrapped724)
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
	flat734 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat734 != nil {
		p.write(*flat734)
		return nil
	} else {
		_t1348 := func(_dollar_dollar *pb.Define) *pb.Fragment {
			return _dollar_dollar.GetFragment()
		}
		_t1349 := _t1348(msg)
		fields732 := _t1349
		unwrapped_fields733 := fields732
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields733)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat741 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat741 != nil {
		p.write(*flat741)
		return nil
	} else {
		_t1350 := func(_dollar_dollar *pb.Fragment) []interface{} {
			p.startPrettyFragment(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		}
		_t1351 := _t1350(msg)
		fields735 := _t1351
		unwrapped_fields736 := fields735
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field737 := unwrapped_fields736[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field737)
		field738 := unwrapped_fields736[1].([]*pb.Declaration)
		if !(len(field738) == 0) {
			p.newline()
			for i740, elem739 := range field738 {
				if (i740 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem739)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat743 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat743 != nil {
		p.write(*flat743)
		return nil
	} else {
		fields742 := msg
		p.pretty_fragment_id(fields742)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat752 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat752 != nil {
		p.write(*flat752)
		return nil
	} else {
		_t1352 := func(_dollar_dollar *pb.Declaration) *pb.Def {
			var _t1353 *pb.Def
			if hasProtoField(_dollar_dollar, "def") {
				_t1353 = _dollar_dollar.GetDef()
			}
			return _t1353
		}
		_t1354 := _t1352(msg)
		deconstruct_result750 := _t1354
		if deconstruct_result750 != nil {
			unwrapped751 := deconstruct_result750
			p.pretty_def(unwrapped751)
		} else {
			_t1355 := func(_dollar_dollar *pb.Declaration) *pb.Algorithm {
				var _t1356 *pb.Algorithm
				if hasProtoField(_dollar_dollar, "algorithm") {
					_t1356 = _dollar_dollar.GetAlgorithm()
				}
				return _t1356
			}
			_t1357 := _t1355(msg)
			deconstruct_result748 := _t1357
			if deconstruct_result748 != nil {
				unwrapped749 := deconstruct_result748
				p.pretty_algorithm(unwrapped749)
			} else {
				_t1358 := func(_dollar_dollar *pb.Declaration) *pb.Constraint {
					var _t1359 *pb.Constraint
					if hasProtoField(_dollar_dollar, "constraint") {
						_t1359 = _dollar_dollar.GetConstraint()
					}
					return _t1359
				}
				_t1360 := _t1358(msg)
				deconstruct_result746 := _t1360
				if deconstruct_result746 != nil {
					unwrapped747 := deconstruct_result746
					p.pretty_constraint(unwrapped747)
				} else {
					_t1361 := func(_dollar_dollar *pb.Declaration) *pb.Data {
						var _t1362 *pb.Data
						if hasProtoField(_dollar_dollar, "data") {
							_t1362 = _dollar_dollar.GetData()
						}
						return _t1362
					}
					_t1363 := _t1361(msg)
					deconstruct_result744 := _t1363
					if deconstruct_result744 != nil {
						unwrapped745 := deconstruct_result744
						p.pretty_data(unwrapped745)
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
	flat759 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat759 != nil {
		p.write(*flat759)
		return nil
	} else {
		_t1364 := func(_dollar_dollar *pb.Def) []interface{} {
			var _t1365 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1365 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1365}
		}
		_t1366 := _t1364(msg)
		fields753 := _t1366
		unwrapped_fields754 := fields753
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field755 := unwrapped_fields754[0].(*pb.RelationId)
		p.pretty_relation_id(field755)
		p.newline()
		field756 := unwrapped_fields754[1].(*pb.Abstraction)
		p.pretty_abstraction(field756)
		field757 := unwrapped_fields754[2].([]*pb.Attribute)
		if field757 != nil {
			p.newline()
			opt_val758 := field757
			p.pretty_attrs(opt_val758)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat764 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat764 != nil {
		p.write(*flat764)
		return nil
	} else {
		_t1367 := func(_dollar_dollar *pb.RelationId) *string {
			var _t1368 *string
			if p.relationIdToString(_dollar_dollar) != nil {
				_t1369 := p.deconstruct_relation_id_string(_dollar_dollar)
				_t1368 = ptr(_t1369)
			}
			return _t1368
		}
		_t1370 := _t1367(msg)
		deconstruct_result762 := _t1370
		if deconstruct_result762 != nil {
			unwrapped763 := *deconstruct_result762
			p.write(":")
			p.write(unwrapped763)
		} else {
			_t1371 := func(_dollar_dollar *pb.RelationId) *pb.UInt128Value {
				_t1372 := p.deconstruct_relation_id_uint128(_dollar_dollar)
				return _t1372
			}
			_t1373 := _t1371(msg)
			deconstruct_result760 := _t1373
			if deconstruct_result760 != nil {
				unwrapped761 := deconstruct_result760
				p.write(p.formatUint128(unwrapped761))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat769 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat769 != nil {
		p.write(*flat769)
		return nil
	} else {
		_t1374 := func(_dollar_dollar *pb.Abstraction) []interface{} {
			_t1375 := p.deconstruct_bindings(_dollar_dollar)
			return []interface{}{_t1375, _dollar_dollar.GetValue()}
		}
		_t1376 := _t1374(msg)
		fields765 := _t1376
		unwrapped_fields766 := fields765
		p.write("(")
		p.indent()
		field767 := unwrapped_fields766[0].([]interface{})
		p.pretty_bindings(field767)
		p.newline()
		field768 := unwrapped_fields766[1].(*pb.Formula)
		p.pretty_formula(field768)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat777 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat777 != nil {
		p.write(*flat777)
		return nil
	} else {
		_t1377 := func(_dollar_dollar []interface{}) []interface{} {
			var _t1378 []*pb.Binding
			if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
				_t1378 = _dollar_dollar[1].([]*pb.Binding)
			}
			return []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1378}
		}
		_t1379 := _t1377(msg)
		fields770 := _t1379
		unwrapped_fields771 := fields770
		p.write("[")
		p.indent()
		field772 := unwrapped_fields771[0].([]*pb.Binding)
		for i774, elem773 := range field772 {
			if (i774 > 0) {
				p.newline()
			}
			p.pretty_binding(elem773)
		}
		field775 := unwrapped_fields771[1].([]*pb.Binding)
		if field775 != nil {
			p.newline()
			opt_val776 := field775
			p.pretty_value_bindings(opt_val776)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat782 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat782 != nil {
		p.write(*flat782)
		return nil
	} else {
		_t1380 := func(_dollar_dollar *pb.Binding) []interface{} {
			return []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		}
		_t1381 := _t1380(msg)
		fields778 := _t1381
		unwrapped_fields779 := fields778
		field780 := unwrapped_fields779[0].(string)
		p.write(field780)
		p.write("::")
		field781 := unwrapped_fields779[1].(*pb.Type)
		p.pretty_type(field781)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat805 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat805 != nil {
		p.write(*flat805)
		return nil
	} else {
		_t1382 := func(_dollar_dollar *pb.Type) *pb.UnspecifiedType {
			var _t1383 *pb.UnspecifiedType
			if hasProtoField(_dollar_dollar, "unspecified_type") {
				_t1383 = _dollar_dollar.GetUnspecifiedType()
			}
			return _t1383
		}
		_t1384 := _t1382(msg)
		deconstruct_result803 := _t1384
		if deconstruct_result803 != nil {
			unwrapped804 := deconstruct_result803
			p.pretty_unspecified_type(unwrapped804)
		} else {
			_t1385 := func(_dollar_dollar *pb.Type) *pb.StringType {
				var _t1386 *pb.StringType
				if hasProtoField(_dollar_dollar, "string_type") {
					_t1386 = _dollar_dollar.GetStringType()
				}
				return _t1386
			}
			_t1387 := _t1385(msg)
			deconstruct_result801 := _t1387
			if deconstruct_result801 != nil {
				unwrapped802 := deconstruct_result801
				p.pretty_string_type(unwrapped802)
			} else {
				_t1388 := func(_dollar_dollar *pb.Type) *pb.IntType {
					var _t1389 *pb.IntType
					if hasProtoField(_dollar_dollar, "int_type") {
						_t1389 = _dollar_dollar.GetIntType()
					}
					return _t1389
				}
				_t1390 := _t1388(msg)
				deconstruct_result799 := _t1390
				if deconstruct_result799 != nil {
					unwrapped800 := deconstruct_result799
					p.pretty_int_type(unwrapped800)
				} else {
					_t1391 := func(_dollar_dollar *pb.Type) *pb.FloatType {
						var _t1392 *pb.FloatType
						if hasProtoField(_dollar_dollar, "float_type") {
							_t1392 = _dollar_dollar.GetFloatType()
						}
						return _t1392
					}
					_t1393 := _t1391(msg)
					deconstruct_result797 := _t1393
					if deconstruct_result797 != nil {
						unwrapped798 := deconstruct_result797
						p.pretty_float_type(unwrapped798)
					} else {
						_t1394 := func(_dollar_dollar *pb.Type) *pb.UInt128Type {
							var _t1395 *pb.UInt128Type
							if hasProtoField(_dollar_dollar, "uint128_type") {
								_t1395 = _dollar_dollar.GetUint128Type()
							}
							return _t1395
						}
						_t1396 := _t1394(msg)
						deconstruct_result795 := _t1396
						if deconstruct_result795 != nil {
							unwrapped796 := deconstruct_result795
							p.pretty_uint128_type(unwrapped796)
						} else {
							_t1397 := func(_dollar_dollar *pb.Type) *pb.Int128Type {
								var _t1398 *pb.Int128Type
								if hasProtoField(_dollar_dollar, "int128_type") {
									_t1398 = _dollar_dollar.GetInt128Type()
								}
								return _t1398
							}
							_t1399 := _t1397(msg)
							deconstruct_result793 := _t1399
							if deconstruct_result793 != nil {
								unwrapped794 := deconstruct_result793
								p.pretty_int128_type(unwrapped794)
							} else {
								_t1400 := func(_dollar_dollar *pb.Type) *pb.DateType {
									var _t1401 *pb.DateType
									if hasProtoField(_dollar_dollar, "date_type") {
										_t1401 = _dollar_dollar.GetDateType()
									}
									return _t1401
								}
								_t1402 := _t1400(msg)
								deconstruct_result791 := _t1402
								if deconstruct_result791 != nil {
									unwrapped792 := deconstruct_result791
									p.pretty_date_type(unwrapped792)
								} else {
									_t1403 := func(_dollar_dollar *pb.Type) *pb.DateTimeType {
										var _t1404 *pb.DateTimeType
										if hasProtoField(_dollar_dollar, "datetime_type") {
											_t1404 = _dollar_dollar.GetDatetimeType()
										}
										return _t1404
									}
									_t1405 := _t1403(msg)
									deconstruct_result789 := _t1405
									if deconstruct_result789 != nil {
										unwrapped790 := deconstruct_result789
										p.pretty_datetime_type(unwrapped790)
									} else {
										_t1406 := func(_dollar_dollar *pb.Type) *pb.MissingType {
											var _t1407 *pb.MissingType
											if hasProtoField(_dollar_dollar, "missing_type") {
												_t1407 = _dollar_dollar.GetMissingType()
											}
											return _t1407
										}
										_t1408 := _t1406(msg)
										deconstruct_result787 := _t1408
										if deconstruct_result787 != nil {
											unwrapped788 := deconstruct_result787
											p.pretty_missing_type(unwrapped788)
										} else {
											_t1409 := func(_dollar_dollar *pb.Type) *pb.DecimalType {
												var _t1410 *pb.DecimalType
												if hasProtoField(_dollar_dollar, "decimal_type") {
													_t1410 = _dollar_dollar.GetDecimalType()
												}
												return _t1410
											}
											_t1411 := _t1409(msg)
											deconstruct_result785 := _t1411
											if deconstruct_result785 != nil {
												unwrapped786 := deconstruct_result785
												p.pretty_decimal_type(unwrapped786)
											} else {
												_t1412 := func(_dollar_dollar *pb.Type) *pb.BooleanType {
													var _t1413 *pb.BooleanType
													if hasProtoField(_dollar_dollar, "boolean_type") {
														_t1413 = _dollar_dollar.GetBooleanType()
													}
													return _t1413
												}
												_t1414 := _t1412(msg)
												deconstruct_result783 := _t1414
												if deconstruct_result783 != nil {
													unwrapped784 := deconstruct_result783
													p.pretty_boolean_type(unwrapped784)
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
	fields806 := msg
	_ = fields806
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields807 := msg
	_ = fields807
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields808 := msg
	_ = fields808
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields809 := msg
	_ = fields809
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields810 := msg
	_ = fields810
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields811 := msg
	_ = fields811
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields812 := msg
	_ = fields812
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields813 := msg
	_ = fields813
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields814 := msg
	_ = fields814
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat819 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat819 != nil {
		p.write(*flat819)
		return nil
	} else {
		_t1415 := func(_dollar_dollar *pb.DecimalType) []interface{} {
			return []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		}
		_t1416 := _t1415(msg)
		fields815 := _t1416
		unwrapped_fields816 := fields815
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field817 := unwrapped_fields816[0].(int64)
		p.write(fmt.Sprintf("%d", field817))
		p.newline()
		field818 := unwrapped_fields816[1].(int64)
		p.write(fmt.Sprintf("%d", field818))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields820 := msg
	_ = fields820
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat824 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat824 != nil {
		p.write(*flat824)
		return nil
	} else {
		fields821 := msg
		p.write("|")
		if !(len(fields821) == 0) {
			p.write(" ")
			for i823, elem822 := range fields821 {
				if (i823 > 0) {
					p.newline()
				}
				p.pretty_binding(elem822)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat851 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat851 != nil {
		p.write(*flat851)
		return nil
	} else {
		_t1417 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
			var _t1418 *pb.Conjunction
			if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
				_t1418 = _dollar_dollar.GetConjunction()
			}
			return _t1418
		}
		_t1419 := _t1417(msg)
		deconstruct_result849 := _t1419
		if deconstruct_result849 != nil {
			unwrapped850 := deconstruct_result849
			p.pretty_true(unwrapped850)
		} else {
			_t1420 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
				var _t1421 *pb.Disjunction
				if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
					_t1421 = _dollar_dollar.GetDisjunction()
				}
				return _t1421
			}
			_t1422 := _t1420(msg)
			deconstruct_result847 := _t1422
			if deconstruct_result847 != nil {
				unwrapped848 := deconstruct_result847
				p.pretty_false(unwrapped848)
			} else {
				_t1423 := func(_dollar_dollar *pb.Formula) *pb.Exists {
					var _t1424 *pb.Exists
					if hasProtoField(_dollar_dollar, "exists") {
						_t1424 = _dollar_dollar.GetExists()
					}
					return _t1424
				}
				_t1425 := _t1423(msg)
				deconstruct_result845 := _t1425
				if deconstruct_result845 != nil {
					unwrapped846 := deconstruct_result845
					p.pretty_exists(unwrapped846)
				} else {
					_t1426 := func(_dollar_dollar *pb.Formula) *pb.Reduce {
						var _t1427 *pb.Reduce
						if hasProtoField(_dollar_dollar, "reduce") {
							_t1427 = _dollar_dollar.GetReduce()
						}
						return _t1427
					}
					_t1428 := _t1426(msg)
					deconstruct_result843 := _t1428
					if deconstruct_result843 != nil {
						unwrapped844 := deconstruct_result843
						p.pretty_reduce(unwrapped844)
					} else {
						_t1429 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
							var _t1430 *pb.Conjunction
							if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
								_t1430 = _dollar_dollar.GetConjunction()
							}
							return _t1430
						}
						_t1431 := _t1429(msg)
						deconstruct_result841 := _t1431
						if deconstruct_result841 != nil {
							unwrapped842 := deconstruct_result841
							p.pretty_conjunction(unwrapped842)
						} else {
							_t1432 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
								var _t1433 *pb.Disjunction
								if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
									_t1433 = _dollar_dollar.GetDisjunction()
								}
								return _t1433
							}
							_t1434 := _t1432(msg)
							deconstruct_result839 := _t1434
							if deconstruct_result839 != nil {
								unwrapped840 := deconstruct_result839
								p.pretty_disjunction(unwrapped840)
							} else {
								_t1435 := func(_dollar_dollar *pb.Formula) *pb.Not {
									var _t1436 *pb.Not
									if hasProtoField(_dollar_dollar, "not") {
										_t1436 = _dollar_dollar.GetNot()
									}
									return _t1436
								}
								_t1437 := _t1435(msg)
								deconstruct_result837 := _t1437
								if deconstruct_result837 != nil {
									unwrapped838 := deconstruct_result837
									p.pretty_not(unwrapped838)
								} else {
									_t1438 := func(_dollar_dollar *pb.Formula) *pb.FFI {
										var _t1439 *pb.FFI
										if hasProtoField(_dollar_dollar, "ffi") {
											_t1439 = _dollar_dollar.GetFfi()
										}
										return _t1439
									}
									_t1440 := _t1438(msg)
									deconstruct_result835 := _t1440
									if deconstruct_result835 != nil {
										unwrapped836 := deconstruct_result835
										p.pretty_ffi(unwrapped836)
									} else {
										_t1441 := func(_dollar_dollar *pb.Formula) *pb.Atom {
											var _t1442 *pb.Atom
											if hasProtoField(_dollar_dollar, "atom") {
												_t1442 = _dollar_dollar.GetAtom()
											}
											return _t1442
										}
										_t1443 := _t1441(msg)
										deconstruct_result833 := _t1443
										if deconstruct_result833 != nil {
											unwrapped834 := deconstruct_result833
											p.pretty_atom(unwrapped834)
										} else {
											_t1444 := func(_dollar_dollar *pb.Formula) *pb.Pragma {
												var _t1445 *pb.Pragma
												if hasProtoField(_dollar_dollar, "pragma") {
													_t1445 = _dollar_dollar.GetPragma()
												}
												return _t1445
											}
											_t1446 := _t1444(msg)
											deconstruct_result831 := _t1446
											if deconstruct_result831 != nil {
												unwrapped832 := deconstruct_result831
												p.pretty_pragma(unwrapped832)
											} else {
												_t1447 := func(_dollar_dollar *pb.Formula) *pb.Primitive {
													var _t1448 *pb.Primitive
													if hasProtoField(_dollar_dollar, "primitive") {
														_t1448 = _dollar_dollar.GetPrimitive()
													}
													return _t1448
												}
												_t1449 := _t1447(msg)
												deconstruct_result829 := _t1449
												if deconstruct_result829 != nil {
													unwrapped830 := deconstruct_result829
													p.pretty_primitive(unwrapped830)
												} else {
													_t1450 := func(_dollar_dollar *pb.Formula) *pb.RelAtom {
														var _t1451 *pb.RelAtom
														if hasProtoField(_dollar_dollar, "rel_atom") {
															_t1451 = _dollar_dollar.GetRelAtom()
														}
														return _t1451
													}
													_t1452 := _t1450(msg)
													deconstruct_result827 := _t1452
													if deconstruct_result827 != nil {
														unwrapped828 := deconstruct_result827
														p.pretty_rel_atom(unwrapped828)
													} else {
														_t1453 := func(_dollar_dollar *pb.Formula) *pb.Cast {
															var _t1454 *pb.Cast
															if hasProtoField(_dollar_dollar, "cast") {
																_t1454 = _dollar_dollar.GetCast()
															}
															return _t1454
														}
														_t1455 := _t1453(msg)
														deconstruct_result825 := _t1455
														if deconstruct_result825 != nil {
															unwrapped826 := deconstruct_result825
															p.pretty_cast(unwrapped826)
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
	fields852 := msg
	_ = fields852
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields853 := msg
	_ = fields853
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat858 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat858 != nil {
		p.write(*flat858)
		return nil
	} else {
		_t1456 := func(_dollar_dollar *pb.Exists) []interface{} {
			_t1457 := p.deconstruct_bindings(_dollar_dollar.GetBody())
			return []interface{}{_t1457, _dollar_dollar.GetBody().GetValue()}
		}
		_t1458 := _t1456(msg)
		fields854 := _t1458
		unwrapped_fields855 := fields854
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field856 := unwrapped_fields855[0].([]interface{})
		p.pretty_bindings(field856)
		p.newline()
		field857 := unwrapped_fields855[1].(*pb.Formula)
		p.pretty_formula(field857)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat864 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat864 != nil {
		p.write(*flat864)
		return nil
	} else {
		_t1459 := func(_dollar_dollar *pb.Reduce) []interface{} {
			return []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		}
		_t1460 := _t1459(msg)
		fields859 := _t1460
		unwrapped_fields860 := fields859
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field861 := unwrapped_fields860[0].(*pb.Abstraction)
		p.pretty_abstraction(field861)
		p.newline()
		field862 := unwrapped_fields860[1].(*pb.Abstraction)
		p.pretty_abstraction(field862)
		p.newline()
		field863 := unwrapped_fields860[2].([]*pb.Term)
		p.pretty_terms(field863)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat868 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat868 != nil {
		p.write(*flat868)
		return nil
	} else {
		fields865 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields865) == 0) {
			p.newline()
			for i867, elem866 := range fields865 {
				if (i867 > 0) {
					p.newline()
				}
				p.pretty_term(elem866)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat873 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat873 != nil {
		p.write(*flat873)
		return nil
	} else {
		_t1461 := func(_dollar_dollar *pb.Term) *pb.Var {
			var _t1462 *pb.Var
			if hasProtoField(_dollar_dollar, "var") {
				_t1462 = _dollar_dollar.GetVar()
			}
			return _t1462
		}
		_t1463 := _t1461(msg)
		deconstruct_result871 := _t1463
		if deconstruct_result871 != nil {
			unwrapped872 := deconstruct_result871
			p.pretty_var(unwrapped872)
		} else {
			_t1464 := func(_dollar_dollar *pb.Term) *pb.Value {
				var _t1465 *pb.Value
				if hasProtoField(_dollar_dollar, "constant") {
					_t1465 = _dollar_dollar.GetConstant()
				}
				return _t1465
			}
			_t1466 := _t1464(msg)
			deconstruct_result869 := _t1466
			if deconstruct_result869 != nil {
				unwrapped870 := deconstruct_result869
				p.pretty_constant(unwrapped870)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat876 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat876 != nil {
		p.write(*flat876)
		return nil
	} else {
		_t1467 := func(_dollar_dollar *pb.Var) string {
			return _dollar_dollar.GetName()
		}
		_t1468 := _t1467(msg)
		fields874 := _t1468
		unwrapped_fields875 := fields874
		p.write(unwrapped_fields875)
	}
	return nil
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) interface{} {
	flat878 := p.tryFlat(msg, func() { p.pretty_constant(msg) })
	if flat878 != nil {
		p.write(*flat878)
		return nil
	} else {
		fields877 := msg
		p.pretty_value(fields877)
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat883 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat883 != nil {
		p.write(*flat883)
		return nil
	} else {
		_t1469 := func(_dollar_dollar *pb.Conjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1470 := _t1469(msg)
		fields879 := _t1470
		unwrapped_fields880 := fields879
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields880) == 0) {
			p.newline()
			for i882, elem881 := range unwrapped_fields880 {
				if (i882 > 0) {
					p.newline()
				}
				p.pretty_formula(elem881)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat888 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat888 != nil {
		p.write(*flat888)
		return nil
	} else {
		_t1471 := func(_dollar_dollar *pb.Disjunction) []*pb.Formula {
			return _dollar_dollar.GetArgs()
		}
		_t1472 := _t1471(msg)
		fields884 := _t1472
		unwrapped_fields885 := fields884
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields885) == 0) {
			p.newline()
			for i887, elem886 := range unwrapped_fields885 {
				if (i887 > 0) {
					p.newline()
				}
				p.pretty_formula(elem886)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat891 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat891 != nil {
		p.write(*flat891)
		return nil
	} else {
		_t1473 := func(_dollar_dollar *pb.Not) *pb.Formula {
			return _dollar_dollar.GetArg()
		}
		_t1474 := _t1473(msg)
		fields889 := _t1474
		unwrapped_fields890 := fields889
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields890)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat897 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat897 != nil {
		p.write(*flat897)
		return nil
	} else {
		_t1475 := func(_dollar_dollar *pb.FFI) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		}
		_t1476 := _t1475(msg)
		fields892 := _t1476
		unwrapped_fields893 := fields892
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field894 := unwrapped_fields893[0].(string)
		p.pretty_name(field894)
		p.newline()
		field895 := unwrapped_fields893[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field895)
		p.newline()
		field896 := unwrapped_fields893[2].([]*pb.Term)
		p.pretty_terms(field896)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat899 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat899 != nil {
		p.write(*flat899)
		return nil
	} else {
		fields898 := msg
		p.write(":")
		p.write(fields898)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat903 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat903 != nil {
		p.write(*flat903)
		return nil
	} else {
		fields900 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields900) == 0) {
			p.newline()
			for i902, elem901 := range fields900 {
				if (i902 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem901)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat910 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat910 != nil {
		p.write(*flat910)
		return nil
	} else {
		_t1477 := func(_dollar_dollar *pb.Atom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1478 := _t1477(msg)
		fields904 := _t1478
		unwrapped_fields905 := fields904
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field906 := unwrapped_fields905[0].(*pb.RelationId)
		p.pretty_relation_id(field906)
		field907 := unwrapped_fields905[1].([]*pb.Term)
		if !(len(field907) == 0) {
			p.newline()
			for i909, elem908 := range field907 {
				if (i909 > 0) {
					p.newline()
				}
				p.pretty_term(elem908)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat917 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat917 != nil {
		p.write(*flat917)
		return nil
	} else {
		_t1479 := func(_dollar_dollar *pb.Pragma) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1480 := _t1479(msg)
		fields911 := _t1480
		unwrapped_fields912 := fields911
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field913 := unwrapped_fields912[0].(string)
		p.pretty_name(field913)
		field914 := unwrapped_fields912[1].([]*pb.Term)
		if !(len(field914) == 0) {
			p.newline()
			for i916, elem915 := range field914 {
				if (i916 > 0) {
					p.newline()
				}
				p.pretty_term(elem915)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat933 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat933 != nil {
		p.write(*flat933)
		return nil
	} else {
		_t1481 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1482 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1482 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1482
		}
		_t1483 := _t1481(msg)
		guard_result932 := _t1483
		if guard_result932 != nil {
			p.pretty_eq(msg)
		} else {
			_t1484 := func(_dollar_dollar *pb.Primitive) []interface{} {
				var _t1485 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
					_t1485 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				return _t1485
			}
			_t1486 := _t1484(msg)
			guard_result931 := _t1486
			if guard_result931 != nil {
				p.pretty_lt(msg)
			} else {
				_t1487 := func(_dollar_dollar *pb.Primitive) []interface{} {
					var _t1488 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
						_t1488 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					return _t1488
				}
				_t1489 := _t1487(msg)
				guard_result930 := _t1489
				if guard_result930 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_t1490 := func(_dollar_dollar *pb.Primitive) []interface{} {
						var _t1491 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
							_t1491 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						return _t1491
					}
					_t1492 := _t1490(msg)
					guard_result929 := _t1492
					if guard_result929 != nil {
						p.pretty_gt(msg)
					} else {
						_t1493 := func(_dollar_dollar *pb.Primitive) []interface{} {
							var _t1494 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
								_t1494 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
							}
							return _t1494
						}
						_t1495 := _t1493(msg)
						guard_result928 := _t1495
						if guard_result928 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_t1496 := func(_dollar_dollar *pb.Primitive) []interface{} {
								var _t1497 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
									_t1497 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								return _t1497
							}
							_t1498 := _t1496(msg)
							guard_result927 := _t1498
							if guard_result927 != nil {
								p.pretty_add(msg)
							} else {
								_t1499 := func(_dollar_dollar *pb.Primitive) []interface{} {
									var _t1500 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
										_t1500 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									return _t1500
								}
								_t1501 := _t1499(msg)
								guard_result926 := _t1501
								if guard_result926 != nil {
									p.pretty_minus(msg)
								} else {
									_t1502 := func(_dollar_dollar *pb.Primitive) []interface{} {
										var _t1503 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
											_t1503 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										return _t1503
									}
									_t1504 := _t1502(msg)
									guard_result925 := _t1504
									if guard_result925 != nil {
										p.pretty_multiply(msg)
									} else {
										_t1505 := func(_dollar_dollar *pb.Primitive) []interface{} {
											var _t1506 []interface{}
											if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
												_t1506 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
											}
											return _t1506
										}
										_t1507 := _t1505(msg)
										guard_result924 := _t1507
										if guard_result924 != nil {
											p.pretty_divide(msg)
										} else {
											_t1508 := func(_dollar_dollar *pb.Primitive) []interface{} {
												return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											}
											_t1509 := _t1508(msg)
											fields918 := _t1509
											unwrapped_fields919 := fields918
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field920 := unwrapped_fields919[0].(string)
											p.pretty_name(field920)
											field921 := unwrapped_fields919[1].([]*pb.RelTerm)
											if !(len(field921) == 0) {
												p.newline()
												for i923, elem922 := range field921 {
													if (i923 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem922)
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
	flat938 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat938 != nil {
		p.write(*flat938)
		return nil
	} else {
		_t1510 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1511 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_eq" {
				_t1511 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1511
		}
		_t1512 := _t1510(msg)
		fields934 := _t1512
		unwrapped_fields935 := fields934
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field936 := unwrapped_fields935[0].(*pb.Term)
		p.pretty_term(field936)
		p.newline()
		field937 := unwrapped_fields935[1].(*pb.Term)
		p.pretty_term(field937)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat943 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat943 != nil {
		p.write(*flat943)
		return nil
	} else {
		_t1513 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1514 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1514 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1514
		}
		_t1515 := _t1513(msg)
		fields939 := _t1515
		unwrapped_fields940 := fields939
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field941 := unwrapped_fields940[0].(*pb.Term)
		p.pretty_term(field941)
		p.newline()
		field942 := unwrapped_fields940[1].(*pb.Term)
		p.pretty_term(field942)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat948 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat948 != nil {
		p.write(*flat948)
		return nil
	} else {
		_t1516 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1517 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
				_t1517 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1517
		}
		_t1518 := _t1516(msg)
		fields944 := _t1518
		unwrapped_fields945 := fields944
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field946 := unwrapped_fields945[0].(*pb.Term)
		p.pretty_term(field946)
		p.newline()
		field947 := unwrapped_fields945[1].(*pb.Term)
		p.pretty_term(field947)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat953 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat953 != nil {
		p.write(*flat953)
		return nil
	} else {
		_t1519 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1520 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
				_t1520 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1520
		}
		_t1521 := _t1519(msg)
		fields949 := _t1521
		unwrapped_fields950 := fields949
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field951 := unwrapped_fields950[0].(*pb.Term)
		p.pretty_term(field951)
		p.newline()
		field952 := unwrapped_fields950[1].(*pb.Term)
		p.pretty_term(field952)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat958 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat958 != nil {
		p.write(*flat958)
		return nil
	} else {
		_t1522 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1523 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
				_t1523 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t1523
		}
		_t1524 := _t1522(msg)
		fields954 := _t1524
		unwrapped_fields955 := fields954
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field956 := unwrapped_fields955[0].(*pb.Term)
		p.pretty_term(field956)
		p.newline()
		field957 := unwrapped_fields955[1].(*pb.Term)
		p.pretty_term(field957)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat964 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat964 != nil {
		p.write(*flat964)
		return nil
	} else {
		_t1525 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1526 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
				_t1526 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1526
		}
		_t1527 := _t1525(msg)
		fields959 := _t1527
		unwrapped_fields960 := fields959
		p.write("(")
		p.write("+")
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

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat970 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat970 != nil {
		p.write(*flat970)
		return nil
	} else {
		_t1528 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1529 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
				_t1529 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1529
		}
		_t1530 := _t1528(msg)
		fields965 := _t1530
		unwrapped_fields966 := fields965
		p.write("(")
		p.write("-")
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

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat976 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat976 != nil {
		p.write(*flat976)
		return nil
	} else {
		_t1531 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1532 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
				_t1532 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1532
		}
		_t1533 := _t1531(msg)
		fields971 := _t1533
		unwrapped_fields972 := fields971
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field973 := unwrapped_fields972[0].(*pb.Term)
		p.pretty_term(field973)
		p.newline()
		field974 := unwrapped_fields972[1].(*pb.Term)
		p.pretty_term(field974)
		p.newline()
		field975 := unwrapped_fields972[2].(*pb.Term)
		p.pretty_term(field975)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat982 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat982 != nil {
		p.write(*flat982)
		return nil
	} else {
		_t1534 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t1535 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
				_t1535 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
			}
			return _t1535
		}
		_t1536 := _t1534(msg)
		fields977 := _t1536
		unwrapped_fields978 := fields977
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field979 := unwrapped_fields978[0].(*pb.Term)
		p.pretty_term(field979)
		p.newline()
		field980 := unwrapped_fields978[1].(*pb.Term)
		p.pretty_term(field980)
		p.newline()
		field981 := unwrapped_fields978[2].(*pb.Term)
		p.pretty_term(field981)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat987 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat987 != nil {
		p.write(*flat987)
		return nil
	} else {
		_t1537 := func(_dollar_dollar *pb.RelTerm) *pb.Value {
			var _t1538 *pb.Value
			if hasProtoField(_dollar_dollar, "specialized_value") {
				_t1538 = _dollar_dollar.GetSpecializedValue()
			}
			return _t1538
		}
		_t1539 := _t1537(msg)
		deconstruct_result985 := _t1539
		if deconstruct_result985 != nil {
			unwrapped986 := deconstruct_result985
			p.pretty_specialized_value(unwrapped986)
		} else {
			_t1540 := func(_dollar_dollar *pb.RelTerm) *pb.Term {
				var _t1541 *pb.Term
				if hasProtoField(_dollar_dollar, "term") {
					_t1541 = _dollar_dollar.GetTerm()
				}
				return _t1541
			}
			_t1542 := _t1540(msg)
			deconstruct_result983 := _t1542
			if deconstruct_result983 != nil {
				unwrapped984 := deconstruct_result983
				p.pretty_term(unwrapped984)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat989 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat989 != nil {
		p.write(*flat989)
		return nil
	} else {
		fields988 := msg
		p.write("#")
		p.pretty_value(fields988)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat996 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat996 != nil {
		p.write(*flat996)
		return nil
	} else {
		_t1543 := func(_dollar_dollar *pb.RelAtom) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		}
		_t1544 := _t1543(msg)
		fields990 := _t1544
		unwrapped_fields991 := fields990
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field992 := unwrapped_fields991[0].(string)
		p.pretty_name(field992)
		field993 := unwrapped_fields991[1].([]*pb.RelTerm)
		if !(len(field993) == 0) {
			p.newline()
			for i995, elem994 := range field993 {
				if (i995 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem994)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1001 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1001 != nil {
		p.write(*flat1001)
		return nil
	} else {
		_t1545 := func(_dollar_dollar *pb.Cast) []interface{} {
			return []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		}
		_t1546 := _t1545(msg)
		fields997 := _t1546
		unwrapped_fields998 := fields997
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field999 := unwrapped_fields998[0].(*pb.Term)
		p.pretty_term(field999)
		p.newline()
		field1000 := unwrapped_fields998[1].(*pb.Term)
		p.pretty_term(field1000)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1005 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1005 != nil {
		p.write(*flat1005)
		return nil
	} else {
		fields1002 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1002) == 0) {
			p.newline()
			for i1004, elem1003 := range fields1002 {
				if (i1004 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1003)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1012 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1012 != nil {
		p.write(*flat1012)
		return nil
	} else {
		_t1547 := func(_dollar_dollar *pb.Attribute) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		}
		_t1548 := _t1547(msg)
		fields1006 := _t1548
		unwrapped_fields1007 := fields1006
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1008 := unwrapped_fields1007[0].(string)
		p.pretty_name(field1008)
		field1009 := unwrapped_fields1007[1].([]*pb.Value)
		if !(len(field1009) == 0) {
			p.newline()
			for i1011, elem1010 := range field1009 {
				if (i1011 > 0) {
					p.newline()
				}
				p.pretty_value(elem1010)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1019 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1019 != nil {
		p.write(*flat1019)
		return nil
	} else {
		_t1549 := func(_dollar_dollar *pb.Algorithm) []interface{} {
			return []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		}
		_t1550 := _t1549(msg)
		fields1013 := _t1550
		unwrapped_fields1014 := fields1013
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1015 := unwrapped_fields1014[0].([]*pb.RelationId)
		if !(len(field1015) == 0) {
			p.newline()
			for i1017, elem1016 := range field1015 {
				if (i1017 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1016)
			}
		}
		p.newline()
		field1018 := unwrapped_fields1014[1].(*pb.Script)
		p.pretty_script(field1018)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1024 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1024 != nil {
		p.write(*flat1024)
		return nil
	} else {
		_t1551 := func(_dollar_dollar *pb.Script) []*pb.Construct {
			return _dollar_dollar.GetConstructs()
		}
		_t1552 := _t1551(msg)
		fields1020 := _t1552
		unwrapped_fields1021 := fields1020
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1021) == 0) {
			p.newline()
			for i1023, elem1022 := range unwrapped_fields1021 {
				if (i1023 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1022)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1029 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1029 != nil {
		p.write(*flat1029)
		return nil
	} else {
		_t1553 := func(_dollar_dollar *pb.Construct) *pb.Loop {
			var _t1554 *pb.Loop
			if hasProtoField(_dollar_dollar, "loop") {
				_t1554 = _dollar_dollar.GetLoop()
			}
			return _t1554
		}
		_t1555 := _t1553(msg)
		deconstruct_result1027 := _t1555
		if deconstruct_result1027 != nil {
			unwrapped1028 := deconstruct_result1027
			p.pretty_loop(unwrapped1028)
		} else {
			_t1556 := func(_dollar_dollar *pb.Construct) *pb.Instruction {
				var _t1557 *pb.Instruction
				if hasProtoField(_dollar_dollar, "instruction") {
					_t1557 = _dollar_dollar.GetInstruction()
				}
				return _t1557
			}
			_t1558 := _t1556(msg)
			deconstruct_result1025 := _t1558
			if deconstruct_result1025 != nil {
				unwrapped1026 := deconstruct_result1025
				p.pretty_instruction(unwrapped1026)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1034 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1034 != nil {
		p.write(*flat1034)
		return nil
	} else {
		_t1559 := func(_dollar_dollar *pb.Loop) []interface{} {
			return []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		}
		_t1560 := _t1559(msg)
		fields1030 := _t1560
		unwrapped_fields1031 := fields1030
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1032 := unwrapped_fields1031[0].([]*pb.Instruction)
		p.pretty_init(field1032)
		p.newline()
		field1033 := unwrapped_fields1031[1].(*pb.Script)
		p.pretty_script(field1033)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1038 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1038 != nil {
		p.write(*flat1038)
		return nil
	} else {
		fields1035 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1035) == 0) {
			p.newline()
			for i1037, elem1036 := range fields1035 {
				if (i1037 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1036)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1049 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1049 != nil {
		p.write(*flat1049)
		return nil
	} else {
		_t1561 := func(_dollar_dollar *pb.Instruction) *pb.Assign {
			var _t1562 *pb.Assign
			if hasProtoField(_dollar_dollar, "assign") {
				_t1562 = _dollar_dollar.GetAssign()
			}
			return _t1562
		}
		_t1563 := _t1561(msg)
		deconstruct_result1047 := _t1563
		if deconstruct_result1047 != nil {
			unwrapped1048 := deconstruct_result1047
			p.pretty_assign(unwrapped1048)
		} else {
			_t1564 := func(_dollar_dollar *pb.Instruction) *pb.Upsert {
				var _t1565 *pb.Upsert
				if hasProtoField(_dollar_dollar, "upsert") {
					_t1565 = _dollar_dollar.GetUpsert()
				}
				return _t1565
			}
			_t1566 := _t1564(msg)
			deconstruct_result1045 := _t1566
			if deconstruct_result1045 != nil {
				unwrapped1046 := deconstruct_result1045
				p.pretty_upsert(unwrapped1046)
			} else {
				_t1567 := func(_dollar_dollar *pb.Instruction) *pb.Break {
					var _t1568 *pb.Break
					if hasProtoField(_dollar_dollar, "break") {
						_t1568 = _dollar_dollar.GetBreak()
					}
					return _t1568
				}
				_t1569 := _t1567(msg)
				deconstruct_result1043 := _t1569
				if deconstruct_result1043 != nil {
					unwrapped1044 := deconstruct_result1043
					p.pretty_break(unwrapped1044)
				} else {
					_t1570 := func(_dollar_dollar *pb.Instruction) *pb.MonoidDef {
						var _t1571 *pb.MonoidDef
						if hasProtoField(_dollar_dollar, "monoid_def") {
							_t1571 = _dollar_dollar.GetMonoidDef()
						}
						return _t1571
					}
					_t1572 := _t1570(msg)
					deconstruct_result1041 := _t1572
					if deconstruct_result1041 != nil {
						unwrapped1042 := deconstruct_result1041
						p.pretty_monoid_def(unwrapped1042)
					} else {
						_t1573 := func(_dollar_dollar *pb.Instruction) *pb.MonusDef {
							var _t1574 *pb.MonusDef
							if hasProtoField(_dollar_dollar, "monus_def") {
								_t1574 = _dollar_dollar.GetMonusDef()
							}
							return _t1574
						}
						_t1575 := _t1573(msg)
						deconstruct_result1039 := _t1575
						if deconstruct_result1039 != nil {
							unwrapped1040 := deconstruct_result1039
							p.pretty_monus_def(unwrapped1040)
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
	flat1056 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1056 != nil {
		p.write(*flat1056)
		return nil
	} else {
		_t1576 := func(_dollar_dollar *pb.Assign) []interface{} {
			var _t1577 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1577 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1577}
		}
		_t1578 := _t1576(msg)
		fields1050 := _t1578
		unwrapped_fields1051 := fields1050
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1052 := unwrapped_fields1051[0].(*pb.RelationId)
		p.pretty_relation_id(field1052)
		p.newline()
		field1053 := unwrapped_fields1051[1].(*pb.Abstraction)
		p.pretty_abstraction(field1053)
		field1054 := unwrapped_fields1051[2].([]*pb.Attribute)
		if field1054 != nil {
			p.newline()
			opt_val1055 := field1054
			p.pretty_attrs(opt_val1055)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1063 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1063 != nil {
		p.write(*flat1063)
		return nil
	} else {
		_t1579 := func(_dollar_dollar *pb.Upsert) []interface{} {
			var _t1580 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1580 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1580}
		}
		_t1581 := _t1579(msg)
		fields1057 := _t1581
		unwrapped_fields1058 := fields1057
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1059 := unwrapped_fields1058[0].(*pb.RelationId)
		p.pretty_relation_id(field1059)
		p.newline()
		field1060 := unwrapped_fields1058[1].([]interface{})
		p.pretty_abstraction_with_arity(field1060)
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

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1068 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1068 != nil {
		p.write(*flat1068)
		return nil
	} else {
		_t1582 := func(_dollar_dollar []interface{}) []interface{} {
			_t1583 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
			return []interface{}{_t1583, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		}
		_t1584 := _t1582(msg)
		fields1064 := _t1584
		unwrapped_fields1065 := fields1064
		p.write("(")
		p.indent()
		field1066 := unwrapped_fields1065[0].([]interface{})
		p.pretty_bindings(field1066)
		p.newline()
		field1067 := unwrapped_fields1065[1].(*pb.Formula)
		p.pretty_formula(field1067)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1075 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1075 != nil {
		p.write(*flat1075)
		return nil
	} else {
		_t1585 := func(_dollar_dollar *pb.Break) []interface{} {
			var _t1586 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1586 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1586}
		}
		_t1587 := _t1585(msg)
		fields1069 := _t1587
		unwrapped_fields1070 := fields1069
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1071 := unwrapped_fields1070[0].(*pb.RelationId)
		p.pretty_relation_id(field1071)
		p.newline()
		field1072 := unwrapped_fields1070[1].(*pb.Abstraction)
		p.pretty_abstraction(field1072)
		field1073 := unwrapped_fields1070[2].([]*pb.Attribute)
		if field1073 != nil {
			p.newline()
			opt_val1074 := field1073
			p.pretty_attrs(opt_val1074)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1083 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1083 != nil {
		p.write(*flat1083)
		return nil
	} else {
		_t1588 := func(_dollar_dollar *pb.MonoidDef) []interface{} {
			var _t1589 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1589 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1589}
		}
		_t1590 := _t1588(msg)
		fields1076 := _t1590
		unwrapped_fields1077 := fields1076
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1078 := unwrapped_fields1077[0].(*pb.Monoid)
		p.pretty_monoid(field1078)
		p.newline()
		field1079 := unwrapped_fields1077[1].(*pb.RelationId)
		p.pretty_relation_id(field1079)
		p.newline()
		field1080 := unwrapped_fields1077[2].([]interface{})
		p.pretty_abstraction_with_arity(field1080)
		field1081 := unwrapped_fields1077[3].([]*pb.Attribute)
		if field1081 != nil {
			p.newline()
			opt_val1082 := field1081
			p.pretty_attrs(opt_val1082)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1092 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1092 != nil {
		p.write(*flat1092)
		return nil
	} else {
		_t1591 := func(_dollar_dollar *pb.Monoid) *pb.OrMonoid {
			var _t1592 *pb.OrMonoid
			if hasProtoField(_dollar_dollar, "or_monoid") {
				_t1592 = _dollar_dollar.GetOrMonoid()
			}
			return _t1592
		}
		_t1593 := _t1591(msg)
		deconstruct_result1090 := _t1593
		if deconstruct_result1090 != nil {
			unwrapped1091 := deconstruct_result1090
			p.pretty_or_monoid(unwrapped1091)
		} else {
			_t1594 := func(_dollar_dollar *pb.Monoid) *pb.MinMonoid {
				var _t1595 *pb.MinMonoid
				if hasProtoField(_dollar_dollar, "min_monoid") {
					_t1595 = _dollar_dollar.GetMinMonoid()
				}
				return _t1595
			}
			_t1596 := _t1594(msg)
			deconstruct_result1088 := _t1596
			if deconstruct_result1088 != nil {
				unwrapped1089 := deconstruct_result1088
				p.pretty_min_monoid(unwrapped1089)
			} else {
				_t1597 := func(_dollar_dollar *pb.Monoid) *pb.MaxMonoid {
					var _t1598 *pb.MaxMonoid
					if hasProtoField(_dollar_dollar, "max_monoid") {
						_t1598 = _dollar_dollar.GetMaxMonoid()
					}
					return _t1598
				}
				_t1599 := _t1597(msg)
				deconstruct_result1086 := _t1599
				if deconstruct_result1086 != nil {
					unwrapped1087 := deconstruct_result1086
					p.pretty_max_monoid(unwrapped1087)
				} else {
					_t1600 := func(_dollar_dollar *pb.Monoid) *pb.SumMonoid {
						var _t1601 *pb.SumMonoid
						if hasProtoField(_dollar_dollar, "sum_monoid") {
							_t1601 = _dollar_dollar.GetSumMonoid()
						}
						return _t1601
					}
					_t1602 := _t1600(msg)
					deconstruct_result1084 := _t1602
					if deconstruct_result1084 != nil {
						unwrapped1085 := deconstruct_result1084
						p.pretty_sum_monoid(unwrapped1085)
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
	fields1093 := msg
	_ = fields1093
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1096 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1096 != nil {
		p.write(*flat1096)
		return nil
	} else {
		_t1603 := func(_dollar_dollar *pb.MinMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1604 := _t1603(msg)
		fields1094 := _t1604
		unwrapped_fields1095 := fields1094
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1095)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1099 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1099 != nil {
		p.write(*flat1099)
		return nil
	} else {
		_t1605 := func(_dollar_dollar *pb.MaxMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1606 := _t1605(msg)
		fields1097 := _t1606
		unwrapped_fields1098 := fields1097
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1098)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1102 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1102 != nil {
		p.write(*flat1102)
		return nil
	} else {
		_t1607 := func(_dollar_dollar *pb.SumMonoid) *pb.Type {
			return _dollar_dollar.GetType()
		}
		_t1608 := _t1607(msg)
		fields1100 := _t1608
		unwrapped_fields1101 := fields1100
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1101)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1110 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1110 != nil {
		p.write(*flat1110)
		return nil
	} else {
		_t1609 := func(_dollar_dollar *pb.MonusDef) []interface{} {
			var _t1610 []*pb.Attribute
			if !(len(_dollar_dollar.GetAttrs()) == 0) {
				_t1610 = _dollar_dollar.GetAttrs()
			}
			return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1610}
		}
		_t1611 := _t1609(msg)
		fields1103 := _t1611
		unwrapped_fields1104 := fields1103
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1105 := unwrapped_fields1104[0].(*pb.Monoid)
		p.pretty_monoid(field1105)
		p.newline()
		field1106 := unwrapped_fields1104[1].(*pb.RelationId)
		p.pretty_relation_id(field1106)
		p.newline()
		field1107 := unwrapped_fields1104[2].([]interface{})
		p.pretty_abstraction_with_arity(field1107)
		field1108 := unwrapped_fields1104[3].([]*pb.Attribute)
		if field1108 != nil {
			p.newline()
			opt_val1109 := field1108
			p.pretty_attrs(opt_val1109)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1117 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1117 != nil {
		p.write(*flat1117)
		return nil
	} else {
		_t1612 := func(_dollar_dollar *pb.Constraint) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		}
		_t1613 := _t1612(msg)
		fields1111 := _t1613
		unwrapped_fields1112 := fields1111
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1113 := unwrapped_fields1112[0].(*pb.RelationId)
		p.pretty_relation_id(field1113)
		p.newline()
		field1114 := unwrapped_fields1112[1].(*pb.Abstraction)
		p.pretty_abstraction(field1114)
		p.newline()
		field1115 := unwrapped_fields1112[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1115)
		p.newline()
		field1116 := unwrapped_fields1112[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1116)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1121 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1121 != nil {
		p.write(*flat1121)
		return nil
	} else {
		fields1118 := msg
		p.write("(")
		p.write("keys")
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

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1125 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1125 != nil {
		p.write(*flat1125)
		return nil
	} else {
		fields1122 := msg
		p.write("(")
		p.write("values")
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

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1132 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1132 != nil {
		p.write(*flat1132)
		return nil
	} else {
		_t1614 := func(_dollar_dollar *pb.Data) *pb.RelEDB {
			var _t1615 *pb.RelEDB
			if hasProtoField(_dollar_dollar, "rel_edb") {
				_t1615 = _dollar_dollar.GetRelEdb()
			}
			return _t1615
		}
		_t1616 := _t1614(msg)
		deconstruct_result1130 := _t1616
		if deconstruct_result1130 != nil {
			unwrapped1131 := deconstruct_result1130
			p.pretty_rel_edb(unwrapped1131)
		} else {
			_t1617 := func(_dollar_dollar *pb.Data) *pb.BeTreeRelation {
				var _t1618 *pb.BeTreeRelation
				if hasProtoField(_dollar_dollar, "betree_relation") {
					_t1618 = _dollar_dollar.GetBetreeRelation()
				}
				return _t1618
			}
			_t1619 := _t1617(msg)
			deconstruct_result1128 := _t1619
			if deconstruct_result1128 != nil {
				unwrapped1129 := deconstruct_result1128
				p.pretty_betree_relation(unwrapped1129)
			} else {
				_t1620 := func(_dollar_dollar *pb.Data) *pb.CSVData {
					var _t1621 *pb.CSVData
					if hasProtoField(_dollar_dollar, "csv_data") {
						_t1621 = _dollar_dollar.GetCsvData()
					}
					return _t1621
				}
				_t1622 := _t1620(msg)
				deconstruct_result1126 := _t1622
				if deconstruct_result1126 != nil {
					unwrapped1127 := deconstruct_result1126
					p.pretty_csv_data(unwrapped1127)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_edb(msg *pb.RelEDB) interface{} {
	flat1138 := p.tryFlat(msg, func() { p.pretty_rel_edb(msg) })
	if flat1138 != nil {
		p.write(*flat1138)
		return nil
	} else {
		_t1623 := func(_dollar_dollar *pb.RelEDB) []interface{} {
			return []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		}
		_t1624 := _t1623(msg)
		fields1133 := _t1624
		unwrapped_fields1134 := fields1133
		p.write("(")
		p.write("rel_edb")
		p.indentSexp()
		p.newline()
		field1135 := unwrapped_fields1134[0].(*pb.RelationId)
		p.pretty_relation_id(field1135)
		p.newline()
		field1136 := unwrapped_fields1134[1].([]string)
		p.pretty_rel_edb_path(field1136)
		p.newline()
		field1137 := unwrapped_fields1134[2].([]*pb.Type)
		p.pretty_rel_edb_types(field1137)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_edb_path(msg []string) interface{} {
	flat1142 := p.tryFlat(msg, func() { p.pretty_rel_edb_path(msg) })
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
			p.write(p.formatStringValue(elem1140))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_edb_types(msg []*pb.Type) interface{} {
	flat1146 := p.tryFlat(msg, func() { p.pretty_rel_edb_types(msg) })
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
			p.pretty_type(elem1144)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1151 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1151 != nil {
		p.write(*flat1151)
		return nil
	} else {
		_t1625 := func(_dollar_dollar *pb.BeTreeRelation) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		}
		_t1626 := _t1625(msg)
		fields1147 := _t1626
		unwrapped_fields1148 := fields1147
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1149 := unwrapped_fields1148[0].(*pb.RelationId)
		p.pretty_relation_id(field1149)
		p.newline()
		field1150 := unwrapped_fields1148[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1150)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1157 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1157 != nil {
		p.write(*flat1157)
		return nil
	} else {
		_t1627 := func(_dollar_dollar *pb.BeTreeInfo) []interface{} {
			_t1628 := p.deconstruct_betree_info_config(_dollar_dollar)
			return []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1628}
		}
		_t1629 := _t1627(msg)
		fields1152 := _t1629
		unwrapped_fields1153 := fields1152
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1154 := unwrapped_fields1153[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1154)
		p.newline()
		field1155 := unwrapped_fields1153[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1155)
		p.newline()
		field1156 := unwrapped_fields1153[2].([][]interface{})
		p.pretty_config_dict(field1156)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1161 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1161 != nil {
		p.write(*flat1161)
		return nil
	} else {
		fields1158 := msg
		p.write("(")
		p.write("key_types")
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

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1165 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1165 != nil {
		p.write(*flat1165)
		return nil
	} else {
		fields1162 := msg
		p.write("(")
		p.write("value_types")
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

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1172 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1172 != nil {
		p.write(*flat1172)
		return nil
	} else {
		_t1630 := func(_dollar_dollar *pb.CSVData) []interface{} {
			return []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		}
		_t1631 := _t1630(msg)
		fields1166 := _t1631
		unwrapped_fields1167 := fields1166
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1168 := unwrapped_fields1167[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1168)
		p.newline()
		field1169 := unwrapped_fields1167[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1169)
		p.newline()
		field1170 := unwrapped_fields1167[2].([]*pb.CSVColumn)
		p.pretty_csv_columns(field1170)
		p.newline()
		field1171 := unwrapped_fields1167[3].(string)
		p.pretty_csv_asof(field1171)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1179 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1179 != nil {
		p.write(*flat1179)
		return nil
	} else {
		_t1632 := func(_dollar_dollar *pb.CSVLocator) []interface{} {
			var _t1633 []string
			if !(len(_dollar_dollar.GetPaths()) == 0) {
				_t1633 = _dollar_dollar.GetPaths()
			}
			var _t1634 *string
			if string(_dollar_dollar.GetInlineData()) != "" {
				_t1634 = ptr(string(_dollar_dollar.GetInlineData()))
			}
			return []interface{}{_t1633, _t1634}
		}
		_t1635 := _t1632(msg)
		fields1173 := _t1635
		unwrapped_fields1174 := fields1173
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1175 := unwrapped_fields1174[0].([]string)
		if field1175 != nil {
			p.newline()
			opt_val1176 := field1175
			p.pretty_csv_locator_paths(opt_val1176)
		}
		field1177 := unwrapped_fields1174[1].(*string)
		if field1177 != nil {
			p.newline()
			opt_val1178 := *field1177
			p.pretty_csv_locator_inline_data(opt_val1178)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1183 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1183 != nil {
		p.write(*flat1183)
		return nil
	} else {
		fields1180 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1180) == 0) {
			p.newline()
			for i1182, elem1181 := range fields1180 {
				if (i1182 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1181))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1185 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1185 != nil {
		p.write(*flat1185)
		return nil
	} else {
		fields1184 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1184))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1188 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1188 != nil {
		p.write(*flat1188)
		return nil
	} else {
		_t1636 := func(_dollar_dollar *pb.CSVConfig) [][]interface{} {
			_t1637 := p.deconstruct_csv_config(_dollar_dollar)
			return _t1637
		}
		_t1638 := _t1636(msg)
		fields1186 := _t1638
		unwrapped_fields1187 := fields1186
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1187)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_columns(msg []*pb.CSVColumn) interface{} {
	flat1192 := p.tryFlat(msg, func() { p.pretty_csv_columns(msg) })
	if flat1192 != nil {
		p.write(*flat1192)
		return nil
	} else {
		fields1189 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1189) == 0) {
			p.newline()
			for i1191, elem1190 := range fields1189 {
				if (i1191 > 0) {
					p.newline()
				}
				p.pretty_csv_column(elem1190)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_column(msg *pb.CSVColumn) interface{} {
	flat1200 := p.tryFlat(msg, func() { p.pretty_csv_column(msg) })
	if flat1200 != nil {
		p.write(*flat1200)
		return nil
	} else {
		_t1639 := func(_dollar_dollar *pb.CSVColumn) []interface{} {
			return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetTargetId(), _dollar_dollar.GetTypes()}
		}
		_t1640 := _t1639(msg)
		fields1193 := _t1640
		unwrapped_fields1194 := fields1193
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1195 := unwrapped_fields1194[0].(string)
		p.write(p.formatStringValue(field1195))
		p.newline()
		field1196 := unwrapped_fields1194[1].(*pb.RelationId)
		p.pretty_relation_id(field1196)
		p.newline()
		p.write("[")
		field1197 := unwrapped_fields1194[2].([]*pb.Type)
		for i1199, elem1198 := range field1197 {
			if (i1199 > 0) {
				p.newline()
			}
			p.pretty_type(elem1198)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) interface{} {
	flat1202 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1202 != nil {
		p.write(*flat1202)
		return nil
	} else {
		fields1201 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1201))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1205 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1205 != nil {
		p.write(*flat1205)
		return nil
	} else {
		_t1641 := func(_dollar_dollar *pb.Undefine) *pb.FragmentId {
			return _dollar_dollar.GetFragmentId()
		}
		_t1642 := _t1641(msg)
		fields1203 := _t1642
		unwrapped_fields1204 := fields1203
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1204)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1210 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1210 != nil {
		p.write(*flat1210)
		return nil
	} else {
		_t1643 := func(_dollar_dollar *pb.Context) []*pb.RelationId {
			return _dollar_dollar.GetRelations()
		}
		_t1644 := _t1643(msg)
		fields1206 := _t1644
		unwrapped_fields1207 := fields1206
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1207) == 0) {
			p.newline()
			for i1209, elem1208 := range unwrapped_fields1207 {
				if (i1209 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1208)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1215 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1215 != nil {
		p.write(*flat1215)
		return nil
	} else {
		_t1645 := func(_dollar_dollar *pb.Snapshot) []interface{} {
			return []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		}
		_t1646 := _t1645(msg)
		fields1211 := _t1646
		unwrapped_fields1212 := fields1211
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		p.newline()
		field1213 := unwrapped_fields1212[0].([]string)
		p.pretty_rel_edb_path(field1213)
		p.newline()
		field1214 := unwrapped_fields1212[1].(*pb.RelationId)
		p.pretty_relation_id(field1214)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1219 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1219 != nil {
		p.write(*flat1219)
		return nil
	} else {
		fields1216 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1216) == 0) {
			p.newline()
			for i1218, elem1217 := range fields1216 {
				if (i1218 > 0) {
					p.newline()
				}
				p.pretty_read(elem1217)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1230 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1230 != nil {
		p.write(*flat1230)
		return nil
	} else {
		_t1647 := func(_dollar_dollar *pb.Read) *pb.Demand {
			var _t1648 *pb.Demand
			if hasProtoField(_dollar_dollar, "demand") {
				_t1648 = _dollar_dollar.GetDemand()
			}
			return _t1648
		}
		_t1649 := _t1647(msg)
		deconstruct_result1228 := _t1649
		if deconstruct_result1228 != nil {
			unwrapped1229 := deconstruct_result1228
			p.pretty_demand(unwrapped1229)
		} else {
			_t1650 := func(_dollar_dollar *pb.Read) *pb.Output {
				var _t1651 *pb.Output
				if hasProtoField(_dollar_dollar, "output") {
					_t1651 = _dollar_dollar.GetOutput()
				}
				return _t1651
			}
			_t1652 := _t1650(msg)
			deconstruct_result1226 := _t1652
			if deconstruct_result1226 != nil {
				unwrapped1227 := deconstruct_result1226
				p.pretty_output(unwrapped1227)
			} else {
				_t1653 := func(_dollar_dollar *pb.Read) *pb.WhatIf {
					var _t1654 *pb.WhatIf
					if hasProtoField(_dollar_dollar, "what_if") {
						_t1654 = _dollar_dollar.GetWhatIf()
					}
					return _t1654
				}
				_t1655 := _t1653(msg)
				deconstruct_result1224 := _t1655
				if deconstruct_result1224 != nil {
					unwrapped1225 := deconstruct_result1224
					p.pretty_what_if(unwrapped1225)
				} else {
					_t1656 := func(_dollar_dollar *pb.Read) *pb.Abort {
						var _t1657 *pb.Abort
						if hasProtoField(_dollar_dollar, "abort") {
							_t1657 = _dollar_dollar.GetAbort()
						}
						return _t1657
					}
					_t1658 := _t1656(msg)
					deconstruct_result1222 := _t1658
					if deconstruct_result1222 != nil {
						unwrapped1223 := deconstruct_result1222
						p.pretty_abort(unwrapped1223)
					} else {
						_t1659 := func(_dollar_dollar *pb.Read) *pb.Export {
							var _t1660 *pb.Export
							if hasProtoField(_dollar_dollar, "export") {
								_t1660 = _dollar_dollar.GetExport()
							}
							return _t1660
						}
						_t1661 := _t1659(msg)
						deconstruct_result1220 := _t1661
						if deconstruct_result1220 != nil {
							unwrapped1221 := deconstruct_result1220
							p.pretty_export(unwrapped1221)
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
	flat1233 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1233 != nil {
		p.write(*flat1233)
		return nil
	} else {
		_t1662 := func(_dollar_dollar *pb.Demand) *pb.RelationId {
			return _dollar_dollar.GetRelationId()
		}
		_t1663 := _t1662(msg)
		fields1231 := _t1663
		unwrapped_fields1232 := fields1231
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1232)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1238 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1238 != nil {
		p.write(*flat1238)
		return nil
	} else {
		_t1664 := func(_dollar_dollar *pb.Output) []interface{} {
			return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		}
		_t1665 := _t1664(msg)
		fields1234 := _t1665
		unwrapped_fields1235 := fields1234
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1236 := unwrapped_fields1235[0].(string)
		p.pretty_name(field1236)
		p.newline()
		field1237 := unwrapped_fields1235[1].(*pb.RelationId)
		p.pretty_relation_id(field1237)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1243 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1243 != nil {
		p.write(*flat1243)
		return nil
	} else {
		_t1666 := func(_dollar_dollar *pb.WhatIf) []interface{} {
			return []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		}
		_t1667 := _t1666(msg)
		fields1239 := _t1667
		unwrapped_fields1240 := fields1239
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1241 := unwrapped_fields1240[0].(string)
		p.pretty_name(field1241)
		p.newline()
		field1242 := unwrapped_fields1240[1].(*pb.Epoch)
		p.pretty_epoch(field1242)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1249 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1249 != nil {
		p.write(*flat1249)
		return nil
	} else {
		_t1668 := func(_dollar_dollar *pb.Abort) []interface{} {
			var _t1669 *string
			if _dollar_dollar.GetName() != "abort" {
				_t1669 = ptr(_dollar_dollar.GetName())
			}
			return []interface{}{_t1669, _dollar_dollar.GetRelationId()}
		}
		_t1670 := _t1668(msg)
		fields1244 := _t1670
		unwrapped_fields1245 := fields1244
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1246 := unwrapped_fields1245[0].(*string)
		if field1246 != nil {
			p.newline()
			opt_val1247 := *field1246
			p.pretty_name(opt_val1247)
		}
		p.newline()
		field1248 := unwrapped_fields1245[1].(*pb.RelationId)
		p.pretty_relation_id(field1248)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1252 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1252 != nil {
		p.write(*flat1252)
		return nil
	} else {
		_t1671 := func(_dollar_dollar *pb.Export) *pb.ExportCSVConfig {
			return _dollar_dollar.GetCsvConfig()
		}
		_t1672 := _t1671(msg)
		fields1250 := _t1672
		unwrapped_fields1251 := fields1250
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1251)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1263 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1263 != nil {
		p.write(*flat1263)
		return nil
	} else {
		_t1673 := func(_dollar_dollar *pb.ExportCSVConfig) []interface{} {
			var _t1674 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
				_t1674 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
			}
			return _t1674
		}
		_t1675 := _t1673(msg)
		deconstruct_result1258 := _t1675
		if deconstruct_result1258 != nil {
			unwrapped1259 := deconstruct_result1258
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1260 := unwrapped1259[0].(string)
			p.pretty_export_csv_path(field1260)
			p.newline()
			field1261 := unwrapped1259[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1261)
			p.newline()
			field1262 := unwrapped1259[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1262)
			p.dedent()
			p.write(")")
		} else {
			_t1676 := func(_dollar_dollar *pb.ExportCSVConfig) []interface{} {
				var _t1677 []interface{}
				if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
					_t1678 := p.deconstruct_export_csv_config(_dollar_dollar)
					_t1677 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1678}
				}
				return _t1677
			}
			_t1679 := _t1676(msg)
			deconstruct_result1253 := _t1679
			if deconstruct_result1253 != nil {
				unwrapped1254 := deconstruct_result1253
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1255 := unwrapped1254[0].(string)
				p.pretty_export_csv_path(field1255)
				p.newline()
				field1256 := unwrapped1254[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1256)
				p.newline()
				field1257 := unwrapped1254[2].([][]interface{})
				p.pretty_config_dict(field1257)
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
	flat1265 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1265 != nil {
		p.write(*flat1265)
		return nil
	} else {
		fields1264 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1264))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1272 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1272 != nil {
		p.write(*flat1272)
		return nil
	} else {
		_t1680 := func(_dollar_dollar *pb.ExportCSVSource) []*pb.ExportCSVColumn {
			var _t1681 []*pb.ExportCSVColumn
			if hasProtoField(_dollar_dollar, "gnf_columns") {
				_t1681 = _dollar_dollar.GetGnfColumns().GetColumns()
			}
			return _t1681
		}
		_t1682 := _t1680(msg)
		deconstruct_result1268 := _t1682
		if deconstruct_result1268 != nil {
			unwrapped1269 := deconstruct_result1268
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1269) == 0) {
				p.newline()
				for i1271, elem1270 := range unwrapped1269 {
					if (i1271 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1270)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_t1683 := func(_dollar_dollar *pb.ExportCSVSource) *pb.RelationId {
				var _t1684 *pb.RelationId
				if hasProtoField(_dollar_dollar, "table_def") {
					_t1684 = _dollar_dollar.GetTableDef()
				}
				return _t1684
			}
			_t1685 := _t1683(msg)
			deconstruct_result1266 := _t1685
			if deconstruct_result1266 != nil {
				unwrapped1267 := deconstruct_result1266
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1267)
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
	flat1277 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1277 != nil {
		p.write(*flat1277)
		return nil
	} else {
		_t1686 := func(_dollar_dollar *pb.ExportCSVColumn) []interface{} {
			return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		}
		_t1687 := _t1686(msg)
		fields1273 := _t1687
		unwrapped_fields1274 := fields1273
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1275 := unwrapped_fields1274[0].(string)
		p.write(p.formatStringValue(field1275))
		p.newline()
		field1276 := unwrapped_fields1274[1].(*pb.RelationId)
		p.pretty_relation_id(field1276)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1281 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1281 != nil {
		p.write(*flat1281)
		return nil
	} else {
		fields1278 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1278) == 0) {
			p.newline()
			for i1280, elem1279 := range fields1278 {
				if (i1280 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1279)
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
	case *pb.ExportCSVSource:
		p.pretty_export_csv_source(m)
	case *pb.ExportCSVColumn:
		p.pretty_export_csv_column(m)
	case []*pb.ExportCSVColumn:
		p.pretty_export_csv_columns_list(m)
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
