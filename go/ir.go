package lqp

import (
	"fmt"
	"math/big"
	"time"
)

// Tree representation of LQP. Each non-terminal (those with more than one
// option) is an "abstract" interface and each terminal is its own struct. All
// structs implement the LqpNode interface.

// SourceInfo represents source location information
type SourceInfo struct {
	File   string
	Line   int
	Column int
}

func (s SourceInfo) String() string {
	return fmt.Sprintf("%s:%d:%d", s.File, s.Line, s.Column)
}

// --- Base Interfaces ---

// LqpNode is the base interface for all LQP nodes
type LqpNode interface {
	GetMeta() *SourceInfo
}

// Declaration is implemented by Def and Algorithm
type Declaration interface {
	LqpNode
	isDeclaration()
}

// Construct is implemented by Loop and Instruction types
type Construct interface {
	LqpNode
	isConstruct()
}

// Instruction is implemented by Assign, Break, Upsert, MonoidDef, MonusDef
type Instruction interface {
	Construct
	isInstruction()
}

// Formula is implemented by all formula types
type Formula interface {
	LqpNode
	isFormula()
}

// Monoid is implemented by OrMonoid, MinMonoid, MaxMonoid, SumMonoid
type Monoid interface {
	LqpNode
	isMonoid()
}

// --- Logic Types ---

// Def represents a definition with a name, body, and attributes
type Def struct {
	Meta  *SourceInfo
	Name  *RelationId
	Body  *Abstraction
	Attrs []*Attribute
}

func (d *Def) GetMeta() *SourceInfo { return d.Meta }
func (d *Def) isDeclaration()       {}

// Algorithm represents an algorithm with global relations and a body
type Algorithm struct {
	Meta   *SourceInfo
	Global []*RelationId
	Body   *Script
}

func (a *Algorithm) GetMeta() *SourceInfo { return a.Meta }
func (a *Algorithm) isDeclaration()       {}

// Script represents a sequence of constructs
type Script struct {
	Meta       *SourceInfo
	Constructs []Construct
}

func (s *Script) GetMeta() *SourceInfo { return s.Meta }

// Loop represents a loop with initialization and body
type Loop struct {
	Meta *SourceInfo
	Init []Instruction
	Body *Script
}

func (l *Loop) GetMeta() *SourceInfo { return l.Meta }
func (l *Loop) isConstruct()         {}

// Assign represents an assignment instruction
type Assign struct {
	Meta  *SourceInfo
	Name  *RelationId
	Body  *Abstraction
	Attrs []*Attribute
}

func (a *Assign) GetMeta() *SourceInfo { return a.Meta }
func (a *Assign) isConstruct()         {}
func (a *Assign) isInstruction()       {}

// Upsert represents an upsert instruction
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

// Break represents a break instruction
type Break struct {
	Meta  *SourceInfo
	Name  *RelationId
	Body  *Abstraction
	Attrs []*Attribute
}

func (b *Break) GetMeta() *SourceInfo { return b.Meta }
func (b *Break) isConstruct()         {}
func (b *Break) isInstruction()       {}

// MonoidDef represents a monoid definition
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

// MonusDef represents a monus definition
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

// --- Monoid Types ---

// OrMonoid represents an OR monoid (only over Booleans)
type OrMonoid struct {
	Meta *SourceInfo
}

func (o *OrMonoid) GetMeta() *SourceInfo { return o.Meta }
func (o *OrMonoid) isMonoid()            {}

// MinMonoid represents a MIN monoid parametrized by a type T
type MinMonoid struct {
	Meta *SourceInfo
	Type *Type
}

func (m *MinMonoid) GetMeta() *SourceInfo { return m.Meta }
func (m *MinMonoid) isMonoid()            {}

// MaxMonoid represents a MAX monoid parametrized by a type T
type MaxMonoid struct {
	Meta *SourceInfo
	Type *Type
}

func (m *MaxMonoid) GetMeta() *SourceInfo { return m.Meta }
func (m *MaxMonoid) isMonoid()            {}

// SumMonoid represents a SUM monoid parametrized by a type T
type SumMonoid struct {
	Meta *SourceInfo
	Type *Type
}

func (s *SumMonoid) GetMeta() *SourceInfo { return s.Meta }
func (s *SumMonoid) isMonoid()            {}

// --- Formula Types ---

// Binding represents a variable binding with its type
type Binding struct {
	Var  *Var
	Type *Type
}

// Abstraction represents an abstraction with variables and a formula value
type Abstraction struct {
	Meta  *SourceInfo
	Vars  []*Binding
	Value Formula
}

func (a *Abstraction) GetMeta() *SourceInfo { return a.Meta }

// Exists represents an existential quantification
type Exists struct {
	Meta *SourceInfo
	Body *Abstraction
}

func (e *Exists) GetMeta() *SourceInfo { return e.Meta }
func (e *Exists) isFormula()           {}

// Reduce represents a reduction operation
type Reduce struct {
	Meta  *SourceInfo
	Op    *Abstraction
	Body  *Abstraction
	Terms []Term
}

func (r *Reduce) GetMeta() *SourceInfo { return r.Meta }
func (r *Reduce) isFormula()           {}

// Conjunction represents a conjunction of formulas
type Conjunction struct {
	Meta *SourceInfo
	Args []Formula
}

func (c *Conjunction) GetMeta() *SourceInfo { return c.Meta }
func (c *Conjunction) isFormula()           {}

// Disjunction represents a disjunction of formulas
type Disjunction struct {
	Meta *SourceInfo
	Args []Formula
}

func (d *Disjunction) GetMeta() *SourceInfo { return d.Meta }
func (d *Disjunction) isFormula()           {}

// Not represents a negation
type Not struct {
	Meta *SourceInfo
	Arg  Formula
}

func (n *Not) GetMeta() *SourceInfo { return n.Meta }
func (n *Not) isFormula()           {}

// FFI represents a foreign function interface call
type FFI struct {
	Meta  *SourceInfo
	Name  string
	Args  []*Abstraction
	Terms []Term
}

func (f *FFI) GetMeta() *SourceInfo { return f.Meta }
func (f *FFI) isFormula()           {}

// Atom represents an atom with a relation name and terms
type Atom struct {
	Meta  *SourceInfo
	Name  *RelationId
	Terms []Term
}

func (a *Atom) GetMeta() *SourceInfo { return a.Meta }
func (a *Atom) isFormula()           {}

// Pragma represents a pragma directive
type Pragma struct {
	Meta  *SourceInfo
	Name  string
	Terms []Term
}

func (p *Pragma) GetMeta() *SourceInfo { return p.Meta }
func (p *Pragma) isFormula()           {}

// Primitive represents a primitive operation
type Primitive struct {
	Meta  *SourceInfo
	Name  string
	Terms []RelTerm
}

func (p *Primitive) GetMeta() *SourceInfo { return p.Meta }
func (p *Primitive) isFormula()           {}

// RelAtom represents a relational atom
type RelAtom struct {
	Meta  *SourceInfo
	Name  string
	Terms []RelTerm
}

func (r *RelAtom) GetMeta() *SourceInfo { return r.Meta }
func (r *RelAtom) isFormula()           {}

// Cast represents a type cast
type Cast struct {
	Meta   *SourceInfo
	Input  Term
	Result Term
}

func (c *Cast) GetMeta() *SourceInfo { return c.Meta }
func (c *Cast) isFormula()           {}

// --- Term Types ---

// Term can be either a Var or a Value
type Term interface {
	LqpNode
	isTerm()
}

// RelTerm can be a Term or a SpecializedValue
type RelTerm interface {
	LqpNode
	isRelTerm()
}

// Var represents a variable
type Var struct {
	Meta *SourceInfo
	Name string
}

func (v *Var) GetMeta() *SourceInfo { return v.Meta }
func (v *Var) isTerm()              {}
func (v *Var) isRelTerm()           {}

// --- Value Types ---

// UInt128Value represents a 128-bit unsigned integer
type UInt128Value struct {
	Meta  *SourceInfo
	Value *big.Int
}

func (u *UInt128Value) GetMeta() *SourceInfo { return u.Meta }

// Int128Value represents a 128-bit signed integer
type Int128Value struct {
	Meta  *SourceInfo
	Value *big.Int
}

func (i *Int128Value) GetMeta() *SourceInfo { return i.Meta }

// MissingValue represents a missing value
type MissingValue struct {
	Meta *SourceInfo
}

func (m *MissingValue) GetMeta() *SourceInfo { return m.Meta }

// DateValue represents a date
type DateValue struct {
	Meta  *SourceInfo
	Value time.Time
}

func (d *DateValue) GetMeta() *SourceInfo { return d.Meta }

// DateTimeValue represents a datetime
type DateTimeValue struct {
	Meta  *SourceInfo
	Value time.Time
}

func (d *DateTimeValue) GetMeta() *SourceInfo { return d.Meta }

// DecimalValue represents a decimal number
type DecimalValue struct {
	Meta      *SourceInfo
	Precision int32
	Scale     int32
	Value     *big.Int
}

func (d *DecimalValue) GetMeta() *SourceInfo { return d.Meta }

// BooleanValue represents a boolean value
type BooleanValue struct {
	Meta  *SourceInfo
	Value bool
}

func (b *BooleanValue) GetMeta() *SourceInfo { return b.Meta }

// ValueData is the union type for value data
type ValueData interface {
	isValueData()
}

// Wrapper types for primitive value data
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

// Value represents a constant value
type Value struct {
	Meta  *SourceInfo
	Value ValueData
}

func (v *Value) GetMeta() *SourceInfo { return v.Meta }
func (v *Value) isTerm()              {}
func (v *Value) isRelTerm()           {}

// SpecializedValue wraps a value for specialized use
type SpecializedValue struct {
	Meta  *SourceInfo
	Value *Value
}

func (s *SpecializedValue) GetMeta() *SourceInfo { return s.Meta }
func (s *SpecializedValue) isRelTerm()           {}

// --- Other Types ---

// Attribute represents an attribute with a name and value arguments
type Attribute struct {
	Meta *SourceInfo
	Name string
	Args []*Value
}

func (a *Attribute) GetMeta() *SourceInfo { return a.Meta }

// RelationId represents a unique identifier for a relation (UInt128)
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

// TypeName represents the name of a type
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

// FragmentId represents a fragment identifier
type FragmentId struct {
	Meta *SourceInfo
	Id   []byte
}

func (f *FragmentId) GetMeta() *SourceInfo { return f.Meta }

// DebugInfo maps relation IDs to their original names
type DebugInfo struct {
	Meta         *SourceInfo
	IdToOrigName map[string]string // Map RelationId.String() to original name
}

func (d *DebugInfo) GetMeta() *SourceInfo { return d.Meta }

// Fragment represents a fragment with an ID, declarations, and debug info
type Fragment struct {
	Meta         *SourceInfo
	Id           *FragmentId
	Declarations []Declaration
	DebugInfo    *DebugInfo
}

func (f *Fragment) GetMeta() *SourceInfo { return f.Meta }

// --- Transaction Types ---

// WriteType is a union type for write operations
type WriteType interface {
	LqpNode
	isWriteType()
}

// Define represents a define operation
type Define struct {
	Meta     *SourceInfo
	Fragment *Fragment
}

func (d *Define) GetMeta() *SourceInfo { return d.Meta }
func (d *Define) isWriteType()         {}

// Undefine represents an undefine operation
type Undefine struct {
	Meta       *SourceInfo
	FragmentId *FragmentId
}

func (u *Undefine) GetMeta() *SourceInfo { return u.Meta }
func (u *Undefine) isWriteType()         {}

// Context represents a context operation
type Context struct {
	Meta      *SourceInfo
	Relations []*RelationId
}

func (c *Context) GetMeta() *SourceInfo { return c.Meta }
func (c *Context) isWriteType()         {}

// Sync represents a sync operation
type Sync struct {
	Meta      *SourceInfo
	Fragments []*FragmentId
}

func (s *Sync) GetMeta() *SourceInfo { return s.Meta }
func (s *Sync) isWriteType()         {}

// Write represents a write operation
type Write struct {
	Meta      *SourceInfo
	WriteType WriteType
}

func (w *Write) GetMeta() *SourceInfo { return w.Meta }

// ReadType is a union type for read operations
type ReadType interface {
	LqpNode
	isReadType()
}

// Demand represents a demand operation
type Demand struct {
	Meta       *SourceInfo
	RelationId *RelationId
}

func (d *Demand) GetMeta() *SourceInfo { return d.Meta }
func (d *Demand) isReadType()          {}

// Output represents an output operation
type Output struct {
	Meta       *SourceInfo
	Name       *string
	RelationId *RelationId
}

func (o *Output) GetMeta() *SourceInfo { return o.Meta }
func (o *Output) isReadType()          {}

// ExportCSVColumn represents a column in a CSV export
type ExportCSVColumn struct {
	Meta       *SourceInfo
	ColumnName string
	ColumnData *RelationId
}

func (e *ExportCSVColumn) GetMeta() *SourceInfo { return e.Meta }

// ExportCSVConfig represents CSV export configuration
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

// Export represents an export operation
type Export struct {
	Meta   *SourceInfo
	Config *ExportCSVConfig
}

func (e *Export) GetMeta() *SourceInfo { return e.Meta }
func (e *Export) isReadType()          {}

// Abort represents an abort operation
type Abort struct {
	Meta       *SourceInfo
	Name       *string
	RelationId *RelationId
}

func (a *Abort) GetMeta() *SourceInfo { return a.Meta }
func (a *Abort) isReadType()          {}

// WhatIf represents a what-if operation
type WhatIf struct {
	Meta   *SourceInfo
	Branch *string
	Epoch  *Epoch
}

func (w *WhatIf) GetMeta() *SourceInfo { return w.Meta }
func (w *WhatIf) isReadType()          {}

// Read represents a read operation
type Read struct {
	Meta     *SourceInfo
	ReadType ReadType
}

func (r *Read) GetMeta() *SourceInfo { return r.Meta }

// Epoch represents an epoch with writes and reads
type Epoch struct {
	Meta   *SourceInfo
	Writes []*Write
	Reads  []*Read
}

func (e *Epoch) GetMeta() *SourceInfo { return e.Meta }

// MaintenanceLevel represents the maintenance level for IVM
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

// IVMConfig represents IVM configuration
type IVMConfig struct {
	Meta  *SourceInfo
	Level MaintenanceLevel
}

func (i *IVMConfig) GetMeta() *SourceInfo { return i.Meta }

// Configure represents configuration settings
type Configure struct {
	Meta             *SourceInfo
	SemanticsVersion int64
	IvmConfig        *IVMConfig
}

func (c *Configure) GetMeta() *SourceInfo { return c.Meta }

// Transaction represents a transaction with epochs and configuration
type Transaction struct {
	Meta      *SourceInfo
	Epochs    []*Epoch
	Configure *Configure
}

func (t *Transaction) GetMeta() *SourceInfo { return t.Meta }
