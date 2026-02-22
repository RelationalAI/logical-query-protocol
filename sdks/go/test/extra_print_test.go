package test

import (
	"testing"

	lqp "logical-query-protocol/src"
	pb "logical-query-protocol/src/lqp/v1"
)

// ---------------------------------------------------------------------------
// Token printers
// ---------------------------------------------------------------------------

func TestDecimalValue(t *testing.T) {
	msg := &pb.DecimalValue{
		Value:     &pb.Int128Value{Low: 123456789, High: 0},
		Precision: 18,
		Scale:     6,
	}
	got := lqp.MsgToStr(msg)
	if got != "123.456789d18" {
		t.Errorf("DecimalValue: got %q", got)
	}
}

func TestInt128Value(t *testing.T) {
	msg := &pb.Int128Value{Low: 42, High: 0}
	got := lqp.MsgToStr(msg)
	if got != "42i128" {
		t.Errorf("Int128Value: got %q", got)
	}
}

func TestInt128ValueNegative(t *testing.T) {
	msg := &pb.Int128Value{Low: 0xFFFFFFFFFFFFFFFF, High: 0xFFFFFFFFFFFFFFFF}
	got := lqp.MsgToStr(msg)
	if got != "-1i128" {
		t.Errorf("Int128Value negative: got %q", got)
	}
}

func TestUInt128Value(t *testing.T) {
	msg := &pb.UInt128Value{Low: 0xFF, High: 0}
	got := lqp.MsgToStr(msg)
	if got != "0xff" {
		t.Errorf("UInt128Value: got %q", got)
	}
}

func TestUInt128ValueZero(t *testing.T) {
	msg := &pb.UInt128Value{Low: 0, High: 0}
	got := lqp.MsgToStr(msg)
	if got != "0x0" {
		t.Errorf("UInt128Value zero: got %q", got)
	}
}

// ---------------------------------------------------------------------------
// Special printers
// ---------------------------------------------------------------------------

func TestMissingValue(t *testing.T) {
	msg := &pb.MissingValue{}
	got := lqp.MsgToStr(msg)
	if got != "missing" {
		t.Errorf("MissingValue: got %q", got)
	}
}

func TestDebugInfoEmpty(t *testing.T) {
	msg := &pb.DebugInfo{}
	got := lqp.MsgToStr(msg)
	if got != "(debug_info)" {
		t.Errorf("DebugInfo empty: got %q", got)
	}
}

func TestDebugInfoOneEntry(t *testing.T) {
	msg := &pb.DebugInfo{
		Ids:       []*pb.RelationId{{IdLow: 1, IdHigh: 0}},
		OrigNames: []string{"my_rel"},
	}
	expected := "(debug_info\n  (0x1 \"my_rel\"))"
	got := lqp.MsgToStr(msg)
	if got != expected {
		t.Errorf("DebugInfo one entry:\nexpected: %q\ngot:      %q", expected, got)
	}
}

// ---------------------------------------------------------------------------
// Generic printers
// ---------------------------------------------------------------------------

func TestBeTreeConfig(t *testing.T) {
	msg := &pb.BeTreeConfig{
		Epsilon:   0.5,
		MaxPivots: 128,
		MaxDeltas: 256,
		MaxLeaf:   512,
	}
	expected := "(be_tree_config\n  :epsilon 0.5\n  :max_pivots 128\n  :max_deltas 256\n  :max_leaf 512)"
	got := lqp.MsgToStr(msg)
	if got != expected {
		t.Errorf("BeTreeConfig:\nexpected: %q\ngot:      %q", expected, got)
	}
}

func TestIVMConfigAuto(t *testing.T) {
	msg := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO}
	expected := "(ivm_config\n  :level auto)"
	got := lqp.MsgToStr(msg)
	if got != expected {
		t.Errorf("IVMConfig auto:\nexpected: %q\ngot:      %q", expected, got)
	}
}

func TestIVMConfigOff(t *testing.T) {
	msg := &pb.IVMConfig{Level: pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF}
	expected := "(ivm_config\n  :level off)"
	got := lqp.MsgToStr(msg)
	if got != expected {
		t.Errorf("IVMConfig off:\nexpected: %q\ngot:      %q", expected, got)
	}
}

func TestBeTreeLocatorRootPageid(t *testing.T) {
	msg := &pb.BeTreeLocator{
		Location:     &pb.BeTreeLocator_RootPageid{RootPageid: &pb.UInt128Value{Low: 42, High: 0}},
		ElementCount: 100,
		TreeHeight:   3,
	}
	expected := "(be_tree_locator\n  :element_count 100\n  :tree_height 3\n  :location (:root_pageid 0x2a))"
	got := lqp.MsgToStr(msg)
	if got != expected {
		t.Errorf("BeTreeLocator root_pageid:\nexpected: %q\ngot:      %q", expected, got)
	}
}

func TestBeTreeLocatorInlineData(t *testing.T) {
	msg := &pb.BeTreeLocator{
		Location:     &pb.BeTreeLocator_InlineData{InlineData: []byte{0xab, 0xcd}},
		ElementCount: 10,
		TreeHeight:   1,
	}
	expected := "(be_tree_locator\n  :element_count 10\n  :tree_height 1\n  :location (:inline_data 0xabcd))"
	got := lqp.MsgToStr(msg)
	if got != expected {
		t.Errorf("BeTreeLocator inline_data:\nexpected: %q\ngot:      %q", expected, got)
	}
}

func TestBeTreeLocatorNoLocation(t *testing.T) {
	msg := &pb.BeTreeLocator{
		ElementCount: 0,
		TreeHeight:   0,
	}
	expected := "(be_tree_locator\n  :element_count 0\n  :tree_height 0\n  :location nothing)"
	got := lqp.MsgToStr(msg)
	if got != expected {
		t.Errorf("BeTreeLocator no location:\nexpected: %q\ngot:      %q", expected, got)
	}
}

// ---------------------------------------------------------------------------
// Oneof-only messages
// ---------------------------------------------------------------------------

func TestTermVar(t *testing.T) {
	msg := &pb.Term{TermType: &pb.Term_Var{Var: &pb.Var{Name: "x"}}}
	got := lqp.MsgToStr(msg)
	if got != "x" {
		t.Errorf("Term var: got %q", got)
	}
}

func TestTermConstantInt(t *testing.T) {
	msg := &pb.Term{TermType: &pb.Term_Constant{Constant: &pb.Value{Value: &pb.Value_IntValue{IntValue: 42}}}}
	got := lqp.MsgToStr(msg)
	if got != "42" {
		t.Errorf("Term constant int: got %q", got)
	}
}

func TestValueInt(t *testing.T) {
	msg := &pb.Value{Value: &pb.Value_IntValue{IntValue: 99}}
	got := lqp.MsgToStr(msg)
	if got != "99" {
		t.Errorf("Value int: got %q", got)
	}
}

func TestValueString(t *testing.T) {
	msg := &pb.Value{Value: &pb.Value_StringValue{StringValue: "hello"}}
	got := lqp.MsgToStr(msg)
	if got != `"hello"` {
		t.Errorf("Value string: got %q", got)
	}
}

func TestValueMissing(t *testing.T) {
	msg := &pb.Value{Value: &pb.Value_MissingValue{MissingValue: &pb.MissingValue{}}}
	got := lqp.MsgToStr(msg)
	if got != "missing" {
		t.Errorf("Value missing: got %q", got)
	}
}

func TestMonoidOr(t *testing.T) {
	msg := &pb.Monoid{Value: &pb.Monoid_OrMonoid{OrMonoid: &pb.OrMonoid{}}}
	got := lqp.MsgToStr(msg)
	if got != "(or)" {
		t.Errorf("Monoid or: got %q", got)
	}
}

func TestInstructionAssign(t *testing.T) {
	msg := &pb.Instruction{
		InstrType: &pb.Instruction_Assign{
			Assign: &pb.Assign{
				Name: &pb.RelationId{IdLow: 1, IdHigh: 0},
				Body: &pb.Abstraction{
					Value: &pb.Formula{
						FormulaType: &pb.Formula_Conjunction{
							Conjunction: &pb.Conjunction{Args: []*pb.Formula{}},
						},
					},
				},
			},
		},
	}
	got := lqp.MsgToStr(msg)
	if len(got) < 7 || got[:7] != "(assign" {
		t.Errorf("Instruction assign: got %q", got)
	}
}

func TestDataRelEDB(t *testing.T) {
	msg := &pb.Data{
		DataType: &pb.Data_RelEdb{
			RelEdb: &pb.RelEDB{
				TargetId: &pb.RelationId{IdLow: 1, IdHigh: 0},
				Path:     []string{"base", "rel"},
			},
		},
	}
	got := lqp.MsgToStr(msg)
	if len(got) < 8 || got[:8] != "(rel_edb" {
		t.Errorf("Data rel_edb: got %q", got)
	}
}

func TestReadDemand(t *testing.T) {
	msg := &pb.Read{
		ReadType: &pb.Read_Demand{
			Demand: &pb.Demand{
				RelationId: &pb.RelationId{IdLow: 1, IdHigh: 0},
			},
		},
	}
	got := lqp.MsgToStr(msg)
	if len(got) < 7 || got[:7] != "(demand" {
		t.Errorf("Read demand: got %q", got)
	}
}
