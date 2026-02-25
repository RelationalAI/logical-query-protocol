@testitem "Equality for empty struct types" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: DateTimeType, FloatType, UInt128Type, Int128Type,
        UnspecifiedType, DateType, MissingType, MissingValue, IntType, StringType,
        BooleanType, OrMonoid

    # All instances of empty struct types should be equal
    @test DateTimeType() == DateTimeType()
    @test FloatType() == FloatType()
    @test UInt128Type() == UInt128Type()
    @test Int128Type() == Int128Type()
    @test UnspecifiedType() == UnspecifiedType()
    @test DateType() == DateType()
    @test MissingType() == MissingType()
    @test MissingValue() == MissingValue()
    @test IntType() == IntType()
    @test StringType() == StringType()
    @test BooleanType() == BooleanType()
    @test OrMonoid() == OrMonoid()

    # Test isequal as well
    @test isequal(DateTimeType(), DateTimeType())
    @test isequal(IntType(), IntType())

    # Test hash consistency
    @test hash(DateTimeType()) == hash(DateTimeType())
    @test hash(FloatType()) == hash(FloatType())
    @test hash(MissingValue()) == hash(MissingValue())
end

@testitem "Equality for RelationId" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: RelationId

    r1 = RelationId(id_low=1, id_high=2)
    r2 = RelationId(id_low=1, id_high=2)
    r3 = RelationId(id_low=1, id_high=3)
    r4 = RelationId(id_low=2, id_high=2)

    # Equality
    @test r1 == r2
    @test r1 != r3
    @test r1 != r4

    # Symmetry
    @test r1 == r2 && r2 == r1

    # Hash consistency
    @test hash(r1) == hash(r2)
    @test hash(r1) != hash(r3)

    # isequal
    @test isequal(r1, r2)
    @test !isequal(r1, r3)

    # Works in Sets and Dicts
    s = Set([r1, r2, r3])
    @test length(s) == 2
    @test r1 in s
    @test r3 in s

    d = Dict(r1 => "a", r3 => "b")
    @test d[r2] == "a"
end

@testitem "Equality for Var" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Var

    v1 = Var(name="x")
    v2 = Var(name="x")
    v3 = Var(name="y")

    # Equality
    @test v1 == v2
    @test v1 != v3
    @test isequal(v1, v2)

    # Hash consistency
    @test hash(v1) == hash(v2)
    @test hash(v1) != hash(v3)

    # Reflexivity
    @test v1 == v1
    @test isequal(v1, v1)

    # Symmetry
    @test v1 == v2 && v2 == v1

    # Transitivity
    v4 = Var(name="x")
    @test v1 == v2 && v2 == v4 && v1 == v4

    # Works in collections
    @test length(Set([v1, v2, v3])) == 2
end

@testitem "Equality for Int128Value and UInt128Value" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Int128Value, UInt128Value

    # Int128Value tests
    i1 = Int128Value(low=1, high=2)
    i2 = Int128Value(low=1, high=2)
    i3 = Int128Value(low=1, high=3)
    i4 = Int128Value(low=1, high=2)

    @test i1 == i2
    @test i1 != i3
    @test isequal(i1, i2)

    # Hash consistency
    @test hash(i1) == hash(i2)

    # Reflexivity
    @test i1 == i1
    @test isequal(i1, i1)

    # Symmetry
    @test i1 == i2 && i2 == i1

    # Transitivity
    @test i1 == i2 && i2 == i4 && i1 == i4

    # UInt128Value tests
    u1 = UInt128Value(low=1, high=2)
    u2 = UInt128Value(low=1, high=2)
    u3 = UInt128Value(low=2, high=2)
    u4 = UInt128Value(low=1, high=2)

    @test u1 == u2
    @test u1 != u3
    @test isequal(u1, u2)

    # Hash consistency
    @test hash(u1) == hash(u2)

    # Reflexivity
    @test u1 == u1
    @test isequal(u1, u1)

    # Symmetry
    @test u1 == u2 && u2 == u1

    # Transitivity
    @test u1 == u2 && u2 == u4 && u1 == u4
end

@testitem "Equality for DecimalType and DecimalValue" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: DecimalType, DecimalValue, Int128Value

    # DecimalType tests
    dt1 = DecimalType(precision=10, scale=2)
    dt2 = DecimalType(precision=10, scale=2)
    dt3 = DecimalType(precision=10, scale=3)
    dt4 = DecimalType(precision=10, scale=2)

    @test dt1 == dt2
    @test dt1 != dt3
    @test isequal(dt1, dt2)

    # Hash consistency
    @test hash(dt1) == hash(dt2)

    # Reflexivity
    @test dt1 == dt1
    @test isequal(dt1, dt1)

    # Symmetry
    @test dt1 == dt2 && dt2 == dt1

    # Transitivity
    @test dt1 == dt2 && dt2 == dt4 && dt1 == dt4

    # DecimalValue tests
    val1 = Int128Value(low=100, high=0)
    val2 = Int128Value(low=200, high=0)
    dv1 = DecimalValue(precision=10, scale=2, value=val1)
    dv2 = DecimalValue(precision=10, scale=2, value=val1)
    dv3 = DecimalValue(precision=10, scale=2, value=val2)
    dv4 = DecimalValue(precision=10, scale=2, value=val1)

    @test dv1 == dv2
    @test dv1 != dv3
    @test isequal(dv1, dv2)

    # Hash consistency
    @test hash(dv1) == hash(dv2)

    # Reflexivity
    @test dv1 == dv1
    @test isequal(dv1, dv1)

    # Symmetry
    @test dv1 == dv2 && dv2 == dv1

    # Transitivity
    @test dv1 == dv2 && dv2 == dv4 && dv1 == dv4
end

@testitem "Equality for DateValue and DateTimeValue" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: DateValue, DateTimeValue

    # DateValue tests
    d1 = DateValue(year=2024, month=1, day=15)
    d2 = DateValue(year=2024, month=1, day=15)
    d3 = DateValue(year=2024, month=1, day=16)
    d4 = DateValue(year=2024, month=1, day=15)

    # Equality and inequality
    @test d1 == d2
    @test d1 != d3
    @test isequal(d1, d2)

    # Hash consistency
    @test hash(d1) == hash(d2)

    # Reflexivity
    @test d1 == d1
    @test isequal(d1, d1)

    # Symmetry
    @test d1 == d2 && d2 == d1

    # Transitivity
    @test d1 == d2 && d2 == d4 && d1 == d4

    # DateTimeValue tests
    dt1 = DateTimeValue(year=2024, month=1, day=15, hour=10, minute=30, second=45, microsecond=123456)
    dt2 = DateTimeValue(year=2024, month=1, day=15, hour=10, minute=30, second=45, microsecond=123456)
    dt3 = DateTimeValue(year=2024, month=1, day=15, hour=10, minute=30, second=45, microsecond=654321)
    dt4 = DateTimeValue(year=2024, month=1, day=15, hour=10, minute=30, second=45, microsecond=123456)

    # Equality and inequality
    @test dt1 == dt2
    @test dt1 != dt3
    @test isequal(dt1, dt2)

    # Hash consistency
    @test hash(dt1) == hash(dt2)

    # Reflexivity
    @test dt1 == dt1
    @test isequal(dt1, dt1)

    # Symmetry
    @test dt1 == dt2 && dt2 == dt1

    # Transitivity
    @test dt1 == dt2 && dt2 == dt4 && dt1 == dt4
end

@testitem "Equality for Value (OneOf type)" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Value
    using ProtoBuf: OneOf

    v1 = Value(value=OneOf(:int_value, 42))
    v2 = Value(value=OneOf(:int_value, 42))
    v3 = Value(value=OneOf(:int_value, 43))
    v4 = Value(value=OneOf(:string_value, "hello"))
    v5 = Value(value=nothing)
    v6 = Value(value=nothing)
    v7 = Value(value=OneOf(:int_value, 42))

    # Same discriminant, same value
    @test v1 == v2
    @test isequal(v1, v2)

    # Hash consistency
    @test hash(v1) == hash(v2)

    # Reflexivity
    @test v1 == v1
    @test isequal(v1, v1)

    # Symmetry
    @test v1 == v2 && v2 == v1

    # Transitivity
    @test v1 == v2 && v2 == v7 && v1 == v7

    # Same discriminant, different value
    @test v1 != v3

    # Different discriminant
    @test v1 != v4

    # Nothing values
    @test v5 == v6
    @test hash(v5) == hash(v6)

    # Nothing vs non-nothing
    @test v1 != v5
end

@testitem "Equality for Monoid types" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: MinMonoid, MaxMonoid, SumMonoid, var"#Type", IntType
    using ProtoBuf: OneOf

    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    t2 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    t3 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))

    # MinMonoid tests
    m1 = MinMonoid(var"#type"=t1)
    m2 = MinMonoid(var"#type"=t2)
    m3 = MinMonoid(var"#type"=nothing)
    m4 = MinMonoid(var"#type"=t3)

    @test m1 == m2
    @test m1 != m3
    @test isequal(m1, m2)

    # Hash consistency
    @test hash(m1) == hash(m2)

    # Reflexivity
    @test m1 == m1
    @test isequal(m1, m1)

    # Symmetry
    @test m1 == m2 && m2 == m1

    # Transitivity
    @test m1 == m2 && m2 == m4 && m1 == m4

    # SumMonoid tests
    s1 = SumMonoid(var"#type"=t1)
    s2 = SumMonoid(var"#type"=t2)
    s4 = SumMonoid(var"#type"=t3)

    @test s1 == s2
    @test isequal(s1, s2)

    # Hash consistency
    @test hash(s1) == hash(s2)

    # Reflexivity
    @test s1 == s1
    @test isequal(s1, s1)

    # Symmetry
    @test s1 == s2 && s2 == s1

    # Transitivity
    @test s1 == s2 && s2 == s4 && s1 == s4

    # MaxMonoid tests
    mx1 = MaxMonoid(var"#type"=t1)
    mx2 = MaxMonoid(var"#type"=t2)
    mx4 = MaxMonoid(var"#type"=t3)

    @test mx1 == mx2
    @test isequal(mx1, mx2)

    # Hash consistency
    @test hash(mx1) == hash(mx2)

    # Reflexivity
    @test mx1 == mx1
    @test isequal(mx1, mx1)

    # Symmetry
    @test mx1 == mx2 && mx2 == mx1

    # Transitivity
    @test mx1 == mx2 && mx2 == mx4 && mx1 == mx4
end

@testitem "Equality for Monoid (OneOf type)" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Monoid, MinMonoid, MaxMonoid, var"#Type", IntType
    using ProtoBuf: OneOf

    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))

    min1 = MinMonoid(var"#type"=t1)
    max1 = MaxMonoid(var"#type"=t1)

    m1 = Monoid(OneOf(:min, min1))
    m2 = Monoid(OneOf(:min, min1))
    m3 = Monoid(OneOf(:max, max1))
    m4 = Monoid(nothing)
    m5 = Monoid(nothing)
    m6 = Monoid(OneOf(:min, min1))

    # Same discriminant, same value
    @test m1 == m2
    @test isequal(m1, m2)

    # Hash consistency
    @test hash(m1) == hash(m2)

    # Reflexivity
    @test m1 == m1
    @test isequal(m1, m1)

    # Symmetry
    @test m1 == m2 && m2 == m1

    # Transitivity
    @test m1 == m2 && m2 == m6 && m1 == m6

    # Different discriminant
    @test m1 != m3

    # Nothing values
    @test m4 == m5
    @test hash(m4) == hash(m5)
    @test isequal(m4, m5)

    # Nothing vs non-nothing
    @test m1 != m4
end

@testitem "Equality for Binding" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Binding, Var, var"#Type", IntType, StringType
    using ProtoBuf: OneOf

    v1 = Var(name="x")
    v2 = Var(name="x")
    v3 = Var(name="y")
    v4 = Var(name="x")
    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    t2 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    t3 = var"#Type"(var"#type"=OneOf(:string_type, StringType()))
    t4 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))

    b1 = Binding(var=v1, var"#type"=t1)
    b2 = Binding(var=v2, var"#type"=t2)
    b3 = Binding(var=v3, var"#type"=t3)
    b4 = Binding(var=v4, var"#type"=t4)

    # Equality and inequality
    @test b1 == b2
    @test b1 != b3
    @test isequal(b1, b2)

    # Hash consistency
    @test hash(b1) == hash(b2)

    # Reflexivity
    @test b1 == b1
    @test isequal(b1, b1)

    # Symmetry
    @test b1 == b2 && b2 == b1

    # Transitivity
    @test b1 == b2 && b2 == b4 && b1 == b4
end

@testitem "Equality for RelAtom" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: RelAtom, RelationId, RelTerm, Value
    using ProtoBuf: OneOf

    v1 = Value(value=OneOf(:int_value, 42))
    rt1 = RelTerm(rel_term_type=OneOf(:specialized_value, v1))

    ra1 = RelAtom(name="aaa", terms=[rt1])
    ra2 = RelAtom(name="aaa", terms=[rt1])
    ra3 = RelAtom(name="bbb", terms=[rt1])
    ra4 = RelAtom(name="aaa", terms=[])
    ra5 = RelAtom(name="aaa", terms=[rt1])

    # Equality and inequality
    @test ra1 == ra2
    @test ra1 != ra3
    @test ra1 != ra4
    @test isequal(ra1, ra2)

    # Hash consistency
    @test hash(ra1) == hash(ra2)

    # Reflexivity
    @test ra1 == ra1
    @test isequal(ra1, ra1)

    # Symmetry
    @test ra1 == ra2 && ra2 == ra1

    # Transitivity
    @test ra1 == ra2 && ra2 == ra5 && ra1 == ra5
end

@testitem "Equality for Attribute" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Attribute, Value
    using ProtoBuf: OneOf

    v1 = Value(value=OneOf(:string_value, "bar"))
    v2 = Value(value=OneOf(:string_value, "baz"))

    a1 = Attribute(name="foo", args=[v1])
    a2 = Attribute(name="foo", args=[v1])
    a3 = Attribute(name="foo", args=[v2])
    a4 = Attribute(name="qux", args=[v1])
    a5 = Attribute(name="foo", args=[v1])

    # Equality and inequality
    @test a1 == a2
    @test a1 != a3
    @test a1 != a4
    @test isequal(a1, a2)

    # Hash consistency
    @test hash(a1) == hash(a2)

    # Reflexivity
    @test a1 == a1
    @test isequal(a1, a1)

    # Symmetry
    @test a1 == a2 && a2 == a1

    # Transitivity
    @test a1 == a2 && a2 == a5 && a1 == a5
end

@testitem "Equality for RelTerm" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: RelTerm, Term, Var, Value
    using ProtoBuf: OneOf

    # RelTerm with Value
    v1 = Value(value=OneOf(:int_value, 42))
    v2 = Value(value=OneOf(:int_value, 42))
    v3 = Value(value=OneOf(:int_value, 99))
    v4 = Value(value=OneOf(:int_value, 42))

    rt1 = RelTerm(rel_term_type=OneOf(:specialized_value, v1))
    rt2 = RelTerm(rel_term_type=OneOf(:specialized_value, v2))
    rt3 = RelTerm(rel_term_type=OneOf(:specialized_value, v3))
    rt8 = RelTerm(rel_term_type=OneOf(:specialized_value, v4))

    # Equality and inequality
    @test rt1 == rt2
    @test rt1 != rt3
    @test isequal(rt1, rt2)

    # Hash consistency
    @test hash(rt1) == hash(rt2)

    # Reflexivity
    @test rt1 == rt1
    @test isequal(rt1, rt1)

    # Symmetry
    @test rt1 == rt2 && rt2 == rt1

    # Transitivity
    @test rt1 == rt2 && rt2 == rt8 && rt1 == rt8

    # RelTerm with Term
    var1 = Var(name="x")
    t1 = Term(term_type=OneOf(:var, var1))
    t2 = Term(term_type=OneOf(:var, var1))

    rt4 = RelTerm(rel_term_type=OneOf(:term, t1))
    rt5 = RelTerm(rel_term_type=OneOf(:term, t2))

    @test rt4 == rt5
    @test hash(rt4) == hash(rt5)

    # Different discriminants
    @test rt1 != rt4

    # Nothing value
    rt6 = RelTerm(rel_term_type=nothing)
    rt7 = RelTerm(rel_term_type=nothing)

    @test rt6 == rt7
    @test hash(rt6) == hash(rt7)
    @test rt1 != rt6
end

@testitem "Equality for Atom" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Atom, RelationId, Term, Var
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    r4 = RelationId(id_low=1, id_high=0)

    v1 = Var(name="x")
    t1 = Term(term_type=OneOf(:var, v1))

    a1 = Atom(name=r1, terms=[t1])
    a2 = Atom(name=r2, terms=[t1])
    a3 = Atom(name=r3, terms=[t1])
    a4 = Atom(name=r1, terms=[])
    a5 = Atom(name=r4, terms=[t1])

    # Equality and inequality
    @test a1 == a2
    @test a1 != a3
    @test a1 != a4
    @test isequal(a1, a2)

    # Hash consistency
    @test hash(a1) == hash(a2)

    # Reflexivity
    @test a1 == a1
    @test isequal(a1, a1)

    # Symmetry
    @test a1 == a2 && a2 == a1

    # Transitivity
    @test a1 == a2 && a2 == a5 && a1 == a5
end

@testitem "Equality for Pragma" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Pragma, Term, Var, Value
    using ProtoBuf: OneOf

    v1 = Value(value=OneOf(:string_value, "true"))
    v2 = Value(value=OneOf(:string_value, "false"))
    t1 = Term(term_type=OneOf(:constant, v1))
    t2 = Term(term_type=OneOf(:constant, v2))

    p1 = Pragma(name="inline", terms=[t1])
    p2 = Pragma(name="inline", terms=[t1])
    p3 = Pragma(name="inline", terms=[t2])
    p4 = Pragma(name="noinline", terms=[t1])
    p5 = Pragma(name="inline", terms=[t1])

    # Equality and inequality
    @test p1 == p2
    @test p1 != p3
    @test p1 != p4
    @test isequal(p1, p2)

    # Hash consistency
    @test hash(p1) == hash(p2)

    # Reflexivity
    @test p1 == p1
    @test isequal(p1, p1)

    # Symmetry
    @test p1 == p2 && p2 == p1

    # Transitivity
    @test p1 == p2 && p2 == p5 && p1 == p5
end

@testitem "Equality for Cast" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Cast, Term, Var, Value
    using ProtoBuf: OneOf

    v = Var(name="x")
    input_term = Term(term_type=OneOf(:var, v))

    val1 = Value(value=OneOf(:int_value, 42))
    result_term1 = Term(term_type=OneOf(:constant, val1))

    val2 = Value(value=OneOf(:int_value, 99))
    result_term2 = Term(term_type=OneOf(:constant, val2))

    c1 = Cast(input=input_term, result=result_term1)
    c2 = Cast(input=input_term, result=result_term1)
    c3 = Cast(input=input_term, result=result_term2)
    c4 = Cast(input=input_term, result=result_term1)

    # Equality and inequality
    @test c1 == c2
    @test c1 != c3
    @test isequal(c1, c2)

    # Hash consistency
    @test hash(c1) == hash(c2)

    # Reflexivity
    @test c1 == c1
    @test isequal(c1, c1)

    # Symmetry
    @test c1 == c2 && c2 == c1

    # Transitivity
    @test c1 == c2 && c2 == c4 && c1 == c4
end

@testitem "Equality for Algorithm" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Algorithm, Script, Construct, Loop, Instruction, Assign, RelationId, Abstraction
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    abs1 = Abstraction(vars=[], value=nothing)
    assign1 = Assign(name=r1, body=abs1, attrs=[])

    i1 = Instruction(instr_type=OneOf(:assign, assign1))
    loop1 = Loop(init=[i1], body=Script(constructs=[]))

    c1 = Construct(construct_type=OneOf(:loop, loop1))
    s1 = Script(constructs=[c1])
    s2 = Script(constructs=[c1])
    s3 = Script(constructs=[])
    s4 = Script(constructs=[c1])

    a1 = Algorithm(var"#global"=[r1], body=s1)
    a2 = Algorithm(var"#global"=[r1], body=s2)
    a3 = Algorithm(var"#global"=[], body=s1)
    a4 = Algorithm(var"#global"=[r1], body=s3)
    a5 = Algorithm(var"#global"=[r1], body=s4)

    # Equality and inequality
    @test a1 == a2
    @test a1 != a3
    @test a1 != a4
    @test isequal(a1, a2)

    # Hash consistency
    @test hash(a1) == hash(a2)

    # Reflexivity
    @test a1 == a1
    @test isequal(a1, a1)

    # Symmetry
    @test a1 == a2 && a2 == a1

    # Transitivity
    @test a1 == a2 && a2 == a5 && a1 == a5
end

@testitem "Equality for Abstraction" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Abstraction, Binding, Var, var"#Type", IntType, Formula, Atom, RelationId
    using ProtoBuf: OneOf

    v1 = Var(name="x")
    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    b1 = Binding(var=v1, var"#type"=t1)

    r1 = RelationId(id_low=1, id_high=0)
    atom = Atom(name=r1, terms=[])
    f1 = Formula(formula_type=OneOf(:atom, atom))

    a1 = Abstraction(vars=[b1], value=f1)
    a2 = Abstraction(vars=[b1], value=f1)
    a3 = Abstraction(vars=[], value=f1)
    a4 = Abstraction(vars=[b1], value=nothing)
    a5 = Abstraction(vars=[b1], value=f1)

    # Equality and inequality
    @test a1 == a2
    @test a1 != a3
    @test a1 != a4
    @test isequal(a1, a2)

    # Hash consistency
    @test hash(a1) == hash(a2)

    # Reflexivity
    @test a1 == a1
    @test isequal(a1, a1)

    # Symmetry
    @test a1 == a2 && a2 == a1

    # Transitivity
    @test a1 == a2 && a2 == a5 && a1 == a5
end

@testitem "Equality for Conjunction and Disjunction" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Conjunction, Disjunction, Formula, Atom, RelationId
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    atom = Atom(name=r1, terms=[])
    f1 = Formula(formula_type=OneOf(:atom, atom))

    # Conjunction tests
    c1 = Conjunction(args=[f1])
    c2 = Conjunction(args=[f1])
    c3 = Conjunction(args=[])
    c4 = Conjunction(args=[f1])

    # Equality and inequality
    @test c1 == c2
    @test c1 != c3
    @test isequal(c1, c2)

    # Hash consistency
    @test hash(c1) == hash(c2)

    # Reflexivity
    @test c1 == c1
    @test isequal(c1, c1)

    # Symmetry
    @test c1 == c2 && c2 == c1

    # Transitivity
    @test c1 == c2 && c2 == c4 && c1 == c4

    # Disjunction tests
    d1 = Disjunction(args=[f1])
    d2 = Disjunction(args=[f1])
    d3 = Disjunction(args=[])
    d4 = Disjunction(args=[f1])

    # Equality and inequality
    @test d1 == d2
    @test d1 != d3
    @test isequal(d1, d2)

    # Hash consistency
    @test hash(d1) == hash(d2)

    # Reflexivity
    @test d1 == d1
    @test isequal(d1, d1)

    # Symmetry
    @test d1 == d2 && d2 == d1

    # Transitivity
    @test d1 == d2 && d2 == d4 && d1 == d4
end

@testitem "Equality for Not and Exists" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Not, Exists, Abstraction, Formula, Atom, RelationId
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    atom = Atom(name=r1, terms=[])
    f1 = Formula(formula_type=OneOf(:atom, atom))
    f2 = Formula(formula_type=OneOf(:atom, atom))
    f3 = Formula(formula_type=OneOf(:atom, atom))

    # Not tests
    n1 = Not(arg=f1)
    n2 = Not(arg=f2)
    n3 = Not(arg=nothing)
    n4 = Not(arg=f3)

    # Equality and inequality
    @test n1 == n2
    @test n1 != n3
    @test isequal(n1, n2)

    # Hash consistency
    @test hash(n1) == hash(n2)

    # Reflexivity
    @test n1 == n1
    @test isequal(n1, n1)

    # Symmetry
    @test n1 == n2 && n2 == n1

    # Transitivity
    @test n1 == n2 && n2 == n4 && n1 == n4

    # Exists tests
    abs1 = Abstraction(vars=[], value=f1)
    abs2 = Abstraction(vars=[], value=f2)
    abs3 = Abstraction(vars=[], value=f3)

    e1 = Exists(body=abs1)
    e2 = Exists(body=abs2)
    e3 = Exists(body=nothing)
    e4 = Exists(body=abs3)

    # Equality and inequality
    @test e1 == e2
    @test e1 != e3
    @test isequal(e1, e2)

    # Hash consistency
    @test hash(e1) == hash(e2)

    # Reflexivity
    @test e1 == e1
    @test isequal(e1, e1)

    # Symmetry
    @test e1 == e2 && e2 == e1

    # Transitivity
    @test e1 == e2 && e2 == e4 && e1 == e4
end

@testitem "Equality for Break" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Break, RelationId, Abstraction, Attribute, Value
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    r4 = RelationId(id_low=1, id_high=0)

    abs1 = Abstraction(vars=[], value=nothing)
    v1 = Value(value=OneOf(:string_value, "v"))
    attr1 = Attribute(name="k", args=[v1])

    b1 = Break(name=r1, body=abs1, attrs=[attr1])
    b2 = Break(name=r2, body=abs1, attrs=[attr1])
    b3 = Break(name=r3, body=abs1, attrs=[attr1])
    b4 = Break(name=r4, body=abs1, attrs=[attr1])

    # Equality and inequality
    @test b1 == b2
    @test b1 != b3
    @test isequal(b1, b2)

    # Hash consistency
    @test hash(b1) == hash(b2)

    # Reflexivity
    @test b1 == b1
    @test isequal(b1, b1)

    # Symmetry
    @test b1 == b2 && b2 == b1

    # Transitivity
    @test b1 == b2 && b2 == b4 && b1 == b4
end

@testitem "Equality for Def and Assign" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Def, Assign, RelationId, Abstraction, Attribute, Value
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    r4 = RelationId(id_low=1, id_high=0)

    abs1 = Abstraction(vars=[], value=nothing)
    v1 = Value(value=OneOf(:string_value, "v"))
    attr1 = Attribute(name="k", args=[v1])

    # Def tests
    d1 = Def(name=r1, body=abs1, attrs=[attr1])
    d2 = Def(name=r2, body=abs1, attrs=[attr1])
    d3 = Def(name=r3, body=abs1, attrs=[attr1])
    d4 = Def(name=r4, body=abs1, attrs=[attr1])

    # Equality and inequality
    @test d1 == d2
    @test d1 != d3
    @test isequal(d1, d2)

    # Hash consistency
    @test hash(d1) == hash(d2)

    # Reflexivity
    @test d1 == d1
    @test isequal(d1, d1)

    # Symmetry
    @test d1 == d2 && d2 == d1

    # Transitivity
    @test d1 == d2 && d2 == d4 && d1 == d4

    # Assign tests
    a1 = Assign(name=r1, body=abs1, attrs=[attr1])
    a2 = Assign(name=r2, body=abs1, attrs=[attr1])
    a3 = Assign(name=r3, body=abs1, attrs=[attr1])
    a4 = Assign(name=r4, body=abs1, attrs=[attr1])

    # Equality and inequality
    @test a1 == a2
    @test a1 != a3
    @test isequal(a1, a2)

    # Hash consistency
    @test hash(a1) == hash(a2)

    # Reflexivity
    @test a1 == a1
    @test isequal(a1, a1)

    # Symmetry
    @test a1 == a2 && a2 == a1

    # Transitivity
    @test a1 == a2 && a2 == a4 && a1 == a4
end

@testitem "Equality for MonusDef" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: MonusDef, Monoid, MinMonoid, RelationId, Abstraction, Attribute, Value, var"#Type", IntType
    using ProtoBuf: OneOf

    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    min1 = MinMonoid(var"#type"=t1)
    mon1 = Monoid(OneOf(:min, min1))

    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    r4 = RelationId(id_low=1, id_high=0)

    abs1 = Abstraction(vars=[], value=nothing)
    v1 = Value(value=OneOf(:string_value, "v"))
    attr1 = Attribute(name="k", args=[v1])

    md1 = MonusDef(monoid=mon1, name=r1, body=abs1, attrs=[attr1], value_arity=2)
    md2 = MonusDef(monoid=mon1, name=r2, body=abs1, attrs=[attr1], value_arity=2)
    md3 = MonusDef(monoid=mon1, name=r3, body=abs1, attrs=[attr1], value_arity=2)
    md4 = MonusDef(monoid=mon1, name=r1, body=abs1, attrs=[attr1], value_arity=3)
    md5 = MonusDef(monoid=mon1, name=r4, body=abs1, attrs=[attr1], value_arity=2)

    # Equality and inequality
    @test md1 == md2
    @test md1 != md3
    @test md1 != md4
    @test isequal(md1, md2)

    # Hash consistency
    @test hash(md1) == hash(md2)

    # Reflexivity
    @test md1 == md1
    @test isequal(md1, md1)

    # Symmetry
    @test md1 == md2 && md2 == md1

    # Transitivity
    @test md1 == md2 && md2 == md5 && md1 == md5
end

@testitem "Equality for FragmentId and DebugInfo" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: FragmentId, DebugInfo, RelationId

    # FragmentId tests
    fid1 = FragmentId(id=UInt8[1, 2, 3])
    fid2 = FragmentId(id=UInt8[1, 2, 3])
    fid3 = FragmentId(id=UInt8[1, 2, 4])
    fid4 = FragmentId(id=UInt8[1, 2, 3])

    # Equality and inequality
    @test fid1 == fid2
    @test fid1 != fid3
    @test isequal(fid1, fid2)

    # Hash consistency
    @test hash(fid1) == hash(fid2)

    # Reflexivity
    @test fid1 == fid1
    @test isequal(fid1, fid1)

    # Symmetry
    @test fid1 == fid2 && fid2 == fid1

    # Transitivity
    @test fid1 == fid2 && fid2 == fid4 && fid1 == fid4

    # DebugInfo tests
    r1 = RelationId(id_low=1, id_high=0)
    di1 = DebugInfo(ids=[r1], orig_names=["x"])
    di2 = DebugInfo(ids=[r1], orig_names=["x"])
    di3 = DebugInfo(ids=[r1], orig_names=["y"])
    di4 = DebugInfo(ids=[r1], orig_names=["x"])

    # Equality and inequality
    @test di1 == di2
    @test di1 != di3
    @test isequal(di1, di2)

    # Hash consistency
    @test hash(di1) == hash(di2)

    # Reflexivity
    @test di1 == di1
    @test isequal(di1, di1)

    # Symmetry
    @test di1 == di2 && di2 == di1

    # Transitivity
    @test di1 == di2 && di2 == di4 && di1 == di4
end

@testitem "Equality for Loop" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Loop, Instruction, Script, Construct, Assign, RelationId, Abstraction
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    abs1 = Abstraction(vars=[], value=nothing)
    assign1 = Assign(name=r1, body=abs1, attrs=[])
    assign2 = Assign(name=r1, body=abs1, attrs=[])
    assign3 = Assign(name=r1, body=abs1, attrs=[])

    i1 = Instruction(instr_type=OneOf(:assign, assign1))
    i2 = Instruction(instr_type=OneOf(:assign, assign2))
    i3 = Instruction(instr_type=OneOf(:assign, assign3))

    c1 = Construct(construct_type=OneOf(:instruction, i1))
    s1 = Script(constructs=[c1])
    s2 = Script(constructs=[c1])
    s3 = Script(constructs=[c1])

    l1 = Loop(init=[i1], body=s1)
    l2 = Loop(init=[i2], body=s2)
    l3 = Loop(init=[], body=s1)
    l4 = Loop(init=[i1], body=Script(constructs=[]))
    l5 = Loop(init=[i3], body=s3)

    # Equality and inequality
    @test l1 == l2
    @test l1 != l3
    @test l1 != l4
    @test isequal(l1, l2)

    # Hash consistency
    @test hash(l1) == hash(l2)

    # Reflexivity
    @test l1 == l1
    @test isequal(l1, l1)

    # Symmetry
    @test l1 == l2 && l2 == l1

    # Transitivity
    @test l1 == l2 && l2 == l5 && l1 == l5
end

@testitem "Equality for Instruction (OneOf wrapper)" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Instruction, Assign, Break, RelationId, Abstraction
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    abs1 = Abstraction(vars=[], value=nothing)

    assign1 = Assign(name=r1, body=abs1, attrs=[])
    assign2 = Assign(name=r1, body=abs1, attrs=[])
    assign3 = Assign(name=r1, body=abs1, attrs=[])
    break1 = Break(name=r1, body=abs1, attrs=[])

    i1 = Instruction(instr_type=OneOf(:assign, assign1))
    i2 = Instruction(instr_type=OneOf(:assign, assign2))
    i3 = Instruction(instr_type=OneOf(:break, break1))
    i4 = Instruction(instr_type=nothing)
    i5 = Instruction(instr_type=nothing)
    i6 = Instruction(instr_type=OneOf(:assign, assign3))

    # Same discriminant, same value
    @test i1 == i2
    @test isequal(i1, i2)

    # Hash consistency
    @test hash(i1) == hash(i2)

    # Reflexivity
    @test i1 == i1
    @test isequal(i1, i1)

    # Symmetry
    @test i1 == i2 && i2 == i1

    # Transitivity
    @test i1 == i2 && i2 == i6 && i1 == i6

    # Different discriminant
    @test i1 != i3

    # Nothing values
    @test i4 == i5
    @test hash(i4) == hash(i5)
    @test isequal(i4, i5)

    # Nothing vs non-nothing
    @test i1 != i4
end

@testitem "Equality for Fragment" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Fragment, FragmentId, Declaration, DebugInfo

    fid1 = FragmentId(id=UInt8[1, 2, 3])
    fid2 = FragmentId(id=UInt8[1, 2, 3])
    fid3 = FragmentId(id=UInt8[1, 2, 3])

    f1 = Fragment(id=fid1, declarations=[], debug_info=nothing)
    f2 = Fragment(id=fid2, declarations=[], debug_info=nothing)
    f3 = Fragment(id=nothing, declarations=[], debug_info=nothing)
    f4 = Fragment(id=fid3, declarations=[], debug_info=nothing)

    # Equality and inequality
    @test f1 == f2
    @test f1 != f3
    @test isequal(f1, f2)

    # Hash consistency
    @test hash(f1) == hash(f2)

    # Reflexivity
    @test f1 == f1
    @test isequal(f1, f1)

    # Symmetry
    @test f1 == f2 && f2 == f1

    # Transitivity
    @test f1 == f2 && f2 == f4 && f1 == f4
end

@testitem "Equality for Transaction components" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Demand, Output, Abort, Sync, Context, RelationId, FragmentId

    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    r4 = RelationId(id_low=1, id_high=0)

    # Demand tests
    d1 = Demand(relation_id=r1)
    d2 = Demand(relation_id=r2)
    d3 = Demand(relation_id=r3)
    d4 = Demand(relation_id=r4)

    @test d1 == d2
    @test d1 != d3
    @test hash(d1) == hash(d2)

    # Hash consistency
    @test hash(d1) == hash(d2)

    # Reflexivity
    @test d1 == d1
    @test isequal(d1, d1)

    # Symmetry
    @test d1 == d2 && d2 == d1

    # Transitivity
    @test d1 == d2 && d2 == d4 && d1 == d4

    # Output tests
    o1 = Output(name="out1", relation_id=r1)
    o2 = Output(name="out1", relation_id=r2)
    o3 = Output(name="out2", relation_id=r1)
    o4 = Output(name="out1", relation_id=r4)

    @test o1 == o2
    @test o1 != o3
    @test isequal(o1, o2)

    # Hash consistency
    @test hash(o1) == hash(o2)

    # Reflexivity
    @test o1 == o1
    @test isequal(o1, o1)

    # Symmetry
    @test o1 == o2 && o2 == o1

    # Transitivity
    @test o1 == o2 && o2 == o4 && o1 == o4

    # Abort tests
    a1 = Abort(name="error", relation_id=r1)
    a2 = Abort(name="error", relation_id=r2)
    a3 = Abort(name="other", relation_id=r1)
    a4 = Abort(name="error", relation_id=r4)

    @test a1 == a2
    @test a1 != a3
    @test isequal(a1, a2)

    # Hash consistency
    @test hash(a1) == hash(a2)

    # Reflexivity
    @test a1 == a1
    @test isequal(a1, a1)

    # Symmetry
    @test a1 == a2 && a2 == a1

    # Transitivity
    @test a1 == a2 && a2 == a4 && a1 == a4

    # Sync tests
    fid1 = FragmentId(id=UInt8[1, 2, 3])
    fid2 = FragmentId(id=UInt8[1, 2, 3])
    fid3 = FragmentId(id=UInt8[4, 5, 6])
    fid4 = FragmentId(id=UInt8[1, 2, 3])

    s1 = Sync(fragments=[fid1])
    s2 = Sync(fragments=[fid2])
    s3 = Sync(fragments=[fid3])
    s4 = Sync(fragments=[fid4])

    @test s1 == s2
    @test s1 != s3
    @test isequal(s1, s2)

    # Hash consistency
    @test hash(s1) == hash(s2)

    # Reflexivity
    @test s1 == s1
    @test isequal(s1, s1)

    # Symmetry
    @test s1 == s2 && s2 == s1

    # Transitivity
    @test s1 == s2 && s2 == s4 && s1 == s4

    # Context tests
    c1 = Context(relations=[r1])
    c2 = Context(relations=[r2])
    c3 = Context(relations=[])
    c4 = Context(relations=[r4])

    @test c1 == c2
    @test c1 != c3
    @test isequal(c1, c2)

    # Hash consistency
    @test hash(c1) == hash(c2)

    # Reflexivity
    @test c1 == c1
    @test isequal(c1, c1)

    # Symmetry
    @test c1 == c2 && c2 == c1

    # Transitivity
    @test c1 == c2 && c2 == c4 && c1 == c4
end

@testitem "Equality for Define" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Define, Fragment, FragmentId

    fid1 = FragmentId(id=UInt8[1, 2, 3])
    fid2 = FragmentId(id=UInt8[1, 2, 3])
    fid3 = FragmentId(id=UInt8[4, 5, 6])
    fid4 = FragmentId(id=UInt8[1, 2, 3])

    f1 = Fragment(id=fid1, declarations=[], debug_info=nothing)
    f2 = Fragment(id=fid2, declarations=[], debug_info=nothing)
    f3 = Fragment(id=fid3, declarations=[], debug_info=nothing)
    f4 = Fragment(id=fid4, declarations=[], debug_info=nothing)

    d1 = Define(fragment=f1)
    d2 = Define(fragment=f2)
    d3 = Define(fragment=f3)
    d4 = Define(fragment=f4)

    # Equality and inequality
    @test d1 == d2
    @test d1 != d3
    @test isequal(d1, d2)

    # Hash consistency
    @test hash(d1) == hash(d2)

    # Reflexivity
    @test d1 == d1
    @test isequal(d1, d1)

    # Symmetry
    @test d1 == d2 && d2 == d1

    # Transitivity
    @test d1 == d2 && d2 == d4 && d1 == d4
end

@testitem "Equality for Snapshot" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Snapshot, RelationId

    r1 = RelationId(id_low=0x1234, id_high=0x0)
    r2 = RelationId(id_low=0x1234, id_high=0x0)
    r3 = RelationId(id_low=0x5678, id_high=0x0)

    s1 = Snapshot(destination_path=["my_edb"], source_relation=r1)
    s2 = Snapshot(destination_path=["my_edb"], source_relation=r2)
    s3 = Snapshot(destination_path=["other_edb"], source_relation=r1)
    s4 = Snapshot(destination_path=["my_edb"], source_relation=r3)
    s5 = Snapshot(destination_path=["my_edb"], source_relation=r1)

    # Equality and inequality
    @test s1 == s2
    @test s1 != s3
    @test s1 != s4
    @test isequal(s1, s2)

    # Hash consistency
    @test hash(s1) == hash(s2)

    # Reflexivity
    @test s1 == s1
    @test isequal(s1, s1)

    # Symmetry
    @test s1 == s2 && s2 == s1

    # Transitivity
    @test s1 == s2 && s2 == s5 && s1 == s5

    # Multi-segment path
    s6 = Snapshot(destination_path=["schema", "table"], source_relation=r1)
    s7 = Snapshot(destination_path=["schema", "table"], source_relation=r1)
    @test s6 == s7
    @test hash(s6) == hash(s7)
    @test s6 != s1
end

@testitem "Equality for Configure" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Configure, IVMConfig, MaintenanceLevel

    ivm1 = IVMConfig(level=MaintenanceLevel.MAINTENANCE_LEVEL_AUTO)
    ivm2 = IVMConfig(level=MaintenanceLevel.MAINTENANCE_LEVEL_AUTO)
    ivm3 = IVMConfig(level=MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    ivm4 = IVMConfig(level=MaintenanceLevel.MAINTENANCE_LEVEL_AUTO)

    c1 = Configure(ivm_config=ivm1)
    c2 = Configure(ivm_config=ivm2)
    c3 = Configure(ivm_config=ivm3)
    c4 = Configure(ivm_config=ivm4)

    # Equality and inequality
    @test c1 == c2
    @test c1 != c3
    @test isequal(c1, c2)

    # Hash consistency
    @test hash(c1) == hash(c2)

    # Reflexivity
    @test c1 == c1
    @test isequal(c1, c1)

    # Symmetry
    @test c1 == c2 && c2 == c1

    # Transitivity
    @test c1 == c2 && c2 == c4 && c1 == c4
end

@testitem "Equality for FunctionalDependency" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: FunctionalDependency, Abstraction, Var

    abs1 = Abstraction(vars=[], value=nothing)
    abs2 = Abstraction(vars=[], value=nothing)
    abs3 = Abstraction(vars=[], value=nothing)
    abs4 = Abstraction(vars=[], value=nothing)

    v1 = Var(name="x")
    v2 = Var(name="y")

    fd1 = FunctionalDependency(guard=abs1, keys=[v1], values=[v2])
    fd2 = FunctionalDependency(guard=abs2, keys=[v1], values=[v2])
    fd3 = FunctionalDependency(guard=abs3, keys=[v2], values=[v1])
    fd4 = FunctionalDependency(guard=abs1, keys=[], values=[v2])
    fd5 = FunctionalDependency(guard=abs1, keys=[v1], values=[])
    fd6 = FunctionalDependency(guard=abs4, keys=[v1], values=[v2])

    # Equality and inequality
    @test fd1 == fd2
    @test fd1 != fd3
    @test fd1 != fd4
    @test fd1 != fd5
    @test isequal(fd1, fd2)

    # Hash consistency
    @test hash(fd1) == hash(fd2)

    # Reflexivity
    @test fd1 == fd1
    @test isequal(fd1, fd1)

    # Symmetry
    @test fd1 == fd2 && fd2 == fd1

    # Transitivity
    @test fd1 == fd2 && fd2 == fd6 && fd1 == fd6
end

@testitem "Equality for Epoch and Transaction" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Epoch, Transaction, Read, Write, Configure

    r1 = Read(read_type=nothing)
    w1 = Write(write_type=nothing)

    # Epoch tests
    e1 = Epoch(writes=[w1], reads=[r1])
    e2 = Epoch(writes=[w1], reads=[r1])
    e3 = Epoch(writes=[], reads=[r1])
    e4 = Epoch(writes=[w1], reads=[r1])

    # Equality and inequality
    @test e1 == e2
    @test e1 != e3
    @test isequal(e1, e2)

    # Hash consistency
    @test hash(e1) == hash(e2)

    # Reflexivity
    @test e1 == e1
    @test isequal(e1, e1)

    # Symmetry
    @test e1 == e2 && e2 == e1

    # Transitivity
    @test e1 == e2 && e2 == e4 && e1 == e4

    # Transaction tests
    t1 = Transaction(epochs=[e1], configure=nothing)
    t2 = Transaction(epochs=[e2], configure=nothing)
    t3 = Transaction(epochs=[], configure=nothing)
    t4 = Transaction(epochs=[e4], configure=nothing)

    # Equality and inequality
    @test t1 == t2
    @test t1 != t3
    @test isequal(t1, t2)

    # Hash consistency
    @test hash(t1) == hash(t2)

    # Reflexivity
    @test t1 == t1
    @test isequal(t1, t1)

    # Symmetry
    @test t1 == t2 && t2 == t1

    # Transitivity
    @test t1 == t2 && t2 == t4 && t1 == t4
end

@testitem "Types work in Sets" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Var, RelationId, Atom, Term, Value
    using ProtoBuf: OneOf

    # Vars
    v1 = Var(name="x")
    v2 = Var(name="x")
    v3 = Var(name="y")
    s = Set([v1, v2, v3])
    @test length(s) == 2
    @test v1 in s
    @test v2 in s
    @test v3 in s

    # RelationIds
    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    s = Set([r1, r2, r3])
    @test length(s) == 2

    # Values with OneOf
    val1 = Value(value=OneOf(:int_value, 1))
    val2 = Value(value=OneOf(:int_value, 1))
    val3 = Value(value=OneOf(:int_value, 2))
    s = Set([val1, val2, val3])
    @test length(s) == 2
end

@testitem "Types work in Dicts" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Var, RelationId, Value
    using ProtoBuf: OneOf

    # Vars as keys
    v1 = Var(name="x")
    v2 = Var(name="x")
    v3 = Var(name="y")
    d = Dict(v1 => 1, v3 => 2)
    @test d[v2] == 1  # v2 == v1, so should retrieve same value
    @test d[v3] == 2

    # RelationIds as keys
    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    d = Dict(r1 => "a", r3 => "b")
    @test d[r2] == "a"
    @test d[r3] == "b"

    # Values as keys
    val1 = Value(value=OneOf(:string_value, "key1"))
    val2 = Value(value=OneOf(:string_value, "key1"))
    val3 = Value(value=OneOf(:string_value, "key2"))
    d = Dict(val1 => 100, val3 => 200)
    @test d[val2] == 100
    @test d[val3] == 200
end

@testitem "Equality for ExportCSVColumn" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: ExportCSVColumn, RelationId

    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    r4 = RelationId(id_low=1, id_high=0)

    col1 = ExportCSVColumn(column_name="name", column_data=r1)
    col2 = ExportCSVColumn(column_name="name", column_data=r2)
    col3 = ExportCSVColumn(column_name="age", column_data=r1)
    col4 = ExportCSVColumn(column_name="name", column_data=r3)
    col5 = ExportCSVColumn(column_name="name", column_data=r4)

    # Equality and inequality
    @test col1 == col2
    @test col1 != col3
    @test col1 != col4
    @test isequal(col1, col2)

    # Hash consistency
    @test hash(col1) == hash(col2)

    # Reflexivity
    @test col1 == col1
    @test isequal(col1, col1)

    # Symmetry
    @test col1 == col2 && col2 == col1

    # Transitivity
    @test col1 == col2 && col2 == col5 && col1 == col5
end

@testitem "Equality for ExportCSVConfig" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: ExportCSVConfig, ExportCSVColumn, RelationId

    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=2, id_high=0)

    col1 = ExportCSVColumn(column_name="name", column_data=r1)
    col2 = ExportCSVColumn(column_name="age", column_data=r2)

    # Test with minimal required fields
    cfg1 = ExportCSVConfig(
        path="/data/output.csv",
        data_columns=[col1, col2]
    )
    cfg2 = ExportCSVConfig(
        path="/data/output.csv",
        data_columns=[col1, col2]
    )
    cfg3 = ExportCSVConfig(
        path="/data/output2.csv",
        data_columns=[col1, col2]
    )
    cfg4 = ExportCSVConfig(
        path="/data/output.csv",
        data_columns=[col1]
    )
    cfg_trans = ExportCSVConfig(
        path="/data/output.csv",
        data_columns=[col1, col2]
    )

    # Equality and inequality
    @test cfg1 == cfg2
    @test cfg1 != cfg3
    @test cfg1 != cfg4
    @test isequal(cfg1, cfg2)

    # Hash consistency
    @test hash(cfg1) == hash(cfg2)

    # Reflexivity
    @test cfg1 == cfg1
    @test isequal(cfg1, cfg1)

    # Symmetry
    @test cfg1 == cfg2 && cfg2 == cfg1

    # Transitivity
    @test cfg1 == cfg2 && cfg2 == cfg_trans && cfg1 == cfg_trans

    # Test with optional fields
    cfg5 = ExportCSVConfig(
        path="/data/output.csv",
        data_columns=[col1],
        partition_size=1000,
        compression="gzip",
        syntax_header_row=true,
        syntax_missing_string="NA",
        syntax_delim=",",
        syntax_quotechar="\"",
        syntax_escapechar="\\"
    )
    cfg6 = ExportCSVConfig(
        path="/data/output.csv",
        data_columns=[col1],
        partition_size=1000,
        compression="gzip",
        syntax_header_row=true,
        syntax_missing_string="NA",
        syntax_delim=",",
        syntax_quotechar="\"",
        syntax_escapechar="\\"
    )
    cfg7 = ExportCSVConfig(
        path="/data/output.csv",
        data_columns=[col1],
        partition_size=2000,
        compression="gzip",
        syntax_header_row=true,
        syntax_missing_string="NA",
        syntax_delim=",",
        syntax_quotechar="\"",
        syntax_escapechar="\\"
    )
    cfg8 = ExportCSVConfig(
        path="/data/output.csv",
        data_columns=[col1],
        partition_size=1000,
        compression="gzip",
        syntax_header_row=true,
        syntax_missing_string="NA",
        syntax_delim=",",
        syntax_quotechar="\"",
        syntax_escapechar="\\"
    )

    # Equality and inequality
    @test cfg5 == cfg6
    @test cfg5 != cfg7
    @test isequal(cfg5, cfg6)

    # Hash consistency
    @test hash(cfg5) == hash(cfg6)

    # Reflexivity
    @test cfg5 == cfg5
    @test isequal(cfg5, cfg5)

    # Symmetry
    @test cfg5 == cfg6 && cfg6 == cfg5

    # Transitivity
    @test cfg5 == cfg6 && cfg6 == cfg8 && cfg5 == cfg8
end

@testitem "Equality for Export" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Export, ExportCSVConfig, ExportCSVColumn, RelationId
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    col1 = ExportCSVColumn(column_name="name", column_data=r1)

    csv_cfg1 = ExportCSVConfig(path="/data/output.csv", data_columns=[col1])
    csv_cfg2 = ExportCSVConfig(path="/data/output.csv", data_columns=[col1])
    csv_cfg3 = ExportCSVConfig(path="/data/other.csv", data_columns=[col1])

    # Create Export instances with OneOf export_config
    e1 = Export(export_config=OneOf(:csv_config, csv_cfg1))
    e2 = Export(export_config=OneOf(:csv_config, csv_cfg2))
    e3 = Export(export_config=OneOf(:csv_config, csv_cfg3))
    e4 = Export(export_config=nothing)
    e5 = Export(export_config=nothing)
    e6 = Export(export_config=OneOf(:csv_config, csv_cfg1))

    # Same discriminant, same value
    @test e1 == e2
    @test isequal(e1, e2)

    # Hash consistency
    @test hash(e1) == hash(e2)

    # Reflexivity
    @test e1 == e1
    @test isequal(e1, e1)

    # Symmetry
    @test e1 == e2 && e2 == e1

    # Transitivity
    @test e1 == e2 && e2 == e6 && e1 == e6

    # Same discriminant, different value
    @test e1 != e3

    # Nothing values
    @test e4 == e5
    @test hash(e4) == hash(e5)
    @test isequal(e4, e5)

    # Nothing vs non-nothing
    @test e1 != e4
end

@testitem "Equality for BeTreeConfig" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: BeTreeConfig

    b1 = BeTreeConfig(epsilon=0.1, max_pivots=100, max_deltas=50, max_leaf=1000)
    b2 = BeTreeConfig(epsilon=0.1, max_pivots=100, max_deltas=50, max_leaf=1000)
    b3 = BeTreeConfig(epsilon=0.2, max_pivots=100, max_deltas=50, max_leaf=1000)
    b4 = BeTreeConfig(epsilon=0.1, max_pivots=200, max_deltas=50, max_leaf=1000)
    b5 = BeTreeConfig(epsilon=0.1, max_pivots=100, max_deltas=50, max_leaf=1000)

    # Equality and inequality
    @test b1 == b2
    @test b1 != b3
    @test b1 != b4
    @test isequal(b1, b2)

    # Hash consistency
    @test hash(b1) == hash(b2)

    # Reflexivity
    @test b1 == b1
    @test isequal(b1, b1)

    # Symmetry
    @test b1 == b2 && b2 == b1

    # Transitivity
    @test b1 == b2 && b2 == b5 && b1 == b5
end

@testitem "Equality for CSVLocator" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: CSVLocator

    c1 = CSVLocator(paths=["/path/to/file.csv"], inline_data=UInt8[])
    c2 = CSVLocator(paths=["/path/to/file.csv"], inline_data=UInt8[])
    c3 = CSVLocator(paths=["/other/path.csv"], inline_data=UInt8[])
    c4 = CSVLocator(paths=[], inline_data=UInt8[1, 2, 3])
    c5 = CSVLocator(paths=["/path/to/file.csv"], inline_data=UInt8[])

    # Equality and inequality
    @test c1 == c2
    @test c1 != c3
    @test c1 != c4
    @test isequal(c1, c2)

    # Hash consistency
    @test hash(c1) == hash(c2)

    # Reflexivity
    @test c1 == c1
    @test isequal(c1, c1)

    # Symmetry
    @test c1 == c2 && c2 == c1

    # Transitivity
    @test c1 == c2 && c2 == c5 && c1 == c5
end

@testitem "Equality for CSVConfig" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: CSVConfig

    c1 = CSVConfig(
        header_row=1, skip=0, new_line="\n", delimiter=",",
        quotechar="\"", escapechar="\\", comment="#",
        missing_strings=["NA", "null"], decimal_separator=".",
        encoding="UTF-8", compression="gzip"
    )
    c2 = CSVConfig(
        header_row=1, skip=0, new_line="\n", delimiter=",",
        quotechar="\"", escapechar="\\", comment="#",
        missing_strings=["NA", "null"], decimal_separator=".",
        encoding="UTF-8", compression="gzip"
    )
    c3 = CSVConfig(
        header_row=2, skip=0, new_line="\n", delimiter=",",
        quotechar="\"", escapechar="\\", comment="#",
        missing_strings=["NA", "null"], decimal_separator=".",
        encoding="UTF-8", compression="gzip"
    )
    c4 = CSVConfig(
        header_row=1, skip=0, new_line="\n", delimiter=";",
        quotechar="\"", escapechar="\\", comment="#",
        missing_strings=["NA", "null"], decimal_separator=".",
        encoding="UTF-8", compression="gzip"
    )
    c5 = CSVConfig(
        header_row=1, skip=0, new_line="\n", delimiter=",",
        quotechar="\"", escapechar="\\", comment="#",
        missing_strings=["NA", "null"], decimal_separator=".",
        encoding="UTF-8", compression="gzip"
    )

    # Equality and inequality
    @test c1 == c2
    @test c1 != c3
    @test c1 != c4
    @test isequal(c1, c2)

    # Hash consistency
    @test hash(c1) == hash(c2)

    # Reflexivity
    @test c1 == c1
    @test isequal(c1, c1)

    # Symmetry
    @test c1 == c2 && c2 == c1

    # Transitivity
    @test c1 == c2 && c2 == c5 && c1 == c5
end

@testitem "Equality for BeTreeLocator" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: BeTreeLocator, UInt128Value
    using ProtoBuf: OneOf

    u1 = UInt128Value(low=1, high=0)
    u2 = UInt128Value(low=1, high=0)
    u3 = UInt128Value(low=2, high=0)

    b1 = BeTreeLocator(location=OneOf(:root_pageid, u1), element_count=100, tree_height=5)
    b2 = BeTreeLocator(location=OneOf(:root_pageid, u2), element_count=100, tree_height=5)
    b3 = BeTreeLocator(location=OneOf(:root_pageid, u3), element_count=100, tree_height=5)
    b4 = BeTreeLocator(location=OneOf(:inline_data, UInt8[1, 2, 3]), element_count=10, tree_height=1)
    b5 = BeTreeLocator(location=nothing, element_count=0, tree_height=0)
    b6 = BeTreeLocator(location=nothing, element_count=0, tree_height=0)
    b7 = BeTreeLocator(location=OneOf(:root_pageid, u1), element_count=100, tree_height=5)

    # Equality and inequality
    @test b1 == b2
    @test b1 != b3
    @test b1 != b4
    @test isequal(b1, b2)

    # Hash consistency
    @test hash(b1) == hash(b2)

    # Reflexivity
    @test b1 == b1
    @test isequal(b1, b1)

    # Symmetry
    @test b1 == b2 && b2 == b1

    # Transitivity
    @test b1 == b2 && b2 == b7 && b1 == b7

    # Nothing values
    @test b5 == b6
    @test hash(b5) == hash(b6)
    @test isequal(b5, b6)

    # Nothing vs non-nothing
    @test b1 != b5
end

@testitem "Equality for RelEDB" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: RelEDB, RelationId, var"#Type", IntType
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))

    e1 = RelEDB(target_id=r1, path=["table", "column"], types=[t1])
    e2 = RelEDB(target_id=r2, path=["table", "column"], types=[t1])
    e3 = RelEDB(target_id=r3, path=["table", "column"], types=[t1])
    e4 = RelEDB(target_id=r1, path=["other", "column"], types=[t1])
    e5 = RelEDB(target_id=r1, path=["table", "column"], types=[t1])

    # Equality and inequality
    @test e1 == e2
    @test e1 != e3
    @test e1 != e4
    @test isequal(e1, e2)

    # Hash consistency
    @test hash(e1) == hash(e2)

    # Reflexivity
    @test e1 == e1
    @test isequal(e1, e1)

    # Symmetry
    @test e1 == e2 && e2 == e1

    # Transitivity
    @test e1 == e2 && e2 == e5 && e1 == e5
end

@testitem "Equality for BeTreeInfo" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: BeTreeInfo, BeTreeConfig, BeTreeLocator, var"#Type", IntType, UInt128Value
    using ProtoBuf: OneOf

    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    t2 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    cfg1 = BeTreeConfig(epsilon=0.1, max_pivots=100, max_deltas=50, max_leaf=1000)
    cfg2 = BeTreeConfig(epsilon=0.1, max_pivots=100, max_deltas=50, max_leaf=1000)
    u1 = UInt128Value(low=1, high=0)
    loc1 = BeTreeLocator(location=OneOf(:root_pageid, u1), element_count=100, tree_height=5)
    loc2 = BeTreeLocator(location=OneOf(:root_pageid, u1), element_count=100, tree_height=5)

    b1 = BeTreeInfo(key_types=[t1], value_types=[t1], storage_config=cfg1, relation_locator=loc1)
    b2 = BeTreeInfo(key_types=[t2], value_types=[t1], storage_config=cfg2, relation_locator=loc2)
    b3 = BeTreeInfo(key_types=[], value_types=[t1], storage_config=cfg1, relation_locator=loc1)
    b4 = BeTreeInfo(key_types=[t1], value_types=[t1], storage_config=nothing, relation_locator=loc1)
    b5 = BeTreeInfo(key_types=[t1], value_types=[t1], storage_config=cfg1, relation_locator=loc1)

    # Equality and inequality
    @test b1 == b2
    @test b1 != b3
    @test b1 != b4
    @test isequal(b1, b2)

    # Hash consistency
    @test hash(b1) == hash(b2)

    # Reflexivity
    @test b1 == b1
    @test isequal(b1, b1)

    # Symmetry
    @test b1 == b2 && b2 == b1

    # Transitivity
    @test b1 == b2 && b2 == b5 && b1 == b5
end

@testitem "Equality for CSVColumn" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: CSVColumn, RelationId, var"#Type", IntType
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))

    c1 = CSVColumn(column_path=["age"], target_id=r1, types=[t1])
    c2 = CSVColumn(column_path=["age"], target_id=r2, types=[t1])
    c3 = CSVColumn(column_path=["name"], target_id=r1, types=[t1])
    c4 = CSVColumn(column_path=["age"], target_id=r3, types=[t1])
    c5 = CSVColumn(column_path=["age"], target_id=r1, types=[t1])

    # Equality and inequality
    @test c1 == c2
    @test c1 != c3
    @test c1 != c4
    @test isequal(c1, c2)

    # Hash consistency
    @test hash(c1) == hash(c2)

    # Reflexivity
    @test c1 == c1
    @test isequal(c1, c1)

    # Symmetry
    @test c1 == c2 && c2 == c1

    # Transitivity
    @test c1 == c2 && c2 == c5 && c1 == c5
end

@testitem "Equality for BeTreeRelation" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: BeTreeRelation, BeTreeInfo, RelationId, var"#Type", IntType
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    r2 = RelationId(id_low=1, id_high=0)
    r3 = RelationId(id_low=2, id_high=0)
    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    info1 = BeTreeInfo(key_types=[t1], value_types=[t1], storage_config=nothing, relation_locator=nothing)
    info2 = BeTreeInfo(key_types=[t1], value_types=[t1], storage_config=nothing, relation_locator=nothing)

    b1 = BeTreeRelation(name=r1, relation_info=info1)
    b2 = BeTreeRelation(name=r2, relation_info=info2)
    b3 = BeTreeRelation(name=r3, relation_info=info1)
    b4 = BeTreeRelation(name=r1, relation_info=nothing)
    b5 = BeTreeRelation(name=r1, relation_info=info1)

    # Equality and inequality
    @test b1 == b2
    @test b1 != b3
    @test b1 != b4
    @test isequal(b1, b2)

    # Hash consistency
    @test hash(b1) == hash(b2)

    # Reflexivity
    @test b1 == b1
    @test isequal(b1, b1)

    # Symmetry
    @test b1 == b2 && b2 == b1

    # Transitivity
    @test b1 == b2 && b2 == b5 && b1 == b5
end

@testitem "Equality for CSVData" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: CSVData, CSVLocator, CSVConfig, CSVColumn, RelationId, var"#Type", IntType
    using ProtoBuf: OneOf

    loc1 = CSVLocator(paths=["/path/to/file.csv"], inline_data=UInt8[])
    loc2 = CSVLocator(paths=["/path/to/file.csv"], inline_data=UInt8[])
    loc3 = CSVLocator(paths=["/other/path.csv"], inline_data=UInt8[])
    cfg1 = CSVConfig(header_row=1, skip=0, new_line="\n", delimiter=",", quotechar="\"", escapechar="\\", comment="", missing_strings=[], decimal_separator=".", encoding="", compression="")
    cfg2 = CSVConfig(header_row=1, skip=0, new_line="\n", delimiter=",", quotechar="\"", escapechar="\\", comment="", missing_strings=[], decimal_separator=".", encoding="", compression="")
    r1 = RelationId(id_low=1, id_high=0)
    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    col1 = CSVColumn(column_path=["age"], target_id=r1, types=[t1])

    d1 = CSVData(locator=loc1, config=cfg1, columns=[col1], asof="2024-01-01")
    d2 = CSVData(locator=loc2, config=cfg2, columns=[col1], asof="2024-01-01")
    d3 = CSVData(locator=loc3, config=cfg1, columns=[col1], asof="2024-01-01")
    d4 = CSVData(locator=loc1, config=cfg1, columns=[], asof="2024-01-01")
    d5 = CSVData(locator=loc1, config=cfg1, columns=[col1], asof="2024-01-02")
    d6 = CSVData(locator=loc1, config=cfg1, columns=[col1], asof="2024-01-01")

    # Equality and inequality
    @test d1 == d2
    @test d1 != d3
    @test d1 != d4
    @test d1 != d5
    @test isequal(d1, d2)

    # Hash consistency
    @test hash(d1) == hash(d2)

    # Reflexivity
    @test d1 == d1
    @test isequal(d1, d1)

    # Symmetry
    @test d1 == d2 && d2 == d1

    # Transitivity
    @test d1 == d2 && d2 == d6 && d1 == d6
end

@testitem "Equality for Data (OneOf type)" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: Data, RelEDB, BeTreeRelation, CSVData, RelationId, BeTreeInfo, CSVLocator, CSVConfig, CSVColumn, var"#Type", IntType
    using ProtoBuf: OneOf

    r1 = RelationId(id_low=1, id_high=0)
    t1 = var"#Type"(var"#type"=OneOf(:int_type, IntType()))
    edb1 = RelEDB(target_id=r1, path=["table"], types=[t1])
    edb2 = RelEDB(target_id=r1, path=["table"], types=[t1])
    info1 = BeTreeInfo(key_types=[t1], value_types=[], storage_config=nothing, relation_locator=nothing)
    betree1 = BeTreeRelation(name=r1, relation_info=info1)
    loc1 = CSVLocator(paths=["/file.csv"], inline_data=UInt8[])
    cfg1 = CSVConfig(header_row=1, skip=0, new_line="\n", delimiter=",", quotechar="\"", escapechar="\\", comment="", missing_strings=[], decimal_separator=".", encoding="", compression="")
    col1 = CSVColumn(column_path=["col"], target_id=r1, types=[t1])
    csv1 = CSVData(locator=loc1, config=cfg1, columns=[col1], asof="")

    d1 = Data(data_type=OneOf(:rel_edb, edb1))
    d2 = Data(data_type=OneOf(:rel_edb, edb2))
    d3 = Data(data_type=OneOf(:betree_relation, betree1))
    d4 = Data(data_type=OneOf(:csv_data, csv1))
    d5 = Data(data_type=nothing)
    d6 = Data(data_type=nothing)
    d7 = Data(data_type=OneOf(:rel_edb, edb1))

    # Same discriminant, same value
    @test d1 == d2
    @test isequal(d1, d2)

    # Hash consistency
    @test hash(d1) == hash(d2)

    # Reflexivity
    @test d1 == d1
    @test isequal(d1, d1)

    # Symmetry
    @test d1 == d2 && d2 == d1

    # Transitivity
    @test d1 == d2 && d2 == d7 && d1 == d7

    # Different discriminants
    @test d1 != d3
    @test d1 != d4
    @test d3 != d4

    # Nothing values
    @test d5 == d6
    @test hash(d5) == hash(d6)
    @test isequal(d5, d6)

    # Nothing vs non-nothing
    @test d1 != d5
end

@testitem "All LQP types have custom equality implementations" tags=[:ring1, :unit] begin
    using LogicalQueryProtocol: LQPSyntax

    # Get all unique types from LQPSyntax
    all_types = Base.uniontypes(LQPSyntax)

    # Track any types missing implementations
    missing_eq = String[]
    missing_hash = String[]
    missing_isequal = String[]

    # For each type, verify it has custom implementations
    for T in all_types
        # Check that == is defined for this specific type
        eq_methods = methods(==, (T, T))
        if length(eq_methods) < 1
            push!(missing_eq, string(T))
            continue
        end

        # Verify it's not just the default fallback
        has_custom_eq = any(eq_methods) do m
            # Check if the method signature matches our type exactly
            sig = m.sig
            if sig isa UnionAll
                sig = Base.unwrap_unionall(sig)
            end
            if sig isa DataType && length(sig.parameters) >= 3
                return sig.parameters[2] == T && sig.parameters[3] == T
            end
            return false
        end
        if !has_custom_eq
            push!(missing_eq, string(T))
        end

        # Check that hash is defined for this specific type
        hash_methods = methods(hash, (T, UInt))
        if length(hash_methods) < 1
            push!(missing_hash, string(T))
            continue
        end

        # Verify it's not just the default fallback
        has_custom_hash = any(hash_methods) do m
            sig = m.sig
            if sig isa UnionAll
                sig = Base.unwrap_unionall(sig)
            end
            if sig isa DataType && length(sig.parameters) >= 2
                return sig.parameters[2] == T
            end
            return false
        end
        if !has_custom_hash
            push!(missing_hash, string(T))
        end

        # Check that isequal is defined for this specific type
        isequal_methods = methods(isequal, (T, T))
        if length(isequal_methods) < 1
            push!(missing_isequal, string(T))
            continue
        end

        # Verify it's not just the default fallback
        has_custom_isequal = any(isequal_methods) do m
            sig = m.sig
            if sig isa UnionAll
                sig = Base.unwrap_unionall(sig)
            end
            if sig isa DataType && length(sig.parameters) >= 3
                return sig.parameters[2] == T && sig.parameters[3] == T
            end
            return false
        end
        if !has_custom_isequal
            push!(missing_isequal, string(T))
        end
    end

    # Report results
    @test isempty(missing_eq)
    if !isempty(missing_eq)
        @error "Types missing custom == implementation:" missing_eq
    end

    @test isempty(missing_hash)
    if !isempty(missing_hash)
        @error "Types missing custom hash implementation:" missing_hash
    end

    @test isempty(missing_isequal)
    if !isempty(missing_isequal)
        @error "Types missing custom isequal implementation:" missing_isequal
    end

    # Print summary if all passed
    if isempty(missing_eq) && isempty(missing_hash) && isempty(missing_isequal)
        println("✓ Verified $(length(all_types)) LQP types have custom ==, hash, and isequal implementations")
    end
end
