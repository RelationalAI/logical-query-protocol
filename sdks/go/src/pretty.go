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
	"strings"

	pb "logical-query-protocol/src/lqp/v1"
)

// PrettyPrinter holds state for pretty printing protobuf messages.
type PrettyPrinter struct {
	w           *bytes.Buffer
	indentLevel int
	atLineStart bool
	debugInfo   map[[2]uint64]string
}

func (p *PrettyPrinter) write(s string) {
	if p.atLineStart && strings.TrimSpace(s) != "" {
		p.w.WriteString(strings.Repeat("  ", p.indentLevel))
		p.atLineStart = false
	}
	p.w.WriteString(s)
}

func (p *PrettyPrinter) newline() {
	p.w.WriteString("\n")
	p.atLineStart = true
}

func (p *PrettyPrinter) indent() {
	p.indentLevel++
}

func (p *PrettyPrinter) dedent() {
	if p.indentLevel > 0 {
		p.indentLevel--
	}
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
func (p *PrettyPrinter) relationIdToString(msg *pb.RelationId) string {
	key := [2]uint64{msg.GetIdLow(), msg.GetIdHigh()}
	if name, ok := p.debugInfo[key]; ok {
		return name
	}
	return ""
}

// relationIdToInt returns a pointer to int64 if the RelationId fits in
// signed 64-bit range, nil otherwise.
func (p *PrettyPrinter) relationIdToInt(msg *pb.RelationId) *int64 {
	if msg.GetIdHigh() == 0 && msg.GetIdLow() <= 0x7FFFFFFFFFFFFFFF {
		v := int64(msg.GetIdLow())
		return &v
	}
	return nil
}

// relationIdToUint128 converts a RelationId to a UInt128Value.
func (p *PrettyPrinter) relationIdToUint128(msg *pb.RelationId) *pb.UInt128Value {
	return &pb.UInt128Value{Low: msg.GetIdLow(), High: msg.GetIdHigh()}
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

func formatBool(b bool) string {
	if b {
		return "true"
	}
	return "false"
}

// --- Helper functions ---

func (p *PrettyPrinter) deconstructBindingsWithArity(abs *pb.Abstraction, value_arity int64) []interface{} {
	n := int64(len(abs.GetVars()))
	key_end := (n - value_arity)
	return []interface{}{abs.GetVars()[0:key_end], abs.GetVars()[key_end:n]}
}

func (p *PrettyPrinter) MakeValueInt64(v int64) *pb.Value {
	_t964 := &pb.Value{}
	_t964.Value = &pb.Value_IntValue{IntValue: v}
	return _t964
}

func (p *PrettyPrinter) MakeValueInt32(v int32) *pb.Value {
	_t965 := &pb.Value{}
	_t965.Value = &pb.Value_IntValue{IntValue: int64(v)}
	return _t965
}

func (p *PrettyPrinter) deconstructCsvConfig(msg *pb.CSVConfig) [][]interface{} {
	result := [][]interface{}{}
	_t966 := p.MakeValueInt32(msg.GetHeaderRow())
	result = append(result, []interface{}{"csv_header_row", _t966})
	_t967 := p.MakeValueInt64(msg.GetSkip())
	result = append(result, []interface{}{"csv_skip", _t967})
	if msg.GetNewLine() != "" {
		_t968 := p.MakeValueString(msg.GetNewLine())
		result = append(result, []interface{}{"csv_new_line", _t968})
	}
	_t969 := p.MakeValueString(msg.GetDelimiter())
	result = append(result, []interface{}{"csv_delimiter", _t969})
	_t970 := p.MakeValueString(msg.GetQuotechar())
	result = append(result, []interface{}{"csv_quotechar", _t970})
	_t971 := p.MakeValueString(msg.GetEscapechar())
	result = append(result, []interface{}{"csv_escapechar", _t971})
	if msg.GetComment() != "" {
		_t972 := p.MakeValueString(msg.GetComment())
		result = append(result, []interface{}{"csv_comment", _t972})
	}
	for _, missing_string := range msg.GetMissingStrings() {
		_t973 := p.MakeValueString(missing_string)
		result = append(result, []interface{}{"csv_missing_strings", _t973})
	}
	_t974 := p.MakeValueString(msg.GetDecimalSeparator())
	result = append(result, []interface{}{"csv_decimal_separator", _t974})
	_t975 := p.MakeValueString(msg.GetEncoding())
	result = append(result, []interface{}{"csv_encoding", _t975})
	_t976 := p.MakeValueString(msg.GetCompression())
	result = append(result, []interface{}{"csv_compression", _t976})
	return listSort(result)
}

func (p *PrettyPrinter) deconstructBindings(abs *pb.Abstraction) []interface{} {
	n := int64(len(abs.GetVars()))
	return []interface{}{abs.GetVars()[0:n], []*pb.Binding{}}
}

func (p *PrettyPrinter) deconstructBetreeInfoConfig(msg *pb.BeTreeInfo) [][]interface{} {
	result := [][]interface{}{}
	_t977 := p.MakeValueFloat64(msg.GetStorageConfig().GetEpsilon())
	result = append(result, []interface{}{"betree_config_epsilon", _t977})
	_t978 := p.MakeValueInt64(msg.GetStorageConfig().GetMaxPivots())
	result = append(result, []interface{}{"betree_config_max_pivots", _t978})
	_t979 := p.MakeValueInt64(msg.GetStorageConfig().GetMaxDeltas())
	result = append(result, []interface{}{"betree_config_max_deltas", _t979})
	_t980 := p.MakeValueInt64(msg.GetStorageConfig().GetMaxLeaf())
	result = append(result, []interface{}{"betree_config_max_leaf", _t980})
	if hasProtoField(msg.GetRelationLocator(), "root_pageid") {
		if msg.GetRelationLocator().GetRootPageid() != nil {
			_t981 := p.MakeValueUint128(msg.GetRelationLocator().GetRootPageid())
			result = append(result, []interface{}{"betree_locator_root_pageid", _t981})
		}
	}
	if hasProtoField(msg.GetRelationLocator(), "inline_data") {
		if msg.GetRelationLocator().GetInlineData() != nil {
			_t982 := p.MakeValueString(string(msg.GetRelationLocator().GetInlineData()))
			result = append(result, []interface{}{"betree_locator_inline_data", _t982})
		}
	}
	_t983 := p.MakeValueInt64(msg.GetRelationLocator().GetElementCount())
	result = append(result, []interface{}{"betree_locator_element_count", _t983})
	_t984 := p.MakeValueInt64(msg.GetRelationLocator().GetTreeHeight())
	result = append(result, []interface{}{"betree_locator_tree_height", _t984})
	return listSort(result)
}

func (p *PrettyPrinter) MakeValueString(v string) *pb.Value {
	_t985 := &pb.Value{}
	_t985.Value = &pb.Value_StringValue{StringValue: v}
	return _t985
}

func (p *PrettyPrinter) deconstructRelationIdUint128(msg *pb.RelationId) *pb.UInt128Value {
	name := p.relationIdToString(msg)
	if name == "" {
		return p.relationIdToUint128(msg)
	}
	return nil
}

func (p *PrettyPrinter) deconstructExportCsvConfig(msg *pb.ExportCSVConfig) [][]interface{} {
	result := [][]interface{}{}
	if msg.PartitionSize != nil {
		_t986 := p.MakeValueInt64(*msg.PartitionSize)
		result = append(result, []interface{}{"partition_size", _t986})
	}
	if msg.Compression != nil {
		_t987 := p.MakeValueString(*msg.Compression)
		result = append(result, []interface{}{"compression", _t987})
	}
	if msg.SyntaxHeaderRow != nil {
		_t988 := p.MakeValueBoolean(*msg.SyntaxHeaderRow)
		result = append(result, []interface{}{"syntax_header_row", _t988})
	}
	if msg.SyntaxMissingString != nil {
		_t989 := p.MakeValueString(*msg.SyntaxMissingString)
		result = append(result, []interface{}{"syntax_missing_string", _t989})
	}
	if msg.SyntaxDelim != nil {
		_t990 := p.MakeValueString(*msg.SyntaxDelim)
		result = append(result, []interface{}{"syntax_delim", _t990})
	}
	if msg.SyntaxQuotechar != nil {
		_t991 := p.MakeValueString(*msg.SyntaxQuotechar)
		result = append(result, []interface{}{"syntax_quotechar", _t991})
	}
	if msg.SyntaxEscapechar != nil {
		_t992 := p.MakeValueString(*msg.SyntaxEscapechar)
		result = append(result, []interface{}{"syntax_escapechar", _t992})
	}
	return listSort(result)
}

func (p *PrettyPrinter) MakeValueBoolean(v bool) *pb.Value {
	_t993 := &pb.Value{}
	_t993.Value = &pb.Value_BooleanValue{BooleanValue: v}
	return _t993
}

func (p *PrettyPrinter) deconstructConfigure(msg *pb.Configure) [][]interface{} {
	result := [][]interface{}{}
	if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO {
		_t994 := p.MakeValueString("auto")
		result = append(result, []interface{}{"ivm.maintenance_level", _t994})
	} else {
		if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL {
			_t995 := p.MakeValueString("all")
			result = append(result, []interface{}{"ivm.maintenance_level", _t995})
		} else {
			if msg.GetIvmConfig().GetLevel() == pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF {
				_t996 := p.MakeValueString("off")
				result = append(result, []interface{}{"ivm.maintenance_level", _t996})
			}
		}
	}
	_t997 := p.MakeValueInt64(msg.GetSemanticsVersion())
	result = append(result, []interface{}{"semantics_version", _t997})
	return listSort(result)
}

func (p *PrettyPrinter) deconstructRelationIdString(msg *pb.RelationId) *string {
	name := p.relationIdToString(msg)
	if name != "" {
		return ptr(name)
	}
	return nil
}

func (p *PrettyPrinter) MakeValueFloat64(v float64) *pb.Value {
	_t998 := &pb.Value{}
	_t998.Value = &pb.Value_FloatValue{FloatValue: v}
	return _t998
}

func (p *PrettyPrinter) MakeValueUint128(v *pb.UInt128Value) *pb.Value {
	_t999 := &pb.Value{}
	_t999.Value = &pb.Value_Uint128Value{Uint128Value: v}
	return _t999
}

// --- Pretty-print methods ---

func (p *PrettyPrinter) pretty_transaction(msg *pb.Transaction) {
	_t462 := func(_dollar_dollar *pb.Transaction) []interface{} {
		var _t463 *pb.Configure
		if hasProtoField(_dollar_dollar, "configure") {
			_t463 = _dollar_dollar.GetConfigure()
		}
		var _t464 *pb.Sync
		if hasProtoField(_dollar_dollar, "sync") {
			_t464 = _dollar_dollar.GetSync()
		}
		return []interface{}{_t463, _t464, _dollar_dollar.GetEpochs()}
	}
	_t465 := _t462(msg)
	fields0 := _t465
	p.write("(")
	p.write("transaction")
	p.indent()
	_t466 := fields0[0]
	var _t467 *pb.Configure
	if _t466 != nil {
		_t467 = _t466.(*pb.Configure)
	}
	field1 := _t467
	if field1 != nil {
		p.newline()
		opt_val2 := field1
		p.pretty_configure(opt_val2)
	}
	_t468 := fields0[1]
	var _t469 *pb.Sync
	if _t468 != nil {
		_t469 = _t468.(*pb.Sync)
	}
	field3 := _t469
	if field3 != nil {
		p.newline()
		opt_val4 := field3
		p.pretty_sync(opt_val4)
	}
	field5 := fields0[2].([]*pb.Epoch)
	if !(len(field5) == 0) {
		p.newline()
		for i7, elem6 := range field5 {
			if (i7 > 0) {
				p.newline()
			}
			p.pretty_epoch(elem6)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_configure(msg *pb.Configure) {
	_t470 := func(_dollar_dollar *pb.Configure) [][]interface{} {
		_t471 := p.deconstructConfigure(_dollar_dollar)
		return _t471
	}
	_t472 := _t470(msg)
	fields8 := _t472
	p.write("(")
	p.write("configure")
	p.indent()
	p.newline()
	p.pretty_config_dict(fields8)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_config_dict(msg [][]interface{}) {
	_t473 := func(_dollar_dollar [][]interface{}) [][]interface{} {
		return _dollar_dollar
	}
	_t474 := _t473(msg)
	fields9 := _t474
	p.write("{")
	p.indent()
	if !(len(fields9) == 0) {
		p.write(" ")
		for i11, elem10 := range fields9 {
			if (i11 > 0) {
				p.newline()
			}
			p.pretty_config_key_value(elem10)
		}
	}
	p.dedent()
	p.write("}")
}

func (p *PrettyPrinter) pretty_config_key_value(msg []interface{}) {
	_t475 := func(_dollar_dollar []interface{}) []interface{} {
		return []interface{}{_dollar_dollar[0].(string), _dollar_dollar[1].(*pb.Value)}
	}
	_t476 := _t475(msg)
	fields12 := _t476
	p.write(":")
	field13 := fields12[0].(string)
	p.write(field13)
	p.write(" ")
	field14 := fields12[1].(*pb.Value)
	p.pretty_value(field14)
}

func (p *PrettyPrinter) pretty_value(msg *pb.Value) {
	_t477 := func(_dollar_dollar *pb.Value) *pb.DateValue {
		var _t478 *pb.DateValue
		if hasProtoField(_dollar_dollar, "date_value") {
			_t478 = _dollar_dollar.GetDateValue()
		}
		return _t478
	}
	_t479 := _t477(msg)
	deconstruct_result32 := _t479
	if deconstruct_result32 != nil {
		unwrapped_deconstruct33 := deconstruct_result32
		p.pretty_date(unwrapped_deconstruct33)
	} else {
		_t480 := func(_dollar_dollar *pb.Value) *pb.DateTimeValue {
			var _t481 *pb.DateTimeValue
			if hasProtoField(_dollar_dollar, "datetime_value") {
				_t481 = _dollar_dollar.GetDatetimeValue()
			}
			return _t481
		}
		_t482 := _t480(msg)
		deconstruct_result30 := _t482
		if deconstruct_result30 != nil {
			unwrapped_deconstruct31 := deconstruct_result30
			p.pretty_datetime(unwrapped_deconstruct31)
		} else {
			_t483 := func(_dollar_dollar *pb.Value) *string {
				var _t484 *string
				if hasProtoField(_dollar_dollar, "string_value") {
					_t484 = ptr(_dollar_dollar.GetStringValue())
				}
				return _t484
			}
			_t485 := _t483(msg)
			deconstruct_result28 := _t485
			if deconstruct_result28 != nil {
				unwrapped_deconstruct29 := *deconstruct_result28
				p.write(p.formatStringValue(unwrapped_deconstruct29))
			} else {
				_t486 := func(_dollar_dollar *pb.Value) *int64 {
					var _t487 *int64
					if hasProtoField(_dollar_dollar, "int_value") {
						_t487 = ptr(_dollar_dollar.GetIntValue())
					}
					return _t487
				}
				_t488 := _t486(msg)
				deconstruct_result26 := _t488
				if deconstruct_result26 != nil {
					unwrapped_deconstruct27 := *deconstruct_result26
					p.write(fmt.Sprintf("%d", unwrapped_deconstruct27))
				} else {
					_t489 := func(_dollar_dollar *pb.Value) *float64 {
						var _t490 *float64
						if hasProtoField(_dollar_dollar, "float_value") {
							_t490 = ptr(_dollar_dollar.GetFloatValue())
						}
						return _t490
					}
					_t491 := _t489(msg)
					deconstruct_result24 := _t491
					if deconstruct_result24 != nil {
						unwrapped_deconstruct25 := *deconstruct_result24
						p.write(fmt.Sprintf("%g", unwrapped_deconstruct25))
					} else {
						_t492 := func(_dollar_dollar *pb.Value) *pb.UInt128Value {
							var _t493 *pb.UInt128Value
							if hasProtoField(_dollar_dollar, "uint128_value") {
								_t493 = _dollar_dollar.GetUint128Value()
							}
							return _t493
						}
						_t494 := _t492(msg)
						deconstruct_result22 := _t494
						if deconstruct_result22 != nil {
							unwrapped_deconstruct23 := deconstruct_result22
							p.write(p.formatUint128(unwrapped_deconstruct23))
						} else {
							_t495 := func(_dollar_dollar *pb.Value) *pb.Int128Value {
								var _t496 *pb.Int128Value
								if hasProtoField(_dollar_dollar, "int128_value") {
									_t496 = _dollar_dollar.GetInt128Value()
								}
								return _t496
							}
							_t497 := _t495(msg)
							deconstruct_result20 := _t497
							if deconstruct_result20 != nil {
								unwrapped_deconstruct21 := deconstruct_result20
								p.write(p.formatInt128(unwrapped_deconstruct21))
							} else {
								_t498 := func(_dollar_dollar *pb.Value) *pb.DecimalValue {
									var _t499 *pb.DecimalValue
									if hasProtoField(_dollar_dollar, "decimal_value") {
										_t499 = _dollar_dollar.GetDecimalValue()
									}
									return _t499
								}
								_t500 := _t498(msg)
								deconstruct_result18 := _t500
								if deconstruct_result18 != nil {
									unwrapped_deconstruct19 := deconstruct_result18
									p.write(p.formatDecimal(unwrapped_deconstruct19))
								} else {
									_t501 := func(_dollar_dollar *pb.Value) *bool {
										var _t502 *bool
										if hasProtoField(_dollar_dollar, "boolean_value") {
											_t502 = ptr(_dollar_dollar.GetBooleanValue())
										}
										return _t502
									}
									_t503 := _t501(msg)
									deconstruct_result16 := _t503
									if deconstruct_result16 != nil {
										unwrapped_deconstruct17 := *deconstruct_result16
										p.pretty_boolean_value(unwrapped_deconstruct17)
									} else {
										_t504 := func(_dollar_dollar *pb.Value) *pb.Value {
											return _dollar_dollar
										}
										_t505 := _t504(msg)
										fields15 := _t505
										_ = fields15
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

func (p *PrettyPrinter) pretty_date(msg *pb.DateValue) {
	_t506 := func(_dollar_dollar *pb.DateValue) []interface{} {
		return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay())}
	}
	_t507 := _t506(msg)
	fields34 := _t507
	p.write("(")
	p.write("date")
	p.indent()
	p.newline()
	field35 := fields34[0].(int64)
	p.write(fmt.Sprintf("%d", field35))
	p.newline()
	field36 := fields34[1].(int64)
	p.write(fmt.Sprintf("%d", field36))
	p.newline()
	field37 := fields34[2].(int64)
	p.write(fmt.Sprintf("%d", field37))
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_datetime(msg *pb.DateTimeValue) {
	_t508 := func(_dollar_dollar *pb.DateTimeValue) []interface{} {
		return []interface{}{int64(_dollar_dollar.GetYear()), int64(_dollar_dollar.GetMonth()), int64(_dollar_dollar.GetDay()), int64(_dollar_dollar.GetHour()), int64(_dollar_dollar.GetMinute()), int64(_dollar_dollar.GetSecond()), ptr(int64(_dollar_dollar.GetMicrosecond()))}
	}
	_t509 := _t508(msg)
	fields38 := _t509
	p.write("(")
	p.write("datetime")
	p.indent()
	p.newline()
	field39 := fields38[0].(int64)
	p.write(fmt.Sprintf("%d", field39))
	p.newline()
	field40 := fields38[1].(int64)
	p.write(fmt.Sprintf("%d", field40))
	p.newline()
	field41 := fields38[2].(int64)
	p.write(fmt.Sprintf("%d", field41))
	p.newline()
	field42 := fields38[3].(int64)
	p.write(fmt.Sprintf("%d", field42))
	p.newline()
	field43 := fields38[4].(int64)
	p.write(fmt.Sprintf("%d", field43))
	p.newline()
	field44 := fields38[5].(int64)
	p.write(fmt.Sprintf("%d", field44))
	_t510 := fields38[6]
	var _t511 *int64
	if _t510 != nil {
		if _t512, ok := _t510.(*int64); ok {
			_t511 = _t512
		} else {
			_t513 := _t510.(int64)
			_t511 = &_t513
		}
	}
	field45 := _t511
	if field45 != nil {
		p.newline()
		opt_val46 := *field45
		p.write(fmt.Sprintf("%d", opt_val46))
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_boolean_value(msg bool) {
	_t514 := func(_dollar_dollar bool) []interface{} {
		var _t515 []interface{}
		if _dollar_dollar {
			_t515 = []interface{}{}
		}
		return _t515
	}
	_t516 := _t514(msg)
	deconstruct_result49 := _t516
	if deconstruct_result49 != nil {
		unwrapped_deconstruct50 := deconstruct_result49
		_ = unwrapped_deconstruct50
		p.write("true")
	} else {
		_t517 := func(_dollar_dollar bool) []interface{} {
			var _t518 []interface{}
			if !(_dollar_dollar) {
				_t518 = []interface{}{}
			}
			return _t518
		}
		_t519 := _t517(msg)
		deconstruct_result47 := _t519
		if deconstruct_result47 != nil {
			unwrapped_deconstruct48 := deconstruct_result47
			_ = unwrapped_deconstruct48
			p.write("false")
		} else {
			panic(ParseError{msg: "No matching rule for boolean_value"})
		}
	}
}

func (p *PrettyPrinter) pretty_sync(msg *pb.Sync) {
	_t520 := func(_dollar_dollar *pb.Sync) []*pb.FragmentId {
		return _dollar_dollar.GetFragments()
	}
	_t521 := _t520(msg)
	fields51 := _t521
	p.write("(")
	p.write("sync")
	p.indent()
	if !(len(fields51) == 0) {
		p.newline()
		for i53, elem52 := range fields51 {
			if (i53 > 0) {
				p.newline()
			}
			p.pretty_fragment_id(elem52)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_fragment_id(msg *pb.FragmentId) {
	_t522 := func(_dollar_dollar *pb.FragmentId) string {
		return p.fragmentIdToString(_dollar_dollar)
	}
	_t523 := _t522(msg)
	fields54 := _t523
	p.write(":")
	p.write(fields54)
}

func (p *PrettyPrinter) pretty_epoch(msg *pb.Epoch) {
	_t524 := func(_dollar_dollar *pb.Epoch) []interface{} {
		var _t525 []*pb.Write
		if !(len(_dollar_dollar.GetWrites()) == 0) {
			_t525 = _dollar_dollar.GetWrites()
		}
		var _t526 []*pb.Read
		if !(len(_dollar_dollar.GetReads()) == 0) {
			_t526 = _dollar_dollar.GetReads()
		}
		return []interface{}{_t525, _t526}
	}
	_t527 := _t524(msg)
	fields55 := _t527
	p.write("(")
	p.write("epoch")
	p.indent()
	_t528 := fields55[0]
	var _t529 []*pb.Write
	if _t528 != nil {
		_t529 = _t528.([]*pb.Write)
	}
	field56 := _t529
	if field56 != nil {
		p.newline()
		opt_val57 := field56
		p.pretty_epoch_writes(opt_val57)
	}
	_t530 := fields55[1]
	var _t531 []*pb.Read
	if _t530 != nil {
		_t531 = _t530.([]*pb.Read)
	}
	field58 := _t531
	if field58 != nil {
		p.newline()
		opt_val59 := field58
		p.pretty_epoch_reads(opt_val59)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_epoch_writes(msg []*pb.Write) {
	_t532 := func(_dollar_dollar []*pb.Write) []*pb.Write {
		return _dollar_dollar
	}
	_t533 := _t532(msg)
	fields60 := _t533
	p.write("(")
	p.write("writes")
	p.indent()
	if !(len(fields60) == 0) {
		p.newline()
		for i62, elem61 := range fields60 {
			if (i62 > 0) {
				p.newline()
			}
			p.pretty_write(elem61)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_write(msg *pb.Write) {
	_t534 := func(_dollar_dollar *pb.Write) *pb.Define {
		var _t535 *pb.Define
		if hasProtoField(_dollar_dollar, "define") {
			_t535 = _dollar_dollar.GetDefine()
		}
		return _t535
	}
	_t536 := _t534(msg)
	deconstruct_result67 := _t536
	if deconstruct_result67 != nil {
		unwrapped_deconstruct68 := deconstruct_result67
		p.pretty_define(unwrapped_deconstruct68)
	} else {
		_t537 := func(_dollar_dollar *pb.Write) *pb.Undefine {
			var _t538 *pb.Undefine
			if hasProtoField(_dollar_dollar, "undefine") {
				_t538 = _dollar_dollar.GetUndefine()
			}
			return _t538
		}
		_t539 := _t537(msg)
		deconstruct_result65 := _t539
		if deconstruct_result65 != nil {
			unwrapped_deconstruct66 := deconstruct_result65
			p.pretty_undefine(unwrapped_deconstruct66)
		} else {
			_t540 := func(_dollar_dollar *pb.Write) *pb.Context {
				var _t541 *pb.Context
				if hasProtoField(_dollar_dollar, "context") {
					_t541 = _dollar_dollar.GetContext()
				}
				return _t541
			}
			_t542 := _t540(msg)
			deconstruct_result63 := _t542
			if deconstruct_result63 != nil {
				unwrapped_deconstruct64 := deconstruct_result63
				p.pretty_context(unwrapped_deconstruct64)
			} else {
				panic(ParseError{msg: "No matching rule for write"})
			}
		}
	}
}

func (p *PrettyPrinter) pretty_define(msg *pb.Define) {
	_t543 := func(_dollar_dollar *pb.Define) *pb.Fragment {
		return _dollar_dollar.GetFragment()
	}
	_t544 := _t543(msg)
	fields69 := _t544
	p.write("(")
	p.write("define")
	p.indent()
	p.newline()
	p.pretty_fragment(fields69)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_fragment(msg *pb.Fragment) {
	_t545 := func(_dollar_dollar *pb.Fragment) []interface{} {
		p.startPrettyFragment(_dollar_dollar)
		return []interface{}{_dollar_dollar.GetId(), _dollar_dollar.GetDeclarations()}
	}
	_t546 := _t545(msg)
	fields70 := _t546
	p.write("(")
	p.write("fragment")
	p.indent()
	p.newline()
	field71 := fields70[0].(*pb.FragmentId)
	p.pretty_new_fragment_id(field71)
	field72 := fields70[1].([]*pb.Declaration)
	if !(len(field72) == 0) {
		p.newline()
		for i74, elem73 := range field72 {
			if (i74 > 0) {
				p.newline()
			}
			p.pretty_declaration(elem73)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_new_fragment_id(msg *pb.FragmentId) {
	_t547 := func(_dollar_dollar *pb.FragmentId) *pb.FragmentId {
		return _dollar_dollar
	}
	_t548 := _t547(msg)
	fields75 := _t548
	p.pretty_fragment_id(fields75)
}

func (p *PrettyPrinter) pretty_declaration(msg *pb.Declaration) {
	_t549 := func(_dollar_dollar *pb.Declaration) *pb.Def {
		var _t550 *pb.Def
		if hasProtoField(_dollar_dollar, "def") {
			_t550 = _dollar_dollar.GetDef()
		}
		return _t550
	}
	_t551 := _t549(msg)
	deconstruct_result82 := _t551
	if deconstruct_result82 != nil {
		unwrapped_deconstruct83 := deconstruct_result82
		p.pretty_def(unwrapped_deconstruct83)
	} else {
		_t552 := func(_dollar_dollar *pb.Declaration) *pb.Algorithm {
			var _t553 *pb.Algorithm
			if hasProtoField(_dollar_dollar, "algorithm") {
				_t553 = _dollar_dollar.GetAlgorithm()
			}
			return _t553
		}
		_t554 := _t552(msg)
		deconstruct_result80 := _t554
		if deconstruct_result80 != nil {
			unwrapped_deconstruct81 := deconstruct_result80
			p.pretty_algorithm(unwrapped_deconstruct81)
		} else {
			_t555 := func(_dollar_dollar *pb.Declaration) *pb.Constraint {
				var _t556 *pb.Constraint
				if hasProtoField(_dollar_dollar, "constraint") {
					_t556 = _dollar_dollar.GetConstraint()
				}
				return _t556
			}
			_t557 := _t555(msg)
			deconstruct_result78 := _t557
			if deconstruct_result78 != nil {
				unwrapped_deconstruct79 := deconstruct_result78
				p.pretty_constraint(unwrapped_deconstruct79)
			} else {
				_t558 := func(_dollar_dollar *pb.Declaration) *pb.Data {
					var _t559 *pb.Data
					if hasProtoField(_dollar_dollar, "data") {
						_t559 = _dollar_dollar.GetData()
					}
					return _t559
				}
				_t560 := _t558(msg)
				deconstruct_result76 := _t560
				if deconstruct_result76 != nil {
					unwrapped_deconstruct77 := deconstruct_result76
					p.pretty_data(unwrapped_deconstruct77)
				} else {
					panic(ParseError{msg: "No matching rule for declaration"})
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_def(msg *pb.Def) {
	_t561 := func(_dollar_dollar *pb.Def) []interface{} {
		var _t562 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t562 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t562}
	}
	_t563 := _t561(msg)
	fields84 := _t563
	p.write("(")
	p.write("def")
	p.indent()
	p.newline()
	field85 := fields84[0].(*pb.RelationId)
	p.pretty_relation_id(field85)
	p.newline()
	field86 := fields84[1].(*pb.Abstraction)
	p.pretty_abstraction(field86)
	_t564 := fields84[2]
	var _t565 []*pb.Attribute
	if _t564 != nil {
		_t565 = _t564.([]*pb.Attribute)
	}
	field87 := _t565
	if field87 != nil {
		p.newline()
		opt_val88 := field87
		p.pretty_attrs(opt_val88)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_relation_id(msg *pb.RelationId) {
	_t566 := func(_dollar_dollar *pb.RelationId) *string {
		_t567 := p.deconstructRelationIdString(_dollar_dollar)
		return _t567
	}
	_t568 := _t566(msg)
	deconstruct_result91 := _t568
	if deconstruct_result91 != nil {
		unwrapped_deconstruct92 := *deconstruct_result91
		p.write(":")
		p.write(unwrapped_deconstruct92)
	} else {
		_t569 := func(_dollar_dollar *pb.RelationId) *pb.UInt128Value {
			_t570 := p.deconstructRelationIdUint128(_dollar_dollar)
			return _t570
		}
		_t571 := _t569(msg)
		deconstruct_result89 := _t571
		if deconstruct_result89 != nil {
			unwrapped_deconstruct90 := deconstruct_result89
			p.write(p.formatUint128(unwrapped_deconstruct90))
		} else {
			panic(ParseError{msg: "No matching rule for relation_id"})
		}
	}
}

func (p *PrettyPrinter) pretty_abstraction(msg *pb.Abstraction) {
	_t572 := func(_dollar_dollar *pb.Abstraction) []interface{} {
		_t573 := p.deconstructBindings(_dollar_dollar)
		return []interface{}{_t573, _dollar_dollar.GetValue()}
	}
	_t574 := _t572(msg)
	fields93 := _t574
	p.write("(")
	field94 := fields93[0].([]interface{})
	p.pretty_bindings(field94)
	p.write(" ")
	field95 := fields93[1].(*pb.Formula)
	p.pretty_formula(field95)
	p.write(")")
}

func (p *PrettyPrinter) pretty_bindings(msg []interface{}) {
	_t575 := func(_dollar_dollar []interface{}) []interface{} {
		var _t576 []*pb.Binding
		if !(len(_dollar_dollar[1].([]*pb.Binding)) == 0) {
			_t576 = _dollar_dollar[1].([]*pb.Binding)
		}
		return []interface{}{_dollar_dollar[0].([]*pb.Binding), _t576}
	}
	_t577 := _t575(msg)
	fields96 := _t577
	p.write("[")
	field97 := fields96[0].([]*pb.Binding)
	for i99, elem98 := range field97 {
		if (i99 > 0) {
			p.newline()
		}
		p.pretty_binding(elem98)
	}
	_t578 := fields96[1]
	var _t579 []*pb.Binding
	if _t578 != nil {
		_t579 = _t578.([]*pb.Binding)
	}
	field100 := _t579
	if field100 != nil {
		p.write(" ")
		opt_val101 := field100
		p.pretty_value_bindings(opt_val101)
	}
	p.write("]")
}

func (p *PrettyPrinter) pretty_binding(msg *pb.Binding) {
	_t580 := func(_dollar_dollar *pb.Binding) []interface{} {
		return []interface{}{_dollar_dollar.GetVar().GetName(), _dollar_dollar.GetType()}
	}
	_t581 := _t580(msg)
	fields102 := _t581
	field103 := fields102[0].(string)
	p.write(field103)
	p.write("::")
	field104 := fields102[1].(*pb.Type)
	p.pretty_type(field104)
}

func (p *PrettyPrinter) pretty_type(msg *pb.Type) {
	_t582 := func(_dollar_dollar *pb.Type) *pb.UnspecifiedType {
		var _t583 *pb.UnspecifiedType
		if hasProtoField(_dollar_dollar, "unspecified_type") {
			_t583 = _dollar_dollar.GetUnspecifiedType()
		}
		return _t583
	}
	_t584 := _t582(msg)
	deconstruct_result125 := _t584
	if deconstruct_result125 != nil {
		unwrapped_deconstruct126 := deconstruct_result125
		p.pretty_unspecified_type(unwrapped_deconstruct126)
	} else {
		_t585 := func(_dollar_dollar *pb.Type) *pb.StringType {
			var _t586 *pb.StringType
			if hasProtoField(_dollar_dollar, "string_type") {
				_t586 = _dollar_dollar.GetStringType()
			}
			return _t586
		}
		_t587 := _t585(msg)
		deconstruct_result123 := _t587
		if deconstruct_result123 != nil {
			unwrapped_deconstruct124 := deconstruct_result123
			p.pretty_string_type(unwrapped_deconstruct124)
		} else {
			_t588 := func(_dollar_dollar *pb.Type) *pb.IntType {
				var _t589 *pb.IntType
				if hasProtoField(_dollar_dollar, "int_type") {
					_t589 = _dollar_dollar.GetIntType()
				}
				return _t589
			}
			_t590 := _t588(msg)
			deconstruct_result121 := _t590
			if deconstruct_result121 != nil {
				unwrapped_deconstruct122 := deconstruct_result121
				p.pretty_int_type(unwrapped_deconstruct122)
			} else {
				_t591 := func(_dollar_dollar *pb.Type) *pb.FloatType {
					var _t592 *pb.FloatType
					if hasProtoField(_dollar_dollar, "float_type") {
						_t592 = _dollar_dollar.GetFloatType()
					}
					return _t592
				}
				_t593 := _t591(msg)
				deconstruct_result119 := _t593
				if deconstruct_result119 != nil {
					unwrapped_deconstruct120 := deconstruct_result119
					p.pretty_float_type(unwrapped_deconstruct120)
				} else {
					_t594 := func(_dollar_dollar *pb.Type) *pb.UInt128Type {
						var _t595 *pb.UInt128Type
						if hasProtoField(_dollar_dollar, "uint128_type") {
							_t595 = _dollar_dollar.GetUint128Type()
						}
						return _t595
					}
					_t596 := _t594(msg)
					deconstruct_result117 := _t596
					if deconstruct_result117 != nil {
						unwrapped_deconstruct118 := deconstruct_result117
						p.pretty_uint128_type(unwrapped_deconstruct118)
					} else {
						_t597 := func(_dollar_dollar *pb.Type) *pb.Int128Type {
							var _t598 *pb.Int128Type
							if hasProtoField(_dollar_dollar, "int128_type") {
								_t598 = _dollar_dollar.GetInt128Type()
							}
							return _t598
						}
						_t599 := _t597(msg)
						deconstruct_result115 := _t599
						if deconstruct_result115 != nil {
							unwrapped_deconstruct116 := deconstruct_result115
							p.pretty_int128_type(unwrapped_deconstruct116)
						} else {
							_t600 := func(_dollar_dollar *pb.Type) *pb.DateType {
								var _t601 *pb.DateType
								if hasProtoField(_dollar_dollar, "date_type") {
									_t601 = _dollar_dollar.GetDateType()
								}
								return _t601
							}
							_t602 := _t600(msg)
							deconstruct_result113 := _t602
							if deconstruct_result113 != nil {
								unwrapped_deconstruct114 := deconstruct_result113
								p.pretty_date_type(unwrapped_deconstruct114)
							} else {
								_t603 := func(_dollar_dollar *pb.Type) *pb.DateTimeType {
									var _t604 *pb.DateTimeType
									if hasProtoField(_dollar_dollar, "datetime_type") {
										_t604 = _dollar_dollar.GetDatetimeType()
									}
									return _t604
								}
								_t605 := _t603(msg)
								deconstruct_result111 := _t605
								if deconstruct_result111 != nil {
									unwrapped_deconstruct112 := deconstruct_result111
									p.pretty_datetime_type(unwrapped_deconstruct112)
								} else {
									_t606 := func(_dollar_dollar *pb.Type) *pb.MissingType {
										var _t607 *pb.MissingType
										if hasProtoField(_dollar_dollar, "missing_type") {
											_t607 = _dollar_dollar.GetMissingType()
										}
										return _t607
									}
									_t608 := _t606(msg)
									deconstruct_result109 := _t608
									if deconstruct_result109 != nil {
										unwrapped_deconstruct110 := deconstruct_result109
										p.pretty_missing_type(unwrapped_deconstruct110)
									} else {
										_t609 := func(_dollar_dollar *pb.Type) *pb.DecimalType {
											var _t610 *pb.DecimalType
											if hasProtoField(_dollar_dollar, "decimal_type") {
												_t610 = _dollar_dollar.GetDecimalType()
											}
											return _t610
										}
										_t611 := _t609(msg)
										deconstruct_result107 := _t611
										if deconstruct_result107 != nil {
											unwrapped_deconstruct108 := deconstruct_result107
											p.pretty_decimal_type(unwrapped_deconstruct108)
										} else {
											_t612 := func(_dollar_dollar *pb.Type) *pb.BooleanType {
												var _t613 *pb.BooleanType
												if hasProtoField(_dollar_dollar, "boolean_type") {
													_t613 = _dollar_dollar.GetBooleanType()
												}
												return _t613
											}
											_t614 := _t612(msg)
											deconstruct_result105 := _t614
											if deconstruct_result105 != nil {
												unwrapped_deconstruct106 := deconstruct_result105
												p.pretty_boolean_type(unwrapped_deconstruct106)
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

func (p *PrettyPrinter) pretty_unspecified_type(msg *pb.UnspecifiedType) {
	_t615 := func(_dollar_dollar *pb.UnspecifiedType) *pb.UnspecifiedType {
		return _dollar_dollar
	}
	_t616 := _t615(msg)
	fields127 := _t616
	_ = fields127
	p.write("UNKNOWN")
}

func (p *PrettyPrinter) pretty_string_type(msg *pb.StringType) {
	_t617 := func(_dollar_dollar *pb.StringType) *pb.StringType {
		return _dollar_dollar
	}
	_t618 := _t617(msg)
	fields128 := _t618
	_ = fields128
	p.write("STRING")
}

func (p *PrettyPrinter) pretty_int_type(msg *pb.IntType) {
	_t619 := func(_dollar_dollar *pb.IntType) *pb.IntType {
		return _dollar_dollar
	}
	_t620 := _t619(msg)
	fields129 := _t620
	_ = fields129
	p.write("INT")
}

func (p *PrettyPrinter) pretty_float_type(msg *pb.FloatType) {
	_t621 := func(_dollar_dollar *pb.FloatType) *pb.FloatType {
		return _dollar_dollar
	}
	_t622 := _t621(msg)
	fields130 := _t622
	_ = fields130
	p.write("FLOAT")
}

func (p *PrettyPrinter) pretty_uint128_type(msg *pb.UInt128Type) {
	_t623 := func(_dollar_dollar *pb.UInt128Type) *pb.UInt128Type {
		return _dollar_dollar
	}
	_t624 := _t623(msg)
	fields131 := _t624
	_ = fields131
	p.write("UINT128")
}

func (p *PrettyPrinter) pretty_int128_type(msg *pb.Int128Type) {
	_t625 := func(_dollar_dollar *pb.Int128Type) *pb.Int128Type {
		return _dollar_dollar
	}
	_t626 := _t625(msg)
	fields132 := _t626
	_ = fields132
	p.write("INT128")
}

func (p *PrettyPrinter) pretty_date_type(msg *pb.DateType) {
	_t627 := func(_dollar_dollar *pb.DateType) *pb.DateType {
		return _dollar_dollar
	}
	_t628 := _t627(msg)
	fields133 := _t628
	_ = fields133
	p.write("DATE")
}

func (p *PrettyPrinter) pretty_datetime_type(msg *pb.DateTimeType) {
	_t629 := func(_dollar_dollar *pb.DateTimeType) *pb.DateTimeType {
		return _dollar_dollar
	}
	_t630 := _t629(msg)
	fields134 := _t630
	_ = fields134
	p.write("DATETIME")
}

func (p *PrettyPrinter) pretty_missing_type(msg *pb.MissingType) {
	_t631 := func(_dollar_dollar *pb.MissingType) *pb.MissingType {
		return _dollar_dollar
	}
	_t632 := _t631(msg)
	fields135 := _t632
	_ = fields135
	p.write("MISSING")
}

func (p *PrettyPrinter) pretty_decimal_type(msg *pb.DecimalType) {
	_t633 := func(_dollar_dollar *pb.DecimalType) []interface{} {
		return []interface{}{int64(_dollar_dollar.GetPrecision()), int64(_dollar_dollar.GetScale())}
	}
	_t634 := _t633(msg)
	fields136 := _t634
	p.write("(")
	p.write("DECIMAL")
	p.indent()
	p.newline()
	field137 := fields136[0].(int64)
	p.write(fmt.Sprintf("%d", field137))
	p.newline()
	field138 := fields136[1].(int64)
	p.write(fmt.Sprintf("%d", field138))
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_boolean_type(msg *pb.BooleanType) {
	_t635 := func(_dollar_dollar *pb.BooleanType) *pb.BooleanType {
		return _dollar_dollar
	}
	_t636 := _t635(msg)
	fields139 := _t636
	_ = fields139
	p.write("BOOLEAN")
}

func (p *PrettyPrinter) pretty_value_bindings(msg []*pb.Binding) {
	_t637 := func(_dollar_dollar []*pb.Binding) []*pb.Binding {
		return _dollar_dollar
	}
	_t638 := _t637(msg)
	fields140 := _t638
	p.write("|")
	if !(len(fields140) == 0) {
		p.write(" ")
		for i142, elem141 := range fields140 {
			if (i142 > 0) {
				p.newline()
			}
			p.pretty_binding(elem141)
		}
	}
}

func (p *PrettyPrinter) pretty_formula(msg *pb.Formula) {
	_t639 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
		var _t640 *pb.Conjunction
		if (hasProtoField(_dollar_dollar, "conjunction") && len(_dollar_dollar.GetConjunction().GetArgs()) == 0) {
			_t640 = _dollar_dollar.GetConjunction()
		}
		return _t640
	}
	_t641 := _t639(msg)
	deconstruct_result167 := _t641
	if deconstruct_result167 != nil {
		unwrapped_deconstruct168 := deconstruct_result167
		p.pretty_true(unwrapped_deconstruct168)
	} else {
		_t642 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
			var _t643 *pb.Disjunction
			if (hasProtoField(_dollar_dollar, "disjunction") && len(_dollar_dollar.GetDisjunction().GetArgs()) == 0) {
				_t643 = _dollar_dollar.GetDisjunction()
			}
			return _t643
		}
		_t644 := _t642(msg)
		deconstruct_result165 := _t644
		if deconstruct_result165 != nil {
			unwrapped_deconstruct166 := deconstruct_result165
			p.pretty_false(unwrapped_deconstruct166)
		} else {
			_t645 := func(_dollar_dollar *pb.Formula) *pb.Exists {
				var _t646 *pb.Exists
				if hasProtoField(_dollar_dollar, "exists") {
					_t646 = _dollar_dollar.GetExists()
				}
				return _t646
			}
			_t647 := _t645(msg)
			deconstruct_result163 := _t647
			if deconstruct_result163 != nil {
				unwrapped_deconstruct164 := deconstruct_result163
				p.pretty_exists(unwrapped_deconstruct164)
			} else {
				_t648 := func(_dollar_dollar *pb.Formula) *pb.Reduce {
					var _t649 *pb.Reduce
					if hasProtoField(_dollar_dollar, "reduce") {
						_t649 = _dollar_dollar.GetReduce()
					}
					return _t649
				}
				_t650 := _t648(msg)
				deconstruct_result161 := _t650
				if deconstruct_result161 != nil {
					unwrapped_deconstruct162 := deconstruct_result161
					p.pretty_reduce(unwrapped_deconstruct162)
				} else {
					_t651 := func(_dollar_dollar *pb.Formula) *pb.Conjunction {
						var _t652 *pb.Conjunction
						if hasProtoField(_dollar_dollar, "conjunction") {
							_t652 = _dollar_dollar.GetConjunction()
						}
						return _t652
					}
					_t653 := _t651(msg)
					deconstruct_result159 := _t653
					if deconstruct_result159 != nil {
						unwrapped_deconstruct160 := deconstruct_result159
						p.pretty_conjunction(unwrapped_deconstruct160)
					} else {
						_t654 := func(_dollar_dollar *pb.Formula) *pb.Disjunction {
							var _t655 *pb.Disjunction
							if hasProtoField(_dollar_dollar, "disjunction") {
								_t655 = _dollar_dollar.GetDisjunction()
							}
							return _t655
						}
						_t656 := _t654(msg)
						deconstruct_result157 := _t656
						if deconstruct_result157 != nil {
							unwrapped_deconstruct158 := deconstruct_result157
							p.pretty_disjunction(unwrapped_deconstruct158)
						} else {
							_t657 := func(_dollar_dollar *pb.Formula) *pb.Not {
								var _t658 *pb.Not
								if hasProtoField(_dollar_dollar, "not") {
									_t658 = _dollar_dollar.GetNot()
								}
								return _t658
							}
							_t659 := _t657(msg)
							deconstruct_result155 := _t659
							if deconstruct_result155 != nil {
								unwrapped_deconstruct156 := deconstruct_result155
								p.pretty_not(unwrapped_deconstruct156)
							} else {
								_t660 := func(_dollar_dollar *pb.Formula) *pb.FFI {
									var _t661 *pb.FFI
									if hasProtoField(_dollar_dollar, "ffi") {
										_t661 = _dollar_dollar.GetFfi()
									}
									return _t661
								}
								_t662 := _t660(msg)
								deconstruct_result153 := _t662
								if deconstruct_result153 != nil {
									unwrapped_deconstruct154 := deconstruct_result153
									p.pretty_ffi(unwrapped_deconstruct154)
								} else {
									_t663 := func(_dollar_dollar *pb.Formula) *pb.Atom {
										var _t664 *pb.Atom
										if hasProtoField(_dollar_dollar, "atom") {
											_t664 = _dollar_dollar.GetAtom()
										}
										return _t664
									}
									_t665 := _t663(msg)
									deconstruct_result151 := _t665
									if deconstruct_result151 != nil {
										unwrapped_deconstruct152 := deconstruct_result151
										p.pretty_atom(unwrapped_deconstruct152)
									} else {
										_t666 := func(_dollar_dollar *pb.Formula) *pb.Pragma {
											var _t667 *pb.Pragma
											if hasProtoField(_dollar_dollar, "pragma") {
												_t667 = _dollar_dollar.GetPragma()
											}
											return _t667
										}
										_t668 := _t666(msg)
										deconstruct_result149 := _t668
										if deconstruct_result149 != nil {
											unwrapped_deconstruct150 := deconstruct_result149
											p.pretty_pragma(unwrapped_deconstruct150)
										} else {
											_t669 := func(_dollar_dollar *pb.Formula) *pb.Primitive {
												var _t670 *pb.Primitive
												if hasProtoField(_dollar_dollar, "primitive") {
													_t670 = _dollar_dollar.GetPrimitive()
												}
												return _t670
											}
											_t671 := _t669(msg)
											deconstruct_result147 := _t671
											if deconstruct_result147 != nil {
												unwrapped_deconstruct148 := deconstruct_result147
												p.pretty_primitive(unwrapped_deconstruct148)
											} else {
												_t672 := func(_dollar_dollar *pb.Formula) *pb.RelAtom {
													var _t673 *pb.RelAtom
													if hasProtoField(_dollar_dollar, "rel_atom") {
														_t673 = _dollar_dollar.GetRelAtom()
													}
													return _t673
												}
												_t674 := _t672(msg)
												deconstruct_result145 := _t674
												if deconstruct_result145 != nil {
													unwrapped_deconstruct146 := deconstruct_result145
													p.pretty_rel_atom(unwrapped_deconstruct146)
												} else {
													_t675 := func(_dollar_dollar *pb.Formula) *pb.Cast {
														var _t676 *pb.Cast
														if hasProtoField(_dollar_dollar, "cast") {
															_t676 = _dollar_dollar.GetCast()
														}
														return _t676
													}
													_t677 := _t675(msg)
													deconstruct_result143 := _t677
													if deconstruct_result143 != nil {
														unwrapped_deconstruct144 := deconstruct_result143
														p.pretty_cast(unwrapped_deconstruct144)
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

func (p *PrettyPrinter) pretty_true(msg *pb.Conjunction) {
	_t678 := func(_dollar_dollar *pb.Conjunction) *pb.Conjunction {
		return _dollar_dollar
	}
	_t679 := _t678(msg)
	fields169 := _t679
	_ = fields169
	p.write("(")
	p.write("true")
	p.write(")")
}

func (p *PrettyPrinter) pretty_false(msg *pb.Disjunction) {
	_t680 := func(_dollar_dollar *pb.Disjunction) *pb.Disjunction {
		return _dollar_dollar
	}
	_t681 := _t680(msg)
	fields170 := _t681
	_ = fields170
	p.write("(")
	p.write("false")
	p.write(")")
}

func (p *PrettyPrinter) pretty_exists(msg *pb.Exists) {
	_t682 := func(_dollar_dollar *pb.Exists) []interface{} {
		_t683 := p.deconstructBindings(_dollar_dollar.GetBody())
		return []interface{}{_t683, _dollar_dollar.GetBody().GetValue()}
	}
	_t684 := _t682(msg)
	fields171 := _t684
	p.write("(")
	p.write("exists")
	p.indent()
	p.newline()
	field172 := fields171[0].([]interface{})
	p.pretty_bindings(field172)
	p.newline()
	field173 := fields171[1].(*pb.Formula)
	p.pretty_formula(field173)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_reduce(msg *pb.Reduce) {
	_t685 := func(_dollar_dollar *pb.Reduce) []interface{} {
		return []interface{}{_dollar_dollar.GetOp(), _dollar_dollar.GetBody(), _dollar_dollar.GetTerms()}
	}
	_t686 := _t685(msg)
	fields174 := _t686
	p.write("(")
	p.write("reduce")
	p.indent()
	p.newline()
	field175 := fields174[0].(*pb.Abstraction)
	p.pretty_abstraction(field175)
	p.newline()
	field176 := fields174[1].(*pb.Abstraction)
	p.pretty_abstraction(field176)
	p.newline()
	field177 := fields174[2].([]*pb.Term)
	p.pretty_terms(field177)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_terms(msg []*pb.Term) {
	_t687 := func(_dollar_dollar []*pb.Term) []*pb.Term {
		return _dollar_dollar
	}
	_t688 := _t687(msg)
	fields178 := _t688
	p.write("(")
	p.write("terms")
	p.indent()
	if !(len(fields178) == 0) {
		p.newline()
		for i180, elem179 := range fields178 {
			if (i180 > 0) {
				p.newline()
			}
			p.pretty_term(elem179)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_term(msg *pb.Term) {
	_t689 := func(_dollar_dollar *pb.Term) *pb.Var {
		var _t690 *pb.Var
		if hasProtoField(_dollar_dollar, "var") {
			_t690 = _dollar_dollar.GetVar()
		}
		return _t690
	}
	_t691 := _t689(msg)
	deconstruct_result183 := _t691
	if deconstruct_result183 != nil {
		unwrapped_deconstruct184 := deconstruct_result183
		p.pretty_var(unwrapped_deconstruct184)
	} else {
		_t692 := func(_dollar_dollar *pb.Term) *pb.Value {
			var _t693 *pb.Value
			if hasProtoField(_dollar_dollar, "constant") {
				_t693 = _dollar_dollar.GetConstant()
			}
			return _t693
		}
		_t694 := _t692(msg)
		deconstruct_result181 := _t694
		if deconstruct_result181 != nil {
			unwrapped_deconstruct182 := deconstruct_result181
			p.pretty_constant(unwrapped_deconstruct182)
		} else {
			panic(ParseError{msg: "No matching rule for term"})
		}
	}
}

func (p *PrettyPrinter) pretty_var(msg *pb.Var) {
	_t695 := func(_dollar_dollar *pb.Var) string {
		return _dollar_dollar.GetName()
	}
	_t696 := _t695(msg)
	fields185 := _t696
	p.write(fields185)
}

func (p *PrettyPrinter) pretty_constant(msg *pb.Value) {
	_t697 := func(_dollar_dollar *pb.Value) *pb.Value {
		return _dollar_dollar
	}
	_t698 := _t697(msg)
	fields186 := _t698
	p.pretty_value(fields186)
}

func (p *PrettyPrinter) pretty_conjunction(msg *pb.Conjunction) {
	_t699 := func(_dollar_dollar *pb.Conjunction) []*pb.Formula {
		return _dollar_dollar.GetArgs()
	}
	_t700 := _t699(msg)
	fields187 := _t700
	p.write("(")
	p.write("and")
	p.indent()
	if !(len(fields187) == 0) {
		p.newline()
		for i189, elem188 := range fields187 {
			if (i189 > 0) {
				p.newline()
			}
			p.pretty_formula(elem188)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_disjunction(msg *pb.Disjunction) {
	_t701 := func(_dollar_dollar *pb.Disjunction) []*pb.Formula {
		return _dollar_dollar.GetArgs()
	}
	_t702 := _t701(msg)
	fields190 := _t702
	p.write("(")
	p.write("or")
	p.indent()
	if !(len(fields190) == 0) {
		p.newline()
		for i192, elem191 := range fields190 {
			if (i192 > 0) {
				p.newline()
			}
			p.pretty_formula(elem191)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_not(msg *pb.Not) {
	_t703 := func(_dollar_dollar *pb.Not) *pb.Formula {
		return _dollar_dollar.GetArg()
	}
	_t704 := _t703(msg)
	fields193 := _t704
	p.write("(")
	p.write("not")
	p.indent()
	p.newline()
	p.pretty_formula(fields193)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_ffi(msg *pb.FFI) {
	_t705 := func(_dollar_dollar *pb.FFI) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs(), _dollar_dollar.GetTerms()}
	}
	_t706 := _t705(msg)
	fields194 := _t706
	p.write("(")
	p.write("ffi")
	p.indent()
	p.newline()
	field195 := fields194[0].(string)
	p.pretty_name(field195)
	p.newline()
	field196 := fields194[1].([]*pb.Abstraction)
	p.pretty_ffi_args(field196)
	p.newline()
	field197 := fields194[2].([]*pb.Term)
	p.pretty_terms(field197)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_name(msg string) {
	_t707 := func(_dollar_dollar string) string {
		return _dollar_dollar
	}
	_t708 := _t707(msg)
	fields198 := _t708
	p.write(":")
	p.write(fields198)
}

func (p *PrettyPrinter) pretty_ffi_args(msg []*pb.Abstraction) {
	_t709 := func(_dollar_dollar []*pb.Abstraction) []*pb.Abstraction {
		return _dollar_dollar
	}
	_t710 := _t709(msg)
	fields199 := _t710
	p.write("(")
	p.write("args")
	p.indent()
	if !(len(fields199) == 0) {
		p.newline()
		for i201, elem200 := range fields199 {
			if (i201 > 0) {
				p.newline()
			}
			p.pretty_abstraction(elem200)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_atom(msg *pb.Atom) {
	_t711 := func(_dollar_dollar *pb.Atom) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
	}
	_t712 := _t711(msg)
	fields202 := _t712
	p.write("(")
	p.write("atom")
	p.indent()
	p.newline()
	field203 := fields202[0].(*pb.RelationId)
	p.pretty_relation_id(field203)
	field204 := fields202[1].([]*pb.Term)
	if !(len(field204) == 0) {
		p.newline()
		for i206, elem205 := range field204 {
			if (i206 > 0) {
				p.newline()
			}
			p.pretty_term(elem205)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_pragma(msg *pb.Pragma) {
	_t713 := func(_dollar_dollar *pb.Pragma) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
	}
	_t714 := _t713(msg)
	fields207 := _t714
	p.write("(")
	p.write("pragma")
	p.indent()
	p.newline()
	field208 := fields207[0].(string)
	p.pretty_name(field208)
	field209 := fields207[1].([]*pb.Term)
	if !(len(field209) == 0) {
		p.newline()
		for i211, elem210 := range field209 {
			if (i211 > 0) {
				p.newline()
			}
			p.pretty_term(elem210)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_primitive(msg *pb.Primitive) {
	_t715 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t716 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t716 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t716
	}
	_t717 := _t715(msg)
	guard_result225 := _t717
	if guard_result225 != nil {
		p.pretty_eq(msg)
	} else {
		_t718 := func(_dollar_dollar *pb.Primitive) []interface{} {
			var _t719 []interface{}
			if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
				_t719 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
			}
			return _t719
		}
		_t720 := _t718(msg)
		guard_result224 := _t720
		if guard_result224 != nil {
			p.pretty_lt(msg)
		} else {
			_t721 := func(_dollar_dollar *pb.Primitive) []interface{} {
				var _t722 []interface{}
				if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
					_t722 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
				}
				return _t722
			}
			_t723 := _t721(msg)
			guard_result223 := _t723
			if guard_result223 != nil {
				p.pretty_lt_eq(msg)
			} else {
				_t724 := func(_dollar_dollar *pb.Primitive) []interface{} {
					var _t725 []interface{}
					if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
						_t725 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
					}
					return _t725
				}
				_t726 := _t724(msg)
				guard_result222 := _t726
				if guard_result222 != nil {
					p.pretty_gt(msg)
				} else {
					_t727 := func(_dollar_dollar *pb.Primitive) []interface{} {
						var _t728 []interface{}
						if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
							_t728 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
						}
						return _t728
					}
					_t729 := _t727(msg)
					guard_result221 := _t729
					if guard_result221 != nil {
						p.pretty_gt_eq(msg)
					} else {
						_t730 := func(_dollar_dollar *pb.Primitive) []interface{} {
							var _t731 []interface{}
							if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
								_t731 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
							}
							return _t731
						}
						_t732 := _t730(msg)
						guard_result220 := _t732
						if guard_result220 != nil {
							p.pretty_add(msg)
						} else {
							_t733 := func(_dollar_dollar *pb.Primitive) []interface{} {
								var _t734 []interface{}
								if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
									_t734 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
								}
								return _t734
							}
							_t735 := _t733(msg)
							guard_result219 := _t735
							if guard_result219 != nil {
								p.pretty_minus(msg)
							} else {
								_t736 := func(_dollar_dollar *pb.Primitive) []interface{} {
									var _t737 []interface{}
									if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
										_t737 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
									}
									return _t737
								}
								_t738 := _t736(msg)
								guard_result218 := _t738
								if guard_result218 != nil {
									p.pretty_multiply(msg)
								} else {
									_t739 := func(_dollar_dollar *pb.Primitive) []interface{} {
										var _t740 []interface{}
										if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
											_t740 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
										}
										return _t740
									}
									_t741 := _t739(msg)
									guard_result217 := _t741
									if guard_result217 != nil {
										p.pretty_divide(msg)
									} else {
										_t742 := func(_dollar_dollar *pb.Primitive) []interface{} {
											return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
										}
										_t743 := _t742(msg)
										fields212 := _t743
										p.write("(")
										p.write("primitive")
										p.indent()
										p.newline()
										field213 := fields212[0].(string)
										p.pretty_name(field213)
										field214 := fields212[1].([]*pb.RelTerm)
										if !(len(field214) == 0) {
											p.newline()
											for i216, elem215 := range field214 {
												if (i216 > 0) {
													p.newline()
												}
												p.pretty_rel_term(elem215)
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

func (p *PrettyPrinter) pretty_eq(msg *pb.Primitive) {
	_t744 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t745 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_eq" {
			_t745 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t745
	}
	_t746 := _t744(msg)
	fields226 := _t746
	unwrapped_fields227 := fields226
	p.write("(")
	p.write("=")
	p.indent()
	p.newline()
	field228 := unwrapped_fields227[0].(*pb.Term)
	p.pretty_term(field228)
	p.newline()
	field229 := unwrapped_fields227[1].(*pb.Term)
	p.pretty_term(field229)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_lt(msg *pb.Primitive) {
	_t747 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t748 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_monotype" {
			_t748 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t748
	}
	_t749 := _t747(msg)
	fields230 := _t749
	unwrapped_fields231 := fields230
	p.write("(")
	p.write("<")
	p.indent()
	p.newline()
	field232 := unwrapped_fields231[0].(*pb.Term)
	p.pretty_term(field232)
	p.newline()
	field233 := unwrapped_fields231[1].(*pb.Term)
	p.pretty_term(field233)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_lt_eq(msg *pb.Primitive) {
	_t750 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t751 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_lt_eq_monotype" {
			_t751 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t751
	}
	_t752 := _t750(msg)
	fields234 := _t752
	unwrapped_fields235 := fields234
	p.write("(")
	p.write("<=")
	p.indent()
	p.newline()
	field236 := unwrapped_fields235[0].(*pb.Term)
	p.pretty_term(field236)
	p.newline()
	field237 := unwrapped_fields235[1].(*pb.Term)
	p.pretty_term(field237)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_gt(msg *pb.Primitive) {
	_t753 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t754 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_monotype" {
			_t754 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t754
	}
	_t755 := _t753(msg)
	fields238 := _t755
	unwrapped_fields239 := fields238
	p.write("(")
	p.write(">")
	p.indent()
	p.newline()
	field240 := unwrapped_fields239[0].(*pb.Term)
	p.pretty_term(field240)
	p.newline()
	field241 := unwrapped_fields239[1].(*pb.Term)
	p.pretty_term(field241)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_gt_eq(msg *pb.Primitive) {
	_t756 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t757 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_gt_eq_monotype" {
			_t757 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm()}
		}
		return _t757
	}
	_t758 := _t756(msg)
	fields242 := _t758
	unwrapped_fields243 := fields242
	p.write("(")
	p.write(">=")
	p.indent()
	p.newline()
	field244 := unwrapped_fields243[0].(*pb.Term)
	p.pretty_term(field244)
	p.newline()
	field245 := unwrapped_fields243[1].(*pb.Term)
	p.pretty_term(field245)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_add(msg *pb.Primitive) {
	_t759 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t760 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_add_monotype" {
			_t760 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		return _t760
	}
	_t761 := _t759(msg)
	fields246 := _t761
	unwrapped_fields247 := fields246
	p.write("(")
	p.write("+")
	p.indent()
	p.newline()
	field248 := unwrapped_fields247[0].(*pb.Term)
	p.pretty_term(field248)
	p.newline()
	field249 := unwrapped_fields247[1].(*pb.Term)
	p.pretty_term(field249)
	p.newline()
	field250 := unwrapped_fields247[2].(*pb.Term)
	p.pretty_term(field250)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_minus(msg *pb.Primitive) {
	_t762 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t763 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_subtract_monotype" {
			_t763 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		return _t763
	}
	_t764 := _t762(msg)
	fields251 := _t764
	unwrapped_fields252 := fields251
	p.write("(")
	p.write("-")
	p.indent()
	p.newline()
	field253 := unwrapped_fields252[0].(*pb.Term)
	p.pretty_term(field253)
	p.newline()
	field254 := unwrapped_fields252[1].(*pb.Term)
	p.pretty_term(field254)
	p.newline()
	field255 := unwrapped_fields252[2].(*pb.Term)
	p.pretty_term(field255)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_multiply(msg *pb.Primitive) {
	_t765 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t766 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_multiply_monotype" {
			_t766 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		return _t766
	}
	_t767 := _t765(msg)
	fields256 := _t767
	unwrapped_fields257 := fields256
	p.write("(")
	p.write("*")
	p.indent()
	p.newline()
	field258 := unwrapped_fields257[0].(*pb.Term)
	p.pretty_term(field258)
	p.newline()
	field259 := unwrapped_fields257[1].(*pb.Term)
	p.pretty_term(field259)
	p.newline()
	field260 := unwrapped_fields257[2].(*pb.Term)
	p.pretty_term(field260)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_divide(msg *pb.Primitive) {
	_t768 := func(_dollar_dollar *pb.Primitive) []interface{} {
		var _t769 []interface{}
		if _dollar_dollar.GetName() == "rel_primitive_divide_monotype" {
			_t769 = []interface{}{_dollar_dollar.GetTerms()[0].GetTerm(), _dollar_dollar.GetTerms()[1].GetTerm(), _dollar_dollar.GetTerms()[2].GetTerm()}
		}
		return _t769
	}
	_t770 := _t768(msg)
	fields261 := _t770
	unwrapped_fields262 := fields261
	p.write("(")
	p.write("/")
	p.indent()
	p.newline()
	field263 := unwrapped_fields262[0].(*pb.Term)
	p.pretty_term(field263)
	p.newline()
	field264 := unwrapped_fields262[1].(*pb.Term)
	p.pretty_term(field264)
	p.newline()
	field265 := unwrapped_fields262[2].(*pb.Term)
	p.pretty_term(field265)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_rel_term(msg *pb.RelTerm) {
	_t771 := func(_dollar_dollar *pb.RelTerm) *pb.Value {
		var _t772 *pb.Value
		if hasProtoField(_dollar_dollar, "specialized_value") {
			_t772 = _dollar_dollar.GetSpecializedValue()
		}
		return _t772
	}
	_t773 := _t771(msg)
	deconstruct_result268 := _t773
	if deconstruct_result268 != nil {
		unwrapped_deconstruct269 := deconstruct_result268
		p.pretty_specialized_value(unwrapped_deconstruct269)
	} else {
		_t774 := func(_dollar_dollar *pb.RelTerm) *pb.Term {
			var _t775 *pb.Term
			if hasProtoField(_dollar_dollar, "term") {
				_t775 = _dollar_dollar.GetTerm()
			}
			return _t775
		}
		_t776 := _t774(msg)
		deconstruct_result266 := _t776
		if deconstruct_result266 != nil {
			unwrapped_deconstruct267 := deconstruct_result266
			p.pretty_term(unwrapped_deconstruct267)
		} else {
			panic(ParseError{msg: "No matching rule for rel_term"})
		}
	}
}

func (p *PrettyPrinter) pretty_specialized_value(msg *pb.Value) {
	_t777 := func(_dollar_dollar *pb.Value) *pb.Value {
		return _dollar_dollar
	}
	_t778 := _t777(msg)
	fields270 := _t778
	p.write("#")
	p.pretty_value(fields270)
}

func (p *PrettyPrinter) pretty_rel_atom(msg *pb.RelAtom) {
	_t779 := func(_dollar_dollar *pb.RelAtom) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetTerms()}
	}
	_t780 := _t779(msg)
	fields271 := _t780
	p.write("(")
	p.write("relatom")
	p.indent()
	p.newline()
	field272 := fields271[0].(string)
	p.pretty_name(field272)
	field273 := fields271[1].([]*pb.RelTerm)
	if !(len(field273) == 0) {
		p.newline()
		for i275, elem274 := range field273 {
			if (i275 > 0) {
				p.newline()
			}
			p.pretty_rel_term(elem274)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_cast(msg *pb.Cast) {
	_t781 := func(_dollar_dollar *pb.Cast) []interface{} {
		return []interface{}{_dollar_dollar.GetInput(), _dollar_dollar.GetResult()}
	}
	_t782 := _t781(msg)
	fields276 := _t782
	p.write("(")
	p.write("cast")
	p.indent()
	p.newline()
	field277 := fields276[0].(*pb.Term)
	p.pretty_term(field277)
	p.newline()
	field278 := fields276[1].(*pb.Term)
	p.pretty_term(field278)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_attrs(msg []*pb.Attribute) {
	_t783 := func(_dollar_dollar []*pb.Attribute) []*pb.Attribute {
		return _dollar_dollar
	}
	_t784 := _t783(msg)
	fields279 := _t784
	p.write("(")
	p.write("attrs")
	p.indent()
	if !(len(fields279) == 0) {
		p.newline()
		for i281, elem280 := range fields279 {
			if (i281 > 0) {
				p.newline()
			}
			p.pretty_attribute(elem280)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_attribute(msg *pb.Attribute) {
	_t785 := func(_dollar_dollar *pb.Attribute) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetArgs()}
	}
	_t786 := _t785(msg)
	fields282 := _t786
	p.write("(")
	p.write("attribute")
	p.indent()
	p.newline()
	field283 := fields282[0].(string)
	p.pretty_name(field283)
	field284 := fields282[1].([]*pb.Value)
	if !(len(field284) == 0) {
		p.newline()
		for i286, elem285 := range field284 {
			if (i286 > 0) {
				p.newline()
			}
			p.pretty_value(elem285)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_algorithm(msg *pb.Algorithm) {
	_t787 := func(_dollar_dollar *pb.Algorithm) []interface{} {
		return []interface{}{_dollar_dollar.GetGlobal(), _dollar_dollar.GetBody()}
	}
	_t788 := _t787(msg)
	fields287 := _t788
	p.write("(")
	p.write("algorithm")
	p.indent()
	field288 := fields287[0].([]*pb.RelationId)
	if !(len(field288) == 0) {
		p.newline()
		for i290, elem289 := range field288 {
			if (i290 > 0) {
				p.newline()
			}
			p.pretty_relation_id(elem289)
		}
	}
	p.newline()
	field291 := fields287[1].(*pb.Script)
	p.pretty_script(field291)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_script(msg *pb.Script) {
	_t789 := func(_dollar_dollar *pb.Script) []*pb.Construct {
		return _dollar_dollar.GetConstructs()
	}
	_t790 := _t789(msg)
	fields292 := _t790
	p.write("(")
	p.write("script")
	p.indent()
	if !(len(fields292) == 0) {
		p.newline()
		for i294, elem293 := range fields292 {
			if (i294 > 0) {
				p.newline()
			}
			p.pretty_construct(elem293)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_construct(msg *pb.Construct) {
	_t791 := func(_dollar_dollar *pb.Construct) *pb.Loop {
		var _t792 *pb.Loop
		if hasProtoField(_dollar_dollar, "loop") {
			_t792 = _dollar_dollar.GetLoop()
		}
		return _t792
	}
	_t793 := _t791(msg)
	deconstruct_result297 := _t793
	if deconstruct_result297 != nil {
		unwrapped_deconstruct298 := deconstruct_result297
		p.pretty_loop(unwrapped_deconstruct298)
	} else {
		_t794 := func(_dollar_dollar *pb.Construct) *pb.Instruction {
			var _t795 *pb.Instruction
			if hasProtoField(_dollar_dollar, "instruction") {
				_t795 = _dollar_dollar.GetInstruction()
			}
			return _t795
		}
		_t796 := _t794(msg)
		deconstruct_result295 := _t796
		if deconstruct_result295 != nil {
			unwrapped_deconstruct296 := deconstruct_result295
			p.pretty_instruction(unwrapped_deconstruct296)
		} else {
			panic(ParseError{msg: "No matching rule for construct"})
		}
	}
}

func (p *PrettyPrinter) pretty_loop(msg *pb.Loop) {
	_t797 := func(_dollar_dollar *pb.Loop) []interface{} {
		return []interface{}{_dollar_dollar.GetInit(), _dollar_dollar.GetBody()}
	}
	_t798 := _t797(msg)
	fields299 := _t798
	p.write("(")
	p.write("loop")
	p.indent()
	p.newline()
	field300 := fields299[0].([]*pb.Instruction)
	p.pretty_init(field300)
	p.newline()
	field301 := fields299[1].(*pb.Script)
	p.pretty_script(field301)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_init(msg []*pb.Instruction) {
	_t799 := func(_dollar_dollar []*pb.Instruction) []*pb.Instruction {
		return _dollar_dollar
	}
	_t800 := _t799(msg)
	fields302 := _t800
	p.write("(")
	p.write("init")
	p.indent()
	if !(len(fields302) == 0) {
		p.newline()
		for i304, elem303 := range fields302 {
			if (i304 > 0) {
				p.newline()
			}
			p.pretty_instruction(elem303)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_instruction(msg *pb.Instruction) {
	_t801 := func(_dollar_dollar *pb.Instruction) *pb.Assign {
		var _t802 *pb.Assign
		if hasProtoField(_dollar_dollar, "assign") {
			_t802 = _dollar_dollar.GetAssign()
		}
		return _t802
	}
	_t803 := _t801(msg)
	deconstruct_result313 := _t803
	if deconstruct_result313 != nil {
		unwrapped_deconstruct314 := deconstruct_result313
		p.pretty_assign(unwrapped_deconstruct314)
	} else {
		_t804 := func(_dollar_dollar *pb.Instruction) *pb.Upsert {
			var _t805 *pb.Upsert
			if hasProtoField(_dollar_dollar, "upsert") {
				_t805 = _dollar_dollar.GetUpsert()
			}
			return _t805
		}
		_t806 := _t804(msg)
		deconstruct_result311 := _t806
		if deconstruct_result311 != nil {
			unwrapped_deconstruct312 := deconstruct_result311
			p.pretty_upsert(unwrapped_deconstruct312)
		} else {
			_t807 := func(_dollar_dollar *pb.Instruction) *pb.Break {
				var _t808 *pb.Break
				if hasProtoField(_dollar_dollar, "break") {
					_t808 = _dollar_dollar.GetBreak()
				}
				return _t808
			}
			_t809 := _t807(msg)
			deconstruct_result309 := _t809
			if deconstruct_result309 != nil {
				unwrapped_deconstruct310 := deconstruct_result309
				p.pretty_break(unwrapped_deconstruct310)
			} else {
				_t810 := func(_dollar_dollar *pb.Instruction) *pb.MonoidDef {
					var _t811 *pb.MonoidDef
					if hasProtoField(_dollar_dollar, "monoid_def") {
						_t811 = _dollar_dollar.GetMonoidDef()
					}
					return _t811
				}
				_t812 := _t810(msg)
				deconstruct_result307 := _t812
				if deconstruct_result307 != nil {
					unwrapped_deconstruct308 := deconstruct_result307
					p.pretty_monoid_def(unwrapped_deconstruct308)
				} else {
					_t813 := func(_dollar_dollar *pb.Instruction) *pb.MonusDef {
						var _t814 *pb.MonusDef
						if hasProtoField(_dollar_dollar, "monus_def") {
							_t814 = _dollar_dollar.GetMonusDef()
						}
						return _t814
					}
					_t815 := _t813(msg)
					deconstruct_result305 := _t815
					if deconstruct_result305 != nil {
						unwrapped_deconstruct306 := deconstruct_result305
						p.pretty_monus_def(unwrapped_deconstruct306)
					} else {
						panic(ParseError{msg: "No matching rule for instruction"})
					}
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_assign(msg *pb.Assign) {
	_t816 := func(_dollar_dollar *pb.Assign) []interface{} {
		var _t817 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t817 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t817}
	}
	_t818 := _t816(msg)
	fields315 := _t818
	p.write("(")
	p.write("assign")
	p.indent()
	p.newline()
	field316 := fields315[0].(*pb.RelationId)
	p.pretty_relation_id(field316)
	p.newline()
	field317 := fields315[1].(*pb.Abstraction)
	p.pretty_abstraction(field317)
	_t819 := fields315[2]
	var _t820 []*pb.Attribute
	if _t819 != nil {
		_t820 = _t819.([]*pb.Attribute)
	}
	field318 := _t820
	if field318 != nil {
		p.newline()
		opt_val319 := field318
		p.pretty_attrs(opt_val319)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_upsert(msg *pb.Upsert) {
	_t821 := func(_dollar_dollar *pb.Upsert) []interface{} {
		var _t822 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t822 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t822}
	}
	_t823 := _t821(msg)
	fields320 := _t823
	p.write("(")
	p.write("upsert")
	p.indent()
	p.newline()
	field321 := fields320[0].(*pb.RelationId)
	p.pretty_relation_id(field321)
	p.newline()
	field322 := fields320[1].([]interface{})
	p.pretty_abstraction_with_arity(field322)
	_t824 := fields320[2]
	var _t825 []*pb.Attribute
	if _t824 != nil {
		_t825 = _t824.([]*pb.Attribute)
	}
	field323 := _t825
	if field323 != nil {
		p.newline()
		opt_val324 := field323
		p.pretty_attrs(opt_val324)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_abstraction_with_arity(msg []interface{}) {
	_t826 := func(_dollar_dollar []interface{}) []interface{} {
		_t827 := p.deconstructBindingsWithArity(_dollar_dollar[0].(*pb.Abstraction), _dollar_dollar[1].(int64))
		return []interface{}{_t827, _dollar_dollar[0].(*pb.Abstraction).GetValue()}
	}
	_t828 := _t826(msg)
	fields325 := _t828
	p.write("(")
	field326 := fields325[0].([]interface{})
	p.pretty_bindings(field326)
	p.write(" ")
	field327 := fields325[1].(*pb.Formula)
	p.pretty_formula(field327)
	p.write(")")
}

func (p *PrettyPrinter) pretty_break(msg *pb.Break) {
	_t829 := func(_dollar_dollar *pb.Break) []interface{} {
		var _t830 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t830 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetBody(), _t830}
	}
	_t831 := _t829(msg)
	fields328 := _t831
	p.write("(")
	p.write("break")
	p.indent()
	p.newline()
	field329 := fields328[0].(*pb.RelationId)
	p.pretty_relation_id(field329)
	p.newline()
	field330 := fields328[1].(*pb.Abstraction)
	p.pretty_abstraction(field330)
	_t832 := fields328[2]
	var _t833 []*pb.Attribute
	if _t832 != nil {
		_t833 = _t832.([]*pb.Attribute)
	}
	field331 := _t833
	if field331 != nil {
		p.newline()
		opt_val332 := field331
		p.pretty_attrs(opt_val332)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_monoid_def(msg *pb.MonoidDef) {
	_t834 := func(_dollar_dollar *pb.MonoidDef) []interface{} {
		var _t835 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t835 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t835}
	}
	_t836 := _t834(msg)
	fields333 := _t836
	p.write("(")
	p.write("monoid")
	p.indent()
	p.newline()
	field334 := fields333[0].(*pb.Monoid)
	p.pretty_monoid(field334)
	p.newline()
	field335 := fields333[1].(*pb.RelationId)
	p.pretty_relation_id(field335)
	p.newline()
	field336 := fields333[2].([]interface{})
	p.pretty_abstraction_with_arity(field336)
	_t837 := fields333[3]
	var _t838 []*pb.Attribute
	if _t837 != nil {
		_t838 = _t837.([]*pb.Attribute)
	}
	field337 := _t838
	if field337 != nil {
		p.newline()
		opt_val338 := field337
		p.pretty_attrs(opt_val338)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_monoid(msg *pb.Monoid) {
	_t839 := func(_dollar_dollar *pb.Monoid) *pb.OrMonoid {
		var _t840 *pb.OrMonoid
		if hasProtoField(_dollar_dollar, "or_monoid") {
			_t840 = _dollar_dollar.GetOrMonoid()
		}
		return _t840
	}
	_t841 := _t839(msg)
	deconstruct_result345 := _t841
	if deconstruct_result345 != nil {
		unwrapped_deconstruct346 := deconstruct_result345
		p.pretty_or_monoid(unwrapped_deconstruct346)
	} else {
		_t842 := func(_dollar_dollar *pb.Monoid) *pb.MinMonoid {
			var _t843 *pb.MinMonoid
			if hasProtoField(_dollar_dollar, "min_monoid") {
				_t843 = _dollar_dollar.GetMinMonoid()
			}
			return _t843
		}
		_t844 := _t842(msg)
		deconstruct_result343 := _t844
		if deconstruct_result343 != nil {
			unwrapped_deconstruct344 := deconstruct_result343
			p.pretty_min_monoid(unwrapped_deconstruct344)
		} else {
			_t845 := func(_dollar_dollar *pb.Monoid) *pb.MaxMonoid {
				var _t846 *pb.MaxMonoid
				if hasProtoField(_dollar_dollar, "max_monoid") {
					_t846 = _dollar_dollar.GetMaxMonoid()
				}
				return _t846
			}
			_t847 := _t845(msg)
			deconstruct_result341 := _t847
			if deconstruct_result341 != nil {
				unwrapped_deconstruct342 := deconstruct_result341
				p.pretty_max_monoid(unwrapped_deconstruct342)
			} else {
				_t848 := func(_dollar_dollar *pb.Monoid) *pb.SumMonoid {
					var _t849 *pb.SumMonoid
					if hasProtoField(_dollar_dollar, "sum_monoid") {
						_t849 = _dollar_dollar.GetSumMonoid()
					}
					return _t849
				}
				_t850 := _t848(msg)
				deconstruct_result339 := _t850
				if deconstruct_result339 != nil {
					unwrapped_deconstruct340 := deconstruct_result339
					p.pretty_sum_monoid(unwrapped_deconstruct340)
				} else {
					panic(ParseError{msg: "No matching rule for monoid"})
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_or_monoid(msg *pb.OrMonoid) {
	_t851 := func(_dollar_dollar *pb.OrMonoid) *pb.OrMonoid {
		return _dollar_dollar
	}
	_t852 := _t851(msg)
	fields347 := _t852
	_ = fields347
	p.write("(")
	p.write("or")
	p.write(")")
}

func (p *PrettyPrinter) pretty_min_monoid(msg *pb.MinMonoid) {
	_t853 := func(_dollar_dollar *pb.MinMonoid) *pb.Type {
		return _dollar_dollar.GetType()
	}
	_t854 := _t853(msg)
	fields348 := _t854
	p.write("(")
	p.write("min")
	p.indent()
	p.newline()
	p.pretty_type(fields348)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_max_monoid(msg *pb.MaxMonoid) {
	_t855 := func(_dollar_dollar *pb.MaxMonoid) *pb.Type {
		return _dollar_dollar.GetType()
	}
	_t856 := _t855(msg)
	fields349 := _t856
	p.write("(")
	p.write("max")
	p.indent()
	p.newline()
	p.pretty_type(fields349)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_sum_monoid(msg *pb.SumMonoid) {
	_t857 := func(_dollar_dollar *pb.SumMonoid) *pb.Type {
		return _dollar_dollar.GetType()
	}
	_t858 := _t857(msg)
	fields350 := _t858
	p.write("(")
	p.write("sum")
	p.indent()
	p.newline()
	p.pretty_type(fields350)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_monus_def(msg *pb.MonusDef) {
	_t859 := func(_dollar_dollar *pb.MonusDef) []interface{} {
		var _t860 []*pb.Attribute
		if !(len(_dollar_dollar.GetAttrs()) == 0) {
			_t860 = _dollar_dollar.GetAttrs()
		}
		return []interface{}{_dollar_dollar.GetMonoid(), _dollar_dollar.GetName(), []interface{}{_dollar_dollar.GetBody(), _dollar_dollar.GetValueArity()}, _t860}
	}
	_t861 := _t859(msg)
	fields351 := _t861
	p.write("(")
	p.write("monus")
	p.indent()
	p.newline()
	field352 := fields351[0].(*pb.Monoid)
	p.pretty_monoid(field352)
	p.newline()
	field353 := fields351[1].(*pb.RelationId)
	p.pretty_relation_id(field353)
	p.newline()
	field354 := fields351[2].([]interface{})
	p.pretty_abstraction_with_arity(field354)
	_t862 := fields351[3]
	var _t863 []*pb.Attribute
	if _t862 != nil {
		_t863 = _t862.([]*pb.Attribute)
	}
	field355 := _t863
	if field355 != nil {
		p.newline()
		opt_val356 := field355
		p.pretty_attrs(opt_val356)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_constraint(msg *pb.Constraint) {
	_t864 := func(_dollar_dollar *pb.Constraint) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetFunctionalDependency().GetGuard(), _dollar_dollar.GetFunctionalDependency().GetKeys(), _dollar_dollar.GetFunctionalDependency().GetValues()}
	}
	_t865 := _t864(msg)
	fields357 := _t865
	p.write("(")
	p.write("functional_dependency")
	p.indent()
	p.newline()
	field358 := fields357[0].(*pb.RelationId)
	p.pretty_relation_id(field358)
	p.newline()
	field359 := fields357[1].(*pb.Abstraction)
	p.pretty_abstraction(field359)
	p.newline()
	field360 := fields357[2].([]*pb.Var)
	p.pretty_functional_dependency_keys(field360)
	p.newline()
	field361 := fields357[3].([]*pb.Var)
	p.pretty_functional_dependency_values(field361)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_functional_dependency_keys(msg []*pb.Var) {
	_t866 := func(_dollar_dollar []*pb.Var) []*pb.Var {
		return _dollar_dollar
	}
	_t867 := _t866(msg)
	fields362 := _t867
	p.write("(")
	p.write("keys")
	p.indent()
	if !(len(fields362) == 0) {
		p.newline()
		for i364, elem363 := range fields362 {
			if (i364 > 0) {
				p.newline()
			}
			p.pretty_var(elem363)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_functional_dependency_values(msg []*pb.Var) {
	_t868 := func(_dollar_dollar []*pb.Var) []*pb.Var {
		return _dollar_dollar
	}
	_t869 := _t868(msg)
	fields365 := _t869
	p.write("(")
	p.write("values")
	p.indent()
	if !(len(fields365) == 0) {
		p.newline()
		for i367, elem366 := range fields365 {
			if (i367 > 0) {
				p.newline()
			}
			p.pretty_var(elem366)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_data(msg *pb.Data) {
	_t870 := func(_dollar_dollar *pb.Data) *pb.RelEDB {
		var _t871 *pb.RelEDB
		if hasProtoField(_dollar_dollar, "rel_edb") {
			_t871 = _dollar_dollar.GetRelEdb()
		}
		return _t871
	}
	_t872 := _t870(msg)
	deconstruct_result372 := _t872
	if deconstruct_result372 != nil {
		unwrapped_deconstruct373 := deconstruct_result372
		p.pretty_rel_edb(unwrapped_deconstruct373)
	} else {
		_t873 := func(_dollar_dollar *pb.Data) *pb.BeTreeRelation {
			var _t874 *pb.BeTreeRelation
			if hasProtoField(_dollar_dollar, "betree_relation") {
				_t874 = _dollar_dollar.GetBetreeRelation()
			}
			return _t874
		}
		_t875 := _t873(msg)
		deconstruct_result370 := _t875
		if deconstruct_result370 != nil {
			unwrapped_deconstruct371 := deconstruct_result370
			p.pretty_betree_relation(unwrapped_deconstruct371)
		} else {
			_t876 := func(_dollar_dollar *pb.Data) *pb.CSVData {
				var _t877 *pb.CSVData
				if hasProtoField(_dollar_dollar, "csv_data") {
					_t877 = _dollar_dollar.GetCsvData()
				}
				return _t877
			}
			_t878 := _t876(msg)
			deconstruct_result368 := _t878
			if deconstruct_result368 != nil {
				unwrapped_deconstruct369 := deconstruct_result368
				p.pretty_csv_data(unwrapped_deconstruct369)
			} else {
				panic(ParseError{msg: "No matching rule for data"})
			}
		}
	}
}

func (p *PrettyPrinter) pretty_rel_edb(msg *pb.RelEDB) {
	_t879 := func(_dollar_dollar *pb.RelEDB) []interface{} {
		return []interface{}{_dollar_dollar.GetTargetId(), _dollar_dollar.GetPath(), _dollar_dollar.GetTypes()}
	}
	_t880 := _t879(msg)
	fields374 := _t880
	p.write("(")
	p.write("rel_edb")
	p.indent()
	p.newline()
	field375 := fields374[0].(*pb.RelationId)
	p.pretty_relation_id(field375)
	p.newline()
	field376 := fields374[1].([]string)
	p.pretty_rel_edb_path(field376)
	p.newline()
	field377 := fields374[2].([]*pb.Type)
	p.pretty_rel_edb_types(field377)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_rel_edb_path(msg []string) {
	_t881 := func(_dollar_dollar []string) []string {
		return _dollar_dollar
	}
	_t882 := _t881(msg)
	fields378 := _t882
	p.write("[")
	for i380, elem379 := range fields378 {
		if (i380 > 0) {
			p.newline()
		}
		p.write(p.formatStringValue(elem379))
	}
	p.write("]")
}

func (p *PrettyPrinter) pretty_rel_edb_types(msg []*pb.Type) {
	_t883 := func(_dollar_dollar []*pb.Type) []*pb.Type {
		return _dollar_dollar
	}
	_t884 := _t883(msg)
	fields381 := _t884
	p.write("[")
	for i383, elem382 := range fields381 {
		if (i383 > 0) {
			p.newline()
		}
		p.pretty_type(elem382)
	}
	p.write("]")
}

func (p *PrettyPrinter) pretty_betree_relation(msg *pb.BeTreeRelation) {
	_t885 := func(_dollar_dollar *pb.BeTreeRelation) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationInfo()}
	}
	_t886 := _t885(msg)
	fields384 := _t886
	p.write("(")
	p.write("betree_relation")
	p.indent()
	p.newline()
	field385 := fields384[0].(*pb.RelationId)
	p.pretty_relation_id(field385)
	p.newline()
	field386 := fields384[1].(*pb.BeTreeInfo)
	p.pretty_betree_info(field386)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_betree_info(msg *pb.BeTreeInfo) {
	_t887 := func(_dollar_dollar *pb.BeTreeInfo) []interface{} {
		_t888 := p.deconstructBetreeInfoConfig(_dollar_dollar)
		return []interface{}{_dollar_dollar.GetKeyTypes(), _dollar_dollar.GetValueTypes(), _t888}
	}
	_t889 := _t887(msg)
	fields387 := _t889
	p.write("(")
	p.write("betree_info")
	p.indent()
	p.newline()
	field388 := fields387[0].([]*pb.Type)
	p.pretty_betree_info_key_types(field388)
	p.newline()
	field389 := fields387[1].([]*pb.Type)
	p.pretty_betree_info_value_types(field389)
	p.newline()
	field390 := fields387[2].([][]interface{})
	p.pretty_config_dict(field390)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_betree_info_key_types(msg []*pb.Type) {
	_t890 := func(_dollar_dollar []*pb.Type) []*pb.Type {
		return _dollar_dollar
	}
	_t891 := _t890(msg)
	fields391 := _t891
	p.write("(")
	p.write("key_types")
	p.indent()
	if !(len(fields391) == 0) {
		p.newline()
		for i393, elem392 := range fields391 {
			if (i393 > 0) {
				p.newline()
			}
			p.pretty_type(elem392)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_betree_info_value_types(msg []*pb.Type) {
	_t892 := func(_dollar_dollar []*pb.Type) []*pb.Type {
		return _dollar_dollar
	}
	_t893 := _t892(msg)
	fields394 := _t893
	p.write("(")
	p.write("value_types")
	p.indent()
	if !(len(fields394) == 0) {
		p.newline()
		for i396, elem395 := range fields394 {
			if (i396 > 0) {
				p.newline()
			}
			p.pretty_type(elem395)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_data(msg *pb.CSVData) {
	_t894 := func(_dollar_dollar *pb.CSVData) []interface{} {
		return []interface{}{_dollar_dollar.GetLocator(), _dollar_dollar.GetConfig(), _dollar_dollar.GetColumns(), _dollar_dollar.GetAsof()}
	}
	_t895 := _t894(msg)
	fields397 := _t895
	p.write("(")
	p.write("csv_data")
	p.indent()
	p.newline()
	field398 := fields397[0].(*pb.CSVLocator)
	p.pretty_csvlocator(field398)
	p.newline()
	field399 := fields397[1].(*pb.CSVConfig)
	p.pretty_csv_config(field399)
	p.newline()
	field400 := fields397[2].([]*pb.CSVColumn)
	p.pretty_csv_columns(field400)
	p.newline()
	field401 := fields397[3].(string)
	p.pretty_csv_asof(field401)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csvlocator(msg *pb.CSVLocator) {
	_t896 := func(_dollar_dollar *pb.CSVLocator) []interface{} {
		var _t897 []string
		if !(len(_dollar_dollar.GetPaths()) == 0) {
			_t897 = _dollar_dollar.GetPaths()
		}
		var _t898 string
		if string(_dollar_dollar.GetInlineData()) != "" {
			_t898 = string(_dollar_dollar.GetInlineData())
		}
		return []interface{}{_t897, _t898}
	}
	_t899 := _t896(msg)
	fields402 := _t899
	p.write("(")
	p.write("csv_locator")
	p.indent()
	_t900 := fields402[0]
	var _t901 []string
	if _t900 != nil {
		_t901 = _t900.([]string)
	}
	field403 := _t901
	if field403 != nil {
		p.newline()
		opt_val404 := field403
		p.pretty_csv_locator_paths(opt_val404)
	}
	_t902 := fields402[1]
	var _t903 *string
	if _t902 != nil {
		if _t904, ok := _t902.(*string); ok {
			_t903 = _t904
		} else {
			_t905 := _t902.(string)
			_t903 = &_t905
		}
	}
	field405 := _t903
	if field405 != nil {
		p.newline()
		opt_val406 := *field405
		p.pretty_csv_locator_inline_data(opt_val406)
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_locator_paths(msg []string) {
	_t906 := func(_dollar_dollar []string) []string {
		return _dollar_dollar
	}
	_t907 := _t906(msg)
	fields407 := _t907
	p.write("(")
	p.write("paths")
	p.indent()
	if !(len(fields407) == 0) {
		p.newline()
		for i409, elem408 := range fields407 {
			if (i409 > 0) {
				p.newline()
			}
			p.write(p.formatStringValue(elem408))
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_locator_inline_data(msg string) {
	_t908 := func(_dollar_dollar string) string {
		return _dollar_dollar
	}
	_t909 := _t908(msg)
	fields410 := _t909
	p.write("(")
	p.write("inline_data")
	p.indent()
	p.newline()
	p.write(p.formatStringValue(fields410))
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_config(msg *pb.CSVConfig) {
	_t910 := func(_dollar_dollar *pb.CSVConfig) [][]interface{} {
		_t911 := p.deconstructCsvConfig(_dollar_dollar)
		return _t911
	}
	_t912 := _t910(msg)
	fields411 := _t912
	p.write("(")
	p.write("csv_config")
	p.indent()
	p.newline()
	p.pretty_config_dict(fields411)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_columns(msg []*pb.CSVColumn) {
	_t913 := func(_dollar_dollar []*pb.CSVColumn) []*pb.CSVColumn {
		return _dollar_dollar
	}
	_t914 := _t913(msg)
	fields412 := _t914
	p.write("(")
	p.write("columns")
	p.indent()
	if !(len(fields412) == 0) {
		p.newline()
		for i414, elem413 := range fields412 {
			if (i414 > 0) {
				p.newline()
			}
			p.pretty_csv_column(elem413)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_column(msg *pb.CSVColumn) {
	_t915 := func(_dollar_dollar *pb.CSVColumn) []interface{} {
		return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetTargetId(), _dollar_dollar.GetTypes()}
	}
	_t916 := _t915(msg)
	fields415 := _t916
	p.write("(")
	p.write("column")
	p.indent()
	p.newline()
	field416 := fields415[0].(string)
	p.write(p.formatStringValue(field416))
	p.newline()
	field417 := fields415[1].(*pb.RelationId)
	p.pretty_relation_id(field417)
	p.newline()
	p.write("[")
	field418 := fields415[2].([]*pb.Type)
	for i420, elem419 := range field418 {
		if (i420 > 0) {
			p.newline()
		}
		p.pretty_type(elem419)
	}
	p.write("]")
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_csv_asof(msg string) {
	_t917 := func(_dollar_dollar string) string {
		return _dollar_dollar
	}
	_t918 := _t917(msg)
	fields421 := _t918
	p.write("(")
	p.write("asof")
	p.indent()
	p.newline()
	p.write(p.formatStringValue(fields421))
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_undefine(msg *pb.Undefine) {
	_t919 := func(_dollar_dollar *pb.Undefine) *pb.FragmentId {
		return _dollar_dollar.GetFragmentId()
	}
	_t920 := _t919(msg)
	fields422 := _t920
	p.write("(")
	p.write("undefine")
	p.indent()
	p.newline()
	p.pretty_fragment_id(fields422)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_context(msg *pb.Context) {
	_t921 := func(_dollar_dollar *pb.Context) []*pb.RelationId {
		return _dollar_dollar.GetRelations()
	}
	_t922 := _t921(msg)
	fields423 := _t922
	p.write("(")
	p.write("context")
	p.indent()
	if !(len(fields423) == 0) {
		p.newline()
		for i425, elem424 := range fields423 {
			if (i425 > 0) {
				p.newline()
			}
			p.pretty_relation_id(elem424)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_epoch_reads(msg []*pb.Read) {
	_t923 := func(_dollar_dollar []*pb.Read) []*pb.Read {
		return _dollar_dollar
	}
	_t924 := _t923(msg)
	fields426 := _t924
	p.write("(")
	p.write("reads")
	p.indent()
	if !(len(fields426) == 0) {
		p.newline()
		for i428, elem427 := range fields426 {
			if (i428 > 0) {
				p.newline()
			}
			p.pretty_read(elem427)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_read(msg *pb.Read) {
	_t925 := func(_dollar_dollar *pb.Read) *pb.Demand {
		var _t926 *pb.Demand
		if hasProtoField(_dollar_dollar, "demand") {
			_t926 = _dollar_dollar.GetDemand()
		}
		return _t926
	}
	_t927 := _t925(msg)
	deconstruct_result437 := _t927
	if deconstruct_result437 != nil {
		unwrapped_deconstruct438 := deconstruct_result437
		p.pretty_demand(unwrapped_deconstruct438)
	} else {
		_t928 := func(_dollar_dollar *pb.Read) *pb.Output {
			var _t929 *pb.Output
			if hasProtoField(_dollar_dollar, "output") {
				_t929 = _dollar_dollar.GetOutput()
			}
			return _t929
		}
		_t930 := _t928(msg)
		deconstruct_result435 := _t930
		if deconstruct_result435 != nil {
			unwrapped_deconstruct436 := deconstruct_result435
			p.pretty_output(unwrapped_deconstruct436)
		} else {
			_t931 := func(_dollar_dollar *pb.Read) *pb.WhatIf {
				var _t932 *pb.WhatIf
				if hasProtoField(_dollar_dollar, "what_if") {
					_t932 = _dollar_dollar.GetWhatIf()
				}
				return _t932
			}
			_t933 := _t931(msg)
			deconstruct_result433 := _t933
			if deconstruct_result433 != nil {
				unwrapped_deconstruct434 := deconstruct_result433
				p.pretty_what_if(unwrapped_deconstruct434)
			} else {
				_t934 := func(_dollar_dollar *pb.Read) *pb.Abort {
					var _t935 *pb.Abort
					if hasProtoField(_dollar_dollar, "abort") {
						_t935 = _dollar_dollar.GetAbort()
					}
					return _t935
				}
				_t936 := _t934(msg)
				deconstruct_result431 := _t936
				if deconstruct_result431 != nil {
					unwrapped_deconstruct432 := deconstruct_result431
					p.pretty_abort(unwrapped_deconstruct432)
				} else {
					_t937 := func(_dollar_dollar *pb.Read) *pb.Export {
						var _t938 *pb.Export
						if hasProtoField(_dollar_dollar, "export") {
							_t938 = _dollar_dollar.GetExport()
						}
						return _t938
					}
					_t939 := _t937(msg)
					deconstruct_result429 := _t939
					if deconstruct_result429 != nil {
						unwrapped_deconstruct430 := deconstruct_result429
						p.pretty_export(unwrapped_deconstruct430)
					} else {
						panic(ParseError{msg: "No matching rule for read"})
					}
				}
			}
		}
	}
}

func (p *PrettyPrinter) pretty_demand(msg *pb.Demand) {
	_t940 := func(_dollar_dollar *pb.Demand) *pb.RelationId {
		return _dollar_dollar.GetRelationId()
	}
	_t941 := _t940(msg)
	fields439 := _t941
	p.write("(")
	p.write("demand")
	p.indent()
	p.newline()
	p.pretty_relation_id(fields439)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_output(msg *pb.Output) {
	_t942 := func(_dollar_dollar *pb.Output) []interface{} {
		return []interface{}{_dollar_dollar.GetName(), _dollar_dollar.GetRelationId()}
	}
	_t943 := _t942(msg)
	fields440 := _t943
	p.write("(")
	p.write("output")
	p.indent()
	p.newline()
	field441 := fields440[0].(string)
	p.pretty_name(field441)
	p.newline()
	field442 := fields440[1].(*pb.RelationId)
	p.pretty_relation_id(field442)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_what_if(msg *pb.WhatIf) {
	_t944 := func(_dollar_dollar *pb.WhatIf) []interface{} {
		return []interface{}{_dollar_dollar.GetBranch(), _dollar_dollar.GetEpoch()}
	}
	_t945 := _t944(msg)
	fields443 := _t945
	p.write("(")
	p.write("what_if")
	p.indent()
	p.newline()
	field444 := fields443[0].(string)
	p.pretty_name(field444)
	p.newline()
	field445 := fields443[1].(*pb.Epoch)
	p.pretty_epoch(field445)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_abort(msg *pb.Abort) {
	_t946 := func(_dollar_dollar *pb.Abort) []interface{} {
		var _t947 string
		if _dollar_dollar.GetName() != "abort" {
			_t947 = _dollar_dollar.GetName()
		}
		return []interface{}{_t947, _dollar_dollar.GetRelationId()}
	}
	_t948 := _t946(msg)
	fields446 := _t948
	p.write("(")
	p.write("abort")
	p.indent()
	_t949 := fields446[0]
	var _t950 *string
	if _t949 != nil {
		if _t951, ok := _t949.(*string); ok {
			_t950 = _t951
		} else {
			_t952 := _t949.(string)
			_t950 = &_t952
		}
	}
	field447 := _t950
	if field447 != nil {
		p.newline()
		opt_val448 := *field447
		p.pretty_name(opt_val448)
	}
	p.newline()
	field449 := fields446[1].(*pb.RelationId)
	p.pretty_relation_id(field449)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_export(msg *pb.Export) {
	_t953 := func(_dollar_dollar *pb.Export) *pb.ExportCSVConfig {
		return _dollar_dollar.GetCsvConfig()
	}
	_t954 := _t953(msg)
	fields450 := _t954
	p.write("(")
	p.write("export")
	p.indent()
	p.newline()
	p.pretty_export_csv_config(fields450)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_export_csv_config(msg *pb.ExportCSVConfig) {
	_t955 := func(_dollar_dollar *pb.ExportCSVConfig) []interface{} {
		_t956 := p.deconstructExportCsvConfig(_dollar_dollar)
		return []interface{}{_dollar_dollar.GetPath(), _dollar_dollar.GetDataColumns(), _t956}
	}
	_t957 := _t955(msg)
	fields451 := _t957
	p.write("(")
	p.write("export_csv_config")
	p.indent()
	p.newline()
	field452 := fields451[0].(string)
	p.pretty_export_csv_path(field452)
	p.newline()
	field453 := fields451[1].([]*pb.ExportCSVColumn)
	p.pretty_export_csv_columns(field453)
	p.newline()
	field454 := fields451[2].([][]interface{})
	p.pretty_config_dict(field454)
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_export_csv_path(msg string) {
	_t958 := func(_dollar_dollar string) string {
		return _dollar_dollar
	}
	_t959 := _t958(msg)
	fields455 := _t959
	p.write("(")
	p.write("path")
	p.indent()
	p.newline()
	p.write(p.formatStringValue(fields455))
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_export_csv_columns(msg []*pb.ExportCSVColumn) {
	_t960 := func(_dollar_dollar []*pb.ExportCSVColumn) []*pb.ExportCSVColumn {
		return _dollar_dollar
	}
	_t961 := _t960(msg)
	fields456 := _t961
	p.write("(")
	p.write("columns")
	p.indent()
	if !(len(fields456) == 0) {
		p.newline()
		for i458, elem457 := range fields456 {
			if (i458 > 0) {
				p.newline()
			}
			p.pretty_export_csv_column(elem457)
		}
	}
	p.dedent()
	p.write(")")
}

func (p *PrettyPrinter) pretty_export_csv_column(msg *pb.ExportCSVColumn) {
	_t962 := func(_dollar_dollar *pb.ExportCSVColumn) []interface{} {
		return []interface{}{_dollar_dollar.GetColumnName(), _dollar_dollar.GetColumnData()}
	}
	_t963 := _t962(msg)
	fields459 := _t963
	p.write("(")
	p.write("column")
	p.indent()
	p.newline()
	field460 := fields459[0].(string)
	p.write(p.formatStringValue(field460))
	p.newline()
	field461 := fields459[1].(*pb.RelationId)
	p.pretty_relation_id(field461)
	p.dedent()
	p.write(")")
}


// ProgramToStr pretty-prints a Transaction protobuf message to a string.
func ProgramToStr(msg *pb.Transaction) string {
	var buf bytes.Buffer
	p := &PrettyPrinter{
		w:           &buf,
		indentLevel: 0,
		atLineStart: true,
		debugInfo:   make(map[[2]uint64]string),
	}
	p.pretty_transaction(msg)
	p.newline()
	return p.getOutput()
}
