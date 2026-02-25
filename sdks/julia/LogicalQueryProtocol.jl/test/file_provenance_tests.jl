@testitem "File provenance - spans valid" setup=[ParserSetup] begin
    test_files_dir = joinpath(@__DIR__, "lqp")
    @test isdir(test_files_dir)

    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))
    @test !isempty(lqp_files)

    for lqp_file in lqp_files
        lqp_path = joinpath(test_files_dir, lqp_file)
        content = read(lqp_path, String)
        _, provenance = Parser.parse(content)

        @test !isempty(provenance)

        for (path, span) in provenance
            # start <= end
            @test span.start.offset <= span.stop.offset
            # offsets in range (1-based byte offsets in Julia)
            @test 1 <= span.start.offset <= ncodeunits(content) + 1
            @test 1 <= span.stop.offset <= ncodeunits(content) + 1
            # lines are 1-based
            @test span.start.line >= 1
            # columns are 1-based
            @test span.start.column >= 1
        end
    end
end

@testitem "File provenance - root spans transaction" setup=[ParserSetup] begin
    test_files_dir = joinpath(@__DIR__, "lqp")
    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))

    for lqp_file in lqp_files
        lqp_path = joinpath(test_files_dir, lqp_file)
        content = read(lqp_path, String)
        _, provenance = Parser.parse(content)

        @test haskey(provenance, ())
        root_span = provenance[()]
        # Use codeunits for byte-based slicing to handle Unicode correctly
        text = String(codeunits(content)[root_span.start.offset:root_span.stop.offset - 1])
        @test startswith(text, "(transaction")
    end
end

@testitem "File provenance - epoch text" setup=[ParserSetup] begin
    test_files_dir = joinpath(@__DIR__, "lqp")
    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))

    for lqp_file in lqp_files
        lqp_path = joinpath(test_files_dir, lqp_file)
        content = read(lqp_path, String)
        _, provenance = Parser.parse(content)

        epoch_count = 0
        idx = 0
        while true
            key = (1, idx)
            haskey(provenance, key) || break
            span = provenance[key]
            text = String(codeunits(content)[span.start.offset:span.stop.offset - 1])
            @test startswith(text, "(epoch")
            epoch_count += 1
            idx += 1
        end
        @test epoch_count > 0
    end
end

@testitem "File provenance - offsets match line and column" setup=[ParserSetup] begin
    test_files_dir = joinpath(@__DIR__, "lqp")
    lqp_files = sort(filter(f -> endswith(f, ".lqp"), readdir(test_files_dir)))

    for lqp_file in lqp_files
        lqp_path = joinpath(test_files_dir, lqp_file)
        content = read(lqp_path, String)
        _, provenance = Parser.parse(content)

        # Build line offset table (1-based byte offsets for Julia)
        bytes = codeunits(content)
        line_starts = [1]
        for i in 1:length(bytes)
            if bytes[i] == UInt8('\n') && i < length(bytes)
                push!(line_starts, i + 1)
            end
        end

        for (path, span) in provenance
            loc = span.start
            if 1 <= loc.line <= length(line_starts)
                expected_offset = line_starts[loc.line] + (loc.column - 1)
                @test loc.offset == expected_offset
            end
        end
    end
end
