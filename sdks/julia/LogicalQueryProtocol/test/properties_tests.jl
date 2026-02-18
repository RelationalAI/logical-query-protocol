@testitem "decimal_precision_to_bits" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: decimal_precision_to_bits

    # Boundary values for each bit width
    @test decimal_precision_to_bits(0) == 8
    @test decimal_precision_to_bits(1) == 8
    @test decimal_precision_to_bits(2) == 8
    @test decimal_precision_to_bits(3) == 16
    @test decimal_precision_to_bits(4) == 16
    @test decimal_precision_to_bits(5) == 32
    @test decimal_precision_to_bits(9) == 32
    @test decimal_precision_to_bits(10) == 64
    @test decimal_precision_to_bits(18) == 64
    @test decimal_precision_to_bits(19) == 128
    @test decimal_precision_to_bits(38) == 128
end

@testitem "decimal_bits_to_precision" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: decimal_bits_to_precision

    @test decimal_bits_to_precision(8) == 2
    @test decimal_bits_to_precision(16) == 4
    @test decimal_bits_to_precision(32) == 9
    @test decimal_bits_to_precision(64) == 18
    @test decimal_bits_to_precision(128) == 38
end

@testitem "decimal roundtrip" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: decimal_precision_to_bits, decimal_bits_to_precision

    # bits_to_precision -> precision_to_bits should recover the original bits
    for bits in [8, 16, 32, 64, 128]
        @test decimal_precision_to_bits(decimal_bits_to_precision(bits)) == bits
    end
end

@testitem "is_supported_decimal_bits" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: is_supported_decimal_bits

    for bits in [8, 16, 32, 64, 128]
        @test is_supported_decimal_bits(bits)
    end
    for bits in [0, 1, 4, 7, 15, 24, 48, 96, 256]
        @test !is_supported_decimal_bits(bits)
    end
end

@testitem "lqp_semantics_version" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: lqp_semantics_version
    using LogicalQueryProtocol.relationalai.lqp.v1: Transaction, Epoch, Configure

    # No configure -> version 0
    txn = Transaction(; epochs=Epoch[])
    @test lqp_semantics_version(txn) == 0

    # With configure
    txn = Transaction(; epochs=Epoch[], configure=Configure(; semantics_version=Int64(3)))
    @test lqp_semantics_version(txn) == 3
end

@testitem "is_read_only / is_write_only" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: is_read_only, is_write_only
    using LogicalQueryProtocol.relationalai.lqp.v1
    using ProtoBuf: OneOf

    # Empty transaction is both read-only and write-only
    txn = Transaction(; epochs=Epoch[])
    @test is_read_only(txn)
    @test is_write_only(txn)

    # Empty epoch is both
    epoch = Epoch(; writes=Write[], reads=Read[])
    @test is_read_only(epoch)
    @test is_write_only(epoch)

    # Epoch with a write
    frag = Fragment(; id=FragmentId(; id=UInt8[1]), declarations=Declaration[])
    define = Define(; fragment=frag)
    write = Write(; write_type=OneOf(:define, define))
    epoch_w = Epoch(; writes=[write], reads=Read[])
    @test !is_read_only(epoch_w)
    @test is_write_only(epoch_w)

    # Epoch with a read
    output = Output(; name=RelationId(; id_low=UInt64(1), id_high=UInt64(0)))
    rd = Read(; read_type=OneOf(:output, output))
    epoch_r = Epoch(; writes=Write[], reads=[rd])
    @test is_read_only(epoch_r)
    @test !is_write_only(epoch_r)

    # Transaction-level: mixed epochs
    txn_mixed = Transaction(; epochs=[epoch_w, epoch_r])
    @test !is_read_only(txn_mixed)
    @test !is_write_only(txn_mixed)
end

@testitem "persistent_id" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: persistent_id, LQPFragmentId
    using LogicalQueryProtocol.relationalai.lqp.v1

    # RelationId
    rid = RelationId(; id_low=UInt64(42), id_high=UInt64(0))
    @test persistent_id(rid) == UInt128(42)

    rid2 = RelationId(; id_low=UInt64(0), id_high=UInt64(1))
    @test persistent_id(rid2) == UInt128(1) << 64

    # FragmentId
    fid = FragmentId(; id=UInt8[1, 2, 3])
    @test persistent_id(fid) == LQPFragmentId(UInt8[1, 2, 3])

    # Def
    def = Def(;
        name=RelationId(; id_low=UInt64(7), id_high=UInt64(0)),
        body=Abstraction(; vars=Binding[], value=Formula()),
    )
    @test persistent_id(def) == UInt128(7)
end
