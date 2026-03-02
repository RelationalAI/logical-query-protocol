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
	_t1423 := &pb.Value{}
	_t1423.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t1423
}

func (p *PrettyPrinter) _make_value_int64(v int64) *pb.Value {
	_t1424 := &pb.Value{}
	_t1424.Value = &pb.Value_IntValue{IntValue: v}
	return _t1424
}

func (p *PrettyPrinter) _make_value_float64(v float64) *pb.Value {
	_t1425 := &pb.Value{}
	_t1425.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t1425
}

func (p *PrettyPrinter) _make_value_string(v string) *pb.Value {
	_t1426 := &pb.Value{}
	_t1426.Value = &pb.Value_StringValue{StringValue: v}
	return _t1426
}

func (p *PrettyPrinter) _make_value_boolean(v bool) *pb.Value {
	_t1427 := &pb.Value{}
	_t1427.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t1427
}

func (p *PrettyPrinter) _make_value_uint128(v *pb.UInt128Value) *pb.Value {
	_t1428 := &pb.Value{}
	_t1428.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t1428
}

func (p *PrettyPrinter) deconstruct_configure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t1429 := p._make_value_string("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t1429})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t1430 := p._make_value_string("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t1430})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t1431 := p._make_value_string("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t1431})
			}
		}
	}
	_t1432 := p._make_value_int64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t1432})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_csv_config(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t1433 := p._make_value_int32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t1433})
	_t1434 := p._make_value_int64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t1434})
	if msg.GetNewLine() != "" {
		_t1435 := p._make_value_string(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t1435})
	}
	_t1436 := p._make_value_string(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t1436})
	_t1437 := p._make_value_string(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t1437})
	_t1438 := p._make_value_string(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t1438})
	if msg.GetComment() != "" {
		_t1439 := p._make_value_string(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t1439})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t1440 := p._make_value_string(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t1440})
	}
	_t1441 := p._make_value_string(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t1441})
	_t1442 := p._make_value_string(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t1442})
	_t1443 := p._make_value_string(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t1443})
	if msg.GetPartitionSizeMb() != 0 {
		_t1444 := p._make_value_int64(msg.GetPartitionSizeMb())
		result = append(result, []interface{}{"csv_partition_size_mb", _t1444})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_betree_info_config(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t1445 := p._make_value_float64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t1445})
	_t1446 := p._make_value_int64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t1446})
	_t1447 := p._make_value_int64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t1447})
	_t1448 := p._make_value_int64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t1448})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t1449 := p._make_value_uint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t1449})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t1450 := p._make_value_string(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t1450})
		}
	}
	_t1451 := p._make_value_int64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t1451})
	_t1452 := p._make_value_int64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t1452})
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_export_csv_config(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t1453 := p._make_value_int64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t1453})
	}
	if msg.Compression != nil {
		_t1454 := p._make_value_string(*msg.Compression)
		result = append(result, []interface{}{"compression", _t1454})
	}
	if msg.SyntaxHeaderRow != nil {
		_t1455 := p._make_value_boolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t1455})
	}
	if msg.SyntaxMissingString != nil {
		_t1456 := p._make_value_string(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t1456})
	}
	if msg.SyntaxDelim != nil {
		_t1457 := p._make_value_string(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t1457})
	}
	if msg.SyntaxQuotechar != nil {
		_t1458 := p._make_value_string(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t1458})
	}
	if msg.SyntaxEscapechar != nil {
		_t1459 := p._make_value_string(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t1459})
	}
	return listSort(result)
}

func (p *PrettyPrinter) deconstruct_relation_id_string(msg *pb.RelationId) string {
	name := p.relationIdToString(msg)
	return *name
}

func (p *PrettyPrinter) deconstruct_relation_id_uint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	var _t1460 interface{}
	if name == nil {
		return p.relationIdToUint128(msg)
	}
	_ = _t1460
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
	flat663 := p.tryFlat(msg, func() { p.pretty_transaction(msg) })
	if flat663 != nil {
		p.write(*flat663)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1308 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t1308 = _dollar_dollar.GetConfigure()
		}
		var _t1309 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t1309 = _dollar_dollar.GetSync()
		}
		fields654 := []interface{}{_t1308, _t1309, _dollar_dollar.GetEpochs()}
		unwrapped_fields655 := fields654
		p.write("(")
		p.write("transaction")
		p.indentSexp()
		field656 := unwrapped_fields655[0].(*pb.Configure)
		if field656 != nil {
			p.newline()
			opt_val657 := field656
			p.pretty_configure(opt_val657)
		}
		field658 := unwrapped_fields655[1].(*pb.Sync)
		if field658 != nil {
			p.newline()
			opt_val659 := field658
			p.pretty_sync(opt_val659)
		}
		field660 := unwrapped_fields655[2].([]*pb.Epoch)
		if !(len(field660) == 0) {
			p.newline()
			for i662, elem661 := range field660 {
				if (i662 > 0) {
					p.newline()
				}
				p.pretty_epoch(elem661)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) interface{} {
	flat666 := p.tryFlat(msg, func() { p.pretty_configure(msg) })
	if flat666 != nil {
		p.write(*flat666)
		return nil
	} else {
		_dollar_dollar := msg
		_t1310 := p.deconstruct_configure(_dollar_dollar)
		fields664 := _t1310
		unwrapped_fields665 := fields664
		p.write("(")
		p.write("configure")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields665)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) interface{} {
	flat670 := p.tryFlat(msg, func() { p.pretty_config_dict(msg) })
	if flat670 != nil {
		p.write(*flat670)
		return nil
	} else {
		fields667 := msg
		p.write("{")
		p.indent()
		if !(len(fields667) == 0) {
			p.newline()
			for i669, elem668 := range fields667 {
				if (i669 > 0) {
					p.newline()
				}
				p.pretty_config_key_value(elem668)
			}
		}
		p.dedent()
		p.write("}")
	}
	return nil
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) interface{} {
	flat675 := p.tryFlat(msg, func() { p.pretty_config_key_value(msg) })
	if flat675 != nil {
		p.write(*flat675)
		return nil
	} else {
		_dollar_dollar := msg
		fields671 := []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
		unwrapped_fields672 := fields671
		p.write(":")
		field673 := unwrapped_fields672[0].(string)
		p.write(field673)
		p.write(" ")
		field674 := unwrapped_fields672[1].(*pb.Value)
		p.pretty_value(field674)
	}
	return nil
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) interface{} {
	flat695 := p.tryFlat(msg, func() { p.pretty_value(msg) })
	if flat695 != nil {
		p.write(*flat695)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1311 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t1311 = _dollar_dollar.GetDateValue()
		}
		deconstruct_result693 := _t1311
		if deconstruct_result693 != nil {
			unwrapped694 := deconstruct_result693
			p.pretty_date(unwrapped694)
		} else {
			_dollar_dollar := msg
			var _t1312 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t1312 = _dollar_dollar.GetDatetimeValue()
			}
			deconstruct_result691 := _t1312
			if deconstruct_result691 != nil {
				unwrapped692 := deconstruct_result691
				p.pretty_datetime(unwrapped692)
			} else {
				_dollar_dollar := msg
				var _t1313 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t1313 = ptr(_dollar_dollar.GetStringValue())
				}
				deconstruct_result689 := _t1313
				if deconstruct_result689 != nil {
					unwrapped690 := *deconstruct_result689
					p.write(p.formatStringValue(unwrapped690))
				} else {
					_dollar_dollar := msg
					var _t1314 *int64
					if hasProtoField(_dollar_dollar, "int_value") {
						_t1314 = ptr(_dollar_dollar.GetIntValue())
					}
					deconstruct_result687 := _t1314
					if deconstruct_result687 != nil {
						unwrapped688 := *deconstruct_result687
						p.write(fmt.Sprintf("%d", unwrapped688))
					} else {
						_dollar_dollar := msg
						var _t1315 *float64
						if hasProtoField(_dollar_dollar, "float_value") {
							_t1315 = ptr(_dollar_dollar.GetFloatValue())
						}
						deconstruct_result685 := _t1315
						if deconstruct_result685 != nil {
							unwrapped686 := *deconstruct_result685
							p.write(formatFloat64(unwrapped686))
						} else {
							_dollar_dollar := msg
							var _t1316 *pb.UInt128Value
							if hasProtoField(_dollar_dollar, "uint128_value") {
								_t1316 = _dollar_dollar.GetUint128Value()
							}
							deconstruct_result683 := _t1316
							if deconstruct_result683 != nil {
								unwrapped684 := deconstruct_result683
								p.write(p.formatUint128(unwrapped684))
							} else {
								_dollar_dollar := msg
								var _t1317 *pb.Int128Value
								if hasProtoField(_dollar_dollar, "int128_value") {
									_t1317 = _dollar_dollar.GetInt128Value()
								}
								deconstruct_result681 := _t1317
								if deconstruct_result681 != nil {
									unwrapped682 := deconstruct_result681
									p.write(p.formatInt128(unwrapped682))
								} else {
									_dollar_dollar := msg
									var _t1318 *pb.DecimalValue
									if hasProtoField(_dollar_dollar, "decimal_value") {
										_t1318 = _dollar_dollar.GetDecimalValue()
									}
									deconstruct_result679 := _t1318
									if deconstruct_result679 != nil {
										unwrapped680 := deconstruct_result679
										p.write(p.formatDecimal(unwrapped680))
									} else {
										_dollar_dollar := msg
										var _t1319 *bool
										if hasProtoField(_dollar_dollar, "boolean_value") {
											_t1319 = ptr(_dollar_dollar.GetBooleanValue())
										}
										deconstruct_result677 := _t1319
										if deconstruct_result677 != nil {
											unwrapped678 := *deconstruct_result677
											p.pretty_boolean_value(unwrapped678)
										} else {
											fields676 := msg
											_ = fields676
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
	flat701 := p.tryFlat(msg, func() { p.pretty_date(msg) })
	if flat701 != nil {
		p.write(*flat701)
		return nil
	} else {
		_dollar_dollar := msg
		fields696 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
		unwrapped_fields697 := fields696
		p.write("(")
		p.write("date")
		p.indentSexp()
		p.newline()
		field698 := unwrapped_fields697[0].(int64)
		p.write(fmt.Sprintf("%d", field698))
		p.newline()
		field699 := unwrapped_fields697[1].(int64)
		p.write(fmt.Sprintf("%d", field699))
		p.newline()
		field700 := unwrapped_fields697[2].(int64)
		p.write(fmt.Sprintf("%d", field700))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) interface{} {
	flat712 := p.tryFlat(msg, func() { p.pretty_datetime(msg) })
	if flat712 != nil {
		p.write(*flat712)
		return nil
	} else {
		_dollar_dollar := msg
		fields702 := []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
		unwrapped_fields703 := fields702
		p.write("(")
		p.write("datetime")
		p.indentSexp()
		p.newline()
		field704 := unwrapped_fields703[0].(int64)
		p.write(fmt.Sprintf("%d", field704))
		p.newline()
		field705 := unwrapped_fields703[1].(int64)
		p.write(fmt.Sprintf("%d", field705))
		p.newline()
		field706 := unwrapped_fields703[2].(int64)
		p.write(fmt.Sprintf("%d", field706))
		p.newline()
		field707 := unwrapped_fields703[3].(int64)
		p.write(fmt.Sprintf("%d", field707))
		p.newline()
		field708 := unwrapped_fields703[4].(int64)
		p.write(fmt.Sprintf("%d", field708))
		p.newline()
		field709 := unwrapped_fields703[5].(int64)
		p.write(fmt.Sprintf("%d", field709))
		field710 := unwrapped_fields703[6].(*int64)
		if field710 != nil {
			p.newline()
			opt_val711 := *field710
			p.write(fmt.Sprintf("%d", opt_val711))
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) interface{} {
	_dollar_dollar := msg
	var _t1320 []interface{}
	if _dollar_dollar {
		_t1320 = []interface{}{}
	}
	deconstruct_result715 := _t1320
	if deconstruct_result715 != nil {
		unwrapped716 := deconstruct_result715
		_ = unwrapped716
		p.write("true")
	} else {
		_dollar_dollar := msg
		var _t1321 []interface{}
		if !(_dollar_dollar) {
			_t1321 = []interface{}{}
		}
		deconstruct_result713 := _t1321
		if deconstruct_result713 != nil {
			unwrapped714 := deconstruct_result713
			_ = unwrapped714
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) interface{} {
	flat721 := p.tryFlat(msg, func() { p.pretty_sync(msg) })
	if flat721 != nil {
		p.write(*flat721)
		return nil
	} else {
		_dollar_dollar := msg
		fields717 := _dollar_dollar.GetFragments()
		unwrapped_fields718 := fields717
		p.write("(")
		p.write("sync")
		p.indentSexp()
		if !(len(unwrapped_fields718) == 0) {
			p.newline()
			for i720, elem719 := range unwrapped_fields718 {
				if (i720 > 0) {
					p.newline()
				}
				p.pretty_fragment_id(elem719)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) interface{} {
	flat724 := p.tryFlat(msg, func() { p.pretty_fragment_id(msg) })
	if flat724 != nil {
		p.write(*flat724)
		return nil
	} else {
		_dollar_dollar := msg
		fields722 := p.fragmentIdToString(_dollar_dollar)
		unwrapped_fields723 := fields722
		p.write(":")
		p.write(unwrapped_fields723)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) interface{} {
	flat731 := p.tryFlat(msg, func() { p.pretty_epoch(msg) })
	if flat731 != nil {
		p.write(*flat731)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1322 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t1322 = _dollar_dollar.GetWrites()
		}
		var _t1323 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t1323 = _dollar_dollar.GetReads()
		}
		fields725 := []interface{}{_t1322, _t1323}
		unwrapped_fields726 := fields725
		p.write("(")
		p.write("epoch")
		p.indentSexp()
		field727 := unwrapped_fields726[0].([]*pb.Write)
		if field727 != nil {
			p.newline()
			opt_val728 := field727
			p.pretty_epoch_writes(opt_val728)
		}
		field729 := unwrapped_fields726[1].([]*pb.Read)
		if field729 != nil {
			p.newline()
			opt_val730 := field729
			p.pretty_epoch_reads(opt_val730)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) interface{} {
	flat735 := p.tryFlat(msg, func() { p.pretty_epoch_writes(msg) })
	if flat735 != nil {
		p.write(*flat735)
		return nil
	} else {
		fields732 := msg
		p.write("(")
		p.write("writes")
		p.indentSexp()
		if !(len(fields732) == 0) {
			p.newline()
			for i734, elem733 := range fields732 {
				if (i734 > 0) {
					p.newline()
				}
				p.pretty_write(elem733)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) interface{} {
	flat744 := p.tryFlat(msg, func() { p.pretty_write(msg) })
	if flat744 != nil {
		p.write(*flat744)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1324 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t1324 = _dollar_dollar.GetDefine()
		}
		deconstruct_result742 := _t1324
		if deconstruct_result742 != nil {
			unwrapped743 := deconstruct_result742
			p.pretty_define(unwrapped743)
		} else {
			_dollar_dollar := msg
			var _t1325 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t1325 = _dollar_dollar.GetUndefine()
			}
			deconstruct_result740 := _t1325
			if deconstruct_result740 != nil {
				unwrapped741 := deconstruct_result740
				p.pretty_undefine(unwrapped741)
			} else {
				_dollar_dollar := msg
				var _t1326 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t1326 = _dollar_dollar.GetContext()
				}
				deconstruct_result738 := _t1326
				if deconstruct_result738 != nil {
					unwrapped739 := deconstruct_result738
					p.pretty_context(unwrapped739)
				} else {
					_dollar_dollar := msg
					var _t1327 *pb.Snapshot
					if hasProtoField(_dollar_dollar, "snapshot") {
						_t1327 = _dollar_dollar.GetSnapshot()
					}
					deconstruct_result736 := _t1327
					if deconstruct_result736 != nil {
						unwrapped737 := deconstruct_result736
						p.pretty_snapshot(unwrapped737)
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
	flat747 := p.tryFlat(msg, func() { p.pretty_define(msg) })
	if flat747 != nil {
		p.write(*flat747)
		return nil
	} else {
		_dollar_dollar := msg
		fields745 := _dollar_dollar.GetFragment()
		unwrapped_fields746 := fields745
		p.write("(")
		p.write("define")
		p.indentSexp()
		p.newline()
		p.pretty_fragment(unwrapped_fields746)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) interface{} {
	flat754 := p.tryFlat(msg, func() { p.pretty_fragment(msg) })
	if flat754 != nil {
		p.write(*flat754)
		return nil
	} else {
		_dollar_dollar := msg
		p.startPrettyFragment(_dollar_dollar)
		fields748 := []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
		unwrapped_fields749 := fields748
		p.write("(")
		p.write("fragment")
		p.indentSexp()
		p.newline()
		field750 := unwrapped_fields749[0].(*pb.FragmentId)
		p.pretty_new_fragment_id(field750)
		field751 := unwrapped_fields749[1].([]*pb.Declaration)
		if !(len(field751) == 0) {
			p.newline()
			for i753, elem752 := range field751 {
				if (i753 > 0) {
					p.newline()
				}
				p.pretty_declaration(elem752)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) interface{} {
	flat756 := p.tryFlat(msg, func() { p.pretty_new_fragment_id(msg) })
	if flat756 != nil {
		p.write(*flat756)
		return nil
	} else {
		fields755 := msg
		p.pretty_fragment_id(fields755)
	}
	return nil
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) interface{} {
	flat765 := p.tryFlat(msg, func() { p.pretty_declaration(msg) })
	if flat765 != nil {
		p.write(*flat765)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1328 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t1328 = _dollar_dollar.GetDef()
		}
		deconstruct_result763 := _t1328
		if deconstruct_result763 != nil {
			unwrapped764 := deconstruct_result763
			p.pretty_def(unwrapped764)
		} else {
			_dollar_dollar := msg
			var _t1329 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t1329 = _dollar_dollar.GetAlgorithm()
			}
			deconstruct_result761 := _t1329
			if deconstruct_result761 != nil {
				unwrapped762 := deconstruct_result761
				p.pretty_algorithm(unwrapped762)
			} else {
				_dollar_dollar := msg
				var _t1330 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t1330 = _dollar_dollar.GetConstraint()
				}
				deconstruct_result759 := _t1330
				if deconstruct_result759 != nil {
					unwrapped760 := deconstruct_result759
					p.pretty_constraint(unwrapped760)
				} else {
					_dollar_dollar := msg
					var _t1331 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t1331 = _dollar_dollar.GetData()
					}
					deconstruct_result757 := _t1331
					if deconstruct_result757 != nil {
						unwrapped758 := deconstruct_result757
						p.pretty_data(unwrapped758)
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
	flat772 := p.tryFlat(msg, func() { p.pretty_def(msg) })
	if flat772 != nil {
		p.write(*flat772)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1332 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1332 = _dollar_dollar.GetAttrs()
		}
		fields766 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1332}
		unwrapped_fields767 := fields766
		p.write("(")
		p.write("def")
		p.indentSexp()
		p.newline()
		field768 := unwrapped_fields767[0].(*pb.RelationId)
		p.pretty_relation_id(field768)
		p.newline()
		field769 := unwrapped_fields767[1].(*pb.Abstraction)
		p.pretty_abstraction(field769)
		field770 := unwrapped_fields767[2].([]*pb.Attribute)
		if field770 != nil {
			p.newline()
			opt_val771 := field770
			p.pretty_attrs(opt_val771)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) interface{} {
	flat777 := p.tryFlat(msg, func() { p.pretty_relation_id(msg) })
	if flat777 != nil {
		p.write(*flat777)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1333 *string
		if p.relationIdToString(_dollar_dollar) != nil {
			_t1334 := p.deconstruct_relation_id_string(_dollar_dollar)
			_t1333 = ptr(_t1334)
		}
		deconstruct_result775 := _t1333
		if deconstruct_result775 != nil {
			unwrapped776 := *deconstruct_result775
			p.write(":")
			p.write(unwrapped776)
		} else {
			_dollar_dollar := msg
			_t1335 := p.deconstruct_relation_id_uint128(_dollar_dollar)
			deconstruct_result773 := _t1335
			if deconstruct_result773 != nil {
				unwrapped774 := deconstruct_result773
				p.write(p.formatUint128(unwrapped774))
			} else {
				panic(ParseError{msg: "No matching rule for relation_id"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) interface{} {
	flat782 := p.tryFlat(msg, func() { p.pretty_abstraction(msg) })
	if flat782 != nil {
		p.write(*flat782)
		return nil
	} else {
		_dollar_dollar := msg
		_t1336 := p.deconstruct_bindings(_dollar_dollar)
		fields778 := []interface{}{_t1336, _dollar_dollar.GetValue()}
		unwrapped_fields779 := fields778
		p.write("(")
		p.indent()
		field780 := unwrapped_fields779[0].([]interface{})
		p.pretty_bindings(field780)
		p.newline()
		field781 := unwrapped_fields779[1].(*pb.Formula)
		p.pretty_formula(field781)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) interface{} {
	flat790 := p.tryFlat(msg, func() { p.pretty_bindings(msg) })
	if flat790 != nil {
		p.write(*flat790)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1337 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t1337 = _dollar_dollar[1].([]*pb.Binding)
		}
		fields783 := []interface{}{_dollar_dollar[0].([]*pb.Binding), _t1337}
		unwrapped_fields784 := fields783
		p.write("[")
		p.indent()
		field785 := unwrapped_fields784[0].([]*pb.Binding)
		for i787, elem786 := range field785 {
			if (i787 > 0) {
				p.newline()
			}
			p.pretty_binding(elem786)
		}
		field788 := unwrapped_fields784[1].([]*pb.Binding)
		if field788 != nil {
			p.newline()
			opt_val789 := field788
			p.pretty_value_bindings(opt_val789)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) interface{} {
	flat795 := p.tryFlat(msg, func() { p.pretty_binding(msg) })
	if flat795 != nil {
		p.write(*flat795)
		return nil
	} else {
		_dollar_dollar := msg
		fields791 := []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
		unwrapped_fields792 := fields791
		field793 := unwrapped_fields792[0].(string)
		p.write(field793)
		p.write("::")
		field794 := unwrapped_fields792[1].(*pb.Type)
		p.pretty_type(field794)
	}
	return nil
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) interface{} {
	flat818 := p.tryFlat(msg, func() { p.pretty_type(msg) })
	if flat818 != nil {
		p.write(*flat818)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1338 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t1338 = _dollar_dollar.GetUnspecifiedType()
		}
		deconstruct_result816 := _t1338
		if deconstruct_result816 != nil {
			unwrapped817 := deconstruct_result816
			p.pretty_unspecified_type(unwrapped817)
		} else {
			_dollar_dollar := msg
			var _t1339 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t1339 = _dollar_dollar.GetStringType()
			}
			deconstruct_result814 := _t1339
			if deconstruct_result814 != nil {
				unwrapped815 := deconstruct_result814
				p.pretty_string_type(unwrapped815)
			} else {
				_dollar_dollar := msg
				var _t1340 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t1340 = _dollar_dollar.GetIntType()
				}
				deconstruct_result812 := _t1340
				if deconstruct_result812 != nil {
					unwrapped813 := deconstruct_result812
					p.pretty_int_type(unwrapped813)
				} else {
					_dollar_dollar := msg
					var _t1341 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t1341 = _dollar_dollar.GetFloatType()
					}
					deconstruct_result810 := _t1341
					if deconstruct_result810 != nil {
						unwrapped811 := deconstruct_result810
						p.pretty_float_type(unwrapped811)
					} else {
						_dollar_dollar := msg
						var _t1342 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t1342 = _dollar_dollar.GetUint128Type()
						}
						deconstruct_result808 := _t1342
						if deconstruct_result808 != nil {
							unwrapped809 := deconstruct_result808
							p.pretty_uint128_type(unwrapped809)
						} else {
							_dollar_dollar := msg
							var _t1343 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t1343 = _dollar_dollar.GetInt128Type()
							}
							deconstruct_result806 := _t1343
							if deconstruct_result806 != nil {
								unwrapped807 := deconstruct_result806
								p.pretty_int128_type(unwrapped807)
							} else {
								_dollar_dollar := msg
								var _t1344 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t1344 = _dollar_dollar.GetDateType()
								}
								deconstruct_result804 := _t1344
								if deconstruct_result804 != nil {
									unwrapped805 := deconstruct_result804
									p.pretty_date_type(unwrapped805)
								} else {
									_dollar_dollar := msg
									var _t1345 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t1345 = _dollar_dollar.GetDatetimeType()
									}
									deconstruct_result802 := _t1345
									if deconstruct_result802 != nil {
										unwrapped803 := deconstruct_result802
										p.pretty_datetime_type(unwrapped803)
									} else {
										_dollar_dollar := msg
										var _t1346 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t1346 = _dollar_dollar.GetMissingType()
										}
										deconstruct_result800 := _t1346
										if deconstruct_result800 != nil {
											unwrapped801 := deconstruct_result800
											p.pretty_missing_type(unwrapped801)
										} else {
											_dollar_dollar := msg
											var _t1347 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t1347 = _dollar_dollar.GetDecimalType()
											}
											deconstruct_result798 := _t1347
											if deconstruct_result798 != nil {
												unwrapped799 := deconstruct_result798
												p.pretty_decimal_type(unwrapped799)
											} else {
												_dollar_dollar := msg
												var _t1348 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t1348 = _dollar_dollar.GetBooleanType()
												}
												deconstruct_result796 := _t1348
												if deconstruct_result796 != nil {
													unwrapped797 := deconstruct_result796
													p.pretty_boolean_type(unwrapped797)
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
	fields819 := msg
	_ = fields819
	p.write("UNKNOWN")
	return nil
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) interface{} {
	fields820 := msg
	_ = fields820
	p.write("STRING")
	return nil
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) interface{} {
	fields821 := msg
	_ = fields821
	p.write("INT")
	return nil
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) interface{} {
	fields822 := msg
	_ = fields822
	p.write("FLOAT")
	return nil
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) interface{} {
	fields823 := msg
	_ = fields823
	p.write("UINT128")
	return nil
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) interface{} {
	fields824 := msg
	_ = fields824
	p.write("INT128")
	return nil
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) interface{} {
	fields825 := msg
	_ = fields825
	p.write("DATE")
	return nil
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) interface{} {
	fields826 := msg
	_ = fields826
	p.write("DATETIME")
	return nil
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) interface{} {
	fields827 := msg
	_ = fields827
	p.write("MISSING")
	return nil
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) interface{} {
	flat832 := p.tryFlat(msg, func() { p.pretty_decimal_type(msg) })
	if flat832 != nil {
		p.write(*flat832)
		return nil
	} else {
		_dollar_dollar := msg
		fields828 := []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
		unwrapped_fields829 := fields828
		p.write("(")
		p.write("DECIMAL")
		p.indentSexp()
		p.newline()
		field830 := unwrapped_fields829[0].(int64)
		p.write(fmt.Sprintf("%d", field830))
		p.newline()
		field831 := unwrapped_fields829[1].(int64)
		p.write(fmt.Sprintf("%d", field831))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) interface{} {
	fields833 := msg
	_ = fields833
	p.write("BOOLEAN")
	return nil
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) interface{} {
	flat837 := p.tryFlat(msg, func() { p.pretty_value_bindings(msg) })
	if flat837 != nil {
		p.write(*flat837)
		return nil
	} else {
		fields834 := msg
		p.write("|")
		if !(len(fields834) == 0) {
			p.write(" ")
			for i836, elem835 := range fields834 {
				if (i836 > 0) {
					p.newline()
				}
				p.pretty_binding(elem835)
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) interface{} {
	flat864 := p.tryFlat(msg, func() { p.pretty_formula(msg) })
	if flat864 != nil {
		p.write(*flat864)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1349 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t1349 = _dollar_dollar.GetConjunction()
		}
		deconstruct_result862 := _t1349
		if deconstruct_result862 != nil {
			unwrapped863 := deconstruct_result862
			p.pretty_true(unwrapped863)
		} else {
			_dollar_dollar := msg
			var _t1350 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t1350 = _dollar_dollar.GetDisjunction()
			}
			deconstruct_result860 := _t1350
			if deconstruct_result860 != nil {
				unwrapped861 := deconstruct_result860
				p.pretty_false(unwrapped861)
			} else {
				_dollar_dollar := msg
				var _t1351 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t1351 = _dollar_dollar.GetExists()
				}
				deconstruct_result858 := _t1351
				if deconstruct_result858 != nil {
					unwrapped859 := deconstruct_result858
					p.pretty_exists(unwrapped859)
				} else {
					_dollar_dollar := msg
					var _t1352 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t1352 = _dollar_dollar.GetReduce()
					}
					deconstruct_result856 := _t1352
					if deconstruct_result856 != nil {
						unwrapped857 := deconstruct_result856
						p.pretty_reduce(unwrapped857)
					} else {
						_dollar_dollar := msg
						var _t1353 *pb.Conjunction
						if (hasProtoField(_dollar_dollar, "conjunction") && !(len(_dollar_dollar.GetConjunction().GetArgs()) == 0)) {
							_t1353 = _dollar_dollar.GetConjunction()
						}
						deconstruct_result854 := _t1353
						if deconstruct_result854 != nil {
							unwrapped855 := deconstruct_result854
							p.pretty_conjunction(unwrapped855)
						} else {
							_dollar_dollar := msg
							var _t1354 *pb.Disjunction
							if (hasProtoField(_dollar_dollar, "disjunction") && !(len(_dollar_dollar.GetDisjunction().GetArgs()) == 0)) {
								_t1354 = _dollar_dollar.GetDisjunction()
							}
							deconstruct_result852 := _t1354
							if deconstruct_result852 != nil {
								unwrapped853 := deconstruct_result852
								p.pretty_disjunction(unwrapped853)
							} else {
								_dollar_dollar := msg
								var _t1355 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t1355 = _dollar_dollar.GetNot()
								}
								deconstruct_result850 := _t1355
								if deconstruct_result850 != nil {
									unwrapped851 := deconstruct_result850
									p.pretty_not(unwrapped851)
								} else {
									_dollar_dollar := msg
									var _t1356 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t1356 = _dollar_dollar.GetFfi()
									}
									deconstruct_result848 := _t1356
									if deconstruct_result848 != nil {
										unwrapped849 := deconstruct_result848
										p.pretty_ffi(unwrapped849)
									} else {
										_dollar_dollar := msg
										var _t1357 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t1357 = _dollar_dollar.GetAtom()
										}
										deconstruct_result846 := _t1357
										if deconstruct_result846 != nil {
											unwrapped847 := deconstruct_result846
											p.pretty_atom(unwrapped847)
										} else {
											_dollar_dollar := msg
											var _t1358 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t1358 = _dollar_dollar.GetPragma()
											}
											deconstruct_result844 := _t1358
											if deconstruct_result844 != nil {
												unwrapped845 := deconstruct_result844
												p.pretty_pragma(unwrapped845)
											} else {
												_dollar_dollar := msg
												var _t1359 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t1359 = _dollar_dollar.GetPrimitive()
												}
												deconstruct_result842 := _t1359
												if deconstruct_result842 != nil {
													unwrapped843 := deconstruct_result842
													p.pretty_primitive(unwrapped843)
												} else {
													_dollar_dollar := msg
													var _t1360 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t1360 = _dollar_dollar.GetRelAtom()
													}
													deconstruct_result840 := _t1360
													if deconstruct_result840 != nil {
														unwrapped841 := deconstruct_result840
														p.pretty_rel_atom(unwrapped841)
													} else {
														_dollar_dollar := msg
														var _t1361 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t1361 = _dollar_dollar.GetCast()
														}
														deconstruct_result838 := _t1361
														if deconstruct_result838 != nil {
															unwrapped839 := deconstruct_result838
															p.pretty_cast(unwrapped839)
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
	fields865 := msg
	_ = fields865
	p.write("(")
	p.write("true")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) interface{} {
	fields866 := msg
	_ = fields866
	p.write("(")
	p.write("false")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) interface{} {
	flat871 := p.tryFlat(msg, func() { p.pretty_exists(msg) })
	if flat871 != nil {
		p.write(*flat871)
		return nil
	} else {
		_dollar_dollar := msg
		_t1362 := p.deconstruct_bindings(_dollar_dollar.GetBody())
		fields867 := []interface{}{_t1362, _dollar_dollar.GetBody().GetValue()}
		unwrapped_fields868 := fields867
		p.write("(")
		p.write("exists")
		p.indentSexp()
		p.newline()
		field869 := unwrapped_fields868[0].([]interface{})
		p.pretty_bindings(field869)
		p.newline()
		field870 := unwrapped_fields868[1].(*pb.Formula)
		p.pretty_formula(field870)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) interface{} {
	flat877 := p.tryFlat(msg, func() { p.pretty_reduce(msg) })
	if flat877 != nil {
		p.write(*flat877)
		return nil
	} else {
		_dollar_dollar := msg
		fields872 := []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
		unwrapped_fields873 := fields872
		p.write("(")
		p.write("reduce")
		p.indentSexp()
		p.newline()
		field874 := unwrapped_fields873[0].(*pb.Abstraction)
		p.pretty_abstraction(field874)
		p.newline()
		field875 := unwrapped_fields873[1].(*pb.Abstraction)
		p.pretty_abstraction(field875)
		p.newline()
		field876 := unwrapped_fields873[2].([]*pb.Term)
		p.pretty_terms(field876)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) interface{} {
	flat881 := p.tryFlat(msg, func() { p.pretty_terms(msg) })
	if flat881 != nil {
		p.write(*flat881)
		return nil
	} else {
		fields878 := msg
		p.write("(")
		p.write("terms")
		p.indentSexp()
		if !(len(fields878) == 0) {
			p.newline()
			for i880, elem879 := range fields878 {
				if (i880 > 0) {
					p.newline()
				}
				p.pretty_term(elem879)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) interface{} {
	flat886 := p.tryFlat(msg, func() { p.pretty_term(msg) })
	if flat886 != nil {
		p.write(*flat886)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1363 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t1363 = _dollar_dollar.GetVar()
		}
		deconstruct_result884 := _t1363
		if deconstruct_result884 != nil {
			unwrapped885 := deconstruct_result884
			p.pretty_var(unwrapped885)
		} else {
			_dollar_dollar := msg
			var _t1364 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t1364 = _dollar_dollar.GetConstant()
			}
			deconstruct_result882 := _t1364
			if deconstruct_result882 != nil {
				unwrapped883 := deconstruct_result882
				p.pretty_constant(unwrapped883)
			} else {
				panic(ParseError{msg: "No matching rule for term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) interface{} {
	flat889 := p.tryFlat(msg, func() { p.pretty_var(msg) })
	if flat889 != nil {
		p.write(*flat889)
		return nil
	} else {
		_dollar_dollar := msg
		fields887 := _dollar_dollar.GetName()
		unwrapped_fields888 := fields887
		p.write(unwrapped_fields888)
	}
	return nil
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) interface{} {
	flat891 := p.tryFlat(msg, func() { p.pretty_constant(msg) })
	if flat891 != nil {
		p.write(*flat891)
		return nil
	} else {
		fields890 := msg
		p.pretty_value(fields890)
	}
	return nil
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) interface{} {
	flat896 := p.tryFlat(msg, func() { p.pretty_conjunction(msg) })
	if flat896 != nil {
		p.write(*flat896)
		return nil
	} else {
		_dollar_dollar := msg
		fields892 := _dollar_dollar.GetArgs()
		unwrapped_fields893 := fields892
		p.write("(")
		p.write("and")
		p.indentSexp()
		if !(len(unwrapped_fields893) == 0) {
			p.newline()
			for i895, elem894 := range unwrapped_fields893 {
				if (i895 > 0) {
					p.newline()
				}
				p.pretty_formula(elem894)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) interface{} {
	flat901 := p.tryFlat(msg, func() { p.pretty_disjunction(msg) })
	if flat901 != nil {
		p.write(*flat901)
		return nil
	} else {
		_dollar_dollar := msg
		fields897 := _dollar_dollar.GetArgs()
		unwrapped_fields898 := fields897
		p.write("(")
		p.write("or")
		p.indentSexp()
		if !(len(unwrapped_fields898) == 0) {
			p.newline()
			for i900, elem899 := range unwrapped_fields898 {
				if (i900 > 0) {
					p.newline()
				}
				p.pretty_formula(elem899)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) interface{} {
	flat904 := p.tryFlat(msg, func() { p.pretty_not(msg) })
	if flat904 != nil {
		p.write(*flat904)
		return nil
	} else {
		_dollar_dollar := msg
		fields902 := _dollar_dollar.GetArg()
		unwrapped_fields903 := fields902
		p.write("(")
		p.write("not")
		p.indentSexp()
		p.newline()
		p.pretty_formula(unwrapped_fields903)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) interface{} {
	flat910 := p.tryFlat(msg, func() { p.pretty_ffi(msg) })
	if flat910 != nil {
		p.write(*flat910)
		return nil
	} else {
		_dollar_dollar := msg
		fields905 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
		unwrapped_fields906 := fields905
		p.write("(")
		p.write("ffi")
		p.indentSexp()
		p.newline()
		field907 := unwrapped_fields906[0].(string)
		p.pretty_name(field907)
		p.newline()
		field908 := unwrapped_fields906[1].([]*pb.Abstraction)
		p.pretty_ffi_args(field908)
		p.newline()
		field909 := unwrapped_fields906[2].([]*pb.Term)
		p.pretty_terms(field909)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_name(msg string) interface{} {
	flat912 := p.tryFlat(msg, func() { p.pretty_name(msg) })
	if flat912 != nil {
		p.write(*flat912)
		return nil
	} else {
		fields911 := msg
		p.write(":")
		p.write(fields911)
	}
	return nil
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) interface{} {
	flat916 := p.tryFlat(msg, func() { p.pretty_ffi_args(msg) })
	if flat916 != nil {
		p.write(*flat916)
		return nil
	} else {
		fields913 := msg
		p.write("(")
		p.write("args")
		p.indentSexp()
		if !(len(fields913) == 0) {
			p.newline()
			for i915, elem914 := range fields913 {
				if (i915 > 0) {
					p.newline()
				}
				p.pretty_abstraction(elem914)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) interface{} {
	flat923 := p.tryFlat(msg, func() { p.pretty_atom(msg) })
	if flat923 != nil {
		p.write(*flat923)
		return nil
	} else {
		_dollar_dollar := msg
		fields917 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields918 := fields917
		p.write("(")
		p.write("atom")
		p.indentSexp()
		p.newline()
		field919 := unwrapped_fields918[0].(*pb.RelationId)
		p.pretty_relation_id(field919)
		field920 := unwrapped_fields918[1].([]*pb.Term)
		if !(len(field920) == 0) {
			p.newline()
			for i922, elem921 := range field920 {
				if (i922 > 0) {
					p.newline()
				}
				p.pretty_term(elem921)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) interface{} {
	flat930 := p.tryFlat(msg, func() { p.pretty_pragma(msg) })
	if flat930 != nil {
		p.write(*flat930)
		return nil
	} else {
		_dollar_dollar := msg
		fields924 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields925 := fields924
		p.write("(")
		p.write("pragma")
		p.indentSexp()
		p.newline()
		field926 := unwrapped_fields925[0].(string)
		p.pretty_name(field926)
		field927 := unwrapped_fields925[1].([]*pb.Term)
		if !(len(field927) == 0) {
			p.newline()
			for i929, elem928 := range field927 {
				if (i929 > 0) {
					p.newline()
				}
				p.pretty_term(elem928)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) interface{} {
	flat946 := p.tryFlat(msg, func() { p.pretty_primitive(msg) })
	if flat946 != nil {
		p.write(*flat946)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1365 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1365 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		guard_result945 := _t1365
		if guard_result945 != nil {
			p.pretty_eq(msg)
		} else {
			_dollar_dollar := msg
			var _t1366 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t1366 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			guard_result944 := _t1366
			if guard_result944 != nil {
				p.pretty_lt(msg)
			} else {
				_dollar_dollar := msg
				var _t1367 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t1367 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				guard_result943 := _t1367
				if guard_result943 != nil {
					p.pretty_lt_eq(msg)
				} else {
					_dollar_dollar := msg
					var _t1368 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t1368 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					guard_result942 := _t1368
					if guard_result942 != nil {
						p.pretty_gt(msg)
					} else {
						_dollar_dollar := msg
						var _t1369 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t1369 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						guard_result941 := _t1369
						if guard_result941 != nil {
							p.pretty_gt_eq(msg)
						} else {
							_dollar_dollar := msg
							var _t1370 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t1370 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							guard_result940 := _t1370
							if guard_result940 != nil {
								p.pretty_add(msg)
							} else {
								_dollar_dollar := msg
								var _t1371 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t1371 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								guard_result939 := _t1371
								if guard_result939 != nil {
									p.pretty_minus(msg)
								} else {
									_dollar_dollar := msg
									var _t1372 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t1372 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									guard_result938 := _t1372
									if guard_result938 != nil {
										p.pretty_multiply(msg)
									} else {
										_dollar_dollar := msg
										var _t1373 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t1373 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										guard_result937 := _t1373
										if guard_result937 != nil {
											p.pretty_divide(msg)
										} else {
											_dollar_dollar := msg
											fields931 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
											unwrapped_fields932 := fields931
											p.write("(")
											p.write("primitive")
											p.indentSexp()
											p.newline()
											field933 := unwrapped_fields932[0].(string)
											p.pretty_name(field933)
											field934 := unwrapped_fields932[1].([]*pb.RelTerm)
											if !(len(field934) == 0) {
												p.newline()
												for i936, elem935 := range field934 {
													if (i936 > 0) {
														p.newline()
													}
													p.pretty_rel_term(elem935)
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
	flat951 := p.tryFlat(msg, func() { p.pretty_eq(msg) })
	if flat951 != nil {
		p.write(*flat951)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1374 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t1374 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields947 := _t1374
		unwrapped_fields948 := fields947
		p.write("(")
		p.write("=")
		p.indentSexp()
		p.newline()
		field949 := unwrapped_fields948[0].(*pb.Term)
		p.pretty_term(field949)
		p.newline()
		field950 := unwrapped_fields948[1].(*pb.Term)
		p.pretty_term(field950)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) interface{} {
	flat956 := p.tryFlat(msg, func() { p.pretty_lt(msg) })
	if flat956 != nil {
		p.write(*flat956)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1375 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t1375 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields952 := _t1375
		unwrapped_fields953 := fields952
		p.write("(")
		p.write("<")
		p.indentSexp()
		p.newline()
		field954 := unwrapped_fields953[0].(*pb.Term)
		p.pretty_term(field954)
		p.newline()
		field955 := unwrapped_fields953[1].(*pb.Term)
		p.pretty_term(field955)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) interface{} {
	flat961 := p.tryFlat(msg, func() { p.pretty_lt_eq(msg) })
	if flat961 != nil {
		p.write(*flat961)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1376 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t1376 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields957 := _t1376
		unwrapped_fields958 := fields957
		p.write("(")
		p.write("<=")
		p.indentSexp()
		p.newline()
		field959 := unwrapped_fields958[0].(*pb.Term)
		p.pretty_term(field959)
		p.newline()
		field960 := unwrapped_fields958[1].(*pb.Term)
		p.pretty_term(field960)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) interface{} {
	flat966 := p.tryFlat(msg, func() { p.pretty_gt(msg) })
	if flat966 != nil {
		p.write(*flat966)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1377 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t1377 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields962 := _t1377
		unwrapped_fields963 := fields962
		p.write("(")
		p.write(">")
		p.indentSexp()
		p.newline()
		field964 := unwrapped_fields963[0].(*pb.Term)
		p.pretty_term(field964)
		p.newline()
		field965 := unwrapped_fields963[1].(*pb.Term)
		p.pretty_term(field965)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) interface{} {
	flat971 := p.tryFlat(msg, func() { p.pretty_gt_eq(msg) })
	if flat971 != nil {
		p.write(*flat971)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1378 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t1378 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		fields967 := _t1378
		unwrapped_fields968 := fields967
		p.write("(")
		p.write(">=")
		p.indentSexp()
		p.newline()
		field969 := unwrapped_fields968[0].(*pb.Term)
		p.pretty_term(field969)
		p.newline()
		field970 := unwrapped_fields968[1].(*pb.Term)
		p.pretty_term(field970)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) interface{} {
	flat977 := p.tryFlat(msg, func() { p.pretty_add(msg) })
	if flat977 != nil {
		p.write(*flat977)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1379 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t1379 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields972 := _t1379
		unwrapped_fields973 := fields972
		p.write("(")
		p.write("+")
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

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) interface{} {
	flat983 := p.tryFlat(msg, func() { p.pretty_minus(msg) })
	if flat983 != nil {
		p.write(*flat983)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1380 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t1380 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields978 := _t1380
		unwrapped_fields979 := fields978
		p.write("(")
		p.write("-")
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

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) interface{} {
	flat989 := p.tryFlat(msg, func() { p.pretty_multiply(msg) })
	if flat989 != nil {
		p.write(*flat989)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1381 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t1381 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields984 := _t1381
		unwrapped_fields985 := fields984
		p.write("(")
		p.write("*")
		p.indentSexp()
		p.newline()
		field986 := unwrapped_fields985[0].(*pb.Term)
		p.pretty_term(field986)
		p.newline()
		field987 := unwrapped_fields985[1].(*pb.Term)
		p.pretty_term(field987)
		p.newline()
		field988 := unwrapped_fields985[2].(*pb.Term)
		p.pretty_term(field988)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) interface{} {
	flat995 := p.tryFlat(msg, func() { p.pretty_divide(msg) })
	if flat995 != nil {
		p.write(*flat995)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1382 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t1382 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		fields990 := _t1382
		unwrapped_fields991 := fields990
		p.write("(")
		p.write("/")
		p.indentSexp()
		p.newline()
		field992 := unwrapped_fields991[0].(*pb.Term)
		p.pretty_term(field992)
		p.newline()
		field993 := unwrapped_fields991[1].(*pb.Term)
		p.pretty_term(field993)
		p.newline()
		field994 := unwrapped_fields991[2].(*pb.Term)
		p.pretty_term(field994)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) interface{} {
	flat1000 := p.tryFlat(msg, func() { p.pretty_rel_term(msg) })
	if flat1000 != nil {
		p.write(*flat1000)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1383 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t1383 = _dollar_dollar.GetSpecializedValue()
		}
		deconstruct_result998 := _t1383
		if deconstruct_result998 != nil {
			unwrapped999 := deconstruct_result998
			p.pretty_specialized_value(unwrapped999)
		} else {
			_dollar_dollar := msg
			var _t1384 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t1384 = _dollar_dollar.GetTerm()
			}
			deconstruct_result996 := _t1384
			if deconstruct_result996 != nil {
				unwrapped997 := deconstruct_result996
				p.pretty_term(unwrapped997)
			} else {
				panic(ParseError{msg: "No matching rule for rel_term"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) interface{} {
	flat1002 := p.tryFlat(msg, func() { p.pretty_specialized_value(msg) })
	if flat1002 != nil {
		p.write(*flat1002)
		return nil
	} else {
		fields1001 := msg
		p.write("#")
		p.pretty_value(fields1001)
	}
	return nil
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) interface{} {
	flat1009 := p.tryFlat(msg, func() { p.pretty_rel_atom(msg) })
	if flat1009 != nil {
		p.write(*flat1009)
		return nil
	} else {
		_dollar_dollar := msg
		fields1003 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
		unwrapped_fields1004 := fields1003
		p.write("(")
		p.write("relatom")
		p.indentSexp()
		p.newline()
		field1005 := unwrapped_fields1004[0].(string)
		p.pretty_name(field1005)
		field1006 := unwrapped_fields1004[1].([]*pb.RelTerm)
		if !(len(field1006) == 0) {
			p.newline()
			for i1008, elem1007 := range field1006 {
				if (i1008 > 0) {
					p.newline()
				}
				p.pretty_rel_term(elem1007)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) interface{} {
	flat1014 := p.tryFlat(msg, func() { p.pretty_cast(msg) })
	if flat1014 != nil {
		p.write(*flat1014)
		return nil
	} else {
		_dollar_dollar := msg
		fields1010 := []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
		unwrapped_fields1011 := fields1010
		p.write("(")
		p.write("cast")
		p.indentSexp()
		p.newline()
		field1012 := unwrapped_fields1011[0].(*pb.Term)
		p.pretty_term(field1012)
		p.newline()
		field1013 := unwrapped_fields1011[1].(*pb.Term)
		p.pretty_term(field1013)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) interface{} {
	flat1018 := p.tryFlat(msg, func() { p.pretty_attrs(msg) })
	if flat1018 != nil {
		p.write(*flat1018)
		return nil
	} else {
		fields1015 := msg
		p.write("(")
		p.write("attrs")
		p.indentSexp()
		if !(len(fields1015) == 0) {
			p.newline()
			for i1017, elem1016 := range fields1015 {
				if (i1017 > 0) {
					p.newline()
				}
				p.pretty_attribute(elem1016)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) interface{} {
	flat1025 := p.tryFlat(msg, func() { p.pretty_attribute(msg) })
	if flat1025 != nil {
		p.write(*flat1025)
		return nil
	} else {
		_dollar_dollar := msg
		fields1019 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
		unwrapped_fields1020 := fields1019
		p.write("(")
		p.write("attribute")
		p.indentSexp()
		p.newline()
		field1021 := unwrapped_fields1020[0].(string)
		p.pretty_name(field1021)
		field1022 := unwrapped_fields1020[1].([]*pb.Value)
		if !(len(field1022) == 0) {
			p.newline()
			for i1024, elem1023 := range field1022 {
				if (i1024 > 0) {
					p.newline()
				}
				p.pretty_value(elem1023)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) interface{} {
	flat1032 := p.tryFlat(msg, func() { p.pretty_algorithm(msg) })
	if flat1032 != nil {
		p.write(*flat1032)
		return nil
	} else {
		_dollar_dollar := msg
		fields1026 := []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
		unwrapped_fields1027 := fields1026
		p.write("(")
		p.write("algorithm")
		p.indentSexp()
		field1028 := unwrapped_fields1027[0].([]*pb.RelationId)
		if !(len(field1028) == 0) {
			p.newline()
			for i1030, elem1029 := range field1028 {
				if (i1030 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1029)
			}
		}
		p.newline()
		field1031 := unwrapped_fields1027[1].(*pb.Script)
		p.pretty_script(field1031)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) interface{} {
	flat1037 := p.tryFlat(msg, func() { p.pretty_script(msg) })
	if flat1037 != nil {
		p.write(*flat1037)
		return nil
	} else {
		_dollar_dollar := msg
		fields1033 := _dollar_dollar.GetConstructs()
		unwrapped_fields1034 := fields1033
		p.write("(")
		p.write("script")
		p.indentSexp()
		if !(len(unwrapped_fields1034) == 0) {
			p.newline()
			for i1036, elem1035 := range unwrapped_fields1034 {
				if (i1036 > 0) {
					p.newline()
				}
				p.pretty_construct(elem1035)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) interface{} {
	flat1042 := p.tryFlat(msg, func() { p.pretty_construct(msg) })
	if flat1042 != nil {
		p.write(*flat1042)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1385 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t1385 = _dollar_dollar.GetLoop()
		}
		deconstruct_result1040 := _t1385
		if deconstruct_result1040 != nil {
			unwrapped1041 := deconstruct_result1040
			p.pretty_loop(unwrapped1041)
		} else {
			_dollar_dollar := msg
			var _t1386 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t1386 = _dollar_dollar.GetInstruction()
			}
			deconstruct_result1038 := _t1386
			if deconstruct_result1038 != nil {
				unwrapped1039 := deconstruct_result1038
				p.pretty_instruction(unwrapped1039)
			} else {
				panic(ParseError{msg: "No matching rule for construct"})
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) interface{} {
	flat1047 := p.tryFlat(msg, func() { p.pretty_loop(msg) })
	if flat1047 != nil {
		p.write(*flat1047)
		return nil
	} else {
		_dollar_dollar := msg
		fields1043 := []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
		unwrapped_fields1044 := fields1043
		p.write("(")
		p.write("loop")
		p.indentSexp()
		p.newline()
		field1045 := unwrapped_fields1044[0].([]*pb.Instruction)
		p.pretty_init(field1045)
		p.newline()
		field1046 := unwrapped_fields1044[1].(*pb.Script)
		p.pretty_script(field1046)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) interface{} {
	flat1051 := p.tryFlat(msg, func() { p.pretty_init(msg) })
	if flat1051 != nil {
		p.write(*flat1051)
		return nil
	} else {
		fields1048 := msg
		p.write("(")
		p.write("init")
		p.indentSexp()
		if !(len(fields1048) == 0) {
			p.newline()
			for i1050, elem1049 := range fields1048 {
				if (i1050 > 0) {
					p.newline()
				}
				p.pretty_instruction(elem1049)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) interface{} {
	flat1062 := p.tryFlat(msg, func() { p.pretty_instruction(msg) })
	if flat1062 != nil {
		p.write(*flat1062)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1387 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t1387 = _dollar_dollar.GetAssign()
		}
		deconstruct_result1060 := _t1387
		if deconstruct_result1060 != nil {
			unwrapped1061 := deconstruct_result1060
			p.pretty_assign(unwrapped1061)
		} else {
			_dollar_dollar := msg
			var _t1388 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t1388 = _dollar_dollar.GetUpsert()
			}
			deconstruct_result1058 := _t1388
			if deconstruct_result1058 != nil {
				unwrapped1059 := deconstruct_result1058
				p.pretty_upsert(unwrapped1059)
			} else {
				_dollar_dollar := msg
				var _t1389 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t1389 = _dollar_dollar.GetBreak()
				}
				deconstruct_result1056 := _t1389
				if deconstruct_result1056 != nil {
					unwrapped1057 := deconstruct_result1056
					p.pretty_break(unwrapped1057)
				} else {
					_dollar_dollar := msg
					var _t1390 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t1390 = _dollar_dollar.GetMonoidDef()
					}
					deconstruct_result1054 := _t1390
					if deconstruct_result1054 != nil {
						unwrapped1055 := deconstruct_result1054
						p.pretty_monoid_def(unwrapped1055)
					} else {
						_dollar_dollar := msg
						var _t1391 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t1391 = _dollar_dollar.GetMonusDef()
						}
						deconstruct_result1052 := _t1391
						if deconstruct_result1052 != nil {
							unwrapped1053 := deconstruct_result1052
							p.pretty_monus_def(unwrapped1053)
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
	flat1069 := p.tryFlat(msg, func() { p.pretty_assign(msg) })
	if flat1069 != nil {
		p.write(*flat1069)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1392 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1392 = _dollar_dollar.GetAttrs()
		}
		fields1063 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1392}
		unwrapped_fields1064 := fields1063
		p.write("(")
		p.write("assign")
		p.indentSexp()
		p.newline()
		field1065 := unwrapped_fields1064[0].(*pb.RelationId)
		p.pretty_relation_id(field1065)
		p.newline()
		field1066 := unwrapped_fields1064[1].(*pb.Abstraction)
		p.pretty_abstraction(field1066)
		field1067 := unwrapped_fields1064[2].([]*pb.Attribute)
		if field1067 != nil {
			p.newline()
			opt_val1068 := field1067
			p.pretty_attrs(opt_val1068)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) interface{} {
	flat1076 := p.tryFlat(msg, func() { p.pretty_upsert(msg) })
	if flat1076 != nil {
		p.write(*flat1076)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1393 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1393 = _dollar_dollar.GetAttrs()
		}
		fields1070 := []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1393}
		unwrapped_fields1071 := fields1070
		p.write("(")
		p.write("upsert")
		p.indentSexp()
		p.newline()
		field1072 := unwrapped_fields1071[0].(*pb.RelationId)
		p.pretty_relation_id(field1072)
		p.newline()
		field1073 := unwrapped_fields1071[1].([]interface{})
		p.pretty_abstraction_with_arity(field1073)
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

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) interface{} {
	flat1081 := p.tryFlat(msg, func() { p.pretty_abstraction_with_arity(msg) })
	if flat1081 != nil {
		p.write(*flat1081)
		return nil
	} else {
		_dollar_dollar := msg
		_t1394 := p.deconstruct_bindings_with_arity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		fields1077 := []interface{}{_t1394, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
		unwrapped_fields1078 := fields1077
		p.write("(")
		p.indent()
		field1079 := unwrapped_fields1078[0].([]interface{})
		p.pretty_bindings(field1079)
		p.newline()
		field1080 := unwrapped_fields1078[1].(*pb.Formula)
		p.pretty_formula(field1080)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) interface{} {
	flat1088 := p.tryFlat(msg, func() { p.pretty_break(msg) })
	if flat1088 != nil {
		p.write(*flat1088)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1395 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1395 = _dollar_dollar.GetAttrs()
		}
		fields1082 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t1395}
		unwrapped_fields1083 := fields1082
		p.write("(")
		p.write("break")
		p.indentSexp()
		p.newline()
		field1084 := unwrapped_fields1083[0].(*pb.RelationId)
		p.pretty_relation_id(field1084)
		p.newline()
		field1085 := unwrapped_fields1083[1].(*pb.Abstraction)
		p.pretty_abstraction(field1085)
		field1086 := unwrapped_fields1083[2].([]*pb.Attribute)
		if field1086 != nil {
			p.newline()
			opt_val1087 := field1086
			p.pretty_attrs(opt_val1087)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) interface{} {
	flat1096 := p.tryFlat(msg, func() { p.pretty_monoid_def(msg) })
	if flat1096 != nil {
		p.write(*flat1096)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1396 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1396 = _dollar_dollar.GetAttrs()
		}
		fields1089 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1396}
		unwrapped_fields1090 := fields1089
		p.write("(")
		p.write("monoid")
		p.indentSexp()
		p.newline()
		field1091 := unwrapped_fields1090[0].(*pb.Monoid)
		p.pretty_monoid(field1091)
		p.newline()
		field1092 := unwrapped_fields1090[1].(*pb.RelationId)
		p.pretty_relation_id(field1092)
		p.newline()
		field1093 := unwrapped_fields1090[2].([]interface{})
		p.pretty_abstraction_with_arity(field1093)
		field1094 := unwrapped_fields1090[3].([]*pb.Attribute)
		if field1094 != nil {
			p.newline()
			opt_val1095 := field1094
			p.pretty_attrs(opt_val1095)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) interface{} {
	flat1105 := p.tryFlat(msg, func() { p.pretty_monoid(msg) })
	if flat1105 != nil {
		p.write(*flat1105)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1397 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t1397 = _dollar_dollar.GetOrMonoid()
		}
		deconstruct_result1103 := _t1397
		if deconstruct_result1103 != nil {
			unwrapped1104 := deconstruct_result1103
			p.pretty_or_monoid(unwrapped1104)
		} else {
			_dollar_dollar := msg
			var _t1398 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t1398 = _dollar_dollar.GetMinMonoid()
			}
			deconstruct_result1101 := _t1398
			if deconstruct_result1101 != nil {
				unwrapped1102 := deconstruct_result1101
				p.pretty_min_monoid(unwrapped1102)
			} else {
				_dollar_dollar := msg
				var _t1399 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t1399 = _dollar_dollar.GetMaxMonoid()
				}
				deconstruct_result1099 := _t1399
				if deconstruct_result1099 != nil {
					unwrapped1100 := deconstruct_result1099
					p.pretty_max_monoid(unwrapped1100)
				} else {
					_dollar_dollar := msg
					var _t1400 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t1400 = _dollar_dollar.GetSumMonoid()
					}
					deconstruct_result1097 := _t1400
					if deconstruct_result1097 != nil {
						unwrapped1098 := deconstruct_result1097
						p.pretty_sum_monoid(unwrapped1098)
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
	fields1106 := msg
	_ = fields1106
	p.write("(")
	p.write("or")
	p.write(")")
	return nil
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) interface{} {
	flat1109 := p.tryFlat(msg, func() { p.pretty_min_monoid(msg) })
	if flat1109 != nil {
		p.write(*flat1109)
		return nil
	} else {
		_dollar_dollar := msg
		fields1107 := _dollar_dollar.GetType()
		unwrapped_fields1108 := fields1107
		p.write("(")
		p.write("min")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1108)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) interface{} {
	flat1112 := p.tryFlat(msg, func() { p.pretty_max_monoid(msg) })
	if flat1112 != nil {
		p.write(*flat1112)
		return nil
	} else {
		_dollar_dollar := msg
		fields1110 := _dollar_dollar.GetType()
		unwrapped_fields1111 := fields1110
		p.write("(")
		p.write("max")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1111)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) interface{} {
	flat1115 := p.tryFlat(msg, func() { p.pretty_sum_monoid(msg) })
	if flat1115 != nil {
		p.write(*flat1115)
		return nil
	} else {
		_dollar_dollar := msg
		fields1113 := _dollar_dollar.GetType()
		unwrapped_fields1114 := fields1113
		p.write("(")
		p.write("sum")
		p.indentSexp()
		p.newline()
		p.pretty_type(unwrapped_fields1114)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) interface{} {
	flat1123 := p.tryFlat(msg, func() { p.pretty_monus_def(msg) })
	if flat1123 != nil {
		p.write(*flat1123)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1401 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t1401 = _dollar_dollar.GetAttrs()
		}
		fields1116 := []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t1401}
		unwrapped_fields1117 := fields1116
		p.write("(")
		p.write("monus")
		p.indentSexp()
		p.newline()
		field1118 := unwrapped_fields1117[0].(*pb.Monoid)
		p.pretty_monoid(field1118)
		p.newline()
		field1119 := unwrapped_fields1117[1].(*pb.RelationId)
		p.pretty_relation_id(field1119)
		p.newline()
		field1120 := unwrapped_fields1117[2].([]interface{})
		p.pretty_abstraction_with_arity(field1120)
		field1121 := unwrapped_fields1117[3].([]*pb.Attribute)
		if field1121 != nil {
			p.newline()
			opt_val1122 := field1121
			p.pretty_attrs(opt_val1122)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) interface{} {
	flat1130 := p.tryFlat(msg, func() { p.pretty_constraint(msg) })
	if flat1130 != nil {
		p.write(*flat1130)
		return nil
	} else {
		_dollar_dollar := msg
		fields1124 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
		unwrapped_fields1125 := fields1124
		p.write("(")
		p.write("functional_dependency")
		p.indentSexp()
		p.newline()
		field1126 := unwrapped_fields1125[0].(*pb.RelationId)
		p.pretty_relation_id(field1126)
		p.newline()
		field1127 := unwrapped_fields1125[1].(*pb.Abstraction)
		p.pretty_abstraction(field1127)
		p.newline()
		field1128 := unwrapped_fields1125[2].([]*pb.Var)
		p.pretty_functional_dependency_keys(field1128)
		p.newline()
		field1129 := unwrapped_fields1125[3].([]*pb.Var)
		p.pretty_functional_dependency_values(field1129)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) interface{} {
	flat1134 := p.tryFlat(msg, func() { p.pretty_functional_dependency_keys(msg) })
	if flat1134 != nil {
		p.write(*flat1134)
		return nil
	} else {
		fields1131 := msg
		p.write("(")
		p.write("keys")
		p.indentSexp()
		if !(len(fields1131) == 0) {
			p.newline()
			for i1133, elem1132 := range fields1131 {
				if (i1133 > 0) {
					p.newline()
				}
				p.pretty_var(elem1132)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) interface{} {
	flat1138 := p.tryFlat(msg, func() { p.pretty_functional_dependency_values(msg) })
	if flat1138 != nil {
		p.write(*flat1138)
		return nil
	} else {
		fields1135 := msg
		p.write("(")
		p.write("values")
		p.indentSexp()
		if !(len(fields1135) == 0) {
			p.newline()
			for i1137, elem1136 := range fields1135 {
				if (i1137 > 0) {
					p.newline()
				}
				p.pretty_var(elem1136)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) interface{} {
	flat1145 := p.tryFlat(msg, func() { p.pretty_data(msg) })
	if flat1145 != nil {
		p.write(*flat1145)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1402 *pb.EDB
		if hasProtoField(_dollar_dollar, "edb") {
			_t1402 = _dollar_dollar.GetEdb()
		}
		deconstruct_result1143 := _t1402
		if deconstruct_result1143 != nil {
			unwrapped1144 := deconstruct_result1143
			p.pretty_edb(unwrapped1144)
		} else {
			_dollar_dollar := msg
			var _t1403 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t1403 = _dollar_dollar.GetBetreeRelation()
			}
			deconstruct_result1141 := _t1403
			if deconstruct_result1141 != nil {
				unwrapped1142 := deconstruct_result1141
				p.pretty_betree_relation(unwrapped1142)
			} else {
				_dollar_dollar := msg
				var _t1404 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t1404 = _dollar_dollar.GetCsvData()
				}
				deconstruct_result1139 := _t1404
				if deconstruct_result1139 != nil {
					unwrapped1140 := deconstruct_result1139
					p.pretty_csv_data(unwrapped1140)
				} else {
					panic(ParseError{msg: "No matching rule for data"})
				}
			}
		}
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb(msg *pb.EDB) interface{} {
	flat1151 := p.tryFlat(msg, func() { p.pretty_edb(msg) })
	if flat1151 != nil {
		p.write(*flat1151)
		return nil
	} else {
		_dollar_dollar := msg
		fields1146 := []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
		unwrapped_fields1147 := fields1146
		p.write("(")
		p.write("edb")
		p.indentSexp()
		p.newline()
		field1148 := unwrapped_fields1147[0].(*pb.RelationId)
		p.pretty_relation_id(field1148)
		p.newline()
		field1149 := unwrapped_fields1147[1].([]string)
		p.pretty_edb_path(field1149)
		p.newline()
		field1150 := unwrapped_fields1147[2].([]*pb.Type)
		p.pretty_edb_types(field1150)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_path(msg []string) interface{} {
	flat1155 := p.tryFlat(msg, func() { p.pretty_edb_path(msg) })
	if flat1155 != nil {
		p.write(*flat1155)
		return nil
	} else {
		fields1152 := msg
		p.write("[")
		p.indent()
		for i1154, elem1153 := range fields1152 {
			if (i1154 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem1153))
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_edb_types(msg []*pb.Type) interface{} {
	flat1159 := p.tryFlat(msg, func() { p.pretty_edb_types(msg) })
	if flat1159 != nil {
		p.write(*flat1159)
		return nil
	} else {
		fields1156 := msg
		p.write("[")
		p.indent()
		for i1158, elem1157 := range fields1156 {
			if (i1158 > 0) {
				p.newline()
			}
			p.pretty_type(elem1157)
		}
		p.dedent()
		p.write("]")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) interface{} {
	flat1164 := p.tryFlat(msg, func() { p.pretty_betree_relation(msg) })
	if flat1164 != nil {
		p.write(*flat1164)
		return nil
	} else {
		_dollar_dollar := msg
		fields1160 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
		unwrapped_fields1161 := fields1160
		p.write("(")
		p.write("betree_relation")
		p.indentSexp()
		p.newline()
		field1162 := unwrapped_fields1161[0].(*pb.RelationId)
		p.pretty_relation_id(field1162)
		p.newline()
		field1163 := unwrapped_fields1161[1].(*pb.BeTreeInfo)
		p.pretty_betree_info(field1163)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) interface{} {
	flat1170 := p.tryFlat(msg, func() { p.pretty_betree_info(msg) })
	if flat1170 != nil {
		p.write(*flat1170)
		return nil
	} else {
		_dollar_dollar := msg
		_t1405 := p.deconstruct_betree_info_config(_dollar_dollar)
		fields1165 := []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t1405}
		unwrapped_fields1166 := fields1165
		p.write("(")
		p.write("betree_info")
		p.indentSexp()
		p.newline()
		field1167 := unwrapped_fields1166[0].([]*pb.Type)
		p.pretty_betree_info_key_types(field1167)
		p.newline()
		field1168 := unwrapped_fields1166[1].([]*pb.Type)
		p.pretty_betree_info_value_types(field1168)
		p.newline()
		field1169 := unwrapped_fields1166[2].([][]interface{})
		p.pretty_config_dict(field1169)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) interface{} {
	flat1174 := p.tryFlat(msg, func() { p.pretty_betree_info_key_types(msg) })
	if flat1174 != nil {
		p.write(*flat1174)
		return nil
	} else {
		fields1171 := msg
		p.write("(")
		p.write("key_types")
		p.indentSexp()
		if !(len(fields1171) == 0) {
			p.newline()
			for i1173, elem1172 := range fields1171 {
				if (i1173 > 0) {
					p.newline()
				}
				p.pretty_type(elem1172)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) interface{} {
	flat1178 := p.tryFlat(msg, func() { p.pretty_betree_info_value_types(msg) })
	if flat1178 != nil {
		p.write(*flat1178)
		return nil
	} else {
		fields1175 := msg
		p.write("(")
		p.write("value_types")
		p.indentSexp()
		if !(len(fields1175) == 0) {
			p.newline()
			for i1177, elem1176 := range fields1175 {
				if (i1177 > 0) {
					p.newline()
				}
				p.pretty_type(elem1176)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) interface{} {
	flat1185 := p.tryFlat(msg, func() { p.pretty_csv_data(msg) })
	if flat1185 != nil {
		p.write(*flat1185)
		return nil
	} else {
		_dollar_dollar := msg
		fields1179 := []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
		unwrapped_fields1180 := fields1179
		p.write("(")
		p.write("csv_data")
		p.indentSexp()
		p.newline()
		field1181 := unwrapped_fields1180[0].(*pb.CSVLocator)
		p.pretty_csvlocator(field1181)
		p.newline()
		field1182 := unwrapped_fields1180[1].(*pb.CSVConfig)
		p.pretty_csv_config(field1182)
		p.newline()
		field1183 := unwrapped_fields1180[2].([]*pb.GNFColumn)
		p.pretty_gnf_columns(field1183)
		p.newline()
		field1184 := unwrapped_fields1180[3].(string)
		p.pretty_csv_asof(field1184)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) interface{} {
	flat1192 := p.tryFlat(msg, func() { p.pretty_csvlocator(msg) })
	if flat1192 != nil {
		p.write(*flat1192)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1406 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t1406 = _dollar_dollar.GetPaths()
		}
		var _t1407 *string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t1407 = ptr(string(_dollar_dollar.GetInlineData()))
		}
		fields1186 := []interface{}{_t1406, _t1407}
		unwrapped_fields1187 := fields1186
		p.write("(")
		p.write("csv_locator")
		p.indentSexp()
		field1188 := unwrapped_fields1187[0].([]string)
		if field1188 != nil {
			p.newline()
			opt_val1189 := field1188
			p.pretty_csv_locator_paths(opt_val1189)
		}
		field1190 := unwrapped_fields1187[1].(*string)
		if field1190 != nil {
			p.newline()
			opt_val1191 := *field1190
			p.pretty_csv_locator_inline_data(opt_val1191)
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) interface{} {
	flat1196 := p.tryFlat(msg, func() { p.pretty_csv_locator_paths(msg) })
	if flat1196 != nil {
		p.write(*flat1196)
		return nil
	} else {
		fields1193 := msg
		p.write("(")
		p.write("paths")
		p.indentSexp()
		if !(len(fields1193) == 0) {
			p.newline()
			for i1195, elem1194 := range fields1193 {
				if (i1195 > 0) {
					p.newline()
				}
				p.write(p.formatStringValue(elem1194))
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) interface{} {
	flat1198 := p.tryFlat(msg, func() { p.pretty_csv_locator_inline_data(msg) })
	if flat1198 != nil {
		p.write(*flat1198)
		return nil
	} else {
		fields1197 := msg
		p.write("(")
		p.write("inline_data")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1197))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) interface{} {
	flat1201 := p.tryFlat(msg, func() { p.pretty_csv_config(msg) })
	if flat1201 != nil {
		p.write(*flat1201)
		return nil
	} else {
		_dollar_dollar := msg
		_t1408 := p.deconstruct_csv_config(_dollar_dollar)
		fields1199 := _t1408
		unwrapped_fields1200 := fields1199
		p.write("(")
		p.write("csv_config")
		p.indentSexp()
		p.newline()
		p.pretty_config_dict(unwrapped_fields1200)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_columns(msg []*pb.GNFColumn) interface{} {
	flat1205 := p.tryFlat(msg, func() { p.pretty_gnf_columns(msg) })
	if flat1205 != nil {
		p.write(*flat1205)
		return nil
	} else {
		fields1202 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1202) == 0) {
			p.newline()
			for i1204, elem1203 := range fields1202 {
				if (i1204 > 0) {
					p.newline()
				}
				p.pretty_gnf_column(elem1203)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column(msg *pb.GNFColumn) interface{} {
	flat1214 := p.tryFlat(msg, func() { p.pretty_gnf_column(msg) })
	if flat1214 != nil {
		p.write(*flat1214)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1409 *pb.RelationId
		if hasProtoField(_dollar_dollar, "target_id") {
			_t1409 = _dollar_dollar.GetTargetId()
		}
		fields1206 := []interface{}{_dollar_dollar.GetColumnPath(), _t1409, _dollar_dollar.GetTypes()}
		unwrapped_fields1207 := fields1206
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1208 := unwrapped_fields1207[0].([]string)
		p.pretty_gnf_column_path(field1208)
		field1209 := unwrapped_fields1207[1].(*pb.RelationId)
		if field1209 != nil {
			p.newline()
			opt_val1210 := field1209
			p.pretty_relation_id(opt_val1210)
		}
		p.newline()
		p.write("[")
		field1211 := unwrapped_fields1207[2].([]*pb.Type)
		for i1213, elem1212 := range field1211 {
			if (i1213 > 0) {
				p.newline()
			}
			p.pretty_type(elem1212)
		}
		p.write("]")
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_gnf_column_path(msg []string) interface{} {
	flat1221 := p.tryFlat(msg, func() { p.pretty_gnf_column_path(msg) })
	if flat1221 != nil {
		p.write(*flat1221)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1410 *string
		if int64(len(_dollar_dollar)) == 1 {
			_t1410 = ptr(_dollar_dollar[0])
		}
		deconstruct_result1219 := _t1410
		if deconstruct_result1219 != nil {
			unwrapped1220 := *deconstruct_result1219
			p.write(p.formatStringValue(unwrapped1220))
		} else {
			_dollar_dollar := msg
			var _t1411 []string
			if int64(len(_dollar_dollar)) != 1 {
				_t1411 = _dollar_dollar
			}
			deconstruct_result1215 := _t1411
			if deconstruct_result1215 != nil {
				unwrapped1216 := deconstruct_result1215
				p.write("[")
				p.indent()
				for i1218, elem1217 := range unwrapped1216 {
					if (i1218 > 0) {
						p.newline()
					}
					p.write(p.formatStringValue(elem1217))
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
	flat1223 := p.tryFlat(msg, func() { p.pretty_csv_asof(msg) })
	if flat1223 != nil {
		p.write(*flat1223)
		return nil
	} else {
		fields1222 := msg
		p.write("(")
		p.write("asof")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1222))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) interface{} {
	flat1226 := p.tryFlat(msg, func() { p.pretty_undefine(msg) })
	if flat1226 != nil {
		p.write(*flat1226)
		return nil
	} else {
		_dollar_dollar := msg
		fields1224 := _dollar_dollar.GetFragmentId()
		unwrapped_fields1225 := fields1224
		p.write("(")
		p.write("undefine")
		p.indentSexp()
		p.newline()
		p.pretty_fragment_id(unwrapped_fields1225)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) interface{} {
	flat1231 := p.tryFlat(msg, func() { p.pretty_context(msg) })
	if flat1231 != nil {
		p.write(*flat1231)
		return nil
	} else {
		_dollar_dollar := msg
		fields1227 := _dollar_dollar.GetRelations()
		unwrapped_fields1228 := fields1227
		p.write("(")
		p.write("context")
		p.indentSexp()
		if !(len(unwrapped_fields1228) == 0) {
			p.newline()
			for i1230, elem1229 := range unwrapped_fields1228 {
				if (i1230 > 0) {
					p.newline()
				}
				p.pretty_relation_id(elem1229)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot(msg *pb.Snapshot) interface{} {
	flat1236 := p.tryFlat(msg, func() { p.pretty_snapshot(msg) })
	if flat1236 != nil {
		p.write(*flat1236)
		return nil
	} else {
		_dollar_dollar := msg
		fields1232 := _dollar_dollar.GetMappings()
		unwrapped_fields1233 := fields1232
		p.write("(")
		p.write("snapshot")
		p.indentSexp()
		if !(len(unwrapped_fields1233) == 0) {
			p.newline()
			for i1235, elem1234 := range unwrapped_fields1233 {
				if (i1235 > 0) {
					p.newline()
				}
				p.pretty_snapshot_mapping(elem1234)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_snapshot_mapping(msg *pb.SnapshotMapping) interface{} {
	flat1241 := p.tryFlat(msg, func() { p.pretty_snapshot_mapping(msg) })
	if flat1241 != nil {
		p.write(*flat1241)
		return nil
	} else {
		_dollar_dollar := msg
		fields1237 := []interface{}{_dollar_dollar.GetDestinationPath(), _dollar_dollar.GetSourceRelation()}
		unwrapped_fields1238 := fields1237
		field1239 := unwrapped_fields1238[0].([]string)
		p.pretty_edb_path(field1239)
		p.write(" ")
		field1240 := unwrapped_fields1238[1].(*pb.RelationId)
		p.pretty_relation_id(field1240)
	}
	return nil
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) interface{} {
	flat1245 := p.tryFlat(msg, func() { p.pretty_epoch_reads(msg) })
	if flat1245 != nil {
		p.write(*flat1245)
		return nil
	} else {
		fields1242 := msg
		p.write("(")
		p.write("reads")
		p.indentSexp()
		if !(len(fields1242) == 0) {
			p.newline()
			for i1244, elem1243 := range fields1242 {
				if (i1244 > 0) {
					p.newline()
				}
				p.pretty_read(elem1243)
			}
		}
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) interface{} {
	flat1256 := p.tryFlat(msg, func() { p.pretty_read(msg) })
	if flat1256 != nil {
		p.write(*flat1256)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1412 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t1412 = _dollar_dollar.GetDemand()
		}
		deconstruct_result1254 := _t1412
		if deconstruct_result1254 != nil {
			unwrapped1255 := deconstruct_result1254
			p.pretty_demand(unwrapped1255)
		} else {
			_dollar_dollar := msg
			var _t1413 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t1413 = _dollar_dollar.GetOutput()
			}
			deconstruct_result1252 := _t1413
			if deconstruct_result1252 != nil {
				unwrapped1253 := deconstruct_result1252
				p.pretty_output(unwrapped1253)
			} else {
				_dollar_dollar := msg
				var _t1414 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t1414 = _dollar_dollar.GetWhatIf()
				}
				deconstruct_result1250 := _t1414
				if deconstruct_result1250 != nil {
					unwrapped1251 := deconstruct_result1250
					p.pretty_what_if(unwrapped1251)
				} else {
					_dollar_dollar := msg
					var _t1415 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t1415 = _dollar_dollar.GetAbort()
					}
					deconstruct_result1248 := _t1415
					if deconstruct_result1248 != nil {
						unwrapped1249 := deconstruct_result1248
						p.pretty_abort(unwrapped1249)
					} else {
						_dollar_dollar := msg
						var _t1416 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t1416 = _dollar_dollar.GetExport()
						}
						deconstruct_result1246 := _t1416
						if deconstruct_result1246 != nil {
							unwrapped1247 := deconstruct_result1246
							p.pretty_export(unwrapped1247)
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
	flat1259 := p.tryFlat(msg, func() { p.pretty_demand(msg) })
	if flat1259 != nil {
		p.write(*flat1259)
		return nil
	} else {
		_dollar_dollar := msg
		fields1257 := _dollar_dollar.GetRelationId()
		unwrapped_fields1258 := fields1257
		p.write("(")
		p.write("demand")
		p.indentSexp()
		p.newline()
		p.pretty_relation_id(unwrapped_fields1258)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) interface{} {
	flat1264 := p.tryFlat(msg, func() { p.pretty_output(msg) })
	if flat1264 != nil {
		p.write(*flat1264)
		return nil
	} else {
		_dollar_dollar := msg
		fields1260 := []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
		unwrapped_fields1261 := fields1260
		p.write("(")
		p.write("output")
		p.indentSexp()
		p.newline()
		field1262 := unwrapped_fields1261[0].(string)
		p.pretty_name(field1262)
		p.newline()
		field1263 := unwrapped_fields1261[1].(*pb.RelationId)
		p.pretty_relation_id(field1263)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) interface{} {
	flat1269 := p.tryFlat(msg, func() { p.pretty_what_if(msg) })
	if flat1269 != nil {
		p.write(*flat1269)
		return nil
	} else {
		_dollar_dollar := msg
		fields1265 := []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
		unwrapped_fields1266 := fields1265
		p.write("(")
		p.write("what_if")
		p.indentSexp()
		p.newline()
		field1267 := unwrapped_fields1266[0].(string)
		p.pretty_name(field1267)
		p.newline()
		field1268 := unwrapped_fields1266[1].(*pb.Epoch)
		p.pretty_epoch(field1268)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) interface{} {
	flat1275 := p.tryFlat(msg, func() { p.pretty_abort(msg) })
	if flat1275 != nil {
		p.write(*flat1275)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1417 *string
		if _dollar_dollar.GetName() != "abort" {
			_t1417 = ptr(_dollar_dollar.GetName())
		}
		fields1270 := []interface{}{_t1417, _dollar_dollar.GetRelationId()}
		unwrapped_fields1271 := fields1270
		p.write("(")
		p.write("abort")
		p.indentSexp()
		field1272 := unwrapped_fields1271[0].(*string)
		if field1272 != nil {
			p.newline()
			opt_val1273 := *field1272
			p.pretty_name(opt_val1273)
		}
		p.newline()
		field1274 := unwrapped_fields1271[1].(*pb.RelationId)
		p.pretty_relation_id(field1274)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) interface{} {
	flat1278 := p.tryFlat(msg, func() { p.pretty_export(msg) })
	if flat1278 != nil {
		p.write(*flat1278)
		return nil
	} else {
		_dollar_dollar := msg
		fields1276 := _dollar_dollar.GetCsvConfig()
		unwrapped_fields1277 := fields1276
		p.write("(")
		p.write("export")
		p.indentSexp()
		p.newline()
		p.pretty_export_csv_config(unwrapped_fields1277)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) interface{} {
	flat1289 := p.tryFlat(msg, func() { p.pretty_export_csv_config(msg) })
	if flat1289 != nil {
		p.write(*flat1289)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1418 []interface{}
		if int64(len(_dollar_dollar.GetDataColumns())) == 0 {
			_t1418 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetCsvSource(), _dollar_dollar.GetCsvConfig()}
		}
		deconstruct_result1284 := _t1418
		if deconstruct_result1284 != nil {
			unwrapped1285 := deconstruct_result1284
			p.write("(")
			p.write("export_csv_config_v2")
			p.indentSexp()
			p.newline()
			field1286 := unwrapped1285[0].(string)
			p.pretty_export_csv_path(field1286)
			p.newline()
			field1287 := unwrapped1285[1].(*pb.ExportCSVSource)
			p.pretty_export_csv_source(field1287)
			p.newline()
			field1288 := unwrapped1285[2].(*pb.CSVConfig)
			p.pretty_csv_config(field1288)
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1419 []interface{}
			if int64(len(_dollar_dollar.GetDataColumns())) != 0 {
				_t1420 := p.deconstruct_export_csv_config(_dollar_dollar)
				_t1419 = []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t1420}
			}
			deconstruct_result1279 := _t1419
			if deconstruct_result1279 != nil {
				unwrapped1280 := deconstruct_result1279
				p.write("(")
				p.write("export_csv_config")
				p.indentSexp()
				p.newline()
				field1281 := unwrapped1280[0].(string)
				p.pretty_export_csv_path(field1281)
				p.newline()
				field1282 := unwrapped1280[1].([]*pb.ExportCSVColumn)
				p.pretty_export_csv_columns_list(field1282)
				p.newline()
				field1283 := unwrapped1280[2].([][]interface{})
				p.pretty_config_dict(field1283)
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
	flat1291 := p.tryFlat(msg, func() { p.pretty_export_csv_path(msg) })
	if flat1291 != nil {
		p.write(*flat1291)
		return nil
	} else {
		fields1290 := msg
		p.write("(")
		p.write("path")
		p.indentSexp()
		p.newline()
		p.write(p.formatStringValue(fields1290))
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_source(msg *pb.ExportCSVSource) interface{} {
	flat1298 := p.tryFlat(msg, func() { p.pretty_export_csv_source(msg) })
	if flat1298 != nil {
		p.write(*flat1298)
		return nil
	} else {
		_dollar_dollar := msg
		var _t1421 []*pb.ExportCSVColumn
		if hasProtoField(_dollar_dollar, "gnf_columns") {
			_t1421 = _dollar_dollar.GetGnfColumns().GetColumns()
		}
		deconstruct_result1294 := _t1421
		if deconstruct_result1294 != nil {
			unwrapped1295 := deconstruct_result1294
			p.write("(")
			p.write("gnf_columns")
			p.indentSexp()
			if !(len(unwrapped1295) == 0) {
				p.newline()
				for i1297, elem1296 := range unwrapped1295 {
					if (i1297 > 0) {
						p.newline()
					}
					p.pretty_export_csv_column(elem1296)
				}
			}
			p.dedent()
			p.write(")")
		} else {
			_dollar_dollar := msg
			var _t1422 *pb.RelationId
			if hasProtoField(_dollar_dollar, "table_def") {
				_t1422 = _dollar_dollar.GetTableDef()
			}
			deconstruct_result1292 := _t1422
			if deconstruct_result1292 != nil {
				unwrapped1293 := deconstruct_result1292
				p.write("(")
				p.write("table_def")
				p.indentSexp()
				p.newline()
				p.pretty_relation_id(unwrapped1293)
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
	flat1303 := p.tryFlat(msg, func() { p.pretty_export_csv_column(msg) })
	if flat1303 != nil {
		p.write(*flat1303)
		return nil
	} else {
		_dollar_dollar := msg
		fields1299 := []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
		unwrapped_fields1300 := fields1299
		p.write("(")
		p.write("column")
		p.indentSexp()
		p.newline()
		field1301 := unwrapped_fields1300[0].(string)
		p.write(p.formatStringValue(field1301))
		p.newline()
		field1302 := unwrapped_fields1300[1].(*pb.RelationId)
		p.pretty_relation_id(field1302)
		p.dedent()
		p.write(")")
	}
	return nil
}

func (p *PrettyPrinter) pretty_export_csv_columns_list(msg []*pb.ExportCSVColumn) interface{} {
	flat1307 := p.tryFlat(msg, func() { p.pretty_export_csv_columns_list(msg) })
	if flat1307 != nil {
		p.write(*flat1307)
		return nil
	} else {
		fields1304 := msg
		p.write("(")
		p.write("columns")
		p.indentSexp()
		if !(len(fields1304) == 0) {
			p.newline()
			for i1306, elem1305 := range fields1304 {
				if (i1306 > 0) {
					p.newline()
				}
				p.pretty_export_csv_column(elem1305)
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
		_t1461 := &pb.UInt128Value{Low: _rid.GetIdLow(), High: _rid.GetIdHigh()}
		p.pprintDispatch(_t1461)
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
