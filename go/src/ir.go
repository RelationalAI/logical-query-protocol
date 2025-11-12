package lqp

import (
	"fmt"
	"math/big"
	"time"
)

// Tree representation of LQP. Each non-terminal (those with more than one
// option) is an "abstract" class and each terminal is its own class. All of
// which are children of LqpNode. Value is an exception -- it is just a value.

type SourceInfo struct {
	File   string
	Line   int
	Column int
}

func (s SourceInfo) String() string {
	return fmt.Sprintf("%s:%d:%d", s.File, s.Line, s.Column)
}

// --- Logic Types ---

type LqpNode interface {
	GetMeta() *SourceInfo
}

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
	Meta   *SourceInfo
	Guard  *Abstraction
	Keys   []*Var
	Values []*Var
}

func (d *FunctionalDependency) GetMeta() *SourceInfo { return d.Meta }
func (d *FunctionalDependency) isDeclaration()       {}
func (d *FunctionalDependency) isConstraint()        {}

// Def(name::RelationId, body::Abstraction, attrs::Attribute[])
type Def struct {
	Meta  *SourceInfo
	Name  *RelationId
	Body  *Abstraction
	Attrs []*Attribute
}

func (d *Def) GetMeta() *SourceInfo { return d.Meta }
func (d *Def) isDeclaration()       {}

// Algorithm(globals::RelationId[], body::Script)
type Algorithm struct {
	Meta   *SourceInfo
	Global []*RelationId
	Body   *Script
}

func (a *Algorithm) GetMeta() *SourceInfo { return a.Meta }
func (a *Algorithm) isDeclaration()       {}

// Script := Construct[]
type Script struct {
	Meta       *SourceInfo
	Constructs []Construct
}

func (s *Script) GetMeta() *SourceInfo { return s.Meta }

// Construct := Loop | Instruction
type Construct interface {
	LqpNode
	isConstruct()
}

// Loop(init::Instruction[], body::Algorithm)
type Loop struct {
	Meta *SourceInfo
	Init []Instruction
	Body *Script
}

func (l *Loop) GetMeta() *SourceInfo { return l.Meta }
func (l *Loop) isConstruct()         {}

// Instruction := Assign | Break | Upsert | MonoidDef | MonusDef
type Instruction interface {
	Construct
	isInstruction()
}

// Assign(name::RelationId, body::Abstraction, attrs::Attribute[])
type Assign struct {
	Meta  *SourceInfo
	Name  *RelationId
	Body  *Abstraction
	Attrs []*Attribute
}

func (a *Assign) GetMeta() *SourceInfo { return a.Meta }
func (a *Assign) isConstruct()         {}
func (a *Assign) isInstruction()       {}

// Upsert(arity::int, name::RelationId, body::Abstraction, attrs::Attribute[])
type Upsert struct {
	Meta       *SourceInfo
	ValueArity int64
	Name       *RelationId
	Body       *Abstraction
	Attrs      []*Attribute
}

func (u *Upsert) GetMeta() *SourceInfo { return u.Meta }
func (u *Upsert) isConstruct()         {}
func (u *Upsert) isInstruction()       {}

// Break(name::RelationId, body::Abstraction, attrs::Attribute[])
type Break struct {
	Meta  *SourceInfo
	Name  *RelationId
	Body  *Abstraction
	Attrs []*Attribute
}

func (b *Break) GetMeta() *SourceInfo { return b.Meta }
func (b *Break) isConstruct()         {}
func (b *Break) isInstruction()       {}

// MonoidDef(arity::int, monoid::Monoid, name::RelationId, body::Abstraction, attrs::Attribute[])
type MonoidDef struct {
	Meta       *SourceInfo
	ValueArity int64
	Monoid     Monoid
	Name       *RelationId
	Body       *Abstraction
	Attrs      []*Attribute
}

func (m *MonoidDef) GetMeta() *SourceInfo { return m.Meta }
func (m *MonoidDef) isConstruct()         {}
func (m *MonoidDef) isInstruction()       {}

// MonusDef(arity::int, monoid::Monoid, name::RelationId, body::Abstraction, attrs::Attribute[])
type MonusDef struct {
	Meta       *SourceInfo
	ValueArity int64
	Monoid     Monoid
	Name       *RelationId
	Body       *Abstraction
	Attrs      []*Attribute
}

func (m *MonusDef) GetMeta() *SourceInfo { return m.Meta }
func (m *MonusDef) isConstruct()         {}
func (m *MonusDef) isInstruction()       {}

// Monoid := OrMonoid | MinMonoid | MaxMonoid | SumMonoid
type Monoid interface {
	LqpNode
	isMonoid()
}

// OrMonoid
type OrMonoid struct {
	Meta *SourceInfo
}

func (o *OrMonoid) GetMeta() *SourceInfo { return o.Meta }
func (o *OrMonoid) isMonoid()            {}

// MinMonoid
type MinMonoid struct {
	Meta *SourceInfo
	Type *Type
}

func (m *MinMonoid) GetMeta() *SourceInfo { return m.Meta }
func (m *MinMonoid) isMonoid()            {}

// MaxMonoid
type MaxMonoid struct {
	Meta *SourceInfo
	Type *Type
}

func (m *MaxMonoid) GetMeta() *SourceInfo { return m.Meta }
func (m *MaxMonoid) isMonoid()            {}

// SumMonoid
type SumMonoid struct {
	Meta *SourceInfo
	Type *Type
}

func (s *SumMonoid) GetMeta() *SourceInfo { return s.Meta }
func (s *SumMonoid) isMonoid()            {}

type Binding struct {
	Var  *Var
	Type *Type
}

// Abstraction(vars::Binding[], value::Formula)
type Abstraction struct {
	Meta  *SourceInfo
	Vars  []*Binding
	Value Formula
}

func (a *Abstraction) GetMeta() *SourceInfo { return a.Meta }

// Formula := Exists | Reduce | Conjunction | Disjunction | Not | FFI | Atom | Pragma | Primitive | TrueVal | FalseVal | RelAtom | Cast
type Formula interface {
	LqpNode
	isFormula()
}

// Exists(body::Abstraction)
type Exists struct {
	Meta *SourceInfo
	Body *Abstraction
}

func (e *Exists) GetMeta() *SourceInfo { return e.Meta }
func (e *Exists) isFormula()           {}

// Reduce(op::Abstraction, body::Abstraction, terms::Term[])
type Reduce struct {
	Meta  *SourceInfo
	Op    *Abstraction
	Body  *Abstraction
	Terms []Term
}

func (r *Reduce) GetMeta() *SourceInfo { return r.Meta }
func (r *Reduce) isFormula()           {}

// Conjunction(args::Formula[])
type Conjunction struct {
	Meta *SourceInfo
	Args []Formula
}

func (c *Conjunction) GetMeta() *SourceInfo { return c.Meta }
func (c *Conjunction) isFormula()           {}

// Disjunction(args::Formula[])
type Disjunction struct {
	Meta *SourceInfo
	Args []Formula
}

func (d *Disjunction) GetMeta() *SourceInfo { return d.Meta }
func (d *Disjunction) isFormula()           {}

// Not(arg::Formula)
type Not struct {
	Meta *SourceInfo
	Arg  Formula
}

func (n *Not) GetMeta() *SourceInfo { return n.Meta }
func (n *Not) isFormula()           {}

// FFI(name::string, args::Abstraction[], terms::Term[])
type FFI struct {
	Meta  *SourceInfo
	Name  string
	Args  []*Abstraction
	Terms []Term
}

func (f *FFI) GetMeta() *SourceInfo { return f.Meta }
func (f *FFI) isFormula()           {}

// Atom(name::RelationId, terms::Term[])
type Atom struct {
	Meta  *SourceInfo
	Name  *RelationId
	Terms []Term
}

func (a *Atom) GetMeta() *SourceInfo { return a.Meta }
func (a *Atom) isFormula()           {}

// Pragma(name::string, terms::Term[])
type Pragma struct {
	Meta  *SourceInfo
	Name  string
	Terms []Term
}

func (p *Pragma) GetMeta() *SourceInfo { return p.Meta }
func (p *Pragma) isFormula()           {}

// Primitive(name::string, terms::RelTerm[])
type Primitive struct {
	Meta  *SourceInfo
	Name  string
	Terms []RelTerm
}

func (p *Primitive) GetMeta() *SourceInfo { return p.Meta }
func (p *Primitive) isFormula()           {}

// RelAtom(name::string, terms::RelTerm[])
type RelAtom struct {
	Meta  *SourceInfo
	Name  string
	Terms []RelTerm
}

func (r *RelAtom) GetMeta() *SourceInfo { return r.Meta }
func (r *RelAtom) isFormula()           {}

// Cast(input::Term, result::Term)
type Cast struct {
	Meta   *SourceInfo
	Input  Term
	Result Term
}

func (c *Cast) GetMeta() *SourceInfo { return c.Meta }
func (c *Cast) isFormula()           {}

// Var(name::string)
type Var struct {
	Meta *SourceInfo
	Name string
}

func (v *Var) GetMeta() *SourceInfo { return v.Meta }
func (v *Var) isTerm()              {}
func (v *Var) isRelTerm()           {}

// UInt128Value(low::fixed64, high::fixed64)
type UInt128Value struct {
	Meta  *SourceInfo
	Value *big.Int
}

func (u *UInt128Value) GetMeta() *SourceInfo { return u.Meta }

// Int128Value(low::fixed64, high::fixed64)
type Int128Value struct {
	Meta  *SourceInfo
	Value *big.Int
}

func (i *Int128Value) GetMeta() *SourceInfo { return i.Meta }

type MissingValue struct {
	Meta *SourceInfo
}

func (m *MissingValue) GetMeta() *SourceInfo { return m.Meta }

// DateValue(year: int, month: int, day: int)
type DateValue struct {
	Meta  *SourceInfo
	Value time.Time
}

func (d *DateValue) GetMeta() *SourceInfo { return d.Meta }

// DatetimeValue(year: int, month: int, day: int, hour: int, minute: int, second: int, microsecond: int)
type DateTimeValue struct {
	Meta  *SourceInfo
	Value time.Time
}

func (d *DateTimeValue) GetMeta() *SourceInfo { return d.Meta }

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
	Meta      *SourceInfo
	Precision int32
	Scale     int32
	Value     *Decimal
}

func (d *DecimalValue) GetMeta() *SourceInfo { return d.Meta }

// BooleanValue(value: bool)
// Note: We need a custom BooleanValue class to distinguish it from Python's `int` type.
// Python's built-in `bool` is a subclass of `int`.
type BooleanValue struct {
	Meta  *SourceInfo
	Value bool
}

func (b *BooleanValue) GetMeta() *SourceInfo { return b.Meta }

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
	Meta  *SourceInfo
	Value ValueData
}

func (v *Value) GetMeta() *SourceInfo { return v.Meta }
func (v *Value) isTerm()              {}
func (v *Value) isRelTerm()           {}

// SpecializedValue(value::Value)
type SpecializedValue struct {
	Meta  *SourceInfo
	Value *Value
}

func (s *SpecializedValue) GetMeta() *SourceInfo { return s.Meta }
func (s *SpecializedValue) isRelTerm()           {}

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
	Meta *SourceInfo
	Name string
	Args []*Value
}

func (a *Attribute) GetMeta() *SourceInfo { return a.Meta }

// RelationId(id::UInt128)
type RelationId struct {
	Meta *SourceInfo
	Id   *big.Int
}

func NewRelationId(id *big.Int, meta *SourceInfo) (*RelationId, error) {
	max := new(big.Int)
	max.SetString("ffffffffffffffffffffffffffffffff", 16)

	if id.Cmp(big.NewInt(0)) < 0 || id.Cmp(max) > 0 {
		return nil, fmt.Errorf("RelationId constructed with out of range (UInt128) number: %s", id.String())
	}

	return &RelationId{Meta: meta, Id: id}, nil
}

func (r *RelationId) GetMeta() *SourceInfo { return r.Meta }

func (r *RelationId) String() string {
	if r.Meta != nil {
		return fmt.Sprintf("RelationId(meta=%s, id=%s)", r.Meta, r.Id)
	}
	return fmt.Sprintf("RelationId(id=%s)", r.Id)
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

func (t TypeName) String() string {
	switch t {
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

// Type represents a type with a name and parameters
type Type struct {
	Meta       *SourceInfo
	TypeName   TypeName
	Parameters []*Value
}

func (t *Type) GetMeta() *SourceInfo { return t.Meta }

// --- Fragment Types ---

// FragmentId(id::bytes)
type FragmentId struct {
	Meta *SourceInfo
	Id   []byte
}

func (f *FragmentId) GetMeta() *SourceInfo { return f.Meta }

// Fragment(id::FragmentId, declarations::Declaration[], debug_info::DebugInfo)
type Fragment struct {
	Meta         *SourceInfo
	Id           *FragmentId
	Declarations []Declaration
	DebugInfo    *DebugInfo
}

func (f *Fragment) GetMeta() *SourceInfo { return f.Meta }

// We can't have map[*RelationId]string (mirroring Python, Julia)
// because the same RelationId at different locations are represented
// as different pointers to memory. So instead we use the string conv.
type DebugInfo struct {
	Meta         *SourceInfo
	IdToOrigName map[string]string
}

func (d *DebugInfo) GetMeta() *SourceInfo { return d.Meta }

// --- Transaction Types ---

// Define(fragment::Fragment)
type Define struct {
	Meta     *SourceInfo
	Fragment *Fragment
}

func (d *Define) GetMeta() *SourceInfo { return d.Meta }
func (d *Define) isWriteType()         {}

// Undefine(fragment_id::FragmentId)
type Undefine struct {
	Meta       *SourceInfo
	FragmentId *FragmentId
}

func (u *Undefine) GetMeta() *SourceInfo { return u.Meta }
func (u *Undefine) isWriteType()         {}

// Context(relations::RelationId[])
type Context struct {
	Meta      *SourceInfo
	Relations []*RelationId
}

func (c *Context) GetMeta() *SourceInfo { return c.Meta }
func (c *Context) isWriteType()         {}

// Sync(fragments::FragmentId[])
type Sync struct {
	Meta      *SourceInfo
	Fragments []*FragmentId
}

func (s *Sync) GetMeta() *SourceInfo { return s.Meta }
func (s *Sync) isWriteType()         {}

type WriteType interface {
	LqpNode
	isWriteType()
}

// Write := Define | Undefine | Context
type Write struct {
	Meta      *SourceInfo
	WriteType WriteType
}

func (w *Write) GetMeta() *SourceInfo { return w.Meta }

// Demand(relation_id::RelationId)
type Demand struct {
	Meta       *SourceInfo
	RelationId *RelationId
}

func (d *Demand) GetMeta() *SourceInfo { return d.Meta }
func (d *Demand) isReadType()          {}

// Output(name::string?, relation_id::RelationId)
type Output struct {
	Meta       *SourceInfo
	Name       *string
	RelationId *RelationId
}

func (o *Output) GetMeta() *SourceInfo { return o.Meta }
func (o *Output) isReadType()          {}

// ExportCSVConfig
type ExportCSVConfig struct {
	Meta        *SourceInfo
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

func (e *ExportCSVConfig) GetMeta() *SourceInfo { return e.Meta }

type ExportCSVColumn struct {
	Meta       *SourceInfo
	ColumnName string
	ColumnData *RelationId
}

func (e *ExportCSVColumn) GetMeta() *SourceInfo { return e.Meta }

// Export(name::string, relation_id::RelationId)
type Export struct {
	Meta   *SourceInfo
	Config *ExportCSVConfig
}

func (e *Export) GetMeta() *SourceInfo { return e.Meta }
func (e *Export) isReadType()          {}

// Abort(name::string?, relation_id::RelationId)
type Abort struct {
	Meta       *SourceInfo
	Name       *string
	RelationId *RelationId
}

func (a *Abort) GetMeta() *SourceInfo { return a.Meta }
func (a *Abort) isReadType()          {}

type ReadType interface {
	LqpNode
	isReadType()
}

// Read := Demand | Output | Export | WhatIf | Abort
type Read struct {
	Meta     *SourceInfo
	ReadType ReadType
}

func (r *Read) GetMeta() *SourceInfo { return r.Meta }

// Epoch(writes::Write[], reads::Read[])
type Epoch struct {
	Meta   *SourceInfo
	Writes []*Write
	Reads  []*Read
}

func (e *Epoch) GetMeta() *SourceInfo { return e.Meta }

// WhatIf(branch::string?, epoch::Epoch)
type WhatIf struct {
	Meta   *SourceInfo
	Branch *string
	Epoch  *Epoch
}

func (w *WhatIf) GetMeta() *SourceInfo { return w.Meta }
func (w *WhatIf) isReadType()          {}

// Transaction(epochs::Epoch[], configure::Configure)
type Transaction struct {
	Meta      *SourceInfo
	Epochs    []*Epoch
	Configure *Configure
}

func (t *Transaction) GetMeta() *SourceInfo { return t.Meta }

// Configure(semantics_version::int, ivm_config::IVMConfig)
type Configure struct {
	Meta             *SourceInfo
	SemanticsVersion int64
	IvmConfig        *IVMConfig
}

func (c *Configure) GetMeta() *SourceInfo { return c.Meta }

// IVMConfig(level::MaintenanceLevel)
type IVMConfig struct {
	Meta  *SourceInfo
	Level MaintenanceLevel
}

func (i *IVMConfig) GetMeta() *SourceInfo { return i.Meta }

type MaintenanceLevel int

const (
	MaintenanceLevelUnspecified MaintenanceLevel = iota
	MaintenanceLevelOff
	MaintenanceLevelAuto
	MaintenanceLevelAll
)

func (m MaintenanceLevel) String() string {
	switch m {
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
