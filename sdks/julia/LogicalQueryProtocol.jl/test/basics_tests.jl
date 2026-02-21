@testitem "Proto type construction" begin
    using LogicalQueryProtocol
    using LogicalQueryProtocol.relationalai.lqp.v1
    using ProtoBuf: OneOf

    v = Var(; name="x")
    @test v.name == "x"

    t = var"#Type"(OneOf(:int_type, IntType()))
    @test !isnothing(t.var"#type")
    @test t.var"#type".name == :int_type
end

@testitem "LQPFragmentId" begin
    using LogicalQueryProtocol: LQPFragmentId

    a = LQPFragmentId(UInt8[1, 2, 3])
    b = LQPFragmentId(UInt8[1, 2, 3])
    c = LQPFragmentId(UInt8[4, 5, 6])
    @test a == b
    @test a != c
    @test hash(a) == hash(b)
    @test a < c
end

@testitem "unwrap / wrap helpers" begin
    using LogicalQueryProtocol: unwrap, wrap_in_formula, wrap_in_term
    using LogicalQueryProtocol.relationalai.lqp.v1
    using ProtoBuf: OneOf

    atom = Atom(; name=RelationId(; id_low=UInt64(1), id_high=UInt64(0)), terms=Term[])
    formula = wrap_in_formula(atom)
    @test formula isa Formula
    @test unwrap(formula) isa Atom
    @test unwrap(formula) == atom

    v = Var(; name="x")
    term = wrap_in_term(v)
    @test term isa Term
    @test unwrap(term) isa Var
    @test unwrap(term) == v
end

@testitem "value_to_type" begin
    using LogicalQueryProtocol: value_to_type
    using LogicalQueryProtocol.relationalai.lqp.v1
    using ProtoBuf: OneOf

    int_val = Value(OneOf(:int_value, Int64(42)))
    int_type = value_to_type(int_val)
    @test int_type.var"#type".name == :int_type

    str_val = Value(OneOf(:string_value, "hello"))
    str_type = value_to_type(str_val)
    @test str_type.var"#type".name == :string_type

    bool_val = Value(OneOf(:boolean_value, true))
    bool_type = value_to_type(bool_val)
    @test bool_type.var"#type".name == :boolean_type
end
