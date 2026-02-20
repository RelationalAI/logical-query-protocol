@testitem "Extra pretty - token: DecimalValue" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto

    pp = PrettyPrinter()
    msg = Proto.DecimalValue(
        precision=Int32(18),
        scale=Int32(6),
        value=Proto.Int128Value(UInt64(123456789), UInt64(0)),
    )
    _pprint_dispatch(pp, msg)
    @test get_output(pp) == "123.456789d18"
end

@testitem "Extra pretty - token: Int128Value" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto

    pp = PrettyPrinter()
    msg = Proto.Int128Value(UInt64(42), UInt64(0))
    _pprint_dispatch(pp, msg)
    @test get_output(pp) == "42i128"

    pp2 = PrettyPrinter()
    msg2 = Proto.Int128Value(typemax(UInt64), typemax(UInt64))
    _pprint_dispatch(pp2, msg2)
    @test get_output(pp2) == "-1i128"
end

@testitem "Extra pretty - token: UInt128Value" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto

    pp = PrettyPrinter()
    msg = Proto.UInt128Value(UInt64(0xff), UInt64(0))
    _pprint_dispatch(pp, msg)
    @test get_output(pp) == "0xff"

    pp2 = PrettyPrinter()
    msg2 = Proto.UInt128Value(UInt64(0), UInt64(0))
    _pprint_dispatch(pp2, msg2)
    @test get_output(pp2) == "0x0"
end

@testitem "Extra pretty - special: MissingValue" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto

    pp = PrettyPrinter()
    _pprint_dispatch(pp, Proto.MissingValue())
    @test get_output(pp) == "missing"
end

@testitem "Extra pretty - special: DebugInfo" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto

    pp = PrettyPrinter()
    _pprint_dispatch(pp, Proto.DebugInfo())
    @test get_output(pp) == "(debug_info)"

    pp2 = PrettyPrinter()
    msg = Proto.DebugInfo(
        ids=[Proto.RelationId(UInt64(1), UInt64(0))],
        orig_names=["my_rel"],
    )
    _pprint_dispatch(pp2, msg)
    @test get_output(pp2) == "(debug_info\n  (0x1 \"my_rel\"))"
end

@testitem "Extra pretty - generic: BeTreeConfig" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto

    pp = PrettyPrinter()
    msg = Proto.BeTreeConfig(
        epsilon=0.5,
        max_pivots=Int64(128),
        max_deltas=Int64(256),
        max_leaf=Int64(512),
    )
    _pprint_dispatch(pp, msg)
    expected = "(be_tree_config\n  :epsilon 0.5\n  :max_pivots 128\n  :max_deltas 256\n  :max_leaf 512)"
    @test get_output(pp) == expected
end

@testitem "Extra pretty - generic: IVMConfig" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto

    pp = PrettyPrinter()
    msg = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO)
    _pprint_dispatch(pp, msg)
    @test get_output(pp) == "(ivm_config\n  :level auto)"

    pp2 = PrettyPrinter()
    msg2 = Proto.IVMConfig(level=Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF)
    _pprint_dispatch(pp2, msg2)
    @test get_output(pp2) == "(ivm_config\n  :level off)"
end

@testitem "Extra pretty - generic: BeTreeLocator" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto
    using ProtoBuf: OneOf

    pp = PrettyPrinter()
    msg = Proto.BeTreeLocator(
        location=OneOf(:root_pageid, Proto.UInt128Value(UInt64(42), UInt64(0))),
        element_count=Int64(100),
        tree_height=Int64(3),
    )
    _pprint_dispatch(pp, msg)
    @test get_output(pp) == "(be_tree_locator\n  :element_count 100\n  :tree_height 3\n  :location (:root_pageid 0x2a))"

    pp2 = PrettyPrinter()
    msg2 = Proto.BeTreeLocator(
        location=OneOf(:inline_data, UInt8[0xab, 0xcd]),
        element_count=Int64(10),
        tree_height=Int64(1),
    )
    _pprint_dispatch(pp2, msg2)
    @test get_output(pp2) == "(be_tree_locator\n  :element_count 10\n  :tree_height 1\n  :location (:inline_data 0xabcd))"

    pp3 = PrettyPrinter()
    msg3 = Proto.BeTreeLocator(
        element_count=Int64(0),
        tree_height=Int64(0),
    )
    _pprint_dispatch(pp3, msg3)
    @test get_output(pp3) == "(be_tree_locator\n  :element_count 0\n  :tree_height 0\n  :location nothing)"
end

@testitem "Extra pretty - enum: MaintenanceLevel" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto

    for (val, str) in [
        (Proto.MaintenanceLevel.MAINTENANCE_LEVEL_UNSPECIFIED, "unspecified"),
        (Proto.MaintenanceLevel.MAINTENANCE_LEVEL_OFF, "off"),
        (Proto.MaintenanceLevel.MAINTENANCE_LEVEL_AUTO, "auto"),
        (Proto.MaintenanceLevel.MAINTENANCE_LEVEL_ALL, "all"),
    ]
        pp = PrettyPrinter()
        _pprint_dispatch(pp, val)
        @test get_output(pp) == str
    end
end

@testitem "Extra pretty - oneof: Term" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto
    using ProtoBuf: OneOf

    pp = PrettyPrinter()
    msg = Proto.Term(OneOf(:var, Proto.Var("x")))
    _pprint_dispatch(pp, msg)
    @test get_output(pp) == "x"

    pp2 = PrettyPrinter()
    msg2 = Proto.Term(OneOf(:constant, Proto.Value(OneOf(:int_value, Int64(42)))))
    _pprint_dispatch(pp2, msg2)
    @test get_output(pp2) == "42"
end

@testitem "Extra pretty - oneof: Value" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto
    using ProtoBuf: OneOf

    pp = PrettyPrinter()
    _pprint_dispatch(pp, Proto.Value(OneOf(:int_value, Int64(99))))
    @test get_output(pp) == "99"

    pp2 = PrettyPrinter()
    _pprint_dispatch(pp2, Proto.Value(OneOf(:string_value, "hello")))
    @test get_output(pp2) == "\"hello\""

    pp3 = PrettyPrinter()
    _pprint_dispatch(pp3, Proto.Value(OneOf(:missing_value, Proto.MissingValue())))
    @test get_output(pp3) == "missing"
end

@testitem "Extra pretty - oneof: Monoid" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto
    using ProtoBuf: OneOf

    pp = PrettyPrinter()
    _pprint_dispatch(pp, Proto.Monoid(OneOf(:or_monoid, Proto.OrMonoid())))
    @test get_output(pp) == "(or)"
end

@testitem "Extra pretty - oneof: Instruction" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto
    using ProtoBuf: OneOf

    pp = PrettyPrinter()
    assign = Proto.Assign(
        name=Proto.RelationId(UInt64(1), UInt64(0)),
        body=Proto.Abstraction(
            value=Proto.Formula(OneOf(:conjunction, Proto.Conjunction())),
        ),
    )
    msg = Proto.Instruction(OneOf(:assign, assign))
    _pprint_dispatch(pp, msg)
    @test startswith(get_output(pp), "(assign")
end

@testitem "Extra pretty - oneof: Data" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto
    using ProtoBuf: OneOf

    pp = PrettyPrinter()
    rel_edb = Proto.RelEDB(
        target_id=Proto.RelationId(UInt64(1), UInt64(0)),
        path=["base", "rel"],
    )
    msg = Proto.Data(OneOf(:rel_edb, rel_edb))
    _pprint_dispatch(pp, msg)
    @test startswith(get_output(pp), "(rel_edb")
end

@testitem "Extra pretty - oneof: Read" begin
    using LogicalQueryProtocol: PrettyPrinter, _pprint_dispatch, get_output, Proto
    using ProtoBuf: OneOf

    pp = PrettyPrinter()
    demand = Proto.Demand(
        relation_id=Proto.RelationId(UInt64(1), UInt64(0)),
    )
    msg = Proto.Read(OneOf(:demand, demand))
    _pprint_dispatch(pp, msg)
    @test startswith(get_output(pp), "(demand")
end
