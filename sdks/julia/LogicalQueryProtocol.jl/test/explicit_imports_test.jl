@testitem "ExplicitImports" begin
    using ExplicitImports: check_no_stale_explicit_imports,
        check_all_explicit_imports_via_owners, check_all_qualified_accesses_via_owners
    using LogicalQueryProtocol: LogicalQueryProtocol

    # check_no_implicit_imports is skipped because the root module intentionally uses
    # `using .relationalai.lqp.v1` (auto-generated protobuf code) which brings in
    # hundreds of implicit imports by design.

    # Names re-exported from Parser and Pretty submodules for the public API.
    reexported_names = (
        # Parser
        :parse, :ParseError, :Lexer, :ParserState,
        :scan_string, :scan_int, :scan_float, :scan_int128, :scan_uint128, :scan_decimal,
        # Pretty
        :PrettyPrinter, :ConstantFormatter, :DefaultConstantFormatter,
        :format_decimal, :format_int128, :format_uint128, :format_int, :format_float,
        :format_string, :format_bool, :format_string_value, :format_float64,
        :_pprint_dispatch, :get_output, :pprint, :pretty, :pretty_debug,
        Symbol("indent!"), Symbol("dedent!"), Symbol("indent_sexp!"),
        :indent_level, :try_flat,
    )

    try
        check_no_stale_explicit_imports(
            LogicalQueryProtocol;
            ignore=reexported_names,
            allow_unanalyzable=(LogicalQueryProtocol.MaintenanceLevel,),
        )
        check_all_explicit_imports_via_owners(LogicalQueryProtocol)
        check_all_qualified_accesses_via_owners(
            LogicalQueryProtocol;
            ignore=(
                :skip, # see https://github.com/JuliaIO/ProtoBuf.jl/pull/271
            ),
        )
        @test true
    catch e
        using ExplicitImports: print_explicit_imports
        print_explicit_imports(LogicalQueryProtocol)
        rethrow()
    end
end
