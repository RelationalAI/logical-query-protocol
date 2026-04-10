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
    rid = RelationId(; id_low=UInt64(1), id_high=UInt64(0))
    output = Output(; name="test_output", relation_id=rid)
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

@testitem "global_ids" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: global_ids, persistent_id, LQPRelationId
    using LogicalQueryProtocol.relationalai.lqp.v1
    using ProtoBuf: OneOf

    rid1 = RelationId(; id_low=UInt64(10), id_high=UInt64(0))
    rid2 = RelationId(; id_low=UInt64(20), id_high=UInt64(0))
    rid3 = RelationId(; id_low=UInt64(30), id_high=UInt64(0))
    t1 = var"#Type"(; var"#type"=OneOf(:int_type, IntType()))

    # Def declaration
    def = Def(;
        name=rid1,
        body=Abstraction(; vars=Binding[], value=Formula()),
    )
    decl_def = Declaration(; declaration_type=OneOf(:def, def))
    @test global_ids(decl_def) == [persistent_id(rid1)]

    # Constraint declaration
    fd = FunctionalDependency(; keys=Var[], values=Var[])
    constraint = Constraint(;
        name=rid2,
        constraint_type=OneOf(:functional_dependency, fd),
    )
    decl_constraint = Declaration(; declaration_type=OneOf(:constraint, constraint))
    @test global_ids(decl_constraint) == [persistent_id(rid2)]

    # EDB data declaration
    edb = EDB(; target_id=rid1)
    data_edb = Data(; data_type=OneOf(:edb, edb))
    decl_edb = Declaration(; declaration_type=OneOf(:data, data_edb))
    @test global_ids(decl_edb) == [persistent_id(rid1)]

    # CSVData declaration with multiple columns
    col1 = GNFColumn(; column_path=["a"], target_id=rid1, types=[t1])
    col2 = GNFColumn(; column_path=["b"], target_id=rid2, types=[t1])
    csv = CSVData(; columns=[col1, col2])
    data_csv = Data(; data_type=OneOf(:csv_data, csv))
    @test global_ids(data_csv) == [persistent_id(rid1), persistent_id(rid2)]

    # CSVData skips columns without target_id
    col_no_target = GNFColumn(; column_path=["c"], types=[t1])
    csv2 = CSVData(; columns=[col1, col_no_target, col2])
    data_csv2 = Data(; data_type=OneOf(:csv_data, csv2))
    @test global_ids(data_csv2) == [persistent_id(rid1), persistent_id(rid2)]

    # IcebergData declaration with multiple columns
    loc = IcebergLocator(; table_name="t", namespace=["n"], warehouse="w")
    cfg = IcebergCatalogConfig(;
        catalog_uri="uri", scope="", properties=Dict(), auth_properties=Dict(),
    )
    icol1 = GNFColumn(; column_path=["x"], target_id=rid1, types=[t1])
    icol2 = GNFColumn(; column_path=["y"], target_id=rid2, types=[t1])
    icol3 = GNFColumn(; column_path=["z"], target_id=rid3, types=[t1])
    iceberg = IcebergData(;
        locator=loc, config=cfg, columns=[icol1, icol2, icol3],
        from_snapshot="s1", to_snapshot="s2", returns_delta=false,
    )
    data_iceberg = Data(; data_type=OneOf(:iceberg_data, iceberg))
    @test global_ids(data_iceberg) == [
        persistent_id(rid1), persistent_id(rid2), persistent_id(rid3),
    ]

    # IcebergData skips columns without target_id
    icol_no_target = GNFColumn(; column_path=["w"], types=[t1])
    iceberg2 = IcebergData(;
        locator=loc, config=cfg, columns=[icol1, icol_no_target, icol3],
        from_snapshot="", to_snapshot="", returns_delta=true,
    )
    data_iceberg2 = Data(; data_type=OneOf(:iceberg_data, iceberg2))
    @test global_ids(data_iceberg2) == [persistent_id(rid1), persistent_id(rid3)]

    # Data routed through Declaration
    decl_iceberg = Declaration(; declaration_type=OneOf(:data, data_iceberg))
    @test global_ids(decl_iceberg) == [
        persistent_id(rid1), persistent_id(rid2), persistent_id(rid3),
    ]
end

@testitem "collect_demanded_relations" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: collect_demanded_relations, persistent_id, LQPRelationId
    using LogicalQueryProtocol.relationalai.lqp.v1
    using ProtoBuf: OneOf

    rid1 = RelationId(; id_low=UInt64(1), id_high=UInt64(0))
    rid2 = RelationId(; id_low=UInt64(2), id_high=UInt64(0))
    rid3 = RelationId(; id_low=UInt64(3), id_high=UInt64(0))
    rid4 = RelationId(; id_low=UInt64(4), id_high=UInt64(0))

    # Empty epoch
    epoch = Epoch(; writes=Write[], reads=Read[])
    @test collect_demanded_relations(epoch) == Set{LQPRelationId}()

    # Demand read
    demand = Demand(; relation_id=rid1)
    rd_demand = Read(; read_type=OneOf(:demand, demand))

    # Output read
    output = Output(; name="out", relation_id=rid2)
    rd_output = Read(; read_type=OneOf(:output, output))

    # Abort read
    abort = Abort(; name="ab", relation_id=rid3)
    rd_abort = Read(; read_type=OneOf(:abort, abort))

    # Epoch with all three read types
    epoch_mixed = Epoch(; writes=Write[], reads=[rd_demand, rd_output, rd_abort])
    ids = collect_demanded_relations(epoch_mixed)
    @test ids == Set([persistent_id(rid1), persistent_id(rid2), persistent_id(rid3)])

    # Duplicate relation IDs are deduplicated
    demand2 = Demand(; relation_id=rid1)
    rd_demand2 = Read(; read_type=OneOf(:demand, demand2))
    epoch_dup = Epoch(; writes=Write[], reads=[rd_demand, rd_demand2])
    @test length(collect_demanded_relations(epoch_dup)) == 1

    # CSV export collects column data relation IDs
    col1 = ExportCSVColumn(; column_name="a", column_data=rid1)
    col2 = ExportCSVColumn(; column_name="b", column_data=rid2)
    csv_config = ExportCSVConfig(; path="/tmp/out", data_columns=[col1, col2])
    export_csv = Export(; export_config=OneOf(:csv_config, csv_config))
    rd_export_csv = Read(; read_type=OneOf(:var"#export", export_csv))
    epoch_csv = Epoch(; writes=Write[], reads=[rd_export_csv])
    csv_ids = collect_demanded_relations(epoch_csv)
    @test csv_ids == Set([persistent_id(rid1), persistent_id(rid2)])

    # CSV export skips columns without column_data
    col_no_data = ExportCSVColumn(; column_name="c")
    csv_config2 = ExportCSVConfig(; path="/tmp/out", data_columns=[col1, col_no_data])
    export_csv2 = Export(; export_config=OneOf(:csv_config, csv_config2))
    rd_export_csv2 = Read(; read_type=OneOf(:var"#export", export_csv2))
    epoch_csv2 = Epoch(; writes=Write[], reads=[rd_export_csv2])
    @test collect_demanded_relations(epoch_csv2) == Set([persistent_id(rid1)])

    # Iceberg export collects table_def relation ID
    loc = IcebergLocator(; table_name="t", namespace=["n"], warehouse="w")
    cfg = IcebergCatalogConfig(;
        catalog_uri="uri", scope="", properties=Dict(), auth_properties=Dict(),
    )
    iceberg_config = ExportIcebergConfig(; locator=loc, config=cfg, table_def=rid4)
    export_iceberg = Export(; export_config=OneOf(:iceberg_config, iceberg_config))
    rd_export_ice = Read(; read_type=OneOf(:var"#export", export_iceberg))
    epoch_ice = Epoch(; writes=Write[], reads=[rd_export_ice])
    @test collect_demanded_relations(epoch_ice) == Set([persistent_id(rid4)])

    # Export with no export_config is handled gracefully
    export_empty = Export()
    rd_export_empty = Read(; read_type=OneOf(:var"#export", export_empty))
    epoch_empty_export = Epoch(; writes=Write[], reads=[rd_export_empty])
    @test collect_demanded_relations(epoch_empty_export) == Set{LQPRelationId}()
end

@testitem "read_lqp" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: read_lqp
    using LogicalQueryProtocol.relationalai.lqp.v1: Transaction

    lqp_dir = joinpath(@__DIR__, "lqp")
    @test isdir(lqp_dir)

    txn = read_lqp(joinpath(lqp_dir, "arithmetic.lqp"))
    @test txn isa Transaction
    @test length(txn.epochs) >= 1
end

@testitem "read_bin" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: read_bin
    using LogicalQueryProtocol.relationalai.lqp.v1: Transaction

    bin_dir = joinpath(@__DIR__, "bin")
    @test isdir(bin_dir)

    txn = read_bin(joinpath(bin_dir, "arithmetic.bin"))
    @test txn isa Transaction
    @test length(txn.epochs) >= 1
end

@testitem "read_lqp and read_bin agree" tags = [:ring1, :unit] begin
    using LogicalQueryProtocol: read_lqp, read_bin

    lqp_dir = joinpath(@__DIR__, "lqp")
    bin_dir = joinpath(@__DIR__, "bin")

    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(lqp_dir)))
    @test !isempty(lqp_files)

    for lqp_file in lqp_files
        bin_file = replace(lqp_file, ".lqp" => ".bin")
        bin_path = joinpath(bin_dir, bin_file)
        isfile(bin_path) || continue

        txn_lqp = read_lqp(joinpath(lqp_dir, lqp_file))
        txn_bin = read_bin(bin_path)
        @test txn_lqp == txn_bin
    end
end
