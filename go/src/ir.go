package lqp

import (
	"crypto/sha256"
	"math/big"
	"time"
)

var _ = sha256.Sum256 // Ensure sha256 is used

// --- Transaction Types ---

// Transaction(epochs::Epoch[], configure::Configure)
type Transaction struct {
	Configure *Configure
	Sync      *Sync
	Epochs    []*Epoch
}

// Sync(fragments::FragmentId[])
type Sync struct {
	Fragments []*FragmentId
}

// Configure(semantics_version::int, ivm_config::IVMConfig)
type Configure struct {
	SemanticsVersion int64
	IvmConfig        *IVMConfig
}

// IVMConfig(level::MaintenanceLevel)
type IVMConfig struct {
	Level MaintenanceLevel
}

type MaintenanceLevel int

const (
	MaintenanceLevelUnspecified MaintenanceLevel = iota
	MaintenanceLevelOff
	MaintenanceLevelAuto
	MaintenanceLevelAll
)

// Epoch(writes::Write[], reads::Read[])
type Epoch struct {
	Writes []*Write
	Reads  []*Read
}

type WriteType interface {
	LqpNode
	isWriteType()
}

// Write := Define | Undefine | Context
type Write struct {
	WriteType WriteType
}

type ReadType interface {
	LqpNode
	isReadType()
}

// Read := Demand | Output | Export | WhatIf | Abort
type Read struct {
	ReadType ReadType
}

// Define(fragment::Fragment)
type Define struct {
	Fragment *Fragment
}

func (d *Define) isWriteType() {}

// Undefine(fragment_id::FragmentId)
type Undefine struct {
	FragmentId *FragmentId
}

func (u *Undefine) isWriteType() {}

// Context(relations::RelationId[])
type Context struct {
	Relations []*RelationId
}

func (c *Context) isWriteType() {}

// Demand(relation_id::RelationId)
type Demand struct {
	RelationId *RelationId
}

func (d *Demand) isReadType() {}

// Output(name::string?, relation_id::RelationId)
type Output struct {
	Name       *string
	RelationId *RelationId
}

func (o *Output) isReadType() {}

// ExportCSVConfig
type ExportCSVConfig struct {
	Path        string
	DataColumns []*ExportCSVColumn

	PartitionSize       *int64
	Compression         *string
	SyntaxHeaderRow     *bool
	SyntaxMissingString *string
	SyntaxDelim         *string
	SyntaxQuotechar     *string
	SyntaxEscapechar    *string
}

type ExportCSVColumn struct {
	ColumnName string
	ColumnData *RelationId
}

// Export(name::string, relation_id::RelationId)
type Export struct {
	Config *ExportCSVConfig
}

func (e *Export) isReadType() {}

// Abort(name::string?, relation_id::RelationId)
type Abort struct {
	Name       *string
	RelationId *RelationId
}

func (a *Abort) isReadType() {}

// WhatIf(branch::string?, epoch::Epoch)
type WhatIf struct {
	Branch *string
	Epoch  *Epoch
}

func (w *WhatIf) isReadType() {}

// --- Fragment Types ---

// FragmentId(id::bytes)
type FragmentId struct {
	Id []byte
}

// Fragment(id::FragmentId, declarations::Declaration[], debug_info::DebugInfo)
type Fragment struct {
	Id           *FragmentId
	Declarations []Declaration
	DebugInfo    *DebugInfo
}

// We can't have map[*RelationId]string (mirroring Python, Julia)
// because the same RelationId at different locations are represented
// as different pointers to memory. So instead we use the string conv.
type DebugInfo struct {
	IdToOrigName map[string]string
}

// --- Logic Types ---

type LqpNode interface{}

// Declaration := Def | Algorithm | Constraint
type Declaration interface {
	LqpNode
	isDeclaration()
}

// Constraint := FunctionalDependency
type Constraint interface {
	Declaration
	isConstraint()
}

// FunctionalDependency(guard::Abstraction, x::Var[], y::Var[])
type FunctionalDependency struct {
	Guard  *Abstraction
	Keys   []*Var
	Values []*Var
}

func (d *FunctionalDependency) isDeclaration() {}
func (d *FunctionalDependency) isConstraint()  {}

// Def(name::RelationId, body::Abstraction, attrs::Attribute[])
type Def struct {
	Name  *RelationId
	Body  *Abstraction
	Attrs []*Attribute
}

func (d *Def) isDeclaration() {}

// Algorithm(globals::RelationId[], body::Script)
type Algorithm struct {
	Global []*RelationId
	Body   *Script
}

func (a *Algorithm) isDeclaration() {}

// Script := Construct[]
type Script struct {
	Constructs []Construct
}

// Construct := Loop | Instruction
type Construct interface {
	LqpNode
	isConstruct()
}

// Loop(init::Instruction[], body::Algorithm)
type Loop struct {
	Init []Instruction
	Body *Script
}

func (l *Loop) isConstruct() {}

// Instruction := Assign | Break | Upsert | MonoidDef | MonusDef
type Instruction interface {
	Construct
	isInstruction()
}

// Assign(name::RelationId, body::Abstraction, attrs::Attribute[])
type Assign struct {
	Name  *RelationId
	Body  *Abstraction
	Attrs []*Attribute
}

func (a *Assign) isConstruct()   {}
func (a *Assign) isInstruction() {}

// Upsert(arity::int, name::RelationId, body::Abstraction, attrs::Attribute[])
type Upsert struct {
	ValueArity int64
	Name       *RelationId
	Body       *Abstraction
	Attrs      []*Attribute
}

func (u *Upsert) isConstruct()   {}
func (u *Upsert) isInstruction() {}

// Break(name::RelationId, body::Abstraction, attrs::Attribute[])
type Break struct {
	Name  *RelationId
	Body  *Abstraction
	Attrs []*Attribute
}

func (b *Break) isConstruct()   {}
func (b *Break) isInstruction() {}

// MonoidDef(arity::int, monoid::Monoid, name::RelationId, body::Abstraction, attrs::Attribute[])
type MonoidDef struct {
	ValueArity int64
	Monoid     Monoid
	Name       *RelationId
	Body       *Abstraction
	Attrs      []*Attribute
}

func (m *MonoidDef) isConstruct()   {}
func (m *MonoidDef) isInstruction() {}

// MonusDef(arity::int, monoid::Monoid, name::RelationId, body::Abstraction, attrs::Attribute[])
type MonusDef struct {
	ValueArity int64
	Monoid     Monoid
	Name       *RelationId
	Body       *Abstraction
	Attrs      []*Attribute
}

func (m *MonusDef) isConstruct()   {}
func (m *MonusDef) isInstruction() {}

// Monoid := OrMonoid | MinMonoid | MaxMonoid | SumMonoid
type Monoid interface {
	LqpNode
	isMonoid()
}

// OrMonoid
type OrMonoid struct {
}

func (o *OrMonoid) isMonoid() {}

// MinMonoid
type MinMonoid struct {
	Type *Type
}

func (m *MinMonoid) isMonoid() {}

// MaxMonoid
type MaxMonoid struct {
	Type *Type
}

func (m *MaxMonoid) isMonoid() {}

// SumMonoid
type SumMonoid struct {
	Type *Type
}

func (s *SumMonoid) isMonoid() {}

type Binding struct {
	Var  *Var
	Type *Type
}

// Abstraction(vars::Binding[], value::Formula)
type Abstraction struct {
	Vars  []*Binding
	Value Formula
}

// Formula := Exists | Reduce | Conjunction | Disjunction | Not | FFI | Atom | Pragma | Primitive | TrueVal | FalseVal | RelAtom | Cast
type Formula interface {
	LqpNode
	isFormula()
}

// Exists(body::Abstraction)
type Exists struct {
	Body *Abstraction
}

func (e *Exists) isFormula() {}

// Reduce(op::Abstraction, body::Abstraction, terms::Term[])
type Reduce struct {
	Op    *Abstraction
	Body  *Abstraction
	Terms []Term
}

func (r *Reduce) isFormula() {}

// Conjunction(args::Formula[])
type Conjunction struct {
	Args []Formula
}

func (c *Conjunction) isFormula() {}

// Disjunction(args::Formula[])
type Disjunction struct {
	Args []Formula
}

func (d *Disjunction) isFormula() {}

// Not(arg::Formula)
type Not struct {
	Arg Formula
}

func (n *Not) isFormula() {}

// FFI(name::string, args::Abstraction[], terms::Term[])
type FFI struct {
	Name  string
	Args  []*Abstraction
	Terms []Term
}

func (f *FFI) isFormula() {}

// Atom(name::RelationId, terms::Term[])
type Atom struct {
	Name  *RelationId
	Terms []Term
}

func (a *Atom) isFormula() {}

// Pragma(name::string, terms::Term[])
type Pragma struct {
	Name  string
	Terms []Term
}

func (p *Pragma) isFormula() {}

// Primitive(name::string, terms::RelTerm[])
type Primitive struct {
	Name  string
	Terms []RelTerm
}

func (p *Primitive) isFormula() {}

// RelAtom(name::string, terms::RelTerm[])
type RelAtom struct {
	Name  string
	Terms []RelTerm
}

func (r *RelAtom) isFormula() {}

// Cast(input::Term, result::Term)
type Cast struct {
	Input  Term
	Result Term
}

func (c *Cast) isFormula() {}

// Var(name::string)
type Var struct {
	Name string
}

func (v *Var) isTerm()    {}
func (v *Var) isRelTerm() {}

// UInt128Value(low::fixed64, high::fixed64)
type UInt128Value struct {
	Value *big.Int
}

// Int128Value(low::fixed64, high::fixed64)
type Int128Value struct {
	Value *big.Int
}

type MissingValue struct{}

// DateValue(year: int, month: int, day: int)
type DateValue struct {
	Value time.Time
}

type DateTimeValue struct {
	Value time.Time
}

// Decimal represents a decimal number as (sign, coefficient, exponent)
// This matches Python's Decimal.as_tuple() representation
// The value is: (-1)^sign * coefficient * 10^exponent
type Decimal struct {
	Sign        int      // 0 for positive, 1 for negative
	Coefficient *big.Int // The digits as an integer
	Exponent    int      // The power of 10
}

// DecimalValue(precision: int, scale: int, value: Decimal)
type DecimalValue struct {
	Precision int32
	Scale     int32
	Value     *Decimal
}

// BooleanValue(value: bool)
// Note: We need a custom BooleanValue class to distinguish it from Python's `int` type.
// Python's built-in `bool` is a subclass of `int`.
type BooleanValue struct {
	Value bool
}

type ValueData interface {
	isValueData()
}

// Need alias to implement isValueData()
type StringValue string
type Int64Value int64
type Float64Value float64

func (s StringValue) isValueData()    {}
func (i Int64Value) isValueData()     {}
func (f Float64Value) isValueData()   {}
func (u *UInt128Value) isValueData()  {}
func (i *Int128Value) isValueData()   {}
func (m *MissingValue) isValueData()  {}
func (d *DateValue) isValueData()     {}
func (d *DateTimeValue) isValueData() {}
func (d *DecimalValue) isValueData()  {}
func (b *BooleanValue) isValueData()  {}

type Value struct {
	Value ValueData
}

func (v *Value) isTerm()    {}
func (v *Value) isRelTerm() {}

// SpecializedValue(value::Value)
type SpecializedValue struct {
	Value *Value
}

func (s *SpecializedValue) isRelTerm() {}

// Term := Var | Value
type Term interface {
	LqpNode
	isTerm()
}

// RelTerm := Term | SpecializedValue
type RelTerm interface {
	LqpNode
	isRelTerm()
}

// Attribute(name::string, args::Constant[])
type Attribute struct {
	Name string
	Args []*Value
}

// RelationId(id::UInt128)
type RelationId struct {
	Id *big.Int
}

type TypeName int

const (
	TypeNameUnspecified TypeName = iota
	TypeNameString
	TypeNameInt
	TypeNameFloat
	TypeNameUInt128
	TypeNameInt128
	TypeNameDate
	TypeNameDateTime
	TypeNameMissing
	TypeNameDecimal
	TypeNameBoolean
)

// Type represents a type with a name and parameters
type Type struct {
	TypeName   TypeName
	Parameters []*Value
}

// String returns the string representation of MaintenanceLevel
func (ml MaintenanceLevel) String() string {
	switch ml {
	case MaintenanceLevelUnspecified:
		return "UNSPECIFIED"
	case MaintenanceLevelOff:
		return "OFF"
	case MaintenanceLevelAuto:
		return "AUTO"
	case MaintenanceLevelAll:
		return "ALL"
	default:
		return "UNKNOWN"
	}
}

// String returns the string representation of TypeName
func (tn TypeName) String() string {
	switch tn {
	case TypeNameUnspecified:
		return "UNSPECIFIED"
	case TypeNameString:
		return "STRING"
	case TypeNameInt:
		return "INT"
	case TypeNameFloat:
		return "FLOAT"
	case TypeNameUInt128:
		return "UINT128"
	case TypeNameInt128:
		return "INT128"
	case TypeNameDate:
		return "DATE"
	case TypeNameDateTime:
		return "DATETIME"
	case TypeNameMissing:
		return "MISSING"
	case TypeNameDecimal:
		return "DECIMAL"
	case TypeNameBoolean:
		return "BOOLEAN"
	default:
		return "UNKNOWN"
	}
}
