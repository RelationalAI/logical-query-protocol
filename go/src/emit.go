package lqp

import (
	"fmt"
	"math/big"

	pb "logical-query-protocol/src/relationalai/lqp/v1"
)

// Maps ir.TypeNames to the associated Proto message for *non-parametric types*.
// Parametric types should be handled in ConvertType
// Difference from Python: it returns a thunk of the ProtoBuf type to avoid
// accidental sharing of the same value, which Python avoids automatically.
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
func ConvertType(rt *Type) *pb.Type {
	if rt.TypeName == TypeNameDecimal {
		if len(rt.Parameters) != 2 {
			panic(fmt.Sprintf("DECIMAL parameters should have only precision and scale, got %d arguments", len(rt.Parameters)))
		}

		precision, ok := rt.Parameters[0].Value.(Int64Value)
		if !ok {
			panic("DECIMAL precision parameter is not an integer")
		}
		scale, ok := rt.Parameters[1].Value.(Int64Value)
		if !ok {
			panic("DECIMAL scale parameter is not an integer")
		}

		if precision > 38 {
			panic(fmt.Sprintf("DECIMAL precision must be less than 38, got %d", precision))
		}
		if scale > precision {
			panic(fmt.Sprintf("DECIMAL precision (%d) must be at least scale (%d)", precision, scale))
		}

		return &pb.Type{
			Type: &pb.Type_DecimalType{
				DecimalType: &pb.DecimalType{
					Precision: int32(precision),
					Scale:     int32(scale),
				},
			},
		}
	}

	factory, ok := nonParametricTypes[rt.TypeName]
	if !ok {
		panic(fmt.Sprintf("unsupported type name: %v", rt.TypeName))
	}
	return factory()
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

func ConvertDate(val *DateValue) *pb.DateValue {
	return &pb.DateValue{
		Year:  int32(val.Value.Year()),
		Month: int32(val.Value.Month()),
		Day:   int32(val.Value.Day()),
	}
}

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

func ConvertDecimal(val *DecimalValue) *pb.DecimalValue {
	// In Python, value is a tuple of digits that need to be reinterpreted as int.
	// In Go, we represent it as an int already.
	value := new(big.Int).Set(val.Value.Coefficient)

	// Adjust value by the exponent. Python's decimal values are (sign, coefficient, exponent),
	// so if we have coefficient 12300 with exponent -4, but we need `scale` of 6, then we need to
	// multiply the coefficient by 10 ** 2 (i.e., 10 ** (6 + -4)) to get the physical value of
	// 1230000.
	// Ensure we stay in the integer realm when the exponent outweighs the scale, e.g.
	// value = 4.4000000000000003552713678800500929355621337890625
	modifier := int(val.Scale) + val.Value.Exponent
	if modifier >= 0 {
		multiplier := new(big.Int).Exp(big.NewInt(10), big.NewInt(int64(modifier)), nil)
		value.Mul(value, multiplier)
	} else {
		divisor := new(big.Int).Exp(big.NewInt(10), big.NewInt(int64(-modifier)), nil)
		value.Div(value, divisor)
	}

	if val.Value.Sign == 1 {
		value.Neg(value)
	}

	int128Val := &Int128Value{
		Meta:  val.Meta,
		Value: value,
	}

	return &pb.DecimalValue{
		Precision: val.Precision,
		Scale:     val.Scale,
		Value:     ConvertInt128(int128Val),
	}
}

func ConvertValue(pv *Value) *pb.Value {
	switch v := pv.Value.(type) {
	case StringValue:
		return &pb.Value{Value: &pb.Value_StringValue{StringValue: string(v)}}
	case Int64Value:
		return &pb.Value{Value: &pb.Value_IntValue{IntValue: int64(v)}}
	case Float64Value:
		return &pb.Value{Value: &pb.Value_FloatValue{FloatValue: float64(v)}}
	case *MissingValue:
		return &pb.Value{Value: &pb.Value_MissingValue{MissingValue: &pb.MissingValue{}}}
	case *UInt128Value:
		return &pb.Value{Value: &pb.Value_Uint128Value{Uint128Value: ConvertUInt128(v)}}
	case *Int128Value:
		return &pb.Value{Value: &pb.Value_Int128Value{Int128Value: ConvertInt128(v)}}
	case *DateValue:
		return &pb.Value{Value: &pb.Value_DateValue{DateValue: ConvertDate(v)}}
	case *DateTimeValue:
		return &pb.Value{Value: &pb.Value_DatetimeValue{DatetimeValue: ConvertDateTime(v)}}
	case *DecimalValue:
		return &pb.Value{Value: &pb.Value_DecimalValue{DecimalValue: ConvertDecimal(v)}}
	case *BooleanValue:
		return &pb.Value{Value: &pb.Value_BooleanValue{BooleanValue: v.Value}}
	}
	panic(fmt.Sprintf("Unsupported Value type: %T", pv.Value))
}

func ConvertVar(v *Var) *pb.Var {
	return &pb.Var{Name: v.Name}
}

func ConvertTerm(t Term) *pb.Term {
	switch term := t.(type) {
	case *Var:
		return &pb.Term{TermType: &pb.Term_Var{Var: ConvertVar(term)}}
	case *Value:
		val := ConvertValue(term)
		return &pb.Term{TermType: &pb.Term_Constant{Constant: val}}
	}
	panic(fmt.Sprintf("Unsupported Term type: %T", t))
}

func ConvertRelTerm(t RelTerm) *pb.RelTerm {
	switch relTerm := t.(type) {
	case *SpecializedValue:
		val := ConvertValue(relTerm.Value)
		return &pb.RelTerm{RelTermType: &pb.RelTerm_SpecializedValue{SpecializedValue: val}}
	case Term:
		term := ConvertTerm(relTerm)
		return &pb.RelTerm{RelTermType: &pb.RelTerm_Term{Term: term}}
	}
	panic(fmt.Sprintf("unsupported RelTerm type: %T", t))
}

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

func ConvertFragmentId(fid *FragmentId) *pb.FragmentId {
	return &pb.FragmentId{Id: fid.Id}
}

func ConvertAttribute(attr *Attribute) *pb.Attribute {
	args := make([]*pb.Value, len(attr.Args))
	for i, arg := range attr.Args {
		val := ConvertValue(arg)
		args[i] = val
	}
	return &pb.Attribute{Name: attr.Name, Args: args}
}

func ConvertAbstraction(abst *Abstraction) *pb.Abstraction {
	bindings := make([]*pb.Binding, len(abst.Vars))
	for i, binding := range abst.Vars {
		bindings[i] = &pb.Binding{
			Var:  ConvertVar(binding.Var),
			Type: ConvertType(binding.Type),
		}
	}

	return &pb.Abstraction{
		Vars:  bindings,
		Value: ConvertFormula(abst.Value),
	}
}

func ConvertFormula(f Formula) *pb.Formula {
	switch formula := f.(type) {
	case *Exists:
		body := ConvertAbstraction(formula.Body)
		return &pb.Formula{FormulaType: &pb.Formula_Exists{Exists: &pb.Exists{Body: body}}}
	case *Reduce:
		op := ConvertAbstraction(formula.Op)
		body := ConvertAbstraction(formula.Body)
		terms := make([]*pb.Term, len(formula.Terms))
		for i, t := range formula.Terms {
			term := ConvertTerm(t)
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_Reduce{Reduce: &pb.Reduce{
			Op:    op,
			Body:  body,
			Terms: terms,
		}}}
	case *Conjunction:
		args := make([]*pb.Formula, len(formula.Args))
		for i, arg := range formula.Args {
			f := ConvertFormula(arg)
			args[i] = f
		}
		return &pb.Formula{FormulaType: &pb.Formula_Conjunction{Conjunction: &pb.Conjunction{Args: args}}}
	case *Disjunction:
		args := make([]*pb.Formula, len(formula.Args))
		for i, arg := range formula.Args {
			f := ConvertFormula(arg)
			args[i] = f
		}
		return &pb.Formula{FormulaType: &pb.Formula_Disjunction{Disjunction: &pb.Disjunction{Args: args}}}
	case *Not:
		arg := ConvertFormula(formula.Arg)
		return &pb.Formula{FormulaType: &pb.Formula_Not{Not: &pb.Not{Arg: arg}}}
	case *FFI:
		args := make([]*pb.Abstraction, len(formula.Args))
		for i, arg := range formula.Args {
			abst := ConvertAbstraction(arg)
			args[i] = abst
		}
		terms := make([]*pb.Term, len(formula.Terms))
		for i, t := range formula.Terms {
			term := ConvertTerm(t)
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_Ffi{Ffi: &pb.FFI{
			Name:  formula.Name,
			Args:  args,
			Terms: terms,
		}}}
	case *Atom:
		terms := make([]*pb.Term, len(formula.Terms))
		for i, t := range formula.Terms {
			term := ConvertTerm(t)
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_Atom{Atom: &pb.Atom{
			Name:  ConvertRelationId(formula.Name),
			Terms: terms,
		}}}
	case *Pragma:
		terms := make([]*pb.Term, len(formula.Terms))
		for i, t := range formula.Terms {
			term := ConvertTerm(t)
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_Pragma{Pragma: &pb.Pragma{
			Name:  formula.Name,
			Terms: terms,
		}}}
	case *Primitive:
		terms := make([]*pb.RelTerm, len(formula.Terms))
		for i, t := range formula.Terms {
			term := ConvertRelTerm(t)
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_Primitive{Primitive: &pb.Primitive{
			Name:  formula.Name,
			Terms: terms,
		}}}
	case *RelAtom:
		terms := make([]*pb.RelTerm, len(formula.Terms))
		for i, t := range formula.Terms {
			term := ConvertRelTerm(t)
			terms[i] = term
		}
		return &pb.Formula{FormulaType: &pb.Formula_RelAtom{RelAtom: &pb.RelAtom{
			Name:  formula.Name,
			Terms: terms,
		}}}
	case *Cast:
		input := ConvertTerm(formula.Input)
		result := ConvertTerm(formula.Result)
		return &pb.Formula{FormulaType: &pb.Formula_Cast{Cast: &pb.Cast{
			Input:  input,
			Result: result,
		}}}
	}
	panic(fmt.Sprintf("unsupported Formula type: %T", f))
}

func ConvertDef(d *Def) *pb.Def {
	body := ConvertAbstraction(d.Body)
	attrs := make([]*pb.Attribute, len(d.Attrs))
	for i, attr := range d.Attrs {
		a := ConvertAttribute(attr)
		attrs[i] = a
	}
	return &pb.Def{
		Name:  ConvertRelationId(d.Name),
		Body:  body,
		Attrs: attrs,
	}
}

func ConvertLoop(l *Loop) *pb.Loop {
	init := make([]*pb.Instruction, len(l.Init))
	for i, instr := range l.Init {
		inst := ConvertInstruction(instr)
		init[i] = inst
	}
	body := ConvertScript(l.Body)
	return &pb.Loop{
		Init: init,
		Body: body,
	}
}

func ConvertDeclaration(decl Declaration) *pb.Declaration {
	switch d := decl.(type) {
	case *Def:
		def := ConvertDef(d)
		return &pb.Declaration{DeclarationType: &pb.Declaration_Def{Def: def}}
	case *Algorithm:
		algo := ConvertAlgorithm(d)
		return &pb.Declaration{DeclarationType: &pb.Declaration_Algorithm{Algorithm: algo}}
	case *FunctionalDependency:
		constraint := ConvertConstraint(d)
		return &pb.Declaration{DeclarationType: &pb.Declaration_Constraint{Constraint: constraint}}
	}
	panic(fmt.Sprintf("unsupported Declaration type: %T", decl))
}

func ConvertConstraint(constraint Constraint) *pb.Constraint {
	switch c := constraint.(type) {
	case *FunctionalDependency:
		return &pb.Constraint{
			ConstraintType: &pb.Constraint_FunctionalDependency{
				FunctionalDependency: ConvertFunctionalDependency(c),
			},
		}
	}
	panic(fmt.Sprintf("unsupported Constraint type: %T", constraint))
}

func ConvertFunctionalDependency(fd *FunctionalDependency) *pb.FunctionalDependency {
	keys := make([]*pb.Var, len(fd.Keys))
	for i, k := range fd.Keys {
		keys[i] = ConvertVar(k)
	}
	values := make([]*pb.Var, len(fd.Values))
	for i, v := range fd.Values {
		values[i] = ConvertVar(v)
	}
	return &pb.FunctionalDependency{
		Guard:  ConvertAbstraction(fd.Guard),
		Keys:   keys,
		Values: values,
	}
}

func ConvertAlgorithm(algo *Algorithm) *pb.Algorithm {
	global := make([]*pb.RelationId, len(algo.Global))
	for i, rid := range algo.Global {
		global[i] = ConvertRelationId(rid)
	}
	body := ConvertScript(algo.Body)
	return &pb.Algorithm{
		Global: global,
		Body:   body,
	}
}

func ConvertInstruction(instr Instruction) *pb.Instruction {
	switch i := instr.(type) {
	case *Assign:
		assign := ConvertAssign(i)
		return &pb.Instruction{InstrType: &pb.Instruction_Assign{Assign: assign}}
	case *Break:
		brk := ConvertBreak(i)
		return &pb.Instruction{InstrType: &pb.Instruction_Break{Break: brk}}
	case *Upsert:
		upsert := ConvertUpsert(i)
		return &pb.Instruction{InstrType: &pb.Instruction_Upsert{Upsert: upsert}}
	case *MonoidDef:
		monoidDef := ConvertMonoidDef(i)
		return &pb.Instruction{InstrType: &pb.Instruction_MonoidDef{MonoidDef: monoidDef}}
	case *MonusDef:
		monusDef := ConvertMonusDef(i)
		return &pb.Instruction{InstrType: &pb.Instruction_MonusDef{MonusDef: monusDef}}
	}
	panic(fmt.Sprintf("unsupported Instruction type: %T", instr))
}

func ConvertAssign(instr *Assign) *pb.Assign {
	body := ConvertAbstraction(instr.Body)
	attrs := make([]*pb.Attribute, len(instr.Attrs))
	for i, attr := range instr.Attrs {
		a := ConvertAttribute(attr)
		attrs[i] = a
	}
	return &pb.Assign{
		Name:  ConvertRelationId(instr.Name),
		Body:  body,
		Attrs: attrs,
	}
}

func ConvertBreak(instr *Break) *pb.Break {
	body := ConvertAbstraction(instr.Body)
	attrs := make([]*pb.Attribute, len(instr.Attrs))
	for i, attr := range instr.Attrs {
		a := ConvertAttribute(attr)
		attrs[i] = a
	}
	return &pb.Break{
		Name:  ConvertRelationId(instr.Name),
		Body:  body,
		Attrs: attrs,
	}
}

func ConvertUpsert(instr *Upsert) *pb.Upsert {
	body := ConvertAbstraction(instr.Body)
	attrs := make([]*pb.Attribute, len(instr.Attrs))
	for i, attr := range instr.Attrs {
		a := ConvertAttribute(attr)
		attrs[i] = a
	}
	return &pb.Upsert{
		ValueArity: instr.ValueArity,
		Name:       ConvertRelationId(instr.Name),
		Body:       body,
		Attrs:      attrs,
	}
}

func ConvertMonoidDef(instr *MonoidDef) *pb.MonoidDef {
	monoid := ConvertMonoid(instr.Monoid)
	body := ConvertAbstraction(instr.Body)
	attrs := make([]*pb.Attribute, len(instr.Attrs))
	for i, attr := range instr.Attrs {
		a := ConvertAttribute(attr)
		attrs[i] = a
	}
	return &pb.MonoidDef{
		ValueArity: instr.ValueArity,
		Monoid:     monoid,
		Name:       ConvertRelationId(instr.Name),
		Body:       body,
		Attrs:      attrs,
	}
}

func ConvertMonusDef(instr *MonusDef) *pb.MonusDef {
	monoid := ConvertMonoid(instr.Monoid)
	body := ConvertAbstraction(instr.Body)
	attrs := make([]*pb.Attribute, len(instr.Attrs))
	for i, attr := range instr.Attrs {
		a := ConvertAttribute(attr)
		attrs[i] = a
	}
	return &pb.MonusDef{
		ValueArity: instr.ValueArity,
		Monoid:     monoid,
		Name:       ConvertRelationId(instr.Name),
		Body:       body,
		Attrs:      attrs,
	}
}

func ConvertMonoid(monoid Monoid) *pb.Monoid {
	switch m := monoid.(type) {
	case *OrMonoid:
		return &pb.Monoid{Value: &pb.Monoid_OrMonoid{OrMonoid: &pb.OrMonoid{}}}
	case *SumMonoid:
		typ := ConvertType(m.Type)
		return &pb.Monoid{Value: &pb.Monoid_SumMonoid{SumMonoid: &pb.SumMonoid{Type: typ}}}
	case *MinMonoid:
		typ := ConvertType(m.Type)
		return &pb.Monoid{Value: &pb.Monoid_MinMonoid{MinMonoid: &pb.MinMonoid{Type: typ}}}
	case *MaxMonoid:
		typ := ConvertType(m.Type)
		return &pb.Monoid{Value: &pb.Monoid_MaxMonoid{MaxMonoid: &pb.MaxMonoid{Type: typ}}}
	}
	panic(fmt.Sprintf("unsupported Monoid type: %T", monoid))
}

func ConvertScript(script *Script) *pb.Script {
	constructs := make([]*pb.Construct, len(script.Constructs))
	for i, c := range script.Constructs {
		construct := ConvertConstruct(c)
		constructs[i] = construct
	}
	return &pb.Script{Constructs: constructs}
}

func ConvertConstruct(construct Construct) *pb.Construct {
	switch c := construct.(type) {
	case *Loop:
		loop := ConvertLoop(c)
		return &pb.Construct{ConstructType: &pb.Construct_Loop{Loop: loop}}
	case Instruction:
		instr := ConvertInstruction(c)
		return &pb.Construct{ConstructType: &pb.Construct_Instruction{Instruction: instr}}
	}
	panic(fmt.Sprintf("unsupported Construct type: %T", construct))
}

func ConvertFragment(frag *Fragment) *pb.Fragment {
	declarations := make([]*pb.Declaration, len(frag.Declarations))
	for i, decl := range frag.Declarations {
		d := ConvertDeclaration(decl)
		declarations[i] = d
	}
	return &pb.Fragment{
		Id:           ConvertFragmentId(frag.Id),
		Declarations: declarations,
		DebugInfo:    ConvertDebugInfo(frag.DebugInfo),
	}
}

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

func ConvertDefine(d *Define) *pb.Define {
	frag := ConvertFragment(d.Fragment)
	return &pb.Define{Fragment: frag}
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
func ConvertWrite(w *Write) *pb.Write {
	switch wt := w.WriteType.(type) {
	case *Define:
		define := ConvertDefine(wt)
		return &pb.Write{WriteType: &pb.Write_Define{Define: define}}
	case *Undefine:
		return &pb.Write{WriteType: &pb.Write_Undefine{Undefine: ConvertUndefine(wt)}}
	case *Context:
		return &pb.Write{WriteType: &pb.Write_Context{Context: ConvertContext(wt)}}
	case *Sync:
		return &pb.Write{WriteType: &pb.Write_Sync{Sync: ConvertSync(wt)}}
	}
	panic(fmt.Sprintf("unsupported Write type: %T", w.WriteType))
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

func ConvertExport(e *Export) *pb.Export {
	return &pb.Export{
		ExportConfig: &pb.Export_CsvConfig{CsvConfig: ConvertExportConfig(e.Config)},
	}
}

func ConvertExportCSVColumn(ec *ExportCSVColumn) *pb.ExportCSVColumn {
	return &pb.ExportCSVColumn{
		ColumnName: ec.ColumnName,
		ColumnData: ConvertRelationId(ec.ColumnData),
	}
}

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
	} else {
		partitionSize := int64(0)
		result.PartitionSize = &partitionSize
	}

	if ec.Compression != nil {
		result.Compression = ec.Compression
	} else {
		compression := ""
		result.Compression = &compression
	}

	if ec.SyntaxHeaderRow != nil {
		result.SyntaxHeaderRow = ec.SyntaxHeaderRow
	} else {
		syntaxHeaderRow := true
		result.SyntaxHeaderRow = &syntaxHeaderRow
	}

	if ec.SyntaxMissingString != nil {
		result.SyntaxMissingString = ec.SyntaxMissingString
	} else {
		syntaxMissingString := ""
		result.SyntaxMissingString = &syntaxMissingString
	}

	if ec.SyntaxDelim != nil {
		result.SyntaxDelim = ec.SyntaxDelim
	} else {
		syntaxDelim := ","
		result.SyntaxDelim = &syntaxDelim
	}

	if ec.SyntaxQuotechar != nil {
		result.SyntaxQuotechar = ec.SyntaxQuotechar
	} else {
		syntaxQuotechar := "\""
		result.SyntaxQuotechar = &syntaxQuotechar
	}

	if ec.SyntaxEscapechar != nil {
		result.SyntaxEscapechar = ec.SyntaxEscapechar
	} else {
		syntaxEscapechar := "\\"
		result.SyntaxEscapechar = &syntaxEscapechar
	}

	return result
}

func ConvertAbort(a *Abort) *pb.Abort {
	result := &pb.Abort{RelationId: ConvertRelationId(a.RelationId)}
	if a.Name != nil {
		result.Name = *a.Name
	}
	return result
}

func ConvertWhatIf(wi *WhatIf) *pb.WhatIf {
	epoch := ConvertEpoch(wi.Epoch)
	result := &pb.WhatIf{Epoch: epoch}
	if wi.Branch != nil {
		result.Branch = *wi.Branch
	}
	return result
}

func ConvertRead(r *Read) *pb.Read {
	switch rt := r.ReadType.(type) {
	case *Demand:
		return &pb.Read{ReadType: &pb.Read_Demand{Demand: ConvertDemand(rt)}}
	case *Output:
		return &pb.Read{ReadType: &pb.Read_Output{Output: ConvertOutput(rt)}}
	case *WhatIf:
		whatIf := ConvertWhatIf(rt)
		return &pb.Read{ReadType: &pb.Read_WhatIf{WhatIf: whatIf}}
	case *Abort:
		return &pb.Read{ReadType: &pb.Read_Abort{Abort: ConvertAbort(rt)}}
	case *Export:
		return &pb.Read{ReadType: &pb.Read_Export{Export: ConvertExport(rt)}}
	}
	panic(fmt.Sprintf("unsupported Read type: %T", r.ReadType))
}

func ConvertEpoch(e *Epoch) *pb.Epoch {
	writes := make([]*pb.Write, len(e.Writes))
	for i, w := range e.Writes {
		write := ConvertWrite(w)
		writes[i] = write
	}

	reads := make([]*pb.Read, len(e.Reads))
	for i, r := range e.Reads {
		read := ConvertRead(r)
		reads[i] = read
	}

	return &pb.Epoch{
		Writes: writes,
		Reads:  reads,
	}
}

func ConvertConfigure(c *Configure) *pb.Configure {
	return &pb.Configure{
		SemanticsVersion: c.SemanticsVersion,
		IvmConfig:        ConvertIVMConfig(c.IvmConfig),
	}
}

func ConvertIVMConfig(c *IVMConfig) *pb.IVMConfig {
	return &pb.IVMConfig{
		Level: ConvertMaintenanceLevel(c.Level),
	}
}

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
	}
	panic(fmt.Sprintf("unsupported MaintenanceLevel: %v", l))
}

func ConvertTransaction(t *Transaction) *pb.Transaction {
	epochs := make([]*pb.Epoch, len(t.Epochs))
	for i, e := range t.Epochs {
		epoch := ConvertEpoch(e)
		epochs[i] = epoch
	}

	return &pb.Transaction{
		Configure: ConvertConfigure(t.Configure),
		Epochs:    epochs,
	}
}

func IrToProto(node LqpNode) interface{} {
	switch n := node.(type) {
	case *Transaction:
		return ConvertTransaction(n)
	case *Fragment:
		return ConvertFragment(n)
	case Declaration:
		return ConvertDeclaration(n)
	case Formula:
		return ConvertFormula(n)
	}
	panic(fmt.Sprintf("unsupported top-level IR node type for conversion: %T", node))
}
