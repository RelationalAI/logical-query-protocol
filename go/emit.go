package lqp

import (
	"fmt"
	"math/big"

	pb "logical-query-protocol/relationalai/lqp/v1"
)

// Maps ir.TypeNames to the associated Proto message for *non-parametric types*.
// Parametric types should be handled in ConvertType
var nonParametricTypes = map[TypeName]func() *pb.Type{
	TypeNameUnspecified: func() *pb.Type {
		return &pb.Type{Type: &pb.Type_UnspecifiedType{UnspecifiedType: &pb.UnspecifiedType{}}}
	},
	TypeNameString:   func() *pb.Type { return &pb.Type{Type: &pb.Type_StringType{StringType: &pb.StringType{}}} },
	TypeNameInt:      func() *pb.Type { return &pb.Type{Type: &pb.Type_IntType{IntType: &pb.IntType{}}} },
	TypeNameFloat:    func() *pb.Type { return &pb.Type{Type: &pb.Type_FloatType{FloatType: &pb.FloatType{}}} },
	TypeNameUInt128:  func() *pb.Type { return &pb.Type{Type: &pb.Type_Uint128Type{Uint128Type: &pb.UInt128Type{}}} },
	TypeNameInt128:   func() *pb.Type { return &pb.Type{Type: &pb.Type_Int128Type{Int128Type: &pb.Int128Type{}}} },
	TypeNameDate:     func() *pb.Type { return &pb.Type{Type: &pb.Type_DateType{DateType: &pb.DateType{}}} },
	TypeNameDateTime: func() *pb.Type { return &pb.Type{Type: &pb.Type_DatetimeType{DatetimeType: &pb.DateTimeType{}}} },
	TypeNameMissing:  func() *pb.Type { return &pb.Type{Type: &pb.Type_MissingType{MissingType: &pb.MissingType{}}} },
	TypeNameBoolean:  func() *pb.Type { return &pb.Type{Type: &pb.Type_BooleanType{BooleanType: &pb.BooleanType{}}} },
}

// ConvertType converts an ir.Type to a protobuf Type
func ConvertType(rt *Type) (*pb.Type, error) {
	if rt.TypeName == TypeNameDecimal {
		if len(rt.Parameters) != 2 {
			return nil, fmt.Errorf("DECIMAL parameters should have only precision and scale, got %d arguments", len(rt.Parameters))
		}

		precision, ok := rt.Parameters[0].Value.(Int64Value)
		if !ok {
			return nil, fmt.Errorf("DECIMAL precision parameter is not an integer")
		}
		scale, ok := rt.Parameters[1].Value.(Int64Value)
		if !ok {
			return nil, fmt.Errorf("DECIMAL scale parameter is not an integer")
		}

		if precision > 38 {
			return nil, fmt.Errorf("DECIMAL precision must be less than 38, got %d", precision)
		}
		if scale > precision {
			return nil, fmt.Errorf("DECIMAL precision (%d) must be at least scale (%d)", precision, scale)
		}

		return &pb.Type{
			Type: &pb.Type_DecimalType{
				DecimalType: &pb.DecimalType{
					Precision: int32(precision),
					Scale:     int32(scale),
				},
			},
		}, nil
	}

	factory, ok := nonParametricTypes[rt.TypeName]
	if !ok {
		return nil, fmt.Errorf("unsupported type name: %v", rt.TypeName)
	}
	return factory(), nil
}

// ConvertUInt128 converts an ir.UInt128Value to a protobuf UInt128Value
func ConvertUInt128(val *UInt128Value) *pb.UInt128Value {
	mask := new(big.Int)
	mask.SetString("FFFFFFFFFFFFFFFF", 16)

	low := new(big.Int).And(val.Value, mask)
	high := new(big.Int).Rsh(val.Value, 64)
	high.And(high, mask)

	return &pb.UInt128Value{
		Low:  low.Uint64(),
		High: high.Uint64(),
	}
}

// ConvertInt128 converts an ir.Int128Value to a protobuf Int128Value
func ConvertInt128(val *Int128Value) *pb.Int128Value {
	mask := new(big.Int)
	mask.SetString("FFFFFFFFFFFFFFFF", 16)

	low := new(big.Int).And(val.Value, mask)
	high := new(big.Int).Rsh(val.Value, 64)
	high.And(high, mask)

	return &pb.Int128Value{
		Low:  low.Uint64(),
		High: high.Uint64(),
	}
}

// ConvertDate converts an ir.DateValue to a protobuf DateValue
func ConvertDate(val *DateValue) *pb.DateValue {
	return &pb.DateValue{
		Year:  int32(val.Value.Year()),
		Month: int32(val.Value.Month()),
		Day:   int32(val.Value.Day()),
	}
}

// ConvertDateTime converts an ir.DateTimeValue to a protobuf DateTimeValue
func ConvertDateTime(val *DateTimeValue) *pb.DateTimeValue {
	return &pb.DateTimeValue{
		Year:        int32(val.Value.Year()),
		Month:       int32(val.Value.Month()),
		Day:         int32(val.Value.Day()),
		Hour:        int32(val.Value.Hour()),
		Minute:      int32(val.Value.Minute()),
		Second:      int32(val.Value.Second()),
		Microsecond: int32(val.Value.Nanosecond() / 1000),
	}
}

// ConvertDecimal converts an ir.DecimalValue to a protobuf DecimalValue
func ConvertDecimal(val *DecimalValue) *pb.DecimalValue {
	// The value is already stored as the physical representation in Int128
	int128Val := &Int128Value{
		Meta:  val.Meta,
		Value: val.Value,
	}

	return &pb.DecimalValue{
		Precision: val.Precision,
		Scale:     val.Scale,
		Value:     ConvertInt128(int128Val),
	}
}

// ConvertValue converts an ir.Value to a protobuf Value
func ConvertValue(pv *Value) (*pb.Value, error) {
	switch v := pv.Value.(type) {
	case StringValue:
		return &pb.Value{Value: &pb.Value_StringValue{StringValue: string(v)}}, nil
	case *MissingValue:
		return &pb.Value{Value: &pb.Value_MissingValue{MissingValue: &pb.MissingValue{}}}, nil
	case Int64Value:
		return &pb.Value{Value: &pb.Value_IntValue{IntValue: int64(v)}}, nil
	case Float64Value:
		return &pb.Value{Value: &pb.Value_FloatValue{FloatValue: float64(v)}}, nil
	case *UInt128Value:
		return &pb.Value{Value: &pb.Value_Uint128Value{Uint128Value: ConvertUInt128(v)}}, nil
	case *Int128Value:
		return &pb.Value{Value: &pb.Value_Int128Value{Int128Value: ConvertInt128(v)}}, nil
	case *DateValue:
		return &pb.Value{Value: &pb.Value_DateValue{DateValue: ConvertDate(v)}}, nil
	case *DateTimeValue:
		return &pb.Value{Value: &pb.Value_DatetimeValue{DatetimeValue: ConvertDateTime(v)}}, nil
	case *DecimalValue:
		return &pb.Value{Value: &pb.Value_DecimalValue{DecimalValue: ConvertDecimal(v)}}, nil
	case *BooleanValue:
		return &pb.Value{Value: &pb.Value_BooleanValue{BooleanValue: v.Value}}, nil
	default:
		return nil, fmt.Errorf("unsupported Value type: %T", v)
	}
}

// ConvertVar converts an ir.Var to a protobuf Var
func ConvertVar(v *Var) *pb.Var {
	return &pb.Var{Name: v.Name}
}

// ConvertTerm converts an ir.Term to a protobuf Term
func ConvertTerm(t Term) (*pb.Term, error) {
	switch term := t.(type) {
	case *Var:
		return &pb.Term{TermType: &pb.Term_Var{Var: ConvertVar(term)}}, nil
	case *Value:
		val, err := ConvertValue(term)
		if err != nil {
			return nil, err
		}
		return &pb.Term{TermType: &pb.Term_Constant{Constant: val}}, nil
	default:
		return nil, fmt.Errorf("unsupported Term type: %T", term)
	}
}

// ConvertRelTerm converts an ir.RelTerm to a protobuf RelTerm
func ConvertRelTerm(t RelTerm) (*pb.RelTerm, error) {
	switch relTerm := t.(type) {
	case *SpecializedValue:
		val, err := ConvertValue(relTerm.Value)
		if err != nil {
			return nil, err
		}
		return &pb.RelTerm{RelTermType: &pb.RelTerm_SpecializedValue{SpecializedValue: val}}, nil
	case Term:
		term, err := ConvertTerm(relTerm)
		if err != nil {
			return nil, err
		}
		return &pb.RelTerm{RelTermType: &pb.RelTerm_Term{Term: term}}, nil
	default:
		return nil, fmt.Errorf("unsupported RelTerm type: %T", relTerm)
	}
}

// ConvertRelationId converts an ir.RelationId to a protobuf RelationId
func ConvertRelationId(rid *RelationId) *pb.RelationId {
	mask := new(big.Int)
	mask.SetString("FFFFFFFFFFFFFFFF", 16)

	low := new(big.Int).And(rid.Id, mask)
	high := new(big.Int).Rsh(rid.Id, 64)
	high.And(high, mask)

	return &pb.RelationId{
		IdLow:  low.Uint64(),
		IdHigh: high.Uint64(),
	}
}

// ConvertFragmentId converts an ir.FragmentId to a protobuf FragmentId
func ConvertFragmentId(fid *FragmentId) *pb.FragmentId {
	return &pb.FragmentId{Id: fid.Id}
}

// ConvertAttribute converts an ir.Attribute to a protobuf Attribute
func ConvertAttribute(attr *Attribute) (*pb.Attribute, error) {
	args := make([]*pb.Value, len(attr.Args))
	for i, arg := range attr.Args {
		val, err := ConvertValue(arg)
		if err != nil {
			return nil, err
		}
		args[i] = val
	}
	return &pb.Attribute{Name: attr.Name, Args: args}, nil
}

// ConvertAbstraction converts an ir.Abstraction to a protobuf Abstraction
func ConvertAbstraction(abst *Abstraction) (*pb.Abstraction, error) {
	bindings := make([]*pb.Binding, len(abst.Vars))
	for i, binding := range abst.Vars {
		typ, err := ConvertType(binding.Type)
		if err != nil {
			return nil, err
		}
		bindings[i] = &pb.Binding{
			Var:  ConvertVar(binding.Var),
			Type: typ,
		}
	}

	formula, err := ConvertFormula(abst.Value)
	if err != nil {
		return nil, err
	}

	return &pb.Abstraction{
		Vars:  bindings,
		Value: formula,
	}, nil
}

// ConvertFormula converts an ir.Formula to a protobuf Formula
func ConvertFormula(f Formula) (*pb.Formula, error) {
	switch formula := f.(type) {
	case *Exists:
		body, err := ConvertAbstraction(formula.Body)
		if err != nil {
			return nil, err
		}
		return &pb.Formula{FormulaType: &pb.Formula_Exists{Exists: &pb.Exists{Body: body}}}, nil

	case *Reduce:
		op, err := ConvertAbstraction(formula.Op)
		if err != nil {
			return nil, err
		}
		body, err := ConvertAbstraction(formula.Body)
		if err != nil {
			return nil, err
		}
		terms := make([]*pb.Term, len(formula.Terms))
		for i, t := range formula.Terms {
			term, err := ConvertTerm(t)
			if err != nil {
				return nil, err
			}
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_Reduce{Reduce: &pb.Reduce{
			Op:    op,
			Body:  body,
			Terms: terms,
		}}}, nil

	case *Conjunction:
		args := make([]*pb.Formula, len(formula.Args))
		for i, arg := range formula.Args {
			f, err := ConvertFormula(arg)
			if err != nil {
				return nil, err
			}
			args[i] = f
		}
		return &pb.Formula{FormulaType: &pb.Formula_Conjunction{Conjunction: &pb.Conjunction{Args: args}}}, nil

	case *Disjunction:
		args := make([]*pb.Formula, len(formula.Args))
		for i, arg := range formula.Args {
			f, err := ConvertFormula(arg)
			if err != nil {
				return nil, err
			}
			args[i] = f
		}
		return &pb.Formula{FormulaType: &pb.Formula_Disjunction{Disjunction: &pb.Disjunction{Args: args}}}, nil

	case *Not:
		arg, err := ConvertFormula(formula.Arg)
		if err != nil {
			return nil, err
		}
		return &pb.Formula{FormulaType: &pb.Formula_Not{Not: &pb.Not{Arg: arg}}}, nil

	case *FFI:
		args := make([]*pb.Abstraction, len(formula.Args))
		for i, arg := range formula.Args {
			abst, err := ConvertAbstraction(arg)
			if err != nil {
				return nil, err
			}
			args[i] = abst
		}
		terms := make([]*pb.Term, len(formula.Terms))
		for i, t := range formula.Terms {
			term, err := ConvertTerm(t)
			if err != nil {
				return nil, err
			}
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_Ffi{Ffi: &pb.FFI{
			Name:  formula.Name,
			Args:  args,
			Terms: terms,
		}}}, nil

	case *Atom:
		terms := make([]*pb.Term, len(formula.Terms))
		for i, t := range formula.Terms {
			term, err := ConvertTerm(t)
			if err != nil {
				return nil, err
			}
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_Atom{Atom: &pb.Atom{
			Name:  ConvertRelationId(formula.Name),
			Terms: terms,
		}}}, nil

	case *Pragma:
		terms := make([]*pb.Term, len(formula.Terms))
		for i, t := range formula.Terms {
			term, err := ConvertTerm(t)
			if err != nil {
				return nil, err
			}
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_Pragma{Pragma: &pb.Pragma{
			Name:  formula.Name,
			Terms: terms,
		}}}, nil

	case *Primitive:
		terms := make([]*pb.RelTerm, len(formula.Terms))
		for i, t := range formula.Terms {
			term, err := ConvertRelTerm(t)
			if err != nil {
				return nil, err
			}
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_Primitive{Primitive: &pb.Primitive{
			Name:  formula.Name,
			Terms: terms,
		}}}, nil

	case *RelAtom:
		terms := make([]*pb.RelTerm, len(formula.Terms))
		for i, t := range formula.Terms {
			term, err := ConvertRelTerm(t)
			if err != nil {
				return nil, err
			}
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_RelAtom{RelAtom: &pb.RelAtom{
			Name:  formula.Name,
			Terms: terms,
		}}}, nil

	case *Cast:
		input, err := ConvertTerm(formula.Input)
		if err != nil {
			return nil, err
		}
		result, err := ConvertTerm(formula.Result)
		if err != nil {
			return nil, err
		}
		return &pb.Formula{FormulaType: &pb.Formula_Cast{Cast: &pb.Cast{
			Input:  input,
			Result: result,
		}}}, nil

	default:
		return nil, fmt.Errorf("unsupported Formula type: %T", formula)
	}
}

// ConvertDef converts an ir.Def to a protobuf Def
func ConvertDef(d *Def) (*pb.Def, error) {
	body, err := ConvertAbstraction(d.Body)
	if err != nil {
		return nil, err
	}
	attrs := make([]*pb.Attribute, len(d.Attrs))
	for i, attr := range d.Attrs {
		a, err := ConvertAttribute(attr)
		if err != nil {
			return nil, err
		}
		attrs[i] = a
	}
	return &pb.Def{
		Name:  ConvertRelationId(d.Name),
		Body:  body,
		Attrs: attrs,
	}, nil
}

// ConvertLoop converts an ir.Loop to a protobuf Loop
func ConvertLoop(l *Loop) (*pb.Loop, error) {
	init := make([]*pb.Instruction, len(l.Init))
	for i, instr := range l.Init {
		inst, err := ConvertInstruction(instr)
		if err != nil {
			return nil, err
		}
		init[i] = inst
	}
	body, err := ConvertScript(l.Body)
	if err != nil {
		return nil, err
	}
	return &pb.Loop{
		Init: init,
		Body: body,
	}, nil
}

// ConvertAlgorithm converts an ir.Algorithm to a protobuf Algorithm
func ConvertAlgorithm(algo *Algorithm) (*pb.Algorithm, error) {
	global := make([]*pb.RelationId, len(algo.Global))
	for i, rid := range algo.Global {
		global[i] = ConvertRelationId(rid)
	}
	body, err := ConvertScript(algo.Body)
	if err != nil {
		return nil, err
	}
	return &pb.Algorithm{
		Global: global,
		Body:   body,
	}, nil
}

// ConvertDeclaration converts an ir.Declaration to a protobuf Declaration
func ConvertDeclaration(decl Declaration) (*pb.Declaration, error) {
	switch d := decl.(type) {
	case *Def:
		def, err := ConvertDef(d)
		if err != nil {
			return nil, err
		}
		return &pb.Declaration{DeclarationType: &pb.Declaration_Def{Def: def}}, nil
	case *Algorithm:
		algo, err := ConvertAlgorithm(d)
		if err != nil {
			return nil, err
		}
		return &pb.Declaration{DeclarationType: &pb.Declaration_Algorithm{Algorithm: algo}}, nil
	default:
		return nil, fmt.Errorf("unsupported Declaration type: %T", decl)
	}
}

// ConvertAssign converts an ir.Assign to a protobuf Assign
func ConvertAssign(instr *Assign) (*pb.Assign, error) {
	body, err := ConvertAbstraction(instr.Body)
	if err != nil {
		return nil, err
	}
	attrs := make([]*pb.Attribute, len(instr.Attrs))
	for i, attr := range instr.Attrs {
		a, err := ConvertAttribute(attr)
		if err != nil {
			return nil, err
		}
		attrs[i] = a
	}
	return &pb.Assign{
		Name:  ConvertRelationId(instr.Name),
		Body:  body,
		Attrs: attrs,
	}, nil
}

// ConvertBreak converts an ir.Break to a protobuf Break
func ConvertBreak(instr *Break) (*pb.Break, error) {
	body, err := ConvertAbstraction(instr.Body)
	if err != nil {
		return nil, err
	}
	attrs := make([]*pb.Attribute, len(instr.Attrs))
	for i, attr := range instr.Attrs {
		a, err := ConvertAttribute(attr)
		if err != nil {
			return nil, err
		}
		attrs[i] = a
	}
	return &pb.Break{
		Name:  ConvertRelationId(instr.Name),
		Body:  body,
		Attrs: attrs,
	}, nil
}

// ConvertUpsert converts an ir.Upsert to a protobuf Upsert
func ConvertUpsert(instr *Upsert) (*pb.Upsert, error) {
	body, err := ConvertAbstraction(instr.Body)
	if err != nil {
		return nil, err
	}
	attrs := make([]*pb.Attribute, len(instr.Attrs))
	for i, attr := range instr.Attrs {
		a, err := ConvertAttribute(attr)
		if err != nil {
			return nil, err
		}
		attrs[i] = a
	}
	return &pb.Upsert{
		ValueArity: instr.ValueArity,
		Name:       ConvertRelationId(instr.Name),
		Body:       body,
		Attrs:      attrs,
	}, nil
}

// ConvertMonoid converts an ir.Monoid to a protobuf Monoid
func ConvertMonoid(monoid Monoid) (*pb.Monoid, error) {
	switch m := monoid.(type) {
	case *OrMonoid:
		return &pb.Monoid{Value: &pb.Monoid_OrMonoid{OrMonoid: &pb.OrMonoid{}}}, nil
	case *SumMonoid:
		typ, err := ConvertType(m.Type)
		if err != nil {
			return nil, err
		}
		return &pb.Monoid{Value: &pb.Monoid_SumMonoid{SumMonoid: &pb.SumMonoid{Type: typ}}}, nil
	case *MinMonoid:
		typ, err := ConvertType(m.Type)
		if err != nil {
			return nil, err
		}
		return &pb.Monoid{Value: &pb.Monoid_MinMonoid{MinMonoid: &pb.MinMonoid{Type: typ}}}, nil
	case *MaxMonoid:
		typ, err := ConvertType(m.Type)
		if err != nil {
			return nil, err
		}
		return &pb.Monoid{Value: &pb.Monoid_MaxMonoid{MaxMonoid: &pb.MaxMonoid{Type: typ}}}, nil
	default:
		return nil, fmt.Errorf("unsupported Monoid type: %T", monoid)
	}
}

// ConvertMonoidDef converts an ir.MonoidDef to a protobuf MonoidDef
func ConvertMonoidDef(instr *MonoidDef) (*pb.MonoidDef, error) {
	monoid, err := ConvertMonoid(instr.Monoid)
	if err != nil {
		return nil, err
	}
	body, err := ConvertAbstraction(instr.Body)
	if err != nil {
		return nil, err
	}
	attrs := make([]*pb.Attribute, len(instr.Attrs))
	for i, attr := range instr.Attrs {
		a, err := ConvertAttribute(attr)
		if err != nil {
			return nil, err
		}
		attrs[i] = a
	}
	return &pb.MonoidDef{
		ValueArity: instr.ValueArity,
		Monoid:     monoid,
		Name:       ConvertRelationId(instr.Name),
		Body:       body,
		Attrs:      attrs,
	}, nil
}

// ConvertMonusDef converts an ir.MonusDef to a protobuf MonusDef
func ConvertMonusDef(instr *MonusDef) (*pb.MonusDef, error) {
	monoid, err := ConvertMonoid(instr.Monoid)
	if err != nil {
		return nil, err
	}
	body, err := ConvertAbstraction(instr.Body)
	if err != nil {
		return nil, err
	}
	attrs := make([]*pb.Attribute, len(instr.Attrs))
	for i, attr := range instr.Attrs {
		a, err := ConvertAttribute(attr)
		if err != nil {
			return nil, err
		}
		attrs[i] = a
	}
	return &pb.MonusDef{
		ValueArity: instr.ValueArity,
		Monoid:     monoid,
		Name:       ConvertRelationId(instr.Name),
		Body:       body,
		Attrs:      attrs,
	}, nil
}

// ConvertInstruction converts an ir.Instruction to a protobuf Instruction
func ConvertInstruction(instr Instruction) (*pb.Instruction, error) {
	switch i := instr.(type) {
	case *Assign:
		assign, err := ConvertAssign(i)
		if err != nil {
			return nil, err
		}
		return &pb.Instruction{InstrType: &pb.Instruction_Assign{Assign: assign}}, nil
	case *Break:
		brk, err := ConvertBreak(i)
		if err != nil {
			return nil, err
		}
		return &pb.Instruction{InstrType: &pb.Instruction_Break{Break: brk}}, nil
	case *Upsert:
		upsert, err := ConvertUpsert(i)
		if err != nil {
			return nil, err
		}
		return &pb.Instruction{InstrType: &pb.Instruction_Upsert{Upsert: upsert}}, nil
	case *MonoidDef:
		monoidDef, err := ConvertMonoidDef(i)
		if err != nil {
			return nil, err
		}
		return &pb.Instruction{InstrType: &pb.Instruction_MonoidDef{MonoidDef: monoidDef}}, nil
	case *MonusDef:
		monusDef, err := ConvertMonusDef(i)
		if err != nil {
			return nil, err
		}
		return &pb.Instruction{InstrType: &pb.Instruction_MonusDef{MonusDef: monusDef}}, nil
	default:
		return nil, fmt.Errorf("unsupported Instruction type: %T", instr)
	}
}

// ConvertConstruct converts an ir.Construct to a protobuf Construct
func ConvertConstruct(construct Construct) (*pb.Construct, error) {
	switch c := construct.(type) {
	case *Loop:
		loop, err := ConvertLoop(c)
		if err != nil {
			return nil, err
		}
		return &pb.Construct{ConstructType: &pb.Construct_Loop{Loop: loop}}, nil
	case Instruction:
		instr, err := ConvertInstruction(c)
		if err != nil {
			return nil, err
		}
		return &pb.Construct{ConstructType: &pb.Construct_Instruction{Instruction: instr}}, nil
	default:
		return nil, fmt.Errorf("unsupported Construct type: %T", construct)
	}
}

// ConvertScript converts an ir.Script to a protobuf Script
func ConvertScript(script *Script) (*pb.Script, error) {
	constructs := make([]*pb.Construct, len(script.Constructs))
	for i, c := range script.Constructs {
		construct, err := ConvertConstruct(c)
		if err != nil {
			return nil, err
		}
		constructs[i] = construct
	}
	return &pb.Script{Constructs: constructs}, nil
}

// ConvertDebugInfo converts an ir.DebugInfo to a protobuf DebugInfo
func ConvertDebugInfo(info *DebugInfo) *pb.DebugInfo {
	ids := make([]*pb.RelationId, 0, len(info.IdToOrigName))
	origNames := make([]string, 0, len(info.IdToOrigName))

	for idStr, name := range info.IdToOrigName {
		// Parse the relation ID from string back to big.Int
		id := new(big.Int)
		id.SetString(idStr, 10)
		rid := &RelationId{Id: id}
		ids = append(ids, ConvertRelationId(rid))
		origNames = append(origNames, name)
	}

	return &pb.DebugInfo{
		Ids:       ids,
		OrigNames: origNames,
	}
}

// ConvertFragment converts an ir.Fragment to a protobuf Fragment
func ConvertFragment(frag *Fragment) (*pb.Fragment, error) {
	declarations := make([]*pb.Declaration, len(frag.Declarations))
	for i, decl := range frag.Declarations {
		d, err := ConvertDeclaration(decl)
		if err != nil {
			return nil, err
		}
		declarations[i] = d
	}

	return &pb.Fragment{
		Id:           ConvertFragmentId(frag.Id),
		Declarations: declarations,
		DebugInfo:    ConvertDebugInfo(frag.DebugInfo),
	}, nil
}

// --- Transaction Types ---

// ConvertDefine converts an ir.Define to a protobuf Define
func ConvertDefine(d *Define) (*pb.Define, error) {
	frag, err := ConvertFragment(d.Fragment)
	if err != nil {
		return nil, err
	}
	return &pb.Define{Fragment: frag}, nil
}

// ConvertUndefine converts an ir.Undefine to a protobuf Undefine
func ConvertUndefine(u *Undefine) *pb.Undefine {
	return &pb.Undefine{FragmentId: ConvertFragmentId(u.FragmentId)}
}

// ConvertContext converts an ir.Context to a protobuf Context
func ConvertContext(c *Context) *pb.Context {
	relations := make([]*pb.RelationId, len(c.Relations))
	for i, rid := range c.Relations {
		relations[i] = ConvertRelationId(rid)
	}
	return &pb.Context{Relations: relations}
}

// ConvertSync converts an ir.Sync to a protobuf Sync
func ConvertSync(s *Sync) *pb.Sync {
	fragments := make([]*pb.FragmentId, len(s.Fragments))
	for i, fid := range s.Fragments {
		fragments[i] = ConvertFragmentId(fid)
	}
	return &pb.Sync{Fragments: fragments}
}

// ConvertWrite converts an ir.Write to a protobuf Write
func ConvertWrite(w *Write) (*pb.Write, error) {
	switch wt := w.WriteType.(type) {
	case *Define:
		define, err := ConvertDefine(wt)
		if err != nil {
			return nil, err
		}
		return &pb.Write{WriteType: &pb.Write_Define{Define: define}}, nil
	case *Undefine:
		return &pb.Write{WriteType: &pb.Write_Undefine{Undefine: ConvertUndefine(wt)}}, nil
	case *Context:
		return &pb.Write{WriteType: &pb.Write_Context{Context: ConvertContext(wt)}}, nil
	case *Sync:
		return &pb.Write{WriteType: &pb.Write_Sync{Sync: ConvertSync(wt)}}, nil
	default:
		return nil, fmt.Errorf("unsupported Write type: %T", wt)
	}
}

// ConvertDemand converts an ir.Demand to a protobuf Demand
func ConvertDemand(d *Demand) *pb.Demand {
	return &pb.Demand{RelationId: ConvertRelationId(d.RelationId)}
}

// ConvertOutput converts an ir.Output to a protobuf Output
func ConvertOutput(o *Output) *pb.Output {
	result := &pb.Output{RelationId: ConvertRelationId(o.RelationId)}
	if o.Name != nil {
		result.Name = *o.Name
	}
	return result
}

// ConvertExportCSVColumn converts an ir.ExportCSVColumn to a protobuf ExportCSVColumn
func ConvertExportCSVColumn(ec *ExportCSVColumn) *pb.ExportCSVColumn {
	return &pb.ExportCSVColumn{
		ColumnName: ec.ColumnName,
		ColumnData: ConvertRelationId(ec.ColumnData),
	}
}

// ConvertExportConfig converts an ir.ExportCSVConfig to a protobuf ExportCSVConfig
func ConvertExportConfig(ec *ExportCSVConfig) *pb.ExportCSVConfig {
	dataColumns := make([]*pb.ExportCSVColumn, len(ec.DataColumns))
	for i, col := range ec.DataColumns {
		dataColumns[i] = ConvertExportCSVColumn(col)
	}

	result := &pb.ExportCSVConfig{
		Path:        ec.Path,
		DataColumns: dataColumns,
	}

	if ec.PartitionSize != nil {
		result.PartitionSize = ec.PartitionSize
	}
	if ec.Compression != nil {
		result.Compression = ec.Compression
	}
	if ec.SyntaxHeaderRow != nil {
		result.SyntaxHeaderRow = ec.SyntaxHeaderRow
	}
	if ec.SyntaxMissingString != nil {
		result.SyntaxMissingString = ec.SyntaxMissingString
	}
	if ec.SyntaxDelim != nil {
		result.SyntaxDelim = ec.SyntaxDelim
	}
	if ec.SyntaxQuotechar != nil {
		result.SyntaxQuotechar = ec.SyntaxQuotechar
	}
	if ec.SyntaxEscapechar != nil {
		result.SyntaxEscapechar = ec.SyntaxEscapechar
	}

	return result
}

// ConvertExport converts an ir.Export to a protobuf Export
func ConvertExport(e *Export) *pb.Export {
	return &pb.Export{
		ExportConfig: &pb.Export_CsvConfig{CsvConfig: ConvertExportConfig(e.Config)},
	}
}

// ConvertAbort converts an ir.Abort to a protobuf Abort
func ConvertAbort(a *Abort) *pb.Abort {
	result := &pb.Abort{RelationId: ConvertRelationId(a.RelationId)}
	if a.Name != nil {
		result.Name = *a.Name
	}
	return result
}

// ConvertEpoch converts an ir.Epoch to a protobuf Epoch
func ConvertEpoch(e *Epoch) (*pb.Epoch, error) {
	writes := make([]*pb.Write, len(e.Writes))
	for i, w := range e.Writes {
		write, err := ConvertWrite(w)
		if err != nil {
			return nil, err
		}
		writes[i] = write
	}

	reads := make([]*pb.Read, len(e.Reads))
	for i, r := range e.Reads {
		read, err := ConvertRead(r)
		if err != nil {
			return nil, err
		}
		reads[i] = read
	}

	return &pb.Epoch{
		Writes: writes,
		Reads:  reads,
	}, nil
}

// ConvertWhatIf converts an ir.WhatIf to a protobuf WhatIf
func ConvertWhatIf(wi *WhatIf) (*pb.WhatIf, error) {
	epoch, err := ConvertEpoch(wi.Epoch)
	if err != nil {
		return nil, err
	}
	result := &pb.WhatIf{Epoch: epoch}
	if wi.Branch != nil {
		result.Branch = *wi.Branch
	}
	return result, nil
}

// ConvertRead converts an ir.Read to a protobuf Read
func ConvertRead(r *Read) (*pb.Read, error) {
	switch rt := r.ReadType.(type) {
	case *Demand:
		return &pb.Read{ReadType: &pb.Read_Demand{Demand: ConvertDemand(rt)}}, nil
	case *Output:
		return &pb.Read{ReadType: &pb.Read_Output{Output: ConvertOutput(rt)}}, nil
	case *WhatIf:
		whatIf, err := ConvertWhatIf(rt)
		if err != nil {
			return nil, err
		}
		return &pb.Read{ReadType: &pb.Read_WhatIf{WhatIf: whatIf}}, nil
	case *Abort:
		return &pb.Read{ReadType: &pb.Read_Abort{Abort: ConvertAbort(rt)}}, nil
	case *Export:
		return &pb.Read{ReadType: &pb.Read_Export{Export: ConvertExport(rt)}}, nil
	default:
		return nil, fmt.Errorf("unsupported Read type: %T", rt)
	}
}

// ConvertMaintenanceLevel converts an ir.MaintenanceLevel to a protobuf MaintenanceLevel
func ConvertMaintenanceLevel(l MaintenanceLevel) pb.MaintenanceLevel {
	switch l {
	case MaintenanceLevelUnspecified:
		return pb.MaintenanceLevel_MAINTENANCE_LEVEL_UNSPECIFIED
	case MaintenanceLevelOff:
		return pb.MaintenanceLevel_MAINTENANCE_LEVEL_OFF
	case MaintenanceLevelAuto:
		return pb.MaintenanceLevel_MAINTENANCE_LEVEL_AUTO
	case MaintenanceLevelAll:
		return pb.MaintenanceLevel_MAINTENANCE_LEVEL_ALL
	default:
		return pb.MaintenanceLevel_MAINTENANCE_LEVEL_UNSPECIFIED
	}
}

// ConvertIVMConfig converts an ir.IVMConfig to a protobuf IVMConfig
func ConvertIVMConfig(c *IVMConfig) *pb.IVMConfig {
	return &pb.IVMConfig{
		Level: ConvertMaintenanceLevel(c.Level),
	}
}

// ConvertConfigure converts an ir.Configure to a protobuf Configure
func ConvertConfigure(c *Configure) *pb.Configure {
	return &pb.Configure{
		SemanticsVersion: c.SemanticsVersion,
		IvmConfig:        ConvertIVMConfig(c.IvmConfig),
	}
}

// ConvertTransaction converts an ir.Transaction to a protobuf Transaction
func ConvertTransaction(t *Transaction) (*pb.Transaction, error) {
	epochs := make([]*pb.Epoch, len(t.Epochs))
	for i, e := range t.Epochs {
		epoch, err := ConvertEpoch(e)
		if err != nil {
			return nil, err
		}
		epochs[i] = epoch
	}

	return &pb.Transaction{
		Configure: ConvertConfigure(t.Configure),
		Epochs:    epochs,
	}, nil
}

// IrToProto converts a top-level IR node to its corresponding protobuf message
func IrToProto(node LqpNode) (interface{}, error) {
	switch n := node.(type) {
	case *Transaction:
		return ConvertTransaction(n)
	case *Fragment:
		return ConvertFragment(n)
	case Declaration:
		return ConvertDeclaration(n)
	case Formula:
		return ConvertFormula(n)
	default:
		return nil, fmt.Errorf("unsupported top-level IR node type for conversion: %T", node)
	}
}
